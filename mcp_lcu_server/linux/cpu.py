#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: CPU operations module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import time
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple

import psutil
import cpuinfo

logger = logging.getLogger(__name__)


class CPUOperations:
    """Class for CPU operations on Linux systems."""
    
    def __init__(self):
        """Initialize CPU operations."""
        self._last_cpu_times: Optional[Dict[int, Any]] = None
        self._last_time = time.time()
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information.
        
        Returns:
            Dictionary with CPU information including:
            - brand_raw: CPU brand string
            - count: Number of CPU cores
            - architecture: CPU architecture
            - flags: List of CPU flags
            - frequency: Current, min, and max CPU frequency
            - cache: Cache sizes (L1, L2, L3)
            - topology: CPU topology information
        """
        info = {}
        
        try:
            # Get CPU info from py-cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            info["brand_raw"] = cpu_info.get("brand_raw", "Unknown")
            info["architecture"] = cpu_info.get("arch", "Unknown")
            info["bits"] = cpu_info.get("bits", 0)
            info["flags"] = cpu_info.get("flags", [])
            info["vendor_id"] = cpu_info.get("vendor_id", "Unknown")
            
            # Get CPU count and topology information
            info["count"] = {
                "physical": psutil.cpu_count(logical=False) or 0,
                "logical": psutil.cpu_count(logical=True) or 0
            }
            
            # Get CPU frequency
            freq = psutil.cpu_freq(percpu=False)
            if freq:
                info["frequency"] = {
                    "current": freq.current,
                    "min": freq.min,
                    "max": freq.max
                }
            else:
                # Try to get frequency from /proc/cpuinfo
                freq_info = self._get_cpu_freq_from_proc()
                info["frequency"] = freq_info if freq_info else {"current": 0, "min": 0, "max": 0}
            
            # Get per-CPU frequency if available
            cpu_freqs = psutil.cpu_freq(percpu=True)
            if cpu_freqs:
                info["per_cpu_frequency"] = [
                    {"current": freq.current, "min": freq.min, "max": freq.max}
                    if freq else {"current": 0, "min": 0, "max": 0}
                    for freq in cpu_freqs
                ]
            
            # Get cache information
            cache_info = self._get_cache_info()
            if cache_info:
                info["cache"] = cache_info
            
            # Get CPU topology information (if available)
            topology = self._get_cpu_topology()
            if topology:
                info["topology"] = topology
            
            # Get CPU vulnerability information
            vulnerabilities = self._get_cpu_vulnerabilities()
            if vulnerabilities:
                info["vulnerabilities"] = vulnerabilities
            
            # Get CPU scaling governor
            governor = self._get_cpu_governor()
            if governor:
                info["governor"] = governor
            
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            # Return basic info even if detailed info fails
            info["error"] = str(e)
        
        return info
    
    def get_cpu_usage(self, per_cpu: bool = False, interval: float = 0.1) -> Union[float, List[float]]:
        """Get CPU usage percentage.
        
        Args:
            per_cpu: Whether to return per-CPU usage
            interval: Time interval for CPU usage calculation (seconds)
        
        Returns:
            CPU usage percentage (0-100) or list of percentages for each CPU
        """
        if interval <= 0:
            interval = 0.1
        
        try:
            return psutil.cpu_percent(interval=interval, percpu=per_cpu)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            if per_cpu:
                # Return zero for each CPU
                return [0.0] * (psutil.cpu_count() or 1)
            return 0.0
    
    def get_cpu_times(self, per_cpu: bool = False) -> Union[Dict[str, float], List[Dict[str, float]]]:
        """Get CPU time spent in various modes.
        
        Args:
            per_cpu: Whether to return per-CPU times
        
        Returns:
            Dictionary with CPU times or list of dictionaries for each CPU
        """
        try:
            # Get CPU times
            if per_cpu:
                times = psutil.cpu_times(percpu=True)
                return [time._asdict() for time in times]
            else:
                return psutil.cpu_times(percpu=False)._asdict()
        except Exception as e:
            logger.error(f"Error getting CPU times: {e}")
            # Return empty dictionary or list
            if per_cpu:
                return [{}] * (psutil.cpu_count() or 1)
            return {}
    
    def get_load_average(self) -> Dict[str, float]:
        """Get system load average.
        
        Returns:
            Dictionary with 1, 5, and 15 minute load averages
        """
        try:
            load_1, load_5, load_15 = os.getloadavg()
            
            # Calculate per-CPU load (normalized)
            cpu_count = psutil.cpu_count(logical=True)
            if cpu_count is None or cpu_count == 0:
                cpu_count = 1
            
            return {
                "1min": load_1,
                "5min": load_5,
                "15min": load_15,
                "1min_per_cpu": load_1 / cpu_count,
                "5min_per_cpu": load_5 / cpu_count,
                "15min_per_cpu": load_15 / cpu_count
            }
        except Exception as e:
            logger.error(f"Error getting load average: {e}")
            return {
                "1min": 0.0,
                "5min": 0.0,
                "15min": 0.0,
                "1min_per_cpu": 0.0,
                "5min_per_cpu": 0.0,
                "15min_per_cpu": 0.0
            }
    
    def get_cpu_stats(self) -> Dict[str, int]:
        """Get CPU statistics.
        
        Returns:
            Dictionary with CPU statistics (ctx_switches, interrupts, soft_interrupts, syscalls)
        """
        try:
            stats = psutil.cpu_stats()
            return {
                "ctx_switches": stats.ctx_switches,
                "interrupts": stats.interrupts,
                "soft_interrupts": stats.soft_interrupts,
                "syscalls": stats.syscalls
            }
        except Exception as e:
            logger.error(f"Error getting CPU stats: {e}")
            return {
                "ctx_switches": 0,
                "interrupts": 0,
                "soft_interrupts": 0,
                "syscalls": 0
            }
    
    def _get_cpu_freq_from_proc(self) -> Optional[Dict[str, float]]:
        """Get CPU frequency from /proc/cpuinfo."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
            
            # Extract CPU frequency
            match = re.search(r"cpu MHz\s*:\s*(\d+\.\d+)", content)
            if match:
                freq = float(match.group(1))
                return {"current": freq, "min": 0, "max": 0}
            
            return None
        except Exception as e:
            logger.error(f"Error getting CPU frequency from /proc/cpuinfo: {e}")
            return None
    
    def _get_cache_info(self) -> Optional[Dict[str, Dict[str, int]]]:
        """Get CPU cache information."""
        cache_info = {}
        
        try:
            # Use lscpu to get cache information
            output = subprocess.check_output(["lscpu", "-b", "-p=CACHE"], 
                                            universal_newlines=True)
            
            # Parse output
            lines = output.strip().split("\n")
            if len(lines) > 1:
                for line in lines:
                    if line.startswith("#"):
                        continue
                    
                    parts = line.split(",")
                    if len(parts) >= 1:
                        cache_size = parts[0].strip()
                        if cache_size:
                            try:
                                level_match = re.search(r"L(\d+).*", cache_size)
                                if level_match:
                                    level = f"L{level_match.group(1)}"
                                    size_match = re.search(r"(\d+)(\w+)", cache_size)
                                    if size_match:
                                        size = int(size_match.group(1))
                                        cache_info[level] = {"size": size}
                            except Exception:
                                pass
            
            # Fallback to psutil if lscpu doesn't provide the information
            if not cache_info:
                # Not all systems have this information available
                return None
            
            return cache_info
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return None
    
    def _get_cpu_topology(self) -> Optional[Dict[str, Any]]:
        """Get CPU topology information."""
        try:
            # Use lscpu to get topology information
            output = subprocess.check_output(["lscpu"], universal_newlines=True)
            
            topology = {}
            
            # Parse output
            for line in output.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "Thread(s) per core":
                        topology["threads_per_core"] = int(value)
                    elif key == "Core(s) per socket":
                        topology["cores_per_socket"] = int(value)
                    elif key == "Socket(s)":
                        topology["sockets"] = int(value)
                    elif key == "NUMA node(s)":
                        topology["numa_nodes"] = int(value)
            
            return topology
        except Exception as e:
            logger.error(f"Error getting CPU topology: {e}")
            return None
    
    def _get_cpu_vulnerabilities(self) -> Optional[Dict[str, str]]:
        """Get CPU vulnerability information."""
        vulnerabilities = {}
        
        try:
            # Check if the vulnerabilities directory exists
            vuln_dir = "/sys/devices/system/cpu/vulnerabilities"
            if not os.path.isdir(vuln_dir):
                return None
            
            # Read each vulnerability file
            for file in os.listdir(vuln_dir):
                try:
                    with open(os.path.join(vuln_dir, file), "r") as f:
                        content = f.read().strip()
                    vulnerabilities[file] = content
                except Exception as e:
                    logger.error(f"Error reading vulnerability file {file}: {e}")
                    vulnerabilities[file] = "Unknown"
            
            return vulnerabilities
        except Exception as e:
            logger.error(f"Error getting CPU vulnerabilities: {e}")
            return None
    
    def _get_cpu_governor(self) -> Optional[Dict[str, str]]:
        """Get CPU scaling governor information."""
        governors = {}
        
        try:
            # Check if the cpufreq directory exists
            cpufreq_dir = "/sys/devices/system/cpu"
            if not os.path.isdir(cpufreq_dir):
                return None
            
            # Read governor for each CPU
            cpu_count = psutil.cpu_count(logical=True) or 0
            for i in range(cpu_count):
                governor_path = os.path.join(cpufreq_dir, f"cpu{i}/cpufreq/scaling_governor")
                if os.path.isfile(governor_path):
                    try:
                        with open(governor_path, "r") as f:
                            content = f.read().strip()
                        governors[f"cpu{i}"] = content
                    except Exception as e:
                        logger.error(f"Error reading governor for cpu{i}: {e}")
                        governors[f"cpu{i}"] = "Unknown"
            
            return governors
        except Exception as e:
            logger.error(f"Error getting CPU governors: {e}")
            return None
