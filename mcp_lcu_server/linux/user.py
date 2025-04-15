#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 15, 2025
#
# Description: User operations module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import pwd
import grp
import time
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class UserOperations:
    """Class for user operations on Linux systems."""
    
    def __init__(self, 
                enable_history: bool = True,
                max_history_entries: int = 100,
                allowed_users: Optional[List[str]] = None):
        """Initialize user operations.
        
        Args:
            enable_history: Whether to enable login history retrieval
            max_history_entries: Maximum number of history entries to return
            allowed_users: List of users whose information can be retrieved (if None, all users are allowed)
        """
        self.enable_history = enable_history
        self.max_history_entries = max_history_entries
        self.allowed_users = set(allowed_users) if allowed_users else None
    
    def list_logged_in_users(self, include_details: bool = True) -> List[Dict[str, Any]]:
        """List currently logged-in users.
        
        Args:
            include_details: Whether to include detailed information
        
        Returns:
            List of dictionaries with user information
        """
        try:
            # Use 'who' command to get logged-in users
            result = subprocess.run(
                ["who", "-u"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error running 'who' command: {result.stderr}")
                return []
            
            users = []
            
            # Parse 'who' output
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                
                # Parse line (username, tty, date, time, idle, pid, host)
                parts = line.split()
                if len(parts) < 5:
                    continue
                
                username = parts[0]
                
                # Skip if not in allowed users
                if self.allowed_users and username not in self.allowed_users:
                    continue
                
                tty = parts[1]
                
                # Parse login time
                login_time_str = " ".join(parts[2:5])
                try:
                    login_time = datetime.strptime(login_time_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    try:
                        login_time = datetime.strptime(login_time_str, "%b %d %H:%M")
                        # Set year to current year
                        login_time = login_time.replace(year=datetime.now().year)
                    except ValueError:
                        login_time = None
                
                # Get idle time and PID
                idle_idx = 5
                pid_idx = 6
                host_idx = 7
                
                idle = parts[idle_idx] if len(parts) > idle_idx else ""
                pid = parts[pid_idx] if len(parts) > pid_idx else ""
                host = parts[host_idx] if len(parts) > host_idx else ""
                
                user_info = {
                    "username": username,
                    "tty": tty,
                    "login_time": login_time.isoformat() if login_time else None,
                    "idle": idle,
                    "pid": pid,
                    "host": host
                }
                
                # Add detailed information if requested
                if include_details:
                    try:
                        user_details = self.get_user_info(username)
                        if user_details:
                            user_info.update({
                                "uid": user_details.get("uid"),
                                "gid": user_details.get("gid"),
                                "home": user_details.get("home"),
                                "shell": user_details.get("shell"),
                                "gecos": user_details.get("gecos")
                            })
                    except Exception as e:
                        logger.error(f"Error getting user details for {username}: {e}")
                
                users.append(user_info)
            
            return users
        except Exception as e:
            logger.error(f"Error listing logged-in users: {e}")
            return []
    
    def get_login_history(self, 
                         username: Optional[str] = None, 
                         limit: Optional[int] = None,
                         include_failed: bool = False) -> List[Dict[str, Any]]:
        """Get login history for a user or all users.
        
        Args:
            username: Username (if None, get history for all users)
            limit: Maximum number of entries to return (if None, use max_history_entries)
            include_failed: Whether to include failed login attempts
        
        Returns:
            List of dictionaries with login history
        """
        if not self.enable_history:
            logger.error("Login history retrieval is disabled")
            return []
        
        # Use default limit if not specified
        if limit is None:
            limit = self.max_history_entries
        
        try:
            # Build 'last' command
            cmd = ["last", "-F"]
            
            # Add username if specified
            if username:
                # Skip if not in allowed users
                if self.allowed_users and username not in self.allowed_users:
                    logger.error(f"User {username} is not in allowed users list")
                    return []
                
                cmd.append(username)
            
            # Add limit
            cmd.extend(["-n", str(limit)])
            
            # Run 'last' command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error running 'last' command: {result.stderr}")
                return []
            
            history = []
            
            # Parse 'last' output
            for line in result.stdout.splitlines():
                if not line.strip() or "wtmp begins" in line:
                    continue
                
                # Parse line (username, tty, host, login_time, logout_time)
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                username = parts[0]
                
                # Skip if not in allowed users
                if self.allowed_users and username not in self.allowed_users:
                    continue
                
                tty = parts[1]
                
                # Get host (may be empty)
                host_idx = 2
                host = parts[host_idx] if len(parts) > host_idx and ":" not in parts[host_idx] else ""
                
                # Skip host index if host is present
                time_idx = host_idx + 1 if host else host_idx
                
                # Parse login time
                login_time_str = " ".join(parts[time_idx:time_idx+5])
                try:
                    login_time = datetime.strptime(login_time_str, "%a %b %d %H:%M:%S %Y")
                except ValueError:
                    login_time = None
                
                # Parse logout time
                logout_idx = time_idx + 5
                if len(parts) > logout_idx + 5 and parts[logout_idx] == "-":
                    logout_time_str = " ".join(parts[logout_idx+1:logout_idx+6])
                    try:
                        logout_time = datetime.strptime(logout_time_str, "%a %b %d %H:%M:%S %Y")
                    except ValueError:
                        logout_time = None
                else:
                    logout_time = None
                
                # Check if still logged in
                still_logged_in = "still logged in" in line
                
                history.append({
                    "username": username,
                    "tty": tty,
                    "host": host,
                    "login_time": login_time.isoformat() if login_time else None,
                    "logout_time": logout_time.isoformat() if logout_time else None,
                    "still_logged_in": still_logged_in
                })
            
            # Add failed login attempts if requested
            if include_failed:
                failed_history = self._get_failed_login_history(username, limit)
                history.extend(failed_history)
                
                # Sort by login time
                history.sort(key=lambda x: x.get("login_time", ""), reverse=True)
                
                # Apply limit
                if limit and len(history) > limit:
                    history = history[:limit]
            
            return history
        except Exception as e:
            logger.error(f"Error getting login history: {e}")
            return []
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a user.
        
        Args:
            username: Username
        
        Returns:
            Dictionary with user information or None if user not found
        """
        try:
            # Skip if not in allowed users
            if self.allowed_users and username not in self.allowed_users:
                logger.error(f"User {username} is not in allowed users list")
                return None
            
            # Get user information from passwd database
            try:
                pwd_entry = pwd.getpwnam(username)
            except KeyError:
                logger.error(f"User {username} not found")
                return None
            
            # Get user's groups
            groups = []
            for group in grp.getgrall():
                if username in group.gr_mem:
                    groups.append({
                        "name": group.gr_name,
                        "gid": group.gr_gid,
                        "members": group.gr_mem
                    })
            
            # Get primary group
            try:
                primary_group = grp.getgrgid(pwd_entry.pw_gid)
                primary_group_name = primary_group.gr_name
            except KeyError:
                primary_group_name = str(pwd_entry.pw_gid)
            
            # Get last login information
            last_login = self._get_last_login(username)
            
            # Get password information
            password_info = self._get_password_info(username)
            
            # Build user info dictionary
            user_info = {
                "username": username,
                "uid": pwd_entry.pw_uid,
                "gid": pwd_entry.pw_gid,
                "primary_group": primary_group_name,
                "groups": groups,
                "home": pwd_entry.pw_dir,
                "shell": pwd_entry.pw_shell,
                "gecos": pwd_entry.pw_gecos,
                "last_login": last_login,
                "password_info": password_info
            }
            
            return user_info
        except Exception as e:
            logger.error(f"Error getting user info for {username}: {e}")
            return None
    
    def search_users(self, 
                    name_pattern: Optional[str] = None,
                    uid_min: Optional[int] = None,
                    uid_max: Optional[int] = None,
                    group: Optional[str] = None,
                    shell: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search users by various criteria.
        
        Args:
            name_pattern: Username pattern (regular expression)
            uid_min: Minimum UID
            uid_max: Maximum UID
            group: Group name
            shell: Shell path
        
        Returns:
            List of dictionaries with user information
        """
        try:
            # Compile name pattern regex
            name_regex = re.compile(name_pattern) if name_pattern else None
            
            # Get group GID if specified
            group_gid = None
            if group:
                try:
                    group_entry = grp.getgrnam(group)
                    group_gid = group_entry.gr_gid
                except KeyError:
                    logger.error(f"Group {group} not found")
                    return []
            
            # Get all users
            users = []
            for pwd_entry in pwd.getpwall():
                username = pwd_entry.pw_name
                
                # Skip if not in allowed users
                if self.allowed_users and username not in self.allowed_users:
                    continue
                
                # Check name pattern
                if name_regex and not name_regex.search(username):
                    continue
                
                # Check UID range
                if uid_min is not None and pwd_entry.pw_uid < uid_min:
                    continue
                
                if uid_max is not None and pwd_entry.pw_uid > uid_max:
                    continue
                
                # Check group
                if group_gid is not None and pwd_entry.pw_gid != group_gid:
                    # Check if user is in the group
                    in_group = False
                    for g in grp.getgrall():
                        if g.gr_gid == group_gid and username in g.gr_mem:
                            in_group = True
                            break
                    
                    if not in_group:
                        continue
                
                # Check shell
                if shell and pwd_entry.pw_shell != shell:
                    continue
                
                # Get primary group
                try:
                    primary_group = grp.getgrgid(pwd_entry.pw_gid)
                    primary_group_name = primary_group.gr_name
                except KeyError:
                    primary_group_name = str(pwd_entry.pw_gid)
                
                # Add user to results
                users.append({
                    "username": username,
                    "uid": pwd_entry.pw_uid,
                    "gid": pwd_entry.pw_gid,
                    "primary_group": primary_group_name,
                    "home": pwd_entry.pw_dir,
                    "shell": pwd_entry.pw_shell,
                    "gecos": pwd_entry.pw_gecos
                })
            
            # Sort by username
            users.sort(key=lambda x: x["username"])
            
            return users
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    def _get_failed_login_history(self, 
                                username: Optional[str] = None, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get failed login history for a user or all users.
        
        Args:
            username: Username (if None, get history for all users)
            limit: Maximum number of entries to return
        
        Returns:
            List of dictionaries with failed login history
        """
        try:
            # Build 'lastb' command
            cmd = ["lastb", "-F"]
            
            # Add username if specified
            if username:
                # Skip if not in allowed users
                if self.allowed_users and username not in self.allowed_users:
                    return []
                
                cmd.append(username)
            
            # Add limit
            if limit:
                cmd.extend(["-n", str(limit)])
            
            # Run 'lastb' command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error running 'lastb' command: {result.stderr}")
                return []
            
            history = []
            
            # Parse 'lastb' output
            for line in result.stdout.splitlines():
                if not line.strip() or "btmp begins" in line:
                    continue
                
                # Parse line (username, tty, host, login_time)
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                username = parts[0]
                
                # Skip if not in allowed users
                if self.allowed_users and username not in self.allowed_users:
                    continue
                
                tty = parts[1]
                
                # Get host (may be empty)
                host_idx = 2
                host = parts[host_idx] if len(parts) > host_idx and ":" not in parts[host_idx] else ""
                
                # Skip host index if host is present
                time_idx = host_idx + 1 if host else host_idx
                
                # Parse login time
                login_time_str = " ".join(parts[time_idx:time_idx+5])
                try:
                    login_time = datetime.strptime(login_time_str, "%a %b %d %H:%M:%S %Y")
                except ValueError:
                    login_time = None
                
                history.append({
                    "username": username,
                    "tty": tty,
                    "host": host,
                    "login_time": login_time.isoformat() if login_time else None,
                    "logout_time": None,
                    "still_logged_in": False,
                    "failed": True
                })
            
            return history
        except Exception as e:
            logger.error(f"Error getting failed login history: {e}")
            return []
    
    def _get_last_login(self, username: str) -> Optional[Dict[str, Any]]:
        """Get last login information for a user.
        
        Args:
            username: Username
        
        Returns:
            Dictionary with last login information or None if not available
        """
        try:
            # Skip if not in allowed users
            if self.allowed_users and username not in self.allowed_users:
                return None
            
            # Run 'lastlog' command
            result = subprocess.run(
                ["lastlog", "-u", username],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error running 'lastlog' command: {result.stderr}")
                return None
            
            # Parse 'lastlog' output
            lines = result.stdout.splitlines()
            if len(lines) < 2:
                return None
            
            # Skip header line
            line = lines[1]
            
            # Parse line (username, port, from, latest)
            parts = line.split()
            if len(parts) < 4:
                return None
            
            username = parts[0]
            
            # Check if never logged in
            if "**Never logged in**" in line:
                return {
                    "username": username,
                    "port": None,
                    "host": None,
                    "time": None,
                    "never_logged_in": True
                }
            
            port = parts[1]
            host = parts[2]
            
            # Parse login time
            time_str = " ".join(parts[3:])
            try:
                login_time = datetime.strptime(time_str, "%a %b %d %H:%M:%S %z %Y")
            except ValueError:
                login_time = None
            
            return {
                "username": username,
                "port": port,
                "host": host,
                "time": login_time.isoformat() if login_time else None,
                "never_logged_in": False
            }
        except Exception as e:
            logger.error(f"Error getting last login for {username}: {e}")
            return None
    
    def _get_password_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get password information for a user.
        
        Args:
            username: Username
        
        Returns:
            Dictionary with password information or None if not available
        """
        try:
            # Skip if not in allowed users
            if self.allowed_users and username not in self.allowed_users:
                return None
            
            # Run 'chage' command
            result = subprocess.run(
                ["chage", "-l", username],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Error running 'chage' command: {result.stderr}")
                return None
            
            # Parse 'chage' output
            info = {}
            
            for line in result.stdout.splitlines():
                if ":" not in line:
                    continue
                
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                
                info[key] = value
            
            return info
        except Exception as e:
            logger.error(f"Error getting password info for {username}: {e}")
            return None
