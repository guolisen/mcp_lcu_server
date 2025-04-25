#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 25, 2025
#
# Description: MCP resources for system logs.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Dict, List, Optional, Any

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.logs import LogOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


class LogResources:
    """Manager for log resources as MCP resources."""
    
    def __init__(self, config: Config):
        """Initialize log resources.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.log_ops = LogOperations(config)
    
    def register_resources(self, mcp: FastMCP) -> None:
        """Register all log resource templates and static resources."""
        
        # Available logs resource
        @mcp.resource("linux://logs/available", 
                     name="Available Logs", 
                     description="List of available log sources on the system",
                     mime_type="application/json")
        def logs_get_available_logs() -> str:
            """Get available logs."""
            try:
                available_logs = self.log_ops.list_available_logs()
                return json.dumps(available_logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting available logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Journal logs resource
        @mcp.resource("linux://logs/journal/{parameters}", 
                     name="Journal Logs", 
                     description="Logs from systemd journal",
                     mime_type="application/json")
        def logs_get_journal_logs(parameters: str) -> str:
            """Get journal logs with parameters."""
            try:
                # Parse parameters: count=100,since=1h,unit=nginx.service,priority=3
                params = {}
                if parameters:
                    param_pairs = parameters.split(",")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                
                # Extract individual parameters
                count = int(params.get("count", "100"))
                since = params.get("since")
                until = params.get("until")
                unit = params.get("unit")
                priority = params.get("priority")
                
                logs = self.log_ops.get_journal_logs(count, since, until, unit, priority)
                return json.dumps(logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting journal logs: {e}")
                return json.dumps({"error": str(e)})
        
        # System logs resource
        @mcp.resource("linux://logs/system/{log_type}/{parameters}", 
                     name="System Logs", 
                     description="Logs from system log files",
                     mime_type="application/json")
        def logs_get_system_logs(log_type: str, parameters: str) -> str:
            """Get system logs with parameters."""
            try:
                # Parse parameters
                params = {}
                if parameters:
                    param_pairs = parameters.split(",")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                
                # Extract individual parameters
                count = int(params.get("count", "100"))
                since = params.get("since")
                until = params.get("until")
                
                logs = self.log_ops.get_system_logs(count, since, until, log_type)
                return json.dumps(logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting system logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Kernel logs resource
        @mcp.resource("linux://logs/kernel/{count}", 
                     name="Kernel Logs", 
                     description="Logs from kernel ring buffer (dmesg)",
                     mime_type="application/json")
        def logs_get_kernel_logs(count: str) -> str:
            """Get kernel logs."""
            try:
                logs = self.log_ops.get_dmesg(int(count))
                return json.dumps(logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting kernel logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Application logs resource
        @mcp.resource("linux://logs/application/{app_name}/{parameters}", 
                     name="Application Logs", 
                     description="Logs for specific applications",
                     mime_type="application/json")
        def logs_get_application_logs(app_name: str, parameters: str) -> str:
            """Get application logs with parameters."""
            try:
                # Parse parameters
                params = {}
                if parameters:
                    param_pairs = parameters.split(",")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                
                # Extract individual parameters
                count = int(params.get("count", "100"))
                since = params.get("since")
                until = params.get("until")
                
                logs = self.log_ops.get_application_log(app_name, count, since, until)
                return json.dumps(logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting application logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Audit logs resource
        @mcp.resource("linux://logs/audit/{parameters}", 
                     name="Audit Logs", 
                     description="Logs from the Linux audit system",
                     mime_type="application/json")
        def logs_get_audit_logs(parameters: str) -> str:
            """Get audit logs with parameters."""
            try:
                # Parse parameters
                params = {}
                if parameters:
                    param_pairs = parameters.split(",")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                
                # Extract individual parameters
                count = int(params.get("count", "100"))
                since = params.get("since")
                until = params.get("until")
                type_filter = params.get("type")
                
                logs = self.log_ops.get_audit_logs(count, since, until, type_filter)
                return json.dumps(logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting audit logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Boot logs resource
        @mcp.resource("linux://logs/boot/{count}", 
                     name="Boot Logs", 
                     description="Logs related to system boot",
                     mime_type="application/json")
        def logs_get_boot_logs(count: str) -> str:
            """Get boot logs."""
            try:
                logs = self.log_ops.get_boot_logs(int(count))
                return json.dumps(logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting boot logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Service logs resource
        @mcp.resource("linux://logs/service/{service}/{count}", 
                     name="Service Logs", 
                     description="Logs for specific systemd services",
                     mime_type="application/json")
        def logs_get_service_logs(service: str, count: str) -> str:
            """Get service logs."""
            try:
                logs = self.log_ops.get_service_status_logs(service, int(count))
                return json.dumps(logs, indent=2)
            except Exception as e:
                logger.error(f"Error getting service logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Log search resource
        @mcp.resource("linux://logs/search/{query}/{parameters}", 
                     name="Log Search", 
                     description="Search across multiple log sources",
                     mime_type="application/json")
        def logs_search(query: str, parameters: str) -> str:
            """Search logs."""
            try:
                # Parse parameters
                params = {}
                if parameters:
                    param_pairs = parameters.split(",")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                
                # Extract individual parameters
                count = int(params.get("count", "100"))
                since = params.get("since")
                until = params.get("until")
                
                # Parse sources
                sources = ["journal", "syslog", "dmesg"]  # Default
                if "sources" in params:
                    try:
                        sources = params["sources"].split("|")
                    except:
                        pass
                
                results = self.log_ops.search_logs(query, sources, count, since, until)
                return json.dumps(results, indent=2)
            except Exception as e:
                logger.error(f"Error searching logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Log analysis resource
        @mcp.resource("linux://logs/analysis/{parameters}", 
                     name="Log Analysis", 
                     description="Analysis of log patterns and issues",
                     mime_type="application/json")
        def logs_analyze(parameters: str) -> str:
            """Analyze logs."""
            try:
                # Parse parameters
                params = {}
                if parameters:
                    param_pairs = parameters.split(",")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                
                # Extract individual parameters
                since = params.get("since", "1h")
                until = params.get("until")
                
                # Parse sources
                sources = ["journal", "syslog"]  # Default
                if "sources" in params:
                    try:
                        sources = params["sources"].split("|")
                    except:
                        pass
                
                analysis = self.log_ops.analyze_logs(sources, since, until)
                return json.dumps(analysis, indent=2)
            except Exception as e:
                logger.error(f"Error analyzing logs: {e}")
                return json.dumps({"error": str(e)})
        
        # Log statistics resource
        @mcp.resource("linux://logs/statistics/{parameters}", 
                     name="Log Statistics", 
                     description="Statistics about log volume and characteristics",
                     mime_type="application/json")
        def logs_get_statistics(parameters: str) -> str:
            """Get log statistics."""
            try:
                # Parse parameters
                params = {}
                if parameters:
                    param_pairs = parameters.split(",")
                    for pair in param_pairs:
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                
                # Extract individual parameters
                days = int(params.get("days", "7"))
                
                # Parse sources
                sources = ["journal", "syslog"]  # Default
                if "sources" in params:
                    try:
                        sources = params["sources"].split("|")
                    except:
                        pass
                
                statistics = self.log_ops.get_log_statistics(sources, days)
                return json.dumps(statistics, indent=2)
            except Exception as e:
                logger.error(f"Error getting log statistics: {e}")
                return json.dumps({"error": str(e)})


def register_log_resources(mcp: FastMCP, config: Config) -> None:
    """Register log resources with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create the resources manager
    resources = LogResources(config)
    
    # Register the resources
    resources.register_resources(mcp)
