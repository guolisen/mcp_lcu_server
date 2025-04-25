#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 25, 2025
#
# Description: MCP tools for system logs.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.logs import LogOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


def register_log_tools(mcp: FastMCP, config: Config) -> None:
    """Register log tools with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create log operations instance
    log_ops = LogOperations(config)
    
    @mcp.tool()
    def log_list_available_logs() -> str:
        """List all available log sources on the system.
        
        This function identifies and returns a list of all available log sources
        on the system, including:
        - System logs (syslog, auth, daemon, etc.)
        - Systemd journal units
        - Application logs (Apache, MySQL, etc.)
        - Special logs (audit, boot, kernel, etc.)
        
        Returns:
            JSON string with available log sources and their details
        """
        logger.info("Listing available log sources")
        
        try:
            available_logs = log_ops.list_available_logs()
            return json.dumps(available_logs, indent=2)
        except Exception as e:
            logger.error(f"Error listing available logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_journal_logs(count: int = 100, 
                           since: Optional[str] = None, 
                           until: Optional[str] = None,
                           unit: Optional[str] = None,
                           priority: Optional[str] = None) -> str:
        """Get logs from the systemd journal.
        
        This function retrieves logs from the systemd journal with various
        filtering options.
        
        Args:
            count: Maximum number of entries to return
            since: Time to start from (e.g., "2h" for 2 hours ago, "2021-04-01" for specific date)
            until: Time to end at
            unit: Filter by systemd unit
            priority: Filter by priority (0-7, emerg to debug)
        
        Returns:
            JSON string with journal log entries
        """
        logger.info(f"Getting journal logs (count={count}, since={since}, unit={unit}, priority={priority})")
        
        try:
            logs = log_ops.get_journal_logs(count, since, until, unit, priority)
            return json.dumps(logs, indent=2)
        except Exception as e:
            logger.error(f"Error getting journal logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_system_logs(count: int = 100,
                          since: Optional[str] = None,
                          until: Optional[str] = None,
                          log_type: str = "syslog") -> str:
        """Get logs from system log files.
        
        This function retrieves logs from various system log files.
        
        Args:
            count: Maximum number of entries to return
            since: Time to start from (e.g., "2h" for 2 hours ago, "2021-04-01" for specific date)
            until: Time to end at
            log_type: Type of log to retrieve (syslog, auth, daemon, etc.)
        
        Returns:
            JSON string with system log entries
        """
        logger.info(f"Getting system logs (count={count}, since={since}, log_type={log_type})")
        
        try:
            logs = log_ops.get_system_logs(count, since, until, log_type)
            return json.dumps(logs, indent=2)
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_dmesg(count: int = 100) -> str:
        """Get kernel logs from dmesg.
        
        This function retrieves logs from the kernel ring buffer.
        
        Args:
            count: Maximum number of entries to return
        
        Returns:
            JSON string with kernel log entries
        """
        logger.info(f"Getting dmesg logs (count={count})")
        
        try:
            logs = log_ops.get_dmesg(count)
            return json.dumps(logs, indent=2)
        except Exception as e:
            logger.error(f"Error getting dmesg logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_application_logs(app_name: str,
                               count: int = 100,
                               since: Optional[str] = None,
                               until: Optional[str] = None) -> str:
        """Get logs for a specific application.
        
        This function retrieves logs for a specific application from its log file
        or from the systemd journal.
        
        Args:
            app_name: Name of the application (e.g., apache, mysql)
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
        
        Returns:
            JSON string with application log entries
        """
        logger.info(f"Getting application logs for {app_name} (count={count}, since={since})")
        
        try:
            logs = log_ops.get_application_log(app_name, count, since, until)
            return json.dumps(logs, indent=2)
        except Exception as e:
            logger.error(f"Error getting application logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_audit_logs(count: int = 100,
                         since: Optional[str] = None,
                         until: Optional[str] = None,
                         type_filter: Optional[str] = None) -> str:
        """Get audit logs.
        
        This function retrieves audit logs from the Linux audit system.
        
        Args:
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
            type_filter: Filter by audit event type
        
        Returns:
            JSON string with audit log entries
        """
        logger.info(f"Getting audit logs (count={count}, since={since}, type={type_filter})")
        
        try:
            logs = log_ops.get_audit_logs(count, since, until, type_filter)
            return json.dumps(logs, indent=2)
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_boot_logs(count: int = 1) -> str:
        """Get boot logs.
        
        This function retrieves logs related to system boot.
        
        Args:
            count: Number of boot sessions to return (1 for current boot)
        
        Returns:
            JSON string with boot log entries
        """
        logger.info(f"Getting boot logs (count={count})")
        
        try:
            logs = log_ops.get_boot_logs(count)
            return json.dumps(logs, indent=2)
        except Exception as e:
            logger.error(f"Error getting boot logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_service_status_logs(service: str, count: int = 100) -> str:
        """Get logs related to a specific systemd service's status changes.
        
        This function retrieves logs related to a specific systemd service.
        
        Args:
            service: Name of the systemd service
            count: Maximum number of entries to return
        
        Returns:
            JSON string with service log entries
        """
        logger.info(f"Getting service logs for {service} (count={count})")
        
        try:
            logs = log_ops.get_service_status_logs(service, count)
            return json.dumps(logs, indent=2)
        except Exception as e:
            logger.error(f"Error getting service logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_search_logs(query: str,
                      sources: List[str] = ["journal", "syslog", "dmesg"],
                      count: int = 100,
                      since: Optional[str] = None,
                      until: Optional[str] = None) -> str:
        """Search across multiple log sources.
        
        This function searches for a specific query across multiple log sources.
        
        Args:
            query: Search query
            sources: List of log sources to search (default: ["journal", "syslog", "dmesg"])
            count: Maximum number of entries to return per source
            since: Time to start from
            until: Time to end at
        
        Returns:
            JSON string with search results
        """
        # Ensure sources is never None
        log_sources = sources if sources else ["journal", "syslog", "dmesg"]
        
        logger.info(f"Searching logs for '{query}' in {log_sources} (count={count}, since={since})")
        
        try:
            results = log_ops.search_logs(query, log_sources, count, since, until)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_analyze_logs(sources: List[str] = ["journal", "syslog"],
                       since: str = "1h",
                       until: Optional[str] = None) -> str:
        """Analyze logs to identify patterns and issues.
        
        This function analyzes logs to identify patterns, errors, warnings,
        and potential issues.
        
        Args:
            sources: List of log sources to analyze (default: ["journal", "syslog"])
            since: Time to start from (default: 1 hour ago)
            until: Time to end at
        
        Returns:
            JSON string with analysis results
        """
        # Ensure sources is never None
        log_sources = sources if sources else ["journal", "syslog"]
        
        logger.info(f"Analyzing logs from {log_sources} (since={since}, until={until})")
        
        try:
            analysis = log_ops.analyze_logs(log_sources, since, until)
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def log_get_statistics(sources: List[str] = ["journal", "syslog"], days: int = 7) -> str:
        """Get statistics about log volume and characteristics over time.
        
        This function generates statistics about log volume, severity distribution,
        and trends over the specified time period.
        
        Args:
            sources: List of log sources to analyze (default: ["journal", "syslog"])
            days: Number of days to analyze
        
        Returns:
            JSON string with log statistics
        """
        # Ensure sources is never None
        log_sources = sources if sources else ["journal", "syslog"]
        
        logger.info(f"Getting log statistics from {log_sources} for {days} days")
        
        try:
            statistics = log_ops.get_log_statistics(log_sources, days)
            return json.dumps(statistics, indent=2)
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return json.dumps({"error": str(e)})
