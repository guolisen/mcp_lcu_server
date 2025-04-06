#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for process information and operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.process import ProcessOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


def register_process_tools(mcp: FastMCP, config: Config) -> None:
    """Register process tools with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create process operations instance with configuration
    process_ops = ProcessOperations(
        allow_kill=config.process.allow_kill,
        allowed_users=config.process.allowed_users
    )
    
    @mcp.tool()
    def list_processes(include_threads: bool = False, 
                      include_username: bool = True,
                      filter_user: Optional[str] = None,
                      sort_by: str = "cpu_percent") -> str:
        """List all processes.
        
        Args:
            include_threads: Whether to include threads
            include_username: Whether to include username
            filter_user: Filter processes by username
            sort_by: Sort processes by this field (cpu_percent, memory_percent, pid, name)
        
        Returns:
            JSON string with list of processes
        """
        logger.info(f"Listing processes (include_threads={include_threads}, include_username={include_username}, filter_user={filter_user}, sort_by={sort_by})")
        
        try:
            processes = process_ops.list_processes(
                include_threads=include_threads,
                include_username=include_username,
                filter_user=filter_user,
                sort_by=sort_by
            )
            
            return json.dumps(processes, indent=2)
        except Exception as e:
            logger.error(f"Error listing processes: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_process_info(pid: int, include_threads: bool = True) -> str:
        """Get detailed information about a process.
        
        Args:
            pid: Process ID
            include_threads: Whether to include threads information
        
        Returns:
            JSON string with process information
        """
        logger.info(f"Getting process info for PID {pid}")
        
        try:
            process_info = process_ops.get_process_info(pid, include_threads=include_threads)
            
            if not process_info:
                return json.dumps({"error": f"Process with PID {pid} not found"})
            
            return json.dumps(process_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting process info: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def list_threads(pid: int) -> str:
        """List threads for a process.
        
        Args:
            pid: Process ID
        
        Returns:
            JSON string with thread information
        """
        logger.info(f"Listing threads for PID {pid}")
        
        try:
            threads = process_ops.list_threads(pid)
            
            if threads is None:
                return json.dumps({"error": f"Process with PID {pid} not found or access denied"})
            
            return json.dumps(threads, indent=2)
        except Exception as e:
            logger.error(f"Error listing threads: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def kill_process(pid: int, signal_name: str = "SIGTERM") -> str:
        """Kill a process.
        
        Args:
            pid: Process ID
            signal_name: Signal name or number (SIGTERM, SIGKILL, etc.)
        
        Returns:
            JSON string with result
        """
        logger.info(f"Killing process with PID {pid} with signal {signal_name}")
        
        try:
            if not config.process.allow_kill:
                return json.dumps({"error": "Process killing is not allowed by configuration", "success": False})
            
            success = process_ops.kill_process(pid, signal_name)
            
            if success:
                return json.dumps({"message": f"Process with PID {pid} killed successfully", "success": True})
            else:
                return json.dumps({"error": f"Failed to kill process with PID {pid}", "success": False})
        except Exception as e:
            logger.error(f"Error killing process: {e}")
            return json.dumps({"error": str(e), "success": False})
    
    @mcp.tool()
    def search_processes(name: Optional[str] = None,
                        cmdline: Optional[str] = None,
                        username: Optional[str] = None,
                        include_threads: bool = False) -> str:
        """Search for processes by name, command line or username.
        
        Args:
            name: Process name pattern (regular expression)
            cmdline: Command line pattern (regular expression)
            username: Username pattern (regular expression)
            include_threads: Whether to include thread information
        
        Returns:
            JSON string with matching processes
        """
        logger.info(f"Searching processes (name={name}, cmdline={cmdline}, username={username})")
        
        try:
            processes = process_ops.search_processes(
                name=name,
                cmdline=cmdline,
                username=username,
                include_threads=include_threads
            )
            
            return json.dumps(processes, indent=2)
        except Exception as e:
            logger.error(f"Error searching processes: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_process_tree(pid: Optional[int] = None) -> str:
        """Get process tree.
        
        Args:
            pid: Root process ID (if None, get the entire process tree)
        
        Returns:
            JSON string with process tree
        """
        logger.info(f"Getting process tree (pid={pid})")
        
        try:
            process_tree = process_ops.get_process_tree(pid)
            
            return json.dumps(process_tree, indent=2)
        except Exception as e:
            logger.error(f"Error getting process tree: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_process_limits(pid: int) -> str:
        """Get process resource limits.
        
        Args:
            pid: Process ID
        
        Returns:
            JSON string with process resource limits
        """
        logger.info(f"Getting process limits for PID {pid}")
        
        try:
            limits = process_ops.get_process_limits(pid)
            
            if not limits:
                return json.dumps({"error": f"Could not get limits for process with PID {pid}"})
            
            return json.dumps(limits, indent=2)
        except Exception as e:
            logger.error(f"Error getting process limits: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def analyze_top_processes(count: int = 10, include_threads: bool = False) -> str:
        """Analyze top processes by CPU and memory usage.
        
        Args:
            count: Number of processes to include
            include_threads: Whether to include thread information
        
        Returns:
            JSON string with detailed analysis of top processes
        """
        logger.info(f"Analyzing top {count} processes")
        
        try:
            # Get top processes by CPU usage
            processes_by_cpu = process_ops.list_processes(
                include_threads=include_threads,
                include_username=True,
                sort_by="cpu_percent"
            )[:count]
            
            # Get top processes by memory usage
            processes_by_memory = process_ops.list_processes(
                include_threads=include_threads,
                include_username=True,
                sort_by="memory_percent"
            )[:count]
            
            # Get detailed info for each unique process
            unique_pids = set()
            detailed_processes = {}
            
            for proc in processes_by_cpu + processes_by_memory:
                pid = proc.get("pid")
                if pid is not None and pid not in unique_pids:
                    unique_pids.add(pid)
                    try:
                        info = process_ops.get_process_info(pid, include_threads=include_threads)
                        if info:
                            detailed_processes[str(pid)] = info
                    except Exception:
                        pass
            
            # Create analysis report
            analysis = {
                "top_cpu_processes": processes_by_cpu,
                "top_memory_processes": processes_by_memory,
                "detailed_processes": detailed_processes,
                "summary": {
                    "total_cpu_usage": sum(p.get("cpu_percent", 0) for p in processes_by_cpu),
                    "total_memory_usage": sum(p.get("memory_percent", 0) for p in processes_by_memory),
                    "top_process_by_cpu": processes_by_cpu[0]["name"] if processes_by_cpu else None,
                    "top_process_by_memory": processes_by_memory[0]["name"] if processes_by_memory else None
                }
            }
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing top processes: {e}")
            return json.dumps({"error": str(e)})
