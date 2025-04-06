#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: System monitoring module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import asyncio
import time
import json
import logging
import socket
import threading
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

import psutil

from mcp_lcu_server.linux.cpu import CPUOperations
from mcp_lcu_server.linux.memory import MemoryOperations
from mcp_lcu_server.linux.process import ProcessOperations
from mcp_lcu_server.linux.storage import StorageOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


class MonitoringOperations:
    """Class for system monitoring on Linux systems."""
    
    def __init__(self, config: Config):
        """Initialize monitoring operations.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.cpu_ops = CPUOperations()
        self.memory_ops = MemoryOperations()
        self.process_ops = ProcessOperations()
        self.storage_ops = StorageOperations()
        
        # Monitoring state
        self.monitoring_enabled = config.monitoring.enabled
        self.monitoring_interval = config.monitoring.interval
        self.monitoring_thread = None
        self.monitoring_lock = threading.Lock()
        self.stop_monitoring_flag = threading.Event()
        
        # Callbacks for monitoring events
        self.callbacks = {}
        
        # Metrics store
        self.metrics_store = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "network": [],
            "system": []
        }
        
        # Maximum number of metrics to store (1 hour worth of data at default interval)
        self.max_metrics = 3600 // self.monitoring_interval
    
    def start_monitoring(self) -> bool:
        """Start system monitoring.
        
        Returns:
            Whether monitoring was started successfully
        """
        with self.monitoring_lock:
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                logger.info("Monitoring is already running")
                return False
            
            if not self.monitoring_enabled:
                logger.info("Monitoring is disabled in configuration")
                return False
            
            # Reset stop flag
            self.stop_monitoring_flag.clear()
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info(f"Started system monitoring (interval: {self.monitoring_interval}s)")
            return True
    
    def stop_monitoring(self) -> bool:
        """Stop system monitoring.
        
        Returns:
            Whether monitoring was stopped successfully
        """
        with self.monitoring_lock:
            if not self.monitoring_thread or not self.monitoring_thread.is_alive():
                logger.info("Monitoring is not running")
                return False
            
            # Set stop flag
            self.stop_monitoring_flag.set()
            
            # Wait for thread to terminate (with timeout)
            self.monitoring_thread.join(timeout=5.0)
            
            if self.monitoring_thread.is_alive():
                logger.warning("Monitoring thread did not terminate gracefully")
                return False
            
            self.monitoring_thread = None
            logger.info("Stopped system monitoring")
            return True
    
    def is_monitoring_running(self) -> bool:
        """Check if monitoring is running.
        
        Returns:
            Whether monitoring is running
        """
        with self.monitoring_lock:
            return self.monitoring_thread is not None and self.monitoring_thread.is_alive()
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring status.
        
        Returns:
            Dictionary with monitoring status
        """
        with self.monitoring_lock:
            return {
                "enabled": self.monitoring_enabled,
                "running": self.is_monitoring_running(),
                "interval": self.monitoring_interval,
                "metrics": {metric: len(data) for metric, data in self.metrics_store.items()}
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status.
        
        Returns:
            Dictionary with system status
        """
        try:
            # Collect current system metrics
            metrics = self._collect_system_metrics()
            
            # Get previous metrics if available
            prev_metrics = self.metrics_store["system"][-1] if self.metrics_store["system"] else None
            
            # Calculate system status from metrics
            status = self._calculate_system_status(metrics, prev_metrics)
            
            return status
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    def get_cpu_metrics(self, count: int = 60) -> List[Dict[str, Any]]:
        """Get CPU metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            List of CPU metrics
        """
        with self.monitoring_lock:
            # Get most recent metrics
            metrics = self.metrics_store["cpu"][-count:] if self.metrics_store["cpu"] else []
            return metrics
    
    def get_memory_metrics(self, count: int = 60) -> List[Dict[str, Any]]:
        """Get memory metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            List of memory metrics
        """
        with self.monitoring_lock:
            # Get most recent metrics
            metrics = self.metrics_store["memory"][-count:] if self.metrics_store["memory"] else []
            return metrics
    
    def get_disk_metrics(self, count: int = 60) -> List[Dict[str, Any]]:
        """Get disk metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            List of disk metrics
        """
        with self.monitoring_lock:
            # Get most recent metrics
            metrics = self.metrics_store["disk"][-count:] if self.metrics_store["disk"] else []
            return metrics
    
    def get_network_metrics(self, count: int = 60) -> List[Dict[str, Any]]:
        """Get network metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            List of network metrics
        """
        with self.monitoring_lock:
            # Get most recent metrics
            metrics = self.metrics_store["network"][-count:] if self.metrics_store["network"] else []
            return metrics
    
    def get_system_metrics(self, count: int = 60) -> List[Dict[str, Any]]:
        """Get system metrics.
        
        Args:
            count: Number of metrics to return (most recent)
        
        Returns:
            List of system metrics
        """
        with self.monitoring_lock:
            # Get most recent metrics
            metrics = self.metrics_store["system"][-count:] if self.metrics_store["system"] else []
            return metrics
    
    def register_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for monitoring events.
        
        Args:
            event_type: Event type (cpu, memory, disk, network, system)
            callback: Callback function to be called when the event occurs
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check system health.
        
        Returns:
            Dictionary with system health information
        """
        try:
            # Get current system status
            status = self.get_system_status()
            
            # Get system metrics
            system_metrics = self.get_system_metrics(60)  # Last hour
            
            # Determine health status
            health_status = "Healthy"
            severity = 0
            issues = []
            
            # Check CPU usage
            cpu_usage = status.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > 90:
                health_status = "Critical"
                severity = 3
                issues.append({
                    "component": "cpu",
                    "severity": "critical",
                    "message": f"High CPU usage ({cpu_usage:.1f}%)"
                })
            elif cpu_usage > 75:
                if severity < 2:
                    health_status = "Warning"
                    severity = 2
                issues.append({
                    "component": "cpu",
                    "severity": "warning",
                    "message": f"Elevated CPU usage ({cpu_usage:.1f}%)"
                })
            
            # Check memory usage
            memory_usage = status.get("memory", {}).get("percent", 0)
            if memory_usage > 90:
                health_status = "Critical"
                severity = 3
                issues.append({
                    "component": "memory",
                    "severity": "critical",
                    "message": f"High memory usage ({memory_usage:.1f}%)"
                })
            elif memory_usage > 75:
                if severity < 2:
                    health_status = "Warning"
                    severity = 2
                issues.append({
                    "component": "memory",
                    "severity": "warning",
                    "message": f"Elevated memory usage ({memory_usage:.1f}%)"
                })
            
            # Check disk usage
            for disk in status.get("disks", []):
                usage = disk.get("percent", 0)
                mountpoint = disk.get("mountpoint", "unknown")
                
                if usage > 90:
                    health_status = "Critical"
                    severity = 3
                    issues.append({
                        "component": "disk",
                        "severity": "critical",
                        "message": f"High disk usage on {mountpoint} ({usage:.1f}%)"
                    })
                elif usage > 75:
                    if severity < 2:
                        health_status = "Warning"
                        severity = 2
                    issues.append({
                        "component": "disk",
                        "severity": "warning",
                        "message": f"Elevated disk usage on {mountpoint} ({usage:.1f}%)"
                    })
            
            # Check system load
            load_avg = status.get("cpu", {}).get("load_average", {})
            load_1min = load_avg.get("1min_per_cpu", 0)
            
            if load_1min > 3.0:
                health_status = "Critical"
                severity = 3
                issues.append({
                    "component": "load",
                    "severity": "critical",
                    "message": f"Very high system load (load per CPU: {load_1min:.1f})"
                })
            elif load_1min > 1.5:
                if severity < 2:
                    health_status = "Warning"
                    severity = 2
                issues.append({
                    "component": "load",
                    "severity": "warning",
                    "message": f"High system load (load per CPU: {load_1min:.1f})"
                })
            
            # Generate recommendations
            recommendations = []
            
            if any(issue["component"] == "cpu" and issue["severity"] == "critical" for issue in issues):
                recommendations.append("Identify and terminate CPU-intensive processes")
            
            if any(issue["component"] == "memory" and issue["severity"] == "critical" for issue in issues):
                recommendations.append("Check for memory leaks or increase system memory")
            
            if any(issue["component"] == "disk" and issue["severity"] == "critical" for issue in issues):
                recommendations.append("Free up disk space by removing unnecessary files")
            
            if any(issue["component"] == "load" and issue["severity"] == "critical" for issue in issues):
                recommendations.append("Reduce system load by terminating unnecessary processes")
            
            # Create health check report
            health_check = {
                "timestamp": time.time(),
                "status": health_status,
                "issues": issues,
                "recommendations": recommendations,
                "system_status": status
            }
            
            return health_check
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {"error": str(e)}
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        prev_net_counters = None
        prev_disk_counters = None
        prev_time = time.time()
        
        while not self.stop_monitoring_flag.is_set():
            try:
                # Get current time
                current_time = time.time()
                elapsed_time = current_time - prev_time
                
                # Collect CPU metrics
                if "cpu" in self.config.monitoring.metrics:
                    cpu_metrics = self._collect_cpu_metrics()
                    self._add_metrics("cpu", cpu_metrics)
                    self._trigger_callbacks("cpu", cpu_metrics)
                
                # Collect memory metrics
                if "memory" in self.config.monitoring.metrics:
                    memory_metrics = self._collect_memory_metrics()
                    self._add_metrics("memory", memory_metrics)
                    self._trigger_callbacks("memory", memory_metrics)
                
                # Collect disk metrics
                if "disk" in self.config.monitoring.metrics:
                    disk_metrics = self._collect_disk_metrics(prev_disk_counters, elapsed_time)
                    self._add_metrics("disk", disk_metrics)
                    self._trigger_callbacks("disk", disk_metrics)
                    
                    # Update previous counters
                    prev_disk_counters = psutil.disk_io_counters(perdisk=True)
                
                # Collect network metrics
                if "network" in self.config.monitoring.metrics:
                    network_metrics = self._collect_network_metrics(prev_net_counters, elapsed_time)
                    self._add_metrics("network", network_metrics)
                    self._trigger_callbacks("network", network_metrics)
                    
                    # Update previous counters
                    prev_net_counters = psutil.net_io_counters(pernic=True)
                
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self._add_metrics("system", system_metrics)
                self._trigger_callbacks("system", system_metrics)
                
                # Calculate system status
                system_status = self._calculate_system_status(system_metrics, None)
                self._trigger_callbacks("status", system_status)
                
                # Update previous time
                prev_time = current_time
                
                # Sleep until next collection
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _add_metrics(self, metric_type: str, metrics: Dict[str, Any]) -> None:
        """Add metrics to the store.
        
        Args:
            metric_type: Metric type (cpu, memory, disk, network, system)
            metrics: Metrics data
        """
        with self.monitoring_lock:
            # Add metrics to store
            self.metrics_store[metric_type].append(metrics)
            
            # Trim metrics if necessary
            if len(self.metrics_store[metric_type]) > self.max_metrics:
                self.metrics_store[metric_type] = self.metrics_store[metric_type][-self.max_metrics:]
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger callbacks for an event.
        
        Args:
            event_type: Event type
            data: Event data
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for event {event_type}: {e}")
    
    def _collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU metrics.
        
        Returns:
            Dictionary with CPU metrics
        """
        try:
            # Get CPU usage
            cpu_usage = self.cpu_ops.get_cpu_usage(per_cpu=True)
            cpu_avg = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
            
            # Get CPU times
            cpu_times = self.cpu_ops.get_cpu_times(per_cpu=False)
            
            # Get load average
            load_avg = self.cpu_ops.get_load_average()
            
            # Get CPU stats
            cpu_stats = self.cpu_ops.get_cpu_stats()
            
            # Create metrics
            metrics = {
                "timestamp": time.time(),
                "usage": {
                    "average": cpu_avg,
                    "per_cpu": cpu_usage
                },
                "times": cpu_times,
                "load_average": load_avg,
                "stats": cpu_stats
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory metrics.
        
        Returns:
            Dictionary with memory metrics
        """
        try:
            # Get memory info
            memory_info = self.memory_ops.get_memory_info()
            
            # Get swap info
            swap_info = self.memory_ops.get_swap_info()
            
            # Create metrics
            metrics = {
                "timestamp": time.time(),
                "memory": {
                    "total": memory_info.get("total", 0),
                    "available": memory_info.get("available", 0),
                    "used": memory_info.get("used", 0),
                    "free": memory_info.get("free", 0),
                    "percent": memory_info.get("percent", 0),
                    "buffers": memory_info.get("buffers", 0),
                    "cached": memory_info.get("cached", 0),
                    "shared": memory_info.get("shared", 0)
                },
                "swap": {
                    "total": swap_info.get("total", 0),
                    "used": swap_info.get("used", 0),
                    "free": swap_info.get("free", 0),
                    "percent": swap_info.get("percent", 0),
                    "sin": swap_info.get("sin", 0),
                    "sout": swap_info.get("sout", 0)
                }
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _collect_disk_metrics(self, 
                             prev_counters: Optional[Dict[str, Any]], 
                             elapsed_time: float) -> Dict[str, Any]:
        """Collect disk metrics.
        
        Args:
            prev_counters: Previous disk I/O counters
            elapsed_time: Elapsed time since last collection
        
        Returns:
            Dictionary with disk metrics
        """
        try:
            # Get disk usage
            partitions = self.storage_ops.list_partitions()
            
            # Filter mounted partitions with usage data
            usage = []
            for partition in partitions:
                if "total" in partition and partition["total"] > 0:
                    usage.append({
                        "device": partition.get("device", ""),
                        "mountpoint": partition.get("mountpoint", ""),
                        "fstype": partition.get("fstype", ""),
                        "total": partition.get("total", 0),
                        "used": partition.get("used", 0),
                        "free": partition.get("free", 0),
                        "percent": partition.get("percent", 0)
                    })
            
            # Get disk I/O counters
            io_counters = psutil.disk_io_counters(perdisk=True)
            
            # Calculate I/O rates
            io_rates = {}
            if prev_counters and elapsed_time > 0:
                for disk, counters in io_counters.items():
                    if disk in prev_counters:
                        prev = prev_counters[disk]
                        read_bytes_rate = (counters.read_bytes - prev.read_bytes) / elapsed_time
                        write_bytes_rate = (counters.write_bytes - prev.write_bytes) / elapsed_time
                        read_count_rate = (counters.read_count - prev.read_count) / elapsed_time
                        write_count_rate = (counters.write_count - prev.write_count) / elapsed_time
                        
                        io_rates[disk] = {
                            "read_bytes_sec": read_bytes_rate,
                            "write_bytes_sec": write_bytes_rate,
                            "read_count_sec": read_count_rate,
                            "write_count_sec": write_count_rate
                        }
            
            # Create metrics
            metrics = {
                "timestamp": time.time(),
                "usage": usage,
                "io_counters": {
                    disk: {
                        "read_count": counters.read_count,
                        "write_count": counters.write_count,
                        "read_bytes": counters.read_bytes,
                        "write_bytes": counters.write_bytes,
                        "read_time": counters.read_time,
                        "write_time": counters.write_time
                    }
                    for disk, counters in io_counters.items()
                },
                "io_rates": io_rates
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting disk metrics: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _collect_network_metrics(self, 
                               prev_counters: Optional[Dict[str, Any]], 
                               elapsed_time: float) -> Dict[str, Any]:
        """Collect network metrics.
        
        Args:
            prev_counters: Previous network I/O counters
            elapsed_time: Elapsed time since last collection
        
        Returns:
            Dictionary with network metrics
        """
        try:
            # Get network I/O counters
            io_counters = psutil.net_io_counters(pernic=True)
            
            # Get network connections
            connections = psutil.net_connections()
            
            # Count connection types
            connection_counts = {
                "tcp": 0,
                "udp": 0,
                "unix": 0,
                "other": 0,
                "established": 0,
                "listening": 0,
                "total": len(connections)
            }
            
            for conn in connections:
                # Count by protocol
                if conn.type == socket.SOCK_STREAM:
                    connection_counts["tcp"] += 1
                elif conn.type == socket.SOCK_DGRAM:
                    connection_counts["udp"] += 1
                elif conn.family == socket.AF_UNIX:
                    connection_counts["unix"] += 1
                else:
                    connection_counts["other"] += 1
                
                # Count by status
                if conn.status == "ESTABLISHED":
                    connection_counts["established"] += 1
                elif conn.status == "LISTEN":
                    connection_counts["listening"] += 1
            
            # Calculate network rates
            net_rates = {}
            if prev_counters and elapsed_time > 0:
                for nic, counters in io_counters.items():
                    if nic in prev_counters:
                        prev = prev_counters[nic]
                        bytes_sent_rate = (counters.bytes_sent - prev.bytes_sent) / elapsed_time
                        bytes_recv_rate = (counters.bytes_recv - prev.bytes_recv) / elapsed_time
                        packets_sent_rate = (counters.packets_sent - prev.packets_sent) / elapsed_time
                        packets_recv_rate = (counters.packets_recv - prev.packets_recv) / elapsed_time
                        
                        net_rates[nic] = {
                            "bytes_sent_sec": bytes_sent_rate,
                            "bytes_recv_sec": bytes_recv_rate,
                            "packets_sent_sec": packets_sent_rate,
                            "packets_recv_sec": packets_recv_rate
                        }
            
            # Create metrics
            metrics = {
                "timestamp": time.time(),
                "io_counters": {
                    nic: {
                        "bytes_sent": counters.bytes_sent,
                        "bytes_recv": counters.bytes_recv,
                        "packets_sent": counters.packets_sent,
                        "packets_recv": counters.packets_recv,
                        "errin": counters.errin,
                        "errout": counters.errout,
                        "dropin": counters.dropin,
                        "dropout": counters.dropout
                    }
                    for nic, counters in io_counters.items()
                },
                "io_rates": net_rates,
                "connections": connection_counts
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics.
        
        Returns:
            Dictionary with system metrics
        """
        try:
            # Get CPU usage
            cpu_usage = self.cpu_ops.get_cpu_usage(per_cpu=False)
            
            # Get memory info
            memory_info = self.memory_ops.get_memory_info()
            
            # Get load average
            load_avg = self.cpu_ops.get_load_average()
            
            # Get disk usage
            partitions = self.storage_ops.list_partitions()
            mounted_partitions = [p for p in partitions if "total" in p and p["total"] > 0]
            disk_usage = [
                {
                    "mountpoint": p.get("mountpoint", ""),
                    "percent": p.get("percent", 0)
                }
                for p in mounted_partitions
            ]
            
            # Get process count
            process_count = len(self.process_ops.list_processes(include_threads=False, include_username=False))
            
            # Get boot time
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Create metrics
            metrics = {
                "timestamp": time.time(),
                "cpu_usage": cpu_usage,
                "memory_usage": memory_info.get("percent", 0),
                "memory_available": memory_info.get("available", 0),
                "load_average": load_avg,
                "disk_usage": disk_usage,
                "process_count": process_count,
                "boot_time": boot_time,
                "uptime": uptime
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {"timestamp": time.time(), "error": str(e)}
    
    def _calculate_system_status(self, 
                                metrics: Dict[str, Any], 
                                prev_metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate system status from metrics.
        
        Args:
            metrics: Current system metrics
            prev_metrics: Previous system metrics
        
        Returns:
            Dictionary with system status
        """
        try:
            # Get CPU usage
            cpu_usage = metrics.get("cpu_usage", 0)
            
            # Get memory usage
            memory_usage = metrics.get("memory_usage", 0)
            memory_available = metrics.get("memory_available", 0)
            
            # Get load average
            load_avg = metrics.get("load_average", {})
            
            # Get disk usage
            disk_usage = metrics.get("disk_usage", [])
            
            # Get process count
            process_count = metrics.get("process_count", 0)
            
            # Get uptime
            uptime = metrics.get("uptime", 0)
            
            # Determine system status
            status = "Healthy"
            
            # Check CPU usage
            if cpu_usage > 90:
                status = "Critical"
            elif cpu_usage > 75 and status != "Critical":
                status = "Degraded"
            elif cpu_usage > 60 and status not in ["Critical", "Degraded"]:
                status = "Warning"
            
            # Check memory usage
            if memory_usage > 90:
                status = "Critical"
            elif memory_usage > 75 and status != "Critical":
                status = "Degraded"
            elif memory_usage > 60 and status not in ["Critical", "Degraded"]:
                status = "Warning"
            
            # Check disk usage
            for disk in disk_usage:
                if disk.get("percent", 0) > 90:
                    status = "Critical"
                    break
                elif disk.get("percent", 0) > 75 and status != "Critical":
                    status = "Degraded"
                elif disk.get("percent", 0) > 60 and status not in ["Critical", "Degraded"]:
                    status = "Warning"
            
            # Create status
            system_status = {
                "timestamp": time.time(),
                "status": status,
                "cpu": {
                    "usage_percent": cpu_usage,
                    "load_average": load_avg
                },
                "memory": {
                    "percent": memory_usage,
                    "available": memory_available,
                    "available_human": self._bytes_to_human(memory_available)
                },
                "disks": [
                    {
                        "mountpoint": disk.get("mountpoint", ""),
                        "percent": disk.get("percent", 0)
                    }
                    for disk in disk_usage
                ],
                "processes": {
                    "count": process_count
                },
                "uptime": {
                    "seconds": uptime,
                    "human": self._format_uptime(uptime)
                }
            }
            
            return system_status
        except Exception as e:
            logger.error(f"Error calculating system status: {e}")
            return {
                "timestamp": time.time(),
                "status": "Unknown",
                "error": str(e)
            }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in seconds to a human-readable string.
        
        Args:
            seconds: Uptime in seconds
        
        Returns:
            Human-readable uptime string
        """
        days = int(seconds // (24 * 3600))
        seconds %= (24 * 3600)
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds %= 60
        
        result = []
        if days > 0:
            result.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0 or days > 0:
            result.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 or hours > 0 or days > 0:
            result.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        result.append(f"{int(seconds)} second{'s' if int(seconds) != 1 else ''}")
        
        return ", ".join(result)
    
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
