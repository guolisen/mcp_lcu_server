#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for CPU information and operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.cpu import CPUOperations

logger = logging.getLogger(__name__)


def register_cpu_tools(mcp: FastMCP) -> None:
    """Register CPU tools with the MCP server.
    
    Args:
        mcp: MCP server.
    """
    # Create CPU operations instance
    cpu_ops = CPUOperations()
    
    @mcp.tool()
    def get_cpu_info() -> str:
        """Get detailed CPU information.
        
        Returns:
            JSON string with CPU information including:
            - brand: CPU model name
            - architecture: CPU architecture
            - count: Number of CPU cores (physical and logical)
            - frequency: CPU frequency information
            - cache: Cache sizes
            - topology: CPU topology information
            - flags: CPU flags
        """
        logger.info("Getting CPU information")
        
        try:
            cpu_info = cpu_ops.get_cpu_info()
            return json.dumps(cpu_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_cpu_usage(per_cpu: bool = False, interval: float = 0.1) -> str:
        """Get CPU usage percentage.
        
        Args:
            per_cpu: Whether to return per-CPU usage
            interval: Time interval for CPU usage calculation (seconds)
        
        Returns:
            JSON string with CPU usage percentage (0-100) or list of percentages for each CPU
        """
        logger.info(f"Getting CPU usage (per_cpu={per_cpu}, interval={interval})")
        
        try:
            usage = cpu_ops.get_cpu_usage(per_cpu=per_cpu, interval=interval)
            
            if per_cpu:
                # Format as list of dictionaries with CPU index
                result = [{"cpu": i, "usage": usage_value} for i, usage_value in enumerate(usage)]
                return json.dumps(result, indent=2)
            else:
                return json.dumps({"usage": usage}, indent=2)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_cpu_times(per_cpu: bool = False) -> str:
        """Get CPU time spent in various modes.
        
        Args:
            per_cpu: Whether to return per-CPU times
        
        Returns:
            JSON string with CPU times spent in user, system, idle, etc. modes
        """
        logger.info(f"Getting CPU times (per_cpu={per_cpu})")
        
        try:
            times = cpu_ops.get_cpu_times(per_cpu=per_cpu)
            
            if per_cpu:
                # Format as list of dictionaries with CPU index
                result = [{"cpu": i, **time_value} for i, time_value in enumerate(times)]
                return json.dumps(result, indent=2)
            else:
                return json.dumps(times, indent=2)
        except Exception as e:
            logger.error(f"Error getting CPU times: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_load_average() -> str:
        """Get system load average.
        
        Returns:
            JSON string with 1, 5, and 15 minute load averages
        """
        logger.info("Getting load average")
        
        try:
            load_avg = cpu_ops.get_load_average()
            return json.dumps(load_avg, indent=2)
        except Exception as e:
            logger.error(f"Error getting load average: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_cpu_stats() -> str:
        """Get CPU statistics.
        
        Returns:
            JSON string with CPU statistics (ctx_switches, interrupts, soft_interrupts, syscalls)
        """
        logger.info("Getting CPU statistics")
        
        try:
            stats = cpu_ops.get_cpu_stats()
            return json.dumps(stats, indent=2)
        except Exception as e:
            logger.error(f"Error getting CPU stats: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def analyze_cpu_performance() -> str:
        """Analyze CPU performance and provide insights.
        
        This function collects comprehensive CPU data and provides analysis:
        - Current CPU utilization and load
        - Comparison of current load with CPU capacity
        - Identification of potential bottlenecks
        - Recommendations for performance improvement
        
        Returns:
            JSON string with CPU performance analysis
        """
        logger.info("Analyzing CPU performance")
        
        try:
            # Collect all CPU information
            cpu_info = cpu_ops.get_cpu_info()
            cpu_usage = cpu_ops.get_cpu_usage(per_cpu=True, interval=0.5)
            load_avg = cpu_ops.get_load_average()
            cpu_times = cpu_ops.get_cpu_times(per_cpu=False)
            cpu_stats = cpu_ops.get_cpu_stats()
            
            # Calculate average CPU usage
            avg_usage = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
            
            # Determine bottleneck status
            bottleneck_status = "None"
            if avg_usage > 90:
                bottleneck_status = "Critical"
            elif avg_usage > 75:
                bottleneck_status = "High"
            elif avg_usage > 50:
                bottleneck_status = "Moderate"
            elif avg_usage > 25:
                bottleneck_status = "Low"
            
            # Check load average relative to CPU count
            logical_cpus = cpu_info.get("count", {}).get("logical", 0) or 1
            load_status = "Normal"
            if load_avg.get("1min_per_cpu", 0) > 1.0:
                load_status = "Overloaded"
            elif load_avg.get("1min_per_cpu", 0) > 0.7:
                load_status = "High"
            
            # Calculate CPU time distribution
            total_time = sum(value for key, value in cpu_times.items() 
                          if key not in ["guest", "guest_nice"])
            
            time_distribution = {}
            if total_time > 0:
                for key, value in cpu_times.items():
                    if key not in ["guest", "guest_nice"]:
                        time_distribution[key] = (value / total_time) * 100
            
            # Generate recommendations
            recommendations = []
            if bottleneck_status in ["High", "Critical"]:
                recommendations.append("Consider upgrading CPU or optimizing workload")
            if load_status in ["High", "Overloaded"]:
                recommendations.append("System is experiencing high load, consider distributing workload")
            if time_distribution.get("iowait", 0) > 10:
                recommendations.append("High I/O wait time indicates potential disk bottleneck")
            if time_distribution.get("steal", 0) > 5:
                recommendations.append("High CPU steal time indicates virtualization contention")
            
            # Create analysis report
            analysis = {
                "timestamp": cpu_ops._last_time,
                "summary": {
                    "logical_cpus": logical_cpus,
                    "physical_cpus": cpu_info.get("count", {}).get("physical", 0),
                    "avg_usage": avg_usage,
                    "bottleneck_status": bottleneck_status,
                    "load_status": load_status,
                    "current_load": load_avg.get("1min", 0),
                    "load_per_cpu": load_avg.get("1min_per_cpu", 0)
                },
                "usage": {
                    "per_cpu": [{"cpu": i, "usage": u} for i, u in enumerate(cpu_usage)],
                    "time_distribution": time_distribution
                },
                "stats": cpu_stats,
                "recommendations": recommendations
            }
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing CPU performance: {e}")
            return json.dumps({"error": str(e)})
