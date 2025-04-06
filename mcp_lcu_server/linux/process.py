#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Process operations module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import time
import signal
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple, Set

import psutil

logger = logging.getLogger(__name__)


class ProcessOperations:
    """Class for process operations on Linux systems."""
    
    def __init__(self, allow_kill: bool = False, allowed_users: Optional[List[str]] = None):
        """Initialize process operations.
        
        Args:
            allow_kill: Whether to allow killing processes
            allowed_users: List of users whose processes can be killed (if None, all users are allowed)
        """
        self.allow_kill = allow_kill
        self.allowed_users = set(allowed_users) if allowed_users else None
    
    def list_processes(self, 
                      include_threads: bool = False, 
                      include_username: bool = True,
                      filter_user: Optional[str] = None,
                      sort_by: str = "cpu_percent") -> List[Dict[str, Any]]:
        """List all processes.
        
        Args:
            include_threads: Whether to include threads
            include_username: Whether to include username
            filter_user: Filter processes by username
            sort_by: Sort processes by this field (cpu_percent, memory_percent, pid, name)
        
        Returns:
            List of dictionaries with process information
        """
        try:
            processes = []
            
            # Get all processes
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'status', 
                                           'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    # Skip if filtering by username and doesn't match
                    if filter_user and proc.info['username'] != filter_user:
                        continue
                    
                    # Create process info dictionary
                    process_info = {
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "status": proc.info['status'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent'],
                        "create_time": proc.info['create_time'],
                    }
                    
                    # Add cmdline if available
                    if proc.info['cmdline']:
                        process_info["cmdline"] = ' '.join(proc.info['cmdline'])
                    
                    # Add username if requested
                    if include_username:
                        process_info["username"] = proc.info['username']
                    
                    # Add threads if requested
                    if include_threads:
                        try:
                            # Get threads information
                            threads = proc.threads()
                            process_info["threads"] = [{"id": t.id, "user_time": t.user_time, 
                                                      "system_time": t.system_time} 
                                                     for t in threads]
                            process_info["num_threads"] = len(threads)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_info["threads"] = []
                            process_info["num_threads"] = 0
                    
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Skip processes that no longer exist or can't be accessed
                    pass
            
            # Sort processes by the specified field
            if sort_by == "cpu_percent":
                processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
            elif sort_by == "memory_percent":
                processes.sort(key=lambda x: x.get("memory_percent", 0), reverse=True)
            elif sort_by == "pid":
                processes.sort(key=lambda x: x.get("pid", 0))
            elif sort_by == "name":
                processes.sort(key=lambda x: x.get("name", "").lower())
            
            return processes
        except Exception as e:
            logger.error(f"Error listing processes: {e}")
            return []
    
    def get_process_info(self, pid: int, include_threads: bool = True) -> Optional[Dict[str, Any]]:
        """Get detailed information about a process.
        
        Args:
            pid: Process ID
            include_threads: Whether to include threads information
        
        Returns:
            Dictionary with process information or None if process not found
        """
        try:
            # Get process by PID
            proc = psutil.Process(pid)
            
            # Get basic process information
            info = {
                "pid": proc.pid,
                "ppid": proc.ppid(),
                "name": proc.name(),
                "exe": proc.exe(),
                "cmdline": proc.cmdline(),
                "status": proc.status(),
                "username": proc.username(),
                "create_time": proc.create_time(),
                "terminal": proc.terminal(),
                "cwd": proc.cwd(),
                "uids": {
                    "real": proc.uids().real,
                    "effective": proc.uids().effective,
                    "saved": proc.uids().saved
                },
                "gids": {
                    "real": proc.gids().real,
                    "effective": proc.gids().effective,
                    "saved": proc.gids().saved
                },
                "cpu_times": {
                    "user": proc.cpu_times().user,
                    "system": proc.cpu_times().system,
                    "children_user": getattr(proc.cpu_times(), "children_user", 0),
                    "children_system": getattr(proc.cpu_times(), "children_system", 0),
                    "iowait": getattr(proc.cpu_times(), "iowait", 0)
                },
                "cpu_percent": proc.cpu_percent(),
                "cpu_affinity": proc.cpu_affinity(),
                "memory_info": {
                    "rss": proc.memory_info().rss,
                    "vms": proc.memory_info().vms,
                    "shared": getattr(proc.memory_info(), "shared", 0),
                    "text": getattr(proc.memory_info(), "text", 0),
                    "data": getattr(proc.memory_info(), "data", 0),
                    "lib": getattr(proc.memory_info(), "lib", 0),
                    "dirty": getattr(proc.memory_info(), "dirty", 0)
                },
                "memory_percent": proc.memory_percent(),
                "children": [child.pid for child in proc.children()],
                "open_files": [{"path": f.path, "fd": f.fd, "position": f.position, "mode": f.mode}
                              for f in proc.open_files()],
                "connections": [{"fd": c.fd, "family": c.family, "type": c.type,
                               "local_addr": f"{c.laddr.ip}:{c.laddr.port}" if hasattr(c.laddr, "ip") else str(c.laddr),
                               "remote_addr": f"{c.raddr.ip}:{c.raddr.port}" if hasattr(c.raddr, "ip") and c.raddr else None,
                               "status": c.status}
                              for c in proc.connections()]
            }
            
            # Add human readable fields
            info["memory_info"]["rss_human"] = self._bytes_to_human(info["memory_info"]["rss"])
            info["memory_info"]["vms_human"] = self._bytes_to_human(info["memory_info"]["vms"])
            
            # Add thread information if requested
            if include_threads:
                threads = proc.threads()
                info["threads"] = [{"id": t.id, "user_time": t.user_time, "system_time": t.system_time}
                                 for t in threads]
                info["num_threads"] = len(threads)
            
            # Try to get process niceness
            try:
                info["nice"] = proc.nice()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            # Try to get process IO counters
            try:
                io = proc.io_counters()
                info["io_counters"] = {
                    "read_count": io.read_count,
                    "write_count": io.write_count,
                    "read_bytes": io.read_bytes,
                    "write_bytes": io.write_bytes,
                    "read_bytes_human": self._bytes_to_human(io.read_bytes),
                    "write_bytes_human": self._bytes_to_human(io.write_bytes)
                }
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            # Try to get process limits
            try:
                limits = self._get_process_limits(pid)
                if limits:
                    info["limits"] = limits
            except Exception:
                pass
            
            # Try to get process environment
            try:
                env = proc.environ()
                info["environ"] = env
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            return info
        except psutil.NoSuchProcess:
            logger.error(f"Process with PID {pid} not found")
            return None
        except psutil.AccessDenied:
            logger.error(f"Access denied to process with PID {pid}")
            # Return partial information
            return {"pid": pid, "error": "Access denied"}
        except Exception as e:
            logger.error(f"Error getting process info for PID {pid}: {e}")
            return None
    
    def list_threads(self, pid: int) -> Optional[List[Dict[str, Any]]]:
        """List threads for a process.
        
        Args:
            pid: Process ID
        
        Returns:
            List of dictionaries with thread information or None if process not found
        """
        try:
            # Get process by PID
            proc = psutil.Process(pid)
            
            # Get threads
            threads = proc.threads()
            
            # Format thread information
            thread_info = []
            for thread in threads:
                thread_info.append({
                    "id": thread.id,
                    "user_time": thread.user_time,
                    "system_time": thread.system_time,
                    "total_time": thread.user_time + thread.system_time
                })
            
            # Sort by total time
            thread_info.sort(key=lambda x: x["total_time"], reverse=True)
            
            return thread_info
        except psutil.NoSuchProcess:
            logger.error(f"Process with PID {pid} not found")
            return None
        except psutil.AccessDenied:
            logger.error(f"Access denied to process with PID {pid}")
            return None
        except Exception as e:
            logger.error(f"Error listing threads for PID {pid}: {e}")
            return None
    
    def kill_process(self, pid: int, signal_name: str = "SIGTERM") -> bool:
        """Kill a process.
        
        Args:
            pid: Process ID
            signal_name: Signal name or number (SIGTERM, SIGKILL, etc.)
        
        Returns:
            Whether the process was killed successfully
        """
        if not self.allow_kill:
            logger.error("Process killing is not allowed")
            return False
        
        try:
            # Get process by PID
            proc = psutil.Process(pid)
            
            # Check if allowed to kill this process
            if self.allowed_users and proc.username() not in self.allowed_users:
                logger.error(f"Not allowed to kill process with PID {pid} owned by {proc.username()}")
                return False
            
            # Get signal number
            sig = self._get_signal_number(signal_name)
            
            # Send signal to process
            proc.send_signal(sig)
            
            # Check if process is still running
            time.sleep(0.1)
            if not psutil.pid_exists(pid):
                return True
            
            # Process is still running
            proc = psutil.Process(pid)
            if proc.status() == psutil.STATUS_ZOMBIE:
                return True
            
            return False
        except psutil.NoSuchProcess:
            logger.error(f"Process with PID {pid} not found")
            return False
        except psutil.AccessDenied:
            logger.error(f"Access denied to process with PID {pid}")
            return False
        except Exception as e:
            logger.error(f"Error killing process with PID {pid}: {e}")
            return False
    
    def search_processes(self, 
                        name: Optional[str] = None,
                        cmdline: Optional[str] = None,
                        username: Optional[str] = None,
                        include_threads: bool = False) -> List[Dict[str, Any]]:
        """Search for processes by name, command line or username.
        
        Args:
            name: Process name pattern (regular expression)
            cmdline: Command line pattern (regular expression)
            username: Username pattern (regular expression)
            include_threads: Whether to include thread information
        
        Returns:
            List of dictionaries with process information
        """
        try:
            processes = []
            
            # Compile regular expressions
            name_regex = re.compile(name, re.IGNORECASE) if name else None
            cmdline_regex = re.compile(cmdline, re.IGNORECASE) if cmdline else None
            username_regex = re.compile(username, re.IGNORECASE) if username else None
            
            # Get all processes
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'status',
                                           'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    # Check if process matches criteria
                    if name_regex and not name_regex.search(proc.info['name']):
                        continue
                    
                    cmdline_str = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if cmdline_regex and not cmdline_regex.search(cmdline_str):
                        continue
                    
                    if username_regex and not username_regex.search(proc.info['username']):
                        continue
                    
                    # Create process info dictionary
                    process_info = {
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "username": proc.info['username'],
                        "cmdline": cmdline_str,
                        "status": proc.info['status'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent'],
                        "create_time": proc.info['create_time'],
                    }
                    
                    # Add threads if requested
                    if include_threads:
                        try:
                            # Get threads information
                            threads = proc.threads()
                            process_info["threads"] = [{"id": t.id, "user_time": t.user_time,
                                                      "system_time": t.system_time}
                                                     for t in threads]
                            process_info["num_threads"] = len(threads)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_info["threads"] = []
                            process_info["num_threads"] = 0
                    
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Skip processes that no longer exist or can't be accessed
                    pass
            
            # Sort processes by CPU usage
            processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
            
            return processes
        except Exception as e:
            logger.error(f"Error searching processes: {e}")
            return []
    
    def get_process_tree(self, pid: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get process tree.
        
        Args:
            pid: Root process ID (if None, get the entire process tree)
        
        Returns:
            List of dictionaries with process tree information
        """
        try:
            # Get process by PID if provided
            if pid:
                try:
                    proc = psutil.Process(pid)
                    root_processes = [proc]
                except psutil.NoSuchProcess:
                    logger.error(f"Process with PID {pid} not found")
                    return []
                except psutil.AccessDenied:
                    logger.error(f"Access denied to process with PID {pid}")
                    return []
            else:
                # Get all processes with PPID 1 (direct children of init)
                root_processes = [proc for proc in psutil.process_iter() if proc.ppid() <= 1]
            
            # Build process tree
            process_tree = []
            for root_proc in root_processes:
                tree = self._build_process_subtree(root_proc)
                if tree:
                    process_tree.append(tree)
            
            return process_tree
        except Exception as e:
            logger.error(f"Error getting process tree: {e}")
            return []
    
    def get_process_limits(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process resource limits.
        
        Args:
            pid: Process ID
        
        Returns:
            Dictionary with process resource limits
        """
        return self._get_process_limits(pid)
    
    def _build_process_subtree(self, proc: psutil.Process) -> Optional[Dict[str, Any]]:
        """Build process subtree recursively.
        
        Args:
            proc: Process
        
        Returns:
            Dictionary with process subtree information
        """
        try:
            # Get process information
            process_info = {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "username": proc.username(),
                "cmdline": ' '.join(proc.cmdline()) if proc.cmdline() else '',
                "children": []
            }
            
            # Get children recursively
            for child in proc.children():
                child_tree = self._build_process_subtree(child)
                if child_tree:
                    process_info["children"].append(child_tree)
            
            return process_info
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Skip processes that no longer exist or can't be accessed
            return None
        except Exception as e:
            logger.error(f"Error building process subtree for PID {proc.pid}: {e}")
            return None
    
    def _get_process_limits(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get process resource limits from /proc/<pid>/limits.
        
        Args:
            pid: Process ID
        
        Returns:
            Dictionary with process resource limits
        """
        try:
            # Check if process exists
            if not os.path.exists(f"/proc/{pid}"):
                return None
            
            # Read process limits
            with open(f"/proc/{pid}/limits", "r") as f:
                content = f.readlines()
            
            limits = {}
            
            # Parse limits
            for line in content[1:]:  # Skip header
                parts = line.strip().split()
                if len(parts) >= 4:
                    # Extract limit name
                    name = ' '.join(parts[:-3]).lower().replace(' ', '_')
                    
                    # Extract soft limit
                    soft = parts[-3]
                    if soft == "unlimited":
                        soft_value = float('inf')
                    else:
                        try:
                            soft_value = int(soft)
                        except ValueError:
                            soft_value = soft
                    
                    # Extract hard limit
                    hard = parts[-2]
                    if hard == "unlimited":
                        hard_value = float('inf')
                    else:
                        try:
                            hard_value = int(hard)
                        except ValueError:
                            hard_value = hard
                    
                    # Extract units
                    units = parts[-1]
                    
                    limits[name] = {
                        "soft": soft_value,
                        "hard": hard_value,
                        "units": units
                    }
            
            return limits
        except Exception as e:
            logger.error(f"Error getting process limits for PID {pid}: {e}")
            return None
    
    def _get_signal_number(self, signal_name: str) -> int:
        """Get signal number from signal name.
        
        Args:
            signal_name: Signal name or number
        
        Returns:
            Signal number
        """
        # Check if signal is already a number
        try:
            return int(signal_name)
        except ValueError:
            pass
        
        # Convert signal name to uppercase and remove "SIG" prefix
        signal_name = signal_name.upper()
        if not signal_name.startswith("SIG"):
            signal_name = "SIG" + signal_name
        
        # Get signal number
        try:
            return getattr(signal, signal_name)
        except AttributeError:
            logger.error(f"Invalid signal name: {signal_name}")
            # Default to SIGTERM
            return signal.SIGTERM
    
    def _bytes_to_human(self, bytes_value: int) -> str:
        """Convert bytes to human readable format.
        
        Args:
            bytes_value: Bytes value
        
        Returns:
            Human readable string
        """
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} EB"
