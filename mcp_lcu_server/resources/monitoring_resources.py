#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP resources for system monitoring.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Dict, List, Optional, Any

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.monitoring import MonitoringOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


class MonitoringResources:
    """Manager for monitoring resources as MCP resources."""
    
    def __init__(self, config: Config):
        """Initialize monitoring resources.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.monitoring_ops = MonitoringOperations(config)
        
        # We don't start monitoring here to avoid duplicate monitoring
        # Monitoring is already started in monitoring_tools.py
    
    def register_resources(self, mcp: FastMCP) -> None:
        """Register all monitoring resource templates and static resources."""
        
        # Monitoring status resource
        @mcp.resource("linux://monitoring/status", 
                     name="Monitoring Status", 
                     description="Current status of the monitoring subsystem",
                     mime_type="application/json")
        def monitoring_get_monitoring_status() -> str:
            """Get monitoring status."""
            try:
                status = self.monitoring_ops.get_monitoring_status()
                return json.dumps(status, indent=2)
            except Exception as e:
                logger.error(f"Error getting monitoring status: {e}")
                return json.dumps({"error": str(e)})
        
        # System status resource
        @mcp.resource("linux://monitoring/system", 
                     name="System Status", 
                     description="Current system status from monitoring",
                     mime_type="application/json")
        def monitoring_get_system_status() -> str:
            """Get system status."""
            try:
                status = self.monitoring_ops.get_system_status()
                return json.dumps(status, indent=2)
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return json.dumps({"error": str(e)})
        
        # System health resource
        @mcp.resource("linux://monitoring/health", 
                     name="System Health", 
                     description="Current system health check",
                     mime_type="application/json")
        def monitoring_get_system_health() -> str:
            """Get system health."""
            try:
                health = self.monitoring_ops.check_system_health()
                return json.dumps(health, indent=2)
            except Exception as e:
                logger.error(f"Error getting system health: {e}")
                return json.dumps({"error": str(e)})
        
        # CPU metrics resource
        @mcp.resource("linux://monitoring/metrics/cpu/{count}", 
                     name="CPU Metrics", 
                     description="CPU metrics from monitoring",
                     mime_type="application/json")
        def monitoring_get_cpu_metrics(count: str) -> str:
            """Get CPU metrics."""
            try:
                metrics = self.monitoring_ops.get_cpu_metrics(int(count))
                return json.dumps(metrics, indent=2)
            except Exception as e:
                logger.error(f"Error getting CPU metrics: {e}")
                return json.dumps({"error": str(e)})
        
        # Memory metrics resource
        @mcp.resource("linux://monitoring/metrics/memory/{count}", 
                     name="Memory Metrics", 
                     description="Memory metrics from monitoring",
                     mime_type="application/json")
        def monitoring_get_memory_metrics(count: str) -> str:
            """Get memory metrics."""
            try:
                metrics = self.monitoring_ops.get_memory_metrics(int(count))
                return json.dumps(metrics, indent=2)
            except Exception as e:
                logger.error(f"Error getting memory metrics: {e}")
                return json.dumps({"error": str(e)})
        
        # Disk metrics resource
        @mcp.resource("linux://monitoring/metrics/disk/{count}", 
                     name="Disk Metrics", 
                     description="Disk metrics from monitoring",
                     mime_type="application/json")
        def monitoring_get_disk_metrics(count: str) -> str:
            """Get disk metrics."""
            try:
                metrics = self.monitoring_ops.get_disk_metrics(int(count))
                return json.dumps(metrics, indent=2)
            except Exception as e:
                logger.error(f"Error getting disk metrics: {e}")
                return json.dumps({"error": str(e)})
        
        # Network metrics resource
        @mcp.resource("linux://monitoring/metrics/network/{count}", 
                     name="Network Metrics", 
                     description="Network metrics from monitoring",
                     mime_type="application/json")
        def monitoring_get_network_metrics(count: str) -> str:
            """Get network metrics."""
            try:
                metrics = self.monitoring_ops.get_network_metrics(int(count))
                return json.dumps(metrics, indent=2)
            except Exception as e:
                logger.error(f"Error getting network metrics: {e}")
                return json.dumps({"error": str(e)})
        
        # System metrics resource
        @mcp.resource("linux://monitoring/metrics/system/{count}", 
                     name="System Metrics", 
                     description="System metrics from monitoring",
                     mime_type="application/json")
        def monitoring_get_system_metrics(count: str) -> str:
            """Get system metrics."""
            try:
                metrics = self.monitoring_ops.get_system_metrics(int(count))
                return json.dumps(metrics, indent=2)
            except Exception as e:
                logger.error(f"Error getting system metrics: {e}")
                return json.dumps({"error": str(e)})
        
        # All metrics types resource
        @mcp.resource("linux://monitoring/metrics/types", 
                     name="Metrics Types", 
                     description="Available metrics types",
                     mime_type="application/json")
        def monitoring_get_metrics_types() -> str:
            """Get available metrics types."""
            try:
                metrics_types = {
                    "types": ["cpu", "memory", "disk", "network", "system"],
                    "description": {
                        "cpu": "CPU usage, times, load average, and statistics",
                        "memory": "Memory usage, swap usage, and memory distribution",
                        "disk": "Disk usage, I/O statistics, and disk rates",
                        "network": "Network I/O statistics, connections, and network rates",
                        "system": "Overall system statistics"
                    }
                }
                return json.dumps(metrics_types, indent=2)
            except Exception as e:
                logger.error(f"Error getting metrics types: {e}")
                return json.dumps({"error": str(e)})


def register_monitoring_resources(mcp: FastMCP, config: Config) -> None:
    """Register monitoring resources with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create the resources manager
    resources = MonitoringResources(config)
    
    # Register the resources
    resources.register_resources(mcp)
