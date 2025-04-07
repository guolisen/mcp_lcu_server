#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for system monitoring.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.monitoring import MonitoringOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


def register_monitoring_tools(mcp: FastMCP, config: Config) -> None:
    """Register monitoring tools with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create monitoring operations instance
    monitoring_ops = MonitoringOperations(config)
    
    # Start monitoring if enabled
    if config.monitoring.enabled:
        monitoring_ops.start_monitoring()
    
    @mcp.tool()
    def monitor_start_monitoring() -> str:
        """Start system monitoring.
        
        Returns:
            JSON string with result
        """
        logger.info("Starting monitoring")
        
        try:
            success = monitoring_ops.start_monitoring()
            if success:
                return json.dumps({"success": True, "message": "Monitoring started successfully"})
            else:
                return json.dumps({"success": False, "message": "Monitoring could not be started or is already running"})
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def monitor_stop_monitoring() -> str:
        """Stop system monitoring.
        
        Returns:
            JSON string with result
        """
        logger.info("Stopping monitoring")
        
        try:
            success = monitoring_ops.stop_monitoring()
            if success:
                return json.dumps({"success": True, "message": "Monitoring stopped successfully"})
            else:
                return json.dumps({"success": False, "message": "Monitoring could not be stopped or is not running"})
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def monitor_get_monitoring_status() -> str:
        """Get monitoring status.
        
        Returns:
            JSON string with monitoring status
        """
        logger.info("Getting monitoring status")
        
        try:
            status = monitoring_ops.get_monitoring_status()
            return json.dumps(status, indent=2)
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_get_system_status() -> str:
        """Get system status.
        
        Returns:
            JSON string with system status
        """
        logger.info("Getting system status")
        
        try:
            status = monitoring_ops.get_system_status()
            return json.dumps(status, indent=2)
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_check_system_health() -> str:
        """Check system health.
        
        Returns:
            JSON string with system health information
        """
        logger.info("Checking system health")
        
        try:
            health = monitoring_ops.check_system_health()
            return json.dumps(health, indent=2)
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_get_cpu_metrics(count: int = 60) -> str:
        """Get CPU metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            JSON string with CPU metrics
        """
        logger.info(f"Getting CPU metrics (count={count})")
        
        try:
            metrics = monitoring_ops.get_cpu_metrics(count)
            return json.dumps(metrics, indent=2)
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_get_memory_metrics(count: int = 60) -> str:
        """Get memory metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            JSON string with memory metrics
        """
        logger.info(f"Getting memory metrics (count={count})")
        
        try:
            metrics = monitoring_ops.get_memory_metrics(count)
            return json.dumps(metrics, indent=2)
        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_get_disk_metrics(count: int = 60) -> str:
        """Get disk metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            JSON string with disk metrics
        """
        logger.info(f"Getting disk metrics (count={count})")
        
        try:
            metrics = monitoring_ops.get_disk_metrics(count)
            return json.dumps(metrics, indent=2)
        except Exception as e:
            logger.error(f"Error getting disk metrics: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_get_network_metrics(count: int = 60) -> str:
        """Get network metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            JSON string with network metrics
        """
        logger.info(f"Getting network metrics (count={count})")
        
        try:
            metrics = monitoring_ops.get_network_metrics(count)
            return json.dumps(metrics, indent=2)
        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_get_system_metrics(count: int = 60) -> str:
        """Get system metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            JSON string with system metrics
        """
        logger.info(f"Getting system metrics (count={count})")
        
        try:
            metrics = monitoring_ops.get_system_metrics(count)
            return json.dumps(metrics, indent=2)
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def monitor_analyze_system_performance() -> str:
        """Analyze system performance and provide insights.
        
        This function collects comprehensive system data and provides analysis:
        - Current resource utilization (CPU, memory, disk, network)
        - Historical trends
        - Identification of potential bottlenecks
        - Recommendations for performance improvement
        
        Returns:
            JSON string with system performance analysis
        """
        logger.info("Analyzing system performance")
        
        try:
            # Get current system status
            status = monitoring_ops.get_system_status()
            
            # Get system metrics for historical data
            system_metrics = monitoring_ops.get_system_metrics(60)  # Last hour
            cpu_metrics = monitoring_ops.get_cpu_metrics(60)
            memory_metrics = monitoring_ops.get_memory_metrics(60)
            
            # Analyze CPU usage
            cpu_usage = status.get("cpu", {}).get("usage_percent", 0)
            cpu_usage_high = False
            cpu_usage_sustained = False
            
            if cpu_usage > 75:
                cpu_usage_high = True
                
                # Check if high CPU usage is sustained
                high_cpu_count = sum(1 for m in cpu_metrics 
                                  if m.get("usage", {}).get("average", 0) > 75)
                if high_cpu_count > len(cpu_metrics) / 2:  # High for more than half the time
                    cpu_usage_sustained = True
            
            # Analyze memory usage
            memory_usage = status.get("memory", {}).get("percent", 0)
            memory_usage_high = False
            memory_usage_sustained = False
            
            if memory_usage > 75:
                memory_usage_high = True
                
                # Check if high memory usage is sustained
                high_memory_count = sum(1 for m in memory_metrics 
                                     if m.get("memory", {}).get("percent", 0) > 75)
                if high_memory_count > len(memory_metrics) / 2:  # High for more than half the time
                    memory_usage_sustained = True
            
            # Analyze disk usage
            disk_usage_high = False
            critical_disks = []
            
            for disk in status.get("disks", []):
                if disk.get("percent", 0) > 85:
                    disk_usage_high = True
                    critical_disks.append(disk)
            
            # Analyze system load
            load_avg = status.get("cpu", {}).get("load_average", {})
            load_1min = load_avg.get("1min_per_cpu", 0)
            load_high = load_1min > 1.0
            
            # Generate insights
            insights = []
            
            if cpu_usage_high:
                if cpu_usage_sustained:
                    insights.append({
                        "component": "cpu",
                        "severity": "high",
                        "message": f"Sustained high CPU usage ({cpu_usage:.1f}%) may indicate insufficient CPU resources or inefficient processes"
                    })
                else:
                    insights.append({
                        "component": "cpu",
                        "severity": "medium",
                        "message": f"Current CPU usage is high ({cpu_usage:.1f}%) but not sustained"
                    })
            
            if memory_usage_high:
                if memory_usage_sustained:
                    insights.append({
                        "component": "memory",
                        "severity": "high",
                        "message": f"Sustained high memory usage ({memory_usage:.1f}%) may indicate memory leaks or insufficient memory resources"
                    })
                else:
                    insights.append({
                        "component": "memory",
                        "severity": "medium",
                        "message": f"Current memory usage is high ({memory_usage:.1f}%) but not sustained"
                    })
            
            if disk_usage_high:
                for disk in critical_disks:
                    insights.append({
                        "component": "disk",
                        "severity": "high",
                        "message": f"Disk usage on {disk.get('mountpoint', 'unknown')} is critically high ({disk.get('percent', 0):.1f}%)"
                    })
            
            if load_high:
                insights.append({
                    "component": "load",
                    "severity": "high",
                    "message": f"System load is high (load per CPU: {load_1min:.1f}) indicating the system may be overloaded"
                })
            
            # Generate recommendations
            recommendations = []
            
            if cpu_usage_sustained:
                recommendations.append("Consider upgrading CPU resources or optimizing CPU-intensive processes")
                recommendations.append("Use 'top' or 'htop' to identify CPU-intensive processes and consider optimizing or throttling them")
            
            if memory_usage_sustained:
                recommendations.append("Consider adding more memory or optimizing memory-intensive applications")
                recommendations.append("Check for memory leaks in long-running processes")
            
            if disk_usage_high:
                recommendations.append("Free up disk space by removing unnecessary files or adding more storage")
                recommendations.append("Use 'du -sh /*' to identify large directories")
            
            if load_high:
                recommendations.append("Distribute workload more evenly or add more CPU resources")
            
            # Create performance analysis
            analysis = {
                "timestamp": status.get("timestamp", 0),
                "summary": {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "load": load_1min,
                    "status": status.get("status", "Unknown")
                },
                "insights": insights,
                "recommendations": recommendations,
                "metrics_analyzed": {
                    "cpu": len(cpu_metrics),
                    "memory": len(memory_metrics),
                    "system": len(system_metrics)
                }
            }
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing system performance: {e}")
            return json.dumps({"error": str(e)})
