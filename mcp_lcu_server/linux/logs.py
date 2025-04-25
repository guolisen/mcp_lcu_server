#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 25, 2025
#
# Description: System logs module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import json
import time
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


class LogOperations:
    """Class for system log operations on Linux systems."""
    
    def __init__(self, config: Config):
        """Initialize log operations.
        
        Args:
            config: Server configuration
        """
        self.config = config
        
        # Default log paths
        self.log_paths = {
            "syslog": "/var/log/syslog",
            "auth": "/var/log/auth.log",
            "daemon": "/var/log/daemon.log",
            "kern": "/var/log/kern.log",
            "mail": "/var/log/mail.log",
            "user": "/var/log/user.log",
            "messages": "/var/log/messages",
            "boot": "/var/log/boot.log",
            "apache_access": "/var/log/apache2/access.log",
            "apache_error": "/var/log/apache2/error.log",
            "mysql": "/var/log/mysql/error.log",
            "postgresql": "/var/log/postgresql/postgresql.log",
            "audit": "/var/log/audit/audit.log",
        }
        
        # Override with custom paths from config if provided
        if hasattr(config, "logs") and hasattr(config.logs, "paths") and config.logs.paths is not None:
            self.log_paths.update(config.logs.paths)
        
        # Maximum number of log entries to return by default
        self.default_max_entries = 1000
        if hasattr(config, "logs") and hasattr(config.logs, "max_entries"):
            self.default_max_entries = config.logs.max_entries
    
    def get_journal_logs(self, 
                        count: int = 100,
                        since: Optional[str] = None, 
                        until: Optional[str] = None,
                        unit: Optional[str] = None,
                        priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs from systemd journal.
        
        Args:
            count: Maximum number of entries to return
            since: Time to start from (e.g., "2h" for 2 hours ago, "2021-04-01" for specific date)
            until: Time to end at
            unit: Filter by systemd unit
            priority: Filter by priority (0-7, emerg to debug)
        
        Returns:
            List of log entries
        """
        try:
            # Construct the journalctl command
            cmd = ["journalctl", "-o", "json"]
            
            # Apply filters
            if since:
                cmd.extend(["--since", since])
            if until:
                cmd.extend(["--until", until])
            if unit:
                cmd.extend(["-u", unit])
            if priority:
                cmd.extend(["-p", priority])
            
            # Limit the number of entries
            cmd.extend(["-n", str(count)])
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error getting journal logs: {result.stderr}")
                return [{"error": result.stderr}]
            
            # Parse the output
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing journal log entry: {e}")
            
            return logs
        
        except Exception as e:
            logger.error(f"Error getting journal logs: {e}")
            return [{"error": str(e)}]
    
    def get_system_logs(self, 
                       count: int = 100,
                       since: Optional[str] = None,
                       until: Optional[str] = None,
                       log_type: str = "syslog") -> List[Dict[str, Any]]:
        """Get logs from system log files.
        
        Args:
            count: Maximum number of entries to return
            since: Time to start from (e.g., "2h" for 2 hours ago, "2021-04-01" for specific date)
            until: Time to end at
            log_type: Type of log to retrieve (syslog, auth, daemon, etc.)
        
        Returns:
            List of log entries
        """
        try:
            log_path = self.log_paths.get(log_type)
            if not log_path or not os.path.exists(log_path):
                logger.error(f"Log file not found: {log_path}")
                return [{"error": f"Log file not found: {log_path}"}]
            
            # Construct the command to read the log file
            cmd = ["tail", "-n", str(count), log_path]
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error reading log file: {result.stderr}")
                return [{"error": result.stderr}]
            
            # Parse the output
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    # Try to parse the log entry
                    log_entry = self._parse_syslog_line(line, log_type)
                    
                    # Apply time filtering if needed
                    if since or until:
                        if "timestamp" in log_entry:
                            # Check if the entry should be included based on timestamps
                            if self._filter_by_time(log_entry["timestamp"], since, until):
                                logs.append(log_entry)
                        else:
                            # If timestamp parsing failed, include the entry anyway
                            logs.append(log_entry)
                    else:
                        # No time filtering, include all entries
                        logs.append(log_entry)
            
            # Keep only the requested number of entries
            return logs[-count:]
        
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return [{"error": str(e)}]
    
    def get_dmesg(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get kernel logs from dmesg.
        
        Args:
            count: Maximum number of entries to return
        
        Returns:
            List of log entries
        """
        try:
            # Run the dmesg command
            cmd = ["dmesg", "--json"]
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # If JSON format fails, try standard format
                cmd = ["dmesg"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Error getting dmesg logs: {result.stderr}")
                    return [{"error": result.stderr}]
                
                # Parse standard format
                logs = []
                for line in result.stdout.strip().split("\n")[-count:]:
                    if line:  # Skip empty lines
                        log_entry = self._parse_dmesg_line(line)
                        logs.append(log_entry)
                
                return logs
            
            # Parse the JSON output
            try:
                all_logs = json.loads(result.stdout)
                # Return the last 'count' entries
                return all_logs[-count:]
            except json.JSONDecodeError:
                # If JSON parsing fails, try line-by-line parsing
                logs = []
                for line in result.stdout.strip().split("\n")[-count:]:
                    if line:  # Skip empty lines
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            log_entry = self._parse_dmesg_line(line)
                            logs.append(log_entry)
                
                return logs
        
        except Exception as e:
            logger.error(f"Error getting dmesg logs: {e}")
            return [{"error": str(e)}]
    
    def get_application_log(self, 
                          app_name: str,
                          count: int = 100,
                          since: Optional[str] = None,
                          until: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs for a specific application.
        
        Args:
            app_name: Name of the application (e.g., apache, mysql)
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
        
        Returns:
            List of log entries
        """
        try:
            # Check if the application has a known log type
            log_type_map = {
                "apache": "apache_error",
                "apache_access": "apache_access",
                "apache_error": "apache_error",
                "mysql": "mysql",
                "postgresql": "postgresql",
                "postgres": "postgresql",
            }
            
            log_type = log_type_map.get(app_name.lower(), app_name.lower())
            
            # Special handling for systemd units
            if not log_type in self.log_paths:
                # Try to get logs from journald for this application
                return self.get_journal_logs(
                    count=count,
                    since=since,
                    until=until,
                    unit=app_name
                )
            
            # Use system_logs for known log types
            return self.get_system_logs(
                count=count,
                since=since,
                until=until,
                log_type=log_type
            )
        
        except Exception as e:
            logger.error(f"Error getting application logs: {e}")
            return [{"error": str(e)}]
    
    def get_audit_logs(self, 
                      count: int = 100,
                      since: Optional[str] = None,
                      until: Optional[str] = None,
                      type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit logs.
        
        Args:
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
            type_filter: Filter by audit event type
        
        Returns:
            List of audit log entries
        """
        try:
            # First check if ausearch is available
            ausearch_available = subprocess.run(["which", "ausearch"], 
                                              capture_output=True).returncode == 0
            
            if ausearch_available:
                # Construct the command
                cmd = ["ausearch", "-i"]
                
                if since:
                    # Convert since to a start time for ausearch
                    if since.endswith("m"):
                        minutes = int(since[:-1])
                        cmd.extend(["-ts", f"recent-{minutes}"])
                    elif since.endswith("h"):
                        hours = int(since[:-1])
                        cmd.extend(["-ts", f"recent-{hours*60}"])
                    else:
                        cmd.extend(["-ts", since])
                
                if type_filter:
                    cmd.extend(["-m", type_filter])
                
                # Execute the command
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0 and result.returncode != 1:  # 1 means no records found
                    logger.error(f"Error getting audit logs: {result.stderr}")
                    return [{"error": result.stderr}]
                
                # Parse the output
                return self._parse_audit_logs(result.stdout, count)
            
            # Try reading directly from audit log file
            log_path = self.log_paths.get("audit")
            if not log_path or not os.path.exists(log_path):
                logger.error(f"Audit log file not found and ausearch not available")
                return [{"error": "Audit log file not found and ausearch not available"}]
            
            # Read the log file
            cmd = ["tail", "-n", str(count * 5), log_path]  # Read more than needed for filtering
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error reading audit log file: {result.stderr}")
                return [{"error": result.stderr}]
            
            # Parse the output
            logs = self._parse_audit_logs(result.stdout, count)
            return logs
        
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return [{"error": str(e)}]
    
    def get_boot_logs(self, count: int = 1) -> List[Dict[str, Any]]:
        """Get boot logs.
        
        Args:
            count: Number of boot sessions to return (1 for current boot)
        
        Returns:
            List of boot log entries
        """
        try:
            # Check if we can use journalctl for boot logs
            cmd = ["journalctl", "-b", "-o", "json", "-n", "100"]
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error getting boot logs from journalctl: {result.stderr}")
                
                # Try alternate approach - read from /var/log/boot.log
                log_path = self.log_paths.get("boot")
                if log_path and os.path.exists(log_path):
                    cmd = ["tail", "-n", "100", log_path]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.error(f"Error reading boot log file: {result.stderr}")
                        return [{"error": result.stderr}]
                    
                    # Parse the output
                    logs = []
                    for line in result.stdout.strip().split("\n"):
                        if line:  # Skip empty lines
                            logs.append({
                                "message": line,
                                "source": "boot.log",
                                "timestamp": None  # Unfortunately boot.log often doesn't have timestamps
                            })
                    
                    return logs
                else:
                    return [{"error": "Boot logs not available"}]
            
            # Parse the output from journalctl
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing boot log entry: {e}")
            
            return logs
        
        except Exception as e:
            logger.error(f"Error getting boot logs: {e}")
            return [{"error": str(e)}]
    
    def get_service_status_logs(self, service: str, count: int = 100) -> List[Dict[str, Any]]:
        """Get logs related to a specific systemd service's status changes.
        
        Args:
            service: Name of the systemd service
            count: Maximum number of entries to return
        
        Returns:
            List of service status log entries
        """
        try:
            # Construct the command to get service status logs
            cmd = ["journalctl", "-u", service, "--output=json", "-n", str(count)]
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error getting service logs: {result.stderr}")
                return [{"error": result.stderr}]
            
            # Parse the output
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing service log entry: {e}")
            
            return logs
        
        except Exception as e:
            logger.error(f"Error getting service logs: {e}")
            return [{"error": str(e)}]
    
    def search_logs(self, 
                  query: str,
                  sources: List[str] = ["journal", "syslog", "dmesg"],
                  count: int = 100,
                  since: Optional[str] = None,
                  until: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Search across multiple log sources.
        
        Args:
            query: Search query
            sources: List of log sources to search
            count: Maximum number of entries to return per source
            since: Time to start from
            until: Time to end at
        
        Returns:
            Dictionary with log sources as keys and lists of matching entries as values
        """
        try:
            results = {}
            
            # Determine which sources to search
            source_map = {
                "journal": self._search_journal,
                "syslog": self._search_syslog,
                "dmesg": self._search_dmesg,
                "auth": lambda q, c, s, u: self._search_system_log(q, c, s, u, "auth"),
                "daemon": lambda q, c, s, u: self._search_system_log(q, c, s, u, "daemon"),
                "kern": lambda q, c, s, u: self._search_system_log(q, c, s, u, "kern"),
                "audit": self._search_audit,
                # Add more sources as needed
            }
            
            # Search each requested source
            for source in sources:
                if source in source_map:
                    search_func = source_map[source]
                    matches = search_func(query, count, since, until)
                    if matches:
                        results[source] = matches
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return {"error": str(e)}
    
    def analyze_logs(self, 
                    sources: List[str] = ["journal", "syslog"],
                    since: Optional[str] = "1h",
                    until: Optional[str] = None) -> Dict[str, Any]:
        """Analyze logs to identify patterns and issues.
        
        Args:
            sources: List of log sources to analyze
            since: Time to start from (default: 1 hour ago)
            until: Time to end at
        
        Returns:
            Analysis results
        """
        try:
            analysis = {
                "timestamp": time.time(),
                "period": {
                    "since": since,
                    "until": until
                },
                "sources": sources,
                "summary": {},
                "error_count": 0,
                "warning_count": 0,
                "critical_issues": [],
                "potential_issues": []
            }
            
            # Get logs from each source
            all_logs = {}
            
            for source in sources:
                if source == "journal":
                    logs = self.get_journal_logs(
                        count=self.default_max_entries,
                        since=since,
                        until=until
                    )
                elif source == "syslog":
                    logs = self.get_system_logs(
                        count=self.default_max_entries,
                        since=since,
                        until=until,
                        log_type="syslog"
                    )
                elif source == "dmesg":
                    logs = self.get_dmesg(count=self.default_max_entries)
                else:
                    # Try as a system log type
                    logs = self.get_system_logs(
                        count=self.default_max_entries,
                        since=since,
                        until=until,
                        log_type=source
                    )
                
                all_logs[source] = logs
            
            # Process each source
            for source, logs in all_logs.items():
                # Count log entries by priority/severity
                priorities = {"emerg": 0, "alert": 0, "crit": 0, "err": 0, 
                             "warning": 0, "notice": 0, "info": 0, "debug": 0}
                
                # Patterns to look for
                error_patterns = [
                    r"error", r"fail", r"exception", r"crash", r"segfault", r"core dump",
                    r"killed", r"fatal", r"panic", r"critical"
                ]
                
                issue_counts = {pattern: 0 for pattern in error_patterns}
                error_examples = {pattern: [] for pattern in error_patterns}
                
                for entry in logs:
                    # Check priority
                    priority = self._extract_priority(entry)
                    if priority in priorities:
                        priorities[priority] += 1
                    
                    # Count errors by category
                    message = self._extract_message(entry).lower()
                    for pattern in error_patterns:
                        if re.search(pattern, message):
                            issue_counts[pattern] += 1
                            
                            # Store example of the issue
                            if len(error_examples[pattern]) < 3:  # Store up to 3 examples
                                error_examples[pattern].append({
                                    "message": self._extract_message(entry),
                                    "timestamp": self._extract_timestamp(entry),
                                    "source": source
                                })
                
                # Add to summary
                analysis["summary"][source] = {
                    "total_entries": len(logs),
                    "priorities": priorities
                }
                
                # Add error and warning counts
                analysis["error_count"] += (
                    priorities.get("emerg", 0) +
                    priorities.get("alert", 0) +
                    priorities.get("crit", 0) +
                    priorities.get("err", 0)
                )
                analysis["warning_count"] += priorities.get("warning", 0)
                
                # Identify critical issues
                for pattern in ["error", "fail", "exception", "crash", "segfault", "core dump"]:
                    if issue_counts[pattern] > 0:
                        analysis["critical_issues"].append({
                            "pattern": pattern,
                            "count": issue_counts[pattern],
                            "source": source,
                            "examples": error_examples[pattern]
                        })
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return {"error": str(e)}
    
    def get_log_statistics(self, 
                         sources: List[str] = ["journal", "syslog"],
                         days: int = 7) -> Dict[str, Any]:
        """Get statistics about log volume and characteristics over time.
        
        Args:
            sources: List of log sources to analyze
            days: Number of days to analyze
        
        Returns:
            Log statistics
        """
        try:
            # Calculate the start date (days ago)
            start_date = datetime.now() - timedelta(days=days)
            start_str = start_date.strftime("%Y-%m-%d")
            
            statistics = {
                "timestamp": time.time(),
                "period": {
                    "days": days,
                    "start_date": start_str
                },
                "sources": {},
                "total_entries": 0,
                "entries_per_day": {},
                "severity_distribution": {
                    "error": 0,
                    "warning": 0,
                    "info": 0,
                    "debug": 0,
                    "other": 0
                }
            }
            
            # Initialize entries per day
            for i in range(days):
                day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                statistics["entries_per_day"][day] = 0
            
            # Analyze each source
            for source in sources:
                # Get logs
                logs = []
                
                if source == "journal":
                    logs = self.get_journal_logs(
                        count=self.default_max_entries * days,
                        since=start_str
                    )
                elif source == "syslog":
                    logs = self.get_system_logs(
                        count=self.default_max_entries * days,
                        since=start_str,
                        log_type="syslog"
                    )
                else:
                    # Try as a system log type
                    logs = self.get_system_logs(
                        count=self.default_max_entries * days,
                        since=start_str,
                        log_type=source
                    )
                
                # Count entries by day and severity
                daily_counts = {}
                severity_counts = {
                    "error": 0,
                    "warning": 0,
                    "info": 0,
                    "debug": 0,
                    "other": 0
                }
                
                for entry in logs:
                    # Count by day
                    day = self._extract_day(entry)
                    if day:
                        daily_counts[day] = daily_counts.get(day, 0) + 1
                    
                    # Count by severity
                    priority = self._extract_priority(entry)
                    if priority in ["emerg", "alert", "crit", "err"]:
                        severity_counts["error"] += 1
                    elif priority == "warning":
                        severity_counts["warning"] += 1
                    elif priority in ["info", "notice"]:
                        severity_counts["info"] += 1
                    elif priority == "debug":
                        severity_counts["debug"] += 1
                    else:
                        severity_counts["other"] += 1
                
                # Add to statistics
                statistics["sources"][source] = {
                    "total_entries": len(logs),
                    "daily_counts": daily_counts,
                    "severity_counts": severity_counts
                }
                
                statistics["total_entries"] += len(logs)
                
                # Add to overall daily counts
                for day, count in daily_counts.items():
                    if day in statistics["entries_per_day"]:
                        statistics["entries_per_day"][day] += count
                
                # Add to overall severity distribution
                for severity, count in severity_counts.items():
                    statistics["severity_distribution"][severity] += count
            
            return statistics
        
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {"error": str(e)}
    
    def list_available_logs(self) -> Dict[str, Any]:
        """List all available log sources on the system.
        
        Returns:
            Dictionary with available log sources and their details
        """
        try:
            available_logs = {
                "system_logs": [],
                "journal_units": [],
                "application_logs": [],
                "special_logs": []
            }
            
            # Check standard system logs
            system_log_types = ["syslog", "auth", "daemon", "kern", "mail", "user", "messages"]
            for log_type in system_log_types:
                path = self.log_paths.get(log_type)
                if path and os.path.exists(path):
                    available_logs["system_logs"].append({
                        "name": log_type,
                        "path": path,
                        "size": os.path.getsize(path)
                    })
            
            # Check journal units
            try:
                cmd = ["journalctl", "--field=_SYSTEMD_UNIT"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    units = sorted(list(set(result.stdout.strip().split("\n"))))
                    for unit in units:
                        if unit and ".service" in unit:
                            available_logs["journal_units"].append({
                                "name": unit,
                                "type": "systemd"
                            })
            except Exception as e:
                logger.error(f"Error listing journal units: {e}")
            
            # Check application logs
            app_log_types = ["apache_access", "apache_error", "mysql", "postgresql"]
            for log_type in app_log_types:
                path = self.log_paths.get(log_type)
                if path and os.path.exists(path):
                    available_logs["application_logs"].append({
                        "name": log_type,
                        "path": path,
                        "size": os.path.getsize(path)
                    })
            
            # Check special logs
            special_log_types = ["audit", "boot"]
            for log_type in special_log_types:
                path = self.log_paths.get(log_type)
                if path and os.path.exists(path):
                    available_logs["special_logs"].append({
                        "name": log_type,
                        "path": path,
                        "size": os.path.getsize(path)
                    })
            
            # Add special source for systemd journal
            available_logs["special_logs"].append({
                "name": "journal",
                "type": "journald",
                "description": "Systemd journal logs"
            })
            
            # Add special source for kernel messages
            available_logs["special_logs"].append({
                "name": "dmesg",
                "type": "kernel",
                "description": "Kernel ring buffer messages"
            })
            
            return available_logs
        
        except Exception as e:
            logger.error(f"Error listing available logs: {e}")
            return {"error": str(e)}
    
    def _search_journal(self, 
                      query: str,
                      count: int,
                      since: Optional[str],
                      until: Optional[str]) -> List[Dict[str, Any]]:
        """Search the systemd journal.
        
        Args:
            query: Search query
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
        
        Returns:
            List of matching log entries
        """
        try:
            # Construct the command
            cmd = ["journalctl", "-g", query, "-o", "json"]
            
            if since:
                cmd.extend(["--since", since])
            if until:
                cmd.extend(["--until", until])
            
            cmd.extend(["-n", str(count)])
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error searching journal: {result.stderr}")
                return []
            
            # Parse the output
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing journald log entry: {e}")
            
            return logs
        
        except Exception as e:
            logger.error(f"Error searching journald: {e}")
            return []
    
    def _search_syslog(self,
                     query: str,
                     count: int,
                     since: Optional[str],
                     until: Optional[str]) -> List[Dict[str, Any]]:
        """Search syslog.
        
        Args:
            query: Search query
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
        
        Returns:
            List of matching log entries
        """
        return self._search_system_log(query, count, since, until, "syslog")
    
    def _search_system_log(self,
                         query: str,
                         count: int,
                         since: Optional[str],
                         until: Optional[str],
                         log_type: str) -> List[Dict[str, Any]]:
        """Search a system log file.
        
        Args:
            query: Search query
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
            log_type: System log type
        
        Returns:
            List of matching log entries
        """
        try:
            log_path = self.log_paths.get(log_type)
            if not log_path or not os.path.exists(log_path):
                logger.error(f"Log file not found: {log_path}")
                return []
            
            # Use grep to search the log file
            cmd = ["grep", "-i", query, log_path]
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0 and result.returncode != 1:  # 1 means no matches found
                logger.error(f"Error searching log file: {result.stderr}")
                return []
            
            # Parse the output
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    log_entry = self._parse_syslog_line(line, log_type)
                    
                    # Apply time filtering if needed
                    if since or until:
                        if "timestamp" in log_entry:
                            if self._filter_by_time(log_entry["timestamp"], since, until):
                                logs.append(log_entry)
                        else:
                            logs.append(log_entry)
                    else:
                        logs.append(log_entry)
            
            # Return only the requested number of entries
            return logs[:count]
        
        except Exception as e:
            logger.error(f"Error searching system log: {e}")
            return []
    
    def _search_dmesg(self,
                    query: str,
                    count: int,
                    since: Optional[str],
                    until: Optional[str]) -> List[Dict[str, Any]]:
        """Search dmesg.
        
        Args:
            query: Search query
            count: Maximum number of entries to return
            since: Time to start from (not used for dmesg)
            until: Time to end at (not used for dmesg)
        
        Returns:
            List of matching log entries
        """
        try:
            # Use dmesg | grep to search
            cmd = ["dmesg", "|", "grep", "-i", query]
            
            # Execute the command using shell=True because we need pipe redirection
            result = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)
            
            if result.returncode != 0 and result.returncode != 1:  # 1 means no matches found
                logger.error(f"Error searching dmesg: {result.stderr}")
                return []
            
            # Parse the output
            logs = []
            for line in result.stdout.strip().split("\n"):
                if line:  # Skip empty lines
                    log_entry = self._parse_dmesg_line(line)
                    logs.append(log_entry)
            
            # Return only the requested number of entries
            return logs[:count]
        
        except Exception as e:
            logger.error(f"Error searching dmesg: {e}")
            return []
    
    def _search_audit(self,
                    query: str,
                    count: int,
                    since: Optional[str],
                    until: Optional[str]) -> List[Dict[str, Any]]:
        """Search audit logs.
        
        Args:
            query: Search query
            count: Maximum number of entries to return
            since: Time to start from
            until: Time to end at
        
        Returns:
            List of matching log entries
        """
        try:
            # Check if ausearch is available
            ausearch_available = subprocess.run(["which", "ausearch"], 
                                              capture_output=True).returncode == 0
            
            if ausearch_available:
                # Construct the command
                cmd = ["ausearch", "-i"]
                
                if since:
                    # Convert since to a start time for ausearch
                    if since.endswith("m"):
                        minutes = int(since[:-1])
                        cmd.extend(["-ts", f"recent-{minutes}"])
                    elif since.endswith("h"):
                        hours = int(since[:-1])
                        cmd.extend(["-ts", f"recent-{hours*60}"])
                    else:
                        cmd.extend(["-ts", since])
                
                # Add search string
                cmd.extend(["--message", query])
                
                # Execute the command
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0 and result.returncode != 1:  # 1 means no records found
                    logger.error(f"Error searching audit logs: {result.stderr}")
                    return []
                
                # Parse the output
                return self._parse_audit_logs(result.stdout, count)
            
            # If ausearch is not available, try with grep
            log_path = self.log_paths.get("audit")
            if not log_path or not os.path.exists(log_path):
                logger.error(f"Audit log file not found and ausearch not available")
                return []
            
            # Use grep to search the log file
            cmd = ["grep", "-i", query, log_path]
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0 and result.returncode != 1:  # 1 means no matches found
                logger.error(f"Error searching audit log file: {result.stderr}")
                return []
            
            # Parse the output
            logs = self._parse_audit_logs(result.stdout, count)
            return logs
        
        except Exception as e:
            logger.error(f"Error searching audit logs: {e}")
            return []
    
    def _parse_syslog_line(self, line: str, log_type: str) -> Dict[str, Any]:
        """Parse a syslog line into a structured format.
        
        Args:
            line: Log line
            log_type: Type of log
        
        Returns:
            Dictionary with parsed log entry
        """
        try:
            # Common syslog format: Apr 25 15:24:01 hostname process[pid]: message
            # Try to parse timestamp
            timestamp = None
            parts = line.split(" ", 3)
            if len(parts) >= 3:
                try:
                    # Try to parse the timestamp part (Apr 25 15:24:01)
                    ts_str = " ".join(parts[:3])
                    timestamp = time.strptime(ts_str, "%b %d %H:%M:%S")
                    timestamp = time.mktime(timestamp)
                except ValueError:
                    pass
            
            # Try to extract priority/severity
            priority = "info"  # default
            if "error" in line.lower() or "err:" in line.lower():
                priority = "err"
            elif "warning" in line.lower() or "warn:" in line.lower():
                priority = "warning"
            elif "notice" in line.lower():
                priority = "notice"
            elif "debug" in line.lower():
                priority = "debug"
            
            # Extract process name and pid
            process_name = None
            pid = None
            process_match = re.search(r'(\S+)\[(\d+)\]:', line)
            if process_match:
                process_name = process_match.group(1)
                pid = int(process_match.group(2))
            
            return {
                "message": line,
                "timestamp": timestamp,
                "priority": priority,
                "process_name": process_name,
                "pid": pid,
                "source": log_type
            }
        
        except Exception as e:
            logger.error(f"Error parsing syslog line: {e}")
            return {"message": line, "source": log_type}
    
    def _parse_dmesg_line(self, line: str) -> Dict[str, Any]:
        """Parse a dmesg line into a structured format.
        
        Args:
            line: Log line
        
        Returns:
            Dictionary with parsed log entry
        """
        try:
            # Common dmesg format: [    0.000000] kernel message
            timestamp = None
            message = line
            
            # Try to extract timestamp
            ts_match = re.match(r'\[\s*(\d+\.\d+)\]', line)
            if ts_match:
                seconds_since_boot = float(ts_match.group(1))
                timestamp = time.time() - seconds_since_boot
                message = line[ts_match.end():].strip()
            
            # Try to extract priority/severity
            priority = "info"  # default
            if "error" in line.lower() or "err:" in line.lower():
                priority = "err"
            elif "warning" in line.lower() or "warn:" in line.lower():
                priority = "warning"
            elif "notice" in line.lower():
                priority = "notice"
            elif "debug" in line.lower():
                priority = "debug"
            
            return {
                "message": message,
                "raw": line,
                "timestamp": timestamp,
                "priority": priority,
                "source": "dmesg"
            }
        
        except Exception as e:
            logger.error(f"Error parsing dmesg line: {e}")
            return {"message": line, "source": "dmesg"}
    
    def _parse_audit_logs(self, output: str, count: int) -> List[Dict[str, Any]]:
        """Parse audit log output.
        
        Args:
            output: Output from ausearch or audit log file
            count: Maximum number of entries to return
        
        Returns:
            List of parsed audit log entries
        """
        try:
            logs = []
            
            # Split into audit records (each record starts with 'type=')
            current_record = ""
            for line in output.split("\n"):
                if line.startswith("type="):
                    if current_record:
                        # Parse the previous record
                        record = self._parse_audit_record(current_record)
                        logs.append(record)
                        
                        # Check if we have enough records
                        if len(logs) >= count:
                            break
                    
                    # Start a new record
                    current_record = line
                elif line and current_record:
                    # Continue previous record
                    current_record += " " + line
            
            # Don't forget the last record
            if current_record and len(logs) < count:
                record = self._parse_audit_record(current_record)
                logs.append(record)
            
            return logs
        
        except Exception as e:
            logger.error(f"Error parsing audit logs: {e}")
            return [{"message": output[:100], "source": "audit", "error": str(e)}]
    
    def _parse_audit_record(self, record: str) -> Dict[str, Any]:
        """Parse a single audit record.
        
        Args:
            record: Audit record string
        
        Returns:
            Dictionary with parsed audit record
        """
        try:
            result = {
                "source": "audit",
                "raw": record
            }
            
            # Extract key-value pairs
            for pair in record.split(" "):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    result[key] = value
            
            # Extract timestamp
            if "msg=audit" in record and ":" in record:
                ts_parts = record.split(":", 1)[0].split("(")[-1]
                try:
                    result["timestamp"] = float(ts_parts)
                except ValueError:
                    pass
            
            # Add printable message
            result["message"] = f"type={result.get('type', 'unknown')} {result.get('msg', '')}"
            
            return result
        
        except Exception as e:
            logger.error(f"Error parsing audit record: {e}")
            return {"source": "audit", "raw": record, "message": record}
    
    def _filter_by_time(self, 
                      timestamp: Optional[float],
                      since: Optional[str],
                      until: Optional[str]) -> bool:
        """Check if a log entry's timestamp is within the specified time range.
        
        Args:
            timestamp: Log entry timestamp
            since: Time to start from
            until: Time to end at
        
        Returns:
            Whether the entry is within the time range
        """
        if timestamp is None:
            return True  # Include entries without timestamps
        
        now = time.time()
        
        # Parse "since" parameter
        if since:
            start_time = None
            
            # Parse relative time specs
            if since.endswith("m"):
                minutes = int(since[:-1])
                start_time = now - minutes * 60
            elif since.endswith("h"):
                hours = int(since[:-1])
                start_time = now - hours * 60 * 60
            elif since.endswith("d"):
                days = int(since[:-1])
                start_time = now - days * 24 * 60 * 60
            else:
                # Try to parse as absolute time
                try:
                    start_time = time.mktime(time.strptime(since, "%Y-%m-%d"))
                except ValueError:
                    try:
                        start_time = time.mktime(time.strptime(since, "%Y-%m-%d %H:%M:%S"))
                    except ValueError:
                        pass
            
            if start_time and timestamp < start_time:
                return False
        
        # Parse "until" parameter
        if until:
            end_time = None
            
            # Parse relative time specs
            if until.endswith("m"):
                minutes = int(until[:-1])
                end_time = now - minutes * 60
            elif until.endswith("h"):
                hours = int(until[:-1])
                end_time = now - hours * 60 * 60
            elif until.endswith("d"):
                days = int(until[:-1])
                end_time = now - days * 24 * 60 * 60
            else:
                # Try to parse as absolute time
                try:
                    end_time = time.mktime(time.strptime(until, "%Y-%m-%d"))
                except ValueError:
                    try:
                        end_time = time.mktime(time.strptime(until, "%Y-%m-%d %H:%M:%S"))
                    except ValueError:
                        pass
            
            if end_time and timestamp > end_time:
                return False
        
        return True
    
    def _extract_priority(self, entry: Dict[str, Any]) -> str:
        """Extract priority from a log entry.
        
        Args:
            entry: Log entry
        
        Returns:
            Priority string
        """
        # Check direct priority field
        if "priority" in entry:
            return entry["priority"]
        
        # Check journald priority
        if "PRIORITY" in entry:
            priority_map = {
                "0": "emerg",
                "1": "alert",
                "2": "crit",
                "3": "err",
                "4": "warning",
                "5": "notice",
                "6": "info",
                "7": "debug"
            }
            return priority_map.get(entry["PRIORITY"], "info")
        
        # Try to guess from message
        message = self._extract_message(entry).lower()
        if "emergency" in message or "emerg" in message:
            return "emerg"
        elif "alert" in message:
            return "alert"
        elif "critical" in message or "crit" in message:
            return "crit"
        elif "error" in message or "err" in message:
            return "err"
        elif "warning" in message or "warn" in message:
            return "warning"
        elif "notice" in message:
            return "notice"
        elif "debug" in message:
            return "debug"
        else:
            return "info"
    
    def _extract_message(self, entry: Dict[str, Any]) -> str:
        """Extract message from a log entry.
        
        Args:
            entry: Log entry
        
        Returns:
            Message string
        """
        if "message" in entry:
            return entry["message"]
        elif "MESSAGE" in entry:
            return entry["MESSAGE"]
        elif "raw" in entry:
            return entry["raw"]
        else:
            # Try to serialize the entire entry as string
            return str(entry)
    
    def _extract_timestamp(self, entry: Dict[str, Any]) -> Optional[float]:
        """Extract timestamp from a log entry.
        
        Args:
            entry: Log entry
        
        Returns:
            Timestamp or None if not available
        """
        if "timestamp" in entry:
            return entry["timestamp"]
        elif "__REALTIME_TIMESTAMP" in entry:
            try:
                # Convert microseconds to seconds
                return int(entry["__REALTIME_TIMESTAMP"]) / 1000000
            except (ValueError, TypeError):
                pass
        elif "SYSLOG_TIMESTAMP" in entry:
            try:
                dt = datetime.strptime(entry["SYSLOG_TIMESTAMP"], "%b %d %H:%M:%S")
                dt = dt.replace(year=datetime.now().year)
                return dt.timestamp()
            except ValueError:
                pass
        return None
    
    def _extract_day(self, entry: Dict[str, Any]) -> Optional[str]:
        """Extract day from a log entry.
        
        Args:
            entry: Log entry
        
        Returns:
            Day string in YYYY-MM-DD format or None if not available
        """
        timestamp = self._extract_timestamp(entry)
        if timestamp:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        return None
