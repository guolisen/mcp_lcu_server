#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 15, 2025
#
# Description: MCP tools for Linux user information and operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.user import UserOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


def register_user_tools(mcp: FastMCP, config: Config) -> None:
    """Register user tools with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create user operations instance with configuration
    user_ops = UserOperations(
        enable_history=config.user.enable_history,
        max_history_entries=config.user.max_history_entries,
        allowed_users=config.user.allowed_users
    )
    
    @mcp.tool()
    def user_list_logged_in(include_details: bool = True) -> str:
        """List currently logged-in users.
        
        Args:
            include_details: Whether to include detailed information
        
        Returns:
            JSON string with list of logged-in users
        """
        logger.info(f"Listing logged-in users (include_details={include_details})")
        
        try:
            users = user_ops.list_logged_in_users(include_details=include_details)
            
            return json.dumps({
                "count": len(users),
                "users": users
            }, indent=2)
        except Exception as e:
            logger.error(f"Error listing logged-in users: {e}")
            return json.dumps({
                "error": str(e),
                "count": 0,
                "users": []
            })
    
    @mcp.tool()
    def user_get_login_history(username: Optional[str] = None, 
                             limit: Optional[int] = None,
                             include_failed: bool = False) -> str:
        """Get login history for a user or all users.
        
        Args:
            username: Username (if None, get history for all users)
            limit: Maximum number of entries to return (if None, use max_history_entries)
            include_failed: Whether to include failed login attempts
        
        Returns:
            JSON string with login history
        """
        logger.info(f"Getting login history (username={username}, limit={limit}, include_failed={include_failed})")
        
        try:
            if not config.user.enable_history:
                return json.dumps({
                    "error": "Login history retrieval is disabled by configuration",
                    "count": 0,
                    "history": []
                })
            
            history = user_ops.get_login_history(
                username=username,
                limit=limit,
                include_failed=include_failed
            )
            
            return json.dumps({
                "count": len(history),
                "history": history
            }, indent=2)
        except Exception as e:
            logger.error(f"Error getting login history: {e}")
            return json.dumps({
                "error": str(e),
                "count": 0,
                "history": []
            })
    
    @mcp.tool()
    def user_get_info(username: str) -> str:
        """Get detailed information about a user.
        
        Args:
            username: Username
        
        Returns:
            JSON string with user information
        """
        logger.info(f"Getting user info for {username}")
        
        try:
            # Skip if not in allowed users
            if config.user.allowed_users and username not in config.user.allowed_users:
                return json.dumps({
                    "error": f"User {username} is not in allowed users list"
                })
            
            user_info = user_ops.get_user_info(username)
            
            if not user_info:
                return json.dumps({
                    "error": f"User {username} not found or access denied"
                })
            
            return json.dumps(user_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return json.dumps({
                "error": str(e)
            })
    
    @mcp.tool()
    def user_search(name_pattern: Optional[str] = None,
                  uid_min: Optional[int] = None,
                  uid_max: Optional[int] = None,
                  group: Optional[str] = None,
                  shell: Optional[str] = None) -> str:
        """Search users by various criteria.
        
        Args:
            name_pattern: Username pattern (regular expression)
            uid_min: Minimum UID
            uid_max: Maximum UID
            group: Group name
            shell: Shell path
        
        Returns:
            JSON string with matching users
        """
        logger.info(f"Searching users (name_pattern={name_pattern}, uid_min={uid_min}, uid_max={uid_max}, group={group}, shell={shell})")
        
        try:
            users = user_ops.search_users(
                name_pattern=name_pattern,
                uid_min=uid_min,
                uid_max=uid_max,
                group=group,
                shell=shell
            )
            
            return json.dumps({
                "count": len(users),
                "users": users
            }, indent=2)
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return json.dumps({
                "error": str(e),
                "count": 0,
                "users": []
            })
    
    @mcp.tool()
    def user_analyze_logins(username: Optional[str] = None, 
                          days: int = 7,
                          include_failed: bool = True) -> str:
        """Analyze login patterns for a user or all users.
        
        Args:
            username: Username (if None, analyze all users)
            days: Number of days to analyze
            include_failed: Whether to include failed login attempts
        
        Returns:
            JSON string with login analysis
        """
        logger.info(f"Analyzing logins (username={username}, days={days}, include_failed={include_failed})")
        
        try:
            if not config.user.enable_history:
                return json.dumps({
                    "error": "Login history retrieval is disabled by configuration"
                })
            
            # Get login history
            history = user_ops.get_login_history(
                username=username,
                limit=None,  # No limit for analysis
                include_failed=include_failed
            )
            
            # Filter by date (last N days)
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            recent_history = [
                entry for entry in history 
                if entry.get("login_time") and entry.get("login_time") >= cutoff_date
            ]
            
            # Group by username
            users_data = {}
            for entry in recent_history:
                username = entry.get("username")
                if not username:
                    continue
                
                if username not in users_data:
                    users_data[username] = {
                        "total_logins": 0,
                        "successful_logins": 0,
                        "failed_logins": 0,
                        "hosts": set(),
                        "ttys": set(),
                        "first_login": None,
                        "last_login": None
                    }
                
                # Update user data
                user_data = users_data[username]
                user_data["total_logins"] += 1
                
                if entry.get("failed", False):
                    user_data["failed_logins"] += 1
                else:
                    user_data["successful_logins"] += 1
                
                if entry.get("host"):
                    user_data["hosts"].add(entry.get("host"))
                
                if entry.get("tty"):
                    user_data["ttys"].add(entry.get("tty"))
                
                login_time = entry.get("login_time")
                if login_time:
                    if not user_data["first_login"] or login_time < user_data["first_login"]:
                        user_data["first_login"] = login_time
                    
                    if not user_data["last_login"] or login_time > user_data["last_login"]:
                        user_data["last_login"] = login_time
            
            # Convert sets to lists for JSON serialization
            for username, user_data in users_data.items():
                user_data["hosts"] = list(user_data["hosts"])
                user_data["ttys"] = list(user_data["ttys"])
            
            # Create summary
            total_logins = sum(data["total_logins"] for data in users_data.values())
            total_successful = sum(data["successful_logins"] for data in users_data.values())
            total_failed = sum(data["failed_logins"] for data in users_data.values())
            
            summary = {
                "total_logins": total_logins,
                "successful_logins": total_successful,
                "failed_logins": total_failed,
                "unique_users": len(users_data),
                "period_days": days
            }
            
            # Add success rate if there are any logins
            if total_logins > 0:
                summary["success_rate"] = round(total_successful / total_logins * 100, 2)
            
            # Create analysis result
            analysis = {
                "summary": summary,
                "users": users_data
            }
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing logins: {e}")
            return json.dumps({
                "error": str(e)
            })
