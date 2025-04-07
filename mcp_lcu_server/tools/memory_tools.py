#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for memory information and operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.memory import MemoryOperations

logger = logging.getLogger(__name__)


def register_memory_tools(mcp: FastMCP) -> None:
    """Register memory tools with the MCP server.
    
    Args:
        mcp: MCP server.
    """
    # Create memory operations instance
    memory_ops = MemoryOperations()
    
    @mcp.tool()
    def memory_get_memory_info() -> str:
        """Get detailed memory information.
        
        Returns:
            JSON string with memory information including:
            - total: Total physical memory
            - available: Available memory
            - used: Used memory
            - free: Free memory
            - percent: Percentage of memory used
            - buffers: Buffers memory
            - cached: Cached memory
            - shared: Shared memory
        """
        logger.info("Getting memory information")
        
        try:
            memory_info = memory_ops.get_memory_info()
            return json.dumps(memory_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def memory_get_memory_usage() -> str:
        """Get memory usage.
        
        Returns:
            JSON string with memory usage information:
            - total: Total physical memory
            - used: Used memory
            - free: Free memory
            - percent: Percentage of memory used
        """
        logger.info("Getting memory usage")
        
        try:
            usage = memory_ops.get_memory_usage()
            return json.dumps(usage, indent=2)
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def memory_get_swap_info() -> str:
        """Get detailed swap information.
        
        Returns:
            JSON string with swap information:
            - total: Total swap memory
            - used: Used swap memory
            - free: Free swap memory
            - percent: Percentage of swap used
            - sin: Number of bytes the system has swapped in from disk
            - sout: Number of bytes the system has swapped out to disk
            - devices: List of swap devices (if available)
        """
        logger.info("Getting swap information")
        
        try:
            swap_info = memory_ops.get_swap_info()
            return json.dumps(swap_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting swap info: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def memory_get_swap_usage() -> str:
        """Get swap usage.
        
        Returns:
            JSON string with swap usage information:
            - total: Total swap memory
            - used: Used swap memory
            - free: Free swap memory
            - percent: Percentage of swap used
        """
        logger.info("Getting swap usage")
        
        try:
            usage = memory_ops.get_swap_usage()
            return json.dumps(usage, indent=2)
        except Exception as e:
            logger.error(f"Error getting swap usage: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def memory_get_memory_stats() -> str:
        """Get comprehensive memory statistics.
        
        Returns:
            JSON string with memory statistics:
            - memory: Memory usage information
            - swap: Swap usage information
            - hugepages: Hugepages information
            - memory_distribution: Memory distribution
        """
        logger.info("Getting memory statistics")
        
        try:
            stats = memory_ops.get_memory_stats()
            return json.dumps(stats, indent=2)
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def memory_analyze_memory_performance() -> str:
        """Analyze memory performance and provide insights.
        
        This function collects comprehensive memory data and provides analysis:
        - Current memory utilization
        - Swap usage and activity
        - Memory pressure assessment
        - Identification of potential bottlenecks
        - Recommendations for performance improvement
        
        Returns:
            JSON string with memory performance analysis
        """
        logger.info("Analyzing memory performance")
        
        try:
            # Collect all memory information
            memory_info = memory_ops.get_memory_info()
            swap_info = memory_ops.get_swap_info()
            
            # Calculate memory pressure
            memory_used_percent = memory_info.get("percent", 0)
            swap_used_percent = swap_info.get("percent", 0)
            
            # Determine memory status
            memory_status = "Normal"
            if memory_used_percent > 90:
                memory_status = "Critical"
            elif memory_used_percent > 75:
                memory_status = "High"
            elif memory_used_percent > 60:
                memory_status = "Moderate"
            
            # Determine swap status
            swap_status = "Normal"
            if swap_used_percent > 75:
                swap_status = "High"
            elif swap_used_percent > 50:
                swap_status = "Moderate"
            
            # Determine if swap is active
            swap_active = False
            if (swap_info.get("sin", 0) > 0 or swap_info.get("sout", 0) > 0) and swap_info.get("total", 0) > 0:
                swap_active = True
            
            # Calculate available memory percentage
            total_memory = memory_info.get("total", 0)
            available_memory = memory_info.get("available", 0)
            available_percent = (available_memory / total_memory * 100) if total_memory > 0 else 0
            
            # Generate recommendations
            recommendations = []
            if memory_status in ["High", "Critical"]:
                recommendations.append("System is running low on memory. Consider closing unused applications or adding more RAM")
            if available_percent < 15:
                recommendations.append("Available memory is critically low, performance degradation likely")
            if swap_status == "High" and swap_active:
                recommendations.append("High swap usage indicates memory pressure. Consider increasing physical memory")
            if swap_used_percent > 90:
                recommendations.append("Swap space is nearly exhausted. Add more swap space or physical memory")
            
            # Check memory distribution
            cached_percent = (memory_info.get("cached", 0) / total_memory * 100) if total_memory > 0 else 0
            buffers_percent = (memory_info.get("buffers", 0) / total_memory * 100) if total_memory > 0 else 0
            
            if cached_percent > 50:
                recommendations.append("Large amount of memory used for cache. This is generally good for performance")
            
            # Create analysis report
            analysis = {
                "summary": {
                    "total_memory": total_memory,
                    "total_memory_human": memory_info.get("total_human", "0 B"),
                    "available_memory": available_memory,
                    "available_memory_human": memory_info.get("available_human", "0 B"),
                    "available_percent": available_percent,
                    "memory_used_percent": memory_used_percent,
                    "memory_status": memory_status,
                    "swap_used_percent": swap_used_percent,
                    "swap_status": swap_status,
                    "swap_active": swap_active
                },
                "memory_distribution": {
                    "used": (memory_info.get("used", 0) / total_memory * 100) if total_memory > 0 else 0,
                    "free": (memory_info.get("free", 0) / total_memory * 100) if total_memory > 0 else 0,
                    "cached": cached_percent,
                    "buffers": buffers_percent,
                    "shared": (memory_info.get("shared", 0) / total_memory * 100) if total_memory > 0 else 0
                },
                "swap_activity": {
                    "total": swap_info.get("total", 0),
                    "total_human": swap_info.get("total_human", "0 B"),
                    "used": swap_info.get("used", 0),
                    "used_human": swap_info.get("used_human", "0 B"),
                    "swapped_in": swap_info.get("sin", 0),
                    "swapped_in_human": swap_info.get("sin_human", "0 B"),
                    "swapped_out": swap_info.get("sout", 0),
                    "swapped_out_human": swap_info.get("sout_human", "0 B")
                },
                "recommendations": recommendations
            }
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing memory performance: {e}")
            return json.dumps({"error": str(e)})
