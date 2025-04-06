#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Memory operations module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple

import psutil

logger = logging.getLogger(__name__)


class MemoryOperations:
    """Class for memory operations on Linux systems."""
    
    def __init__(self):
        """Initialize memory operations."""
        pass
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information.
        
        Returns:
            Dictionary with memory information including:
            - total: Total physical memory
            - available: Available memory
            - used: Used memory
            - free: Free memory
            - percent: Percentage of memory used
            - buffers: Buffers memory
            - cached: Cached memory
            - shared: Shared memory
        """
        try:
            # Get memory info from psutil
            vm = psutil.virtual_memory()
            
            info = {
                "total": vm.total,
                "available": vm.available,
                "used": vm.used,
                "free": vm.free,
                "percent": vm.percent,
                "buffers": getattr(vm, "buffers", 0),
                "cached": getattr(vm, "cached", 0),
                "shared": getattr(vm, "shared", 0),
            }
            
            # Convert to human readable format
            info["total_human"] = self._bytes_to_human(vm.total)
            info["available_human"] = self._bytes_to_human(vm.available)
            info["used_human"] = self._bytes_to_human(vm.used)
            info["free_human"] = self._bytes_to_human(vm.free)
            info["buffers_human"] = self._bytes_to_human(getattr(vm, "buffers", 0))
            info["cached_human"] = self._bytes_to_human(getattr(vm, "cached", 0))
            info["shared_human"] = self._bytes_to_human(getattr(vm, "shared", 0))
            
            # Get memory info from /proc/meminfo for additional details
            proc_info = self._get_memory_info_from_proc()
            if proc_info:
                # Merge info from /proc/meminfo
                info.update(proc_info)
            
            return info
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {
                "error": str(e),
                "total": 0,
                "available": 0,
                "used": 0,
                "free": 0,
                "percent": 0,
                "buffers": 0,
                "cached": 0,
                "shared": 0
            }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage.
        
        Returns:
            Dictionary with memory usage information:
            - total: Total physical memory
            - used: Used memory
            - free: Free memory
            - percent: Percentage of memory used
        """
        try:
            # Get memory info from psutil
            vm = psutil.virtual_memory()
            
            usage = {
                "total": vm.total,
                "used": vm.used,
                "free": vm.free,
                "percent": vm.percent
            }
            
            # Convert to human readable format
            usage["total_human"] = self._bytes_to_human(vm.total)
            usage["used_human"] = self._bytes_to_human(vm.used)
            usage["free_human"] = self._bytes_to_human(vm.free)
            
            return usage
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {
                "error": str(e),
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0
            }
    
    def get_swap_info(self) -> Dict[str, Any]:
        """Get detailed swap information.
        
        Returns:
            Dictionary with swap information:
            - total: Total swap memory
            - used: Used swap memory
            - free: Free swap memory
            - percent: Percentage of swap used
            - sin: Number of bytes the system has swapped in from disk
            - sout: Number of bytes the system has swapped out to disk
        """
        try:
            # Get swap info from psutil
            swap = psutil.swap_memory()
            
            info = {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent,
                "sin": swap.sin,
                "sout": swap.sout
            }
            
            # Convert to human readable format
            info["total_human"] = self._bytes_to_human(swap.total)
            info["used_human"] = self._bytes_to_human(swap.used)
            info["free_human"] = self._bytes_to_human(swap.free)
            info["sin_human"] = self._bytes_to_human(swap.sin)
            info["sout_human"] = self._bytes_to_human(swap.sout)
            
            # Get swap info from /proc/swaps for additional details
            proc_info = self._get_swap_info_from_proc()
            if proc_info:
                # Include swap devices information
                info["devices"] = proc_info
            
            return info
        except Exception as e:
            logger.error(f"Error getting swap info: {e}")
            return {
                "error": str(e),
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0,
                "sin": 0,
                "sout": 0
            }
    
    def get_swap_usage(self) -> Dict[str, Any]:
        """Get swap usage.
        
        Returns:
            Dictionary with swap usage information:
            - total: Total swap memory
            - used: Used swap memory
            - free: Free swap memory
            - percent: Percentage of swap used
        """
        try:
            # Get swap info from psutil
            swap = psutil.swap_memory()
            
            usage = {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            }
            
            # Convert to human readable format
            usage["total_human"] = self._bytes_to_human(swap.total)
            usage["used_human"] = self._bytes_to_human(swap.used)
            usage["free_human"] = self._bytes_to_human(swap.free)
            
            return usage
        except Exception as e:
            logger.error(f"Error getting swap usage: {e}")
            return {
                "error": str(e),
                "total": 0,
                "used": 0,
                "free": 0,
                "percent": 0
            }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics.
        
        Returns:
            Dictionary with memory statistics:
            - memory: Memory usage information
            - swap: Swap usage information
            - hugepages: Hugepages information
            - memory_distribution: Memory distribution
        """
        try:
            memory_info = self.get_memory_info()
            swap_info = self.get_swap_info()
            
            # Calculate memory distribution
            memory_total = memory_info.get("total", 0)
            memory_distribution = {}
            
            if memory_total > 0:
                memory_distribution["used"] = (memory_info.get("used", 0) / memory_total) * 100
                memory_distribution["free"] = (memory_info.get("free", 0) / memory_total) * 100
                memory_distribution["buffers"] = (memory_info.get("buffers", 0) / memory_total) * 100
                memory_distribution["cached"] = (memory_info.get("cached", 0) / memory_total) * 100
                memory_distribution["shared"] = (memory_info.get("shared", 0) / memory_total) * 100
            
            # Get hugepages information
            hugepages = self._get_hugepages_info()
            
            # Create comprehensive stats
            stats = {
                "memory": {
                    "total": memory_info.get("total", 0),
                    "available": memory_info.get("available", 0),
                    "used": memory_info.get("used", 0),
                    "free": memory_info.get("free", 0),
                    "percent": memory_info.get("percent", 0),
                    "buffers": memory_info.get("buffers", 0),
                    "cached": memory_info.get("cached", 0),
                    "shared": memory_info.get("shared", 0),
                },
                "swap": {
                    "total": swap_info.get("total", 0),
                    "used": swap_info.get("used", 0),
                    "free": swap_info.get("free", 0),
                    "percent": swap_info.get("percent", 0),
                    "sin": swap_info.get("sin", 0),
                    "sout": swap_info.get("sout", 0),
                },
                "hugepages": hugepages,
                "memory_distribution": memory_distribution
            }
            
            # Add human readable formats
            stats["memory"]["total_human"] = self._bytes_to_human(memory_info.get("total", 0))
            stats["memory"]["available_human"] = self._bytes_to_human(memory_info.get("available", 0))
            stats["memory"]["used_human"] = self._bytes_to_human(memory_info.get("used", 0))
            stats["memory"]["free_human"] = self._bytes_to_human(memory_info.get("free", 0))
            stats["memory"]["buffers_human"] = self._bytes_to_human(memory_info.get("buffers", 0))
            stats["memory"]["cached_human"] = self._bytes_to_human(memory_info.get("cached", 0))
            stats["memory"]["shared_human"] = self._bytes_to_human(memory_info.get("shared", 0))
            
            stats["swap"]["total_human"] = self._bytes_to_human(swap_info.get("total", 0))
            stats["swap"]["used_human"] = self._bytes_to_human(swap_info.get("used", 0))
            stats["swap"]["free_human"] = self._bytes_to_human(swap_info.get("free", 0))
            stats["swap"]["sin_human"] = self._bytes_to_human(swap_info.get("sin", 0))
            stats["swap"]["sout_human"] = self._bytes_to_human(swap_info.get("sout", 0))
            
            return stats
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {
                "error": str(e),
                "memory": {},
                "swap": {},
                "hugepages": {},
                "memory_distribution": {}
            }
    
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
    
    def _get_memory_info_from_proc(self) -> Optional[Dict[str, Any]]:
        """Get memory information from /proc/meminfo."""
        try:
            with open("/proc/meminfo", "r") as f:
                content = f.read()
            
            # Parse memory info
            info = {}
            
            # Define patterns for interesting values
            patterns = {
                "MemTotal": r"MemTotal:\s+(\d+)",
                "MemFree": r"MemFree:\s+(\d+)",
                "MemAvailable": r"MemAvailable:\s+(\d+)",
                "Buffers": r"Buffers:\s+(\d+)",
                "Cached": r"Cached:\s+(\d+)",
                "SwapCached": r"SwapCached:\s+(\d+)",
                "Active": r"Active:\s+(\d+)",
                "Inactive": r"Inactive:\s+(\d+)",
                "ActiveAnon": r"ActiveAnon:\s+(\d+)",
                "InactiveAnon": r"InactiveAnon:\s+(\d+)",
                "ActiveFile": r"ActiveFile:\s+(\d+)",
                "InactiveFile": r"InactiveFile:\s+(\d+)",
                "Unevictable": r"Unevictable:\s+(\d+)",
                "Mlocked": r"Mlocked:\s+(\d+)",
                "SwapTotal": r"SwapTotal:\s+(\d+)",
                "SwapFree": r"SwapFree:\s+(\d+)",
                "Dirty": r"Dirty:\s+(\d+)",
                "Writeback": r"Writeback:\s+(\d+)",
                "AnonPages": r"AnonPages:\s+(\d+)",
                "Mapped": r"Mapped:\s+(\d+)",
                "Shmem": r"Shmem:\s+(\d+)",
                "Slab": r"Slab:\s+(\d+)",
                "SReclaimable": r"SReclaimable:\s+(\d+)",
                "SUnreclaim": r"SUnreclaim:\s+(\d+)",
                "KernelStack": r"KernelStack:\s+(\d+)",
                "PageTables": r"PageTables:\s+(\d+)",
                "NFS_Unstable": r"NFS_Unstable:\s+(\d+)",
                "Bounce": r"Bounce:\s+(\d+)",
                "WritebackTmp": r"WritebackTmp:\s+(\d+)",
                "CommitLimit": r"CommitLimit:\s+(\d+)",
                "Committed_AS": r"Committed_AS:\s+(\d+)",
                "VmallocTotal": r"VmallocTotal:\s+(\d+)",
                "VmallocUsed": r"VmallocUsed:\s+(\d+)",
                "VmallocChunk": r"VmallocChunk:\s+(\d+)",
                "HardwareCorrupted": r"HardwareCorrupted:\s+(\d+)",
                "AnonHugePages": r"AnonHugePages:\s+(\d+)",
                "ShmemHugePages": r"ShmemHugePages:\s+(\d+)",
                "ShmemPmdMapped": r"ShmemPmdMapped:\s+(\d+)",
                "CmaTotal": r"CmaTotal:\s+(\d+)",
                "CmaFree": r"CmaFree:\s+(\d+)",
                "HugePages_Total": r"HugePages_Total:\s+(\d+)",
                "HugePages_Free": r"HugePages_Free:\s+(\d+)",
                "HugePages_Rsvd": r"HugePages_Rsvd:\s+(\d+)",
                "HugePages_Surp": r"HugePages_Surp:\s+(\d+)",
                "Hugepagesize": r"Hugepagesize:\s+(\d+)",
                "DirectMap4k": r"DirectMap4k:\s+(\d+)",
                "DirectMap2M": r"DirectMap2M:\s+(\d+)",
                "DirectMap1G": r"DirectMap1G:\s+(\d+)",
            }
            
            # Extract values
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    info[key.lower()] = int(match.group(1)) * 1024  # Convert from KB to bytes
            
            return info
        except Exception as e:
            logger.error(f"Error getting memory info from /proc/meminfo: {e}")
            return None
    
    def _get_swap_info_from_proc(self) -> Optional[List[Dict[str, Any]]]:
        """Get swap information from /proc/swaps."""
        try:
            with open("/proc/swaps", "r") as f:
                content = f.readlines()
            
            # Skip header
            if len(content) <= 1:
                return None
            
            swap_devices = []
            
            # Parse each swap device
            for line in content[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    device = {
                        "filename": parts[0],
                        "type": parts[1],
                        "size": int(parts[2]) * 1024,  # Convert from KB to bytes
                        "used": int(parts[3]) * 1024,  # Convert from KB to bytes
                        "priority": int(parts[4]),
                        "size_human": self._bytes_to_human(int(parts[2]) * 1024),
                        "used_human": self._bytes_to_human(int(parts[3]) * 1024),
                    }
                    swap_devices.append(device)
            
            return swap_devices
        except Exception as e:
            logger.error(f"Error getting swap info from /proc/swaps: {e}")
            return None
    
    def _get_hugepages_info(self) -> Dict[str, Any]:
        """Get hugepages information."""
        hugepages = {}
        
        try:
            # Try to get hugepages information from /proc/meminfo
            with open("/proc/meminfo", "r") as f:
                content = f.read()
            
            # Extract hugepages information
            patterns = {
                "total": r"HugePages_Total:\s+(\d+)",
                "free": r"HugePages_Free:\s+(\d+)",
                "reserved": r"HugePages_Rsvd:\s+(\d+)",
                "surplus": r"HugePages_Surp:\s+(\d+)",
                "size": r"Hugepagesize:\s+(\d+)",
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    value = int(match.group(1))
                    if key == "size":
                        value *= 1024  # Convert from KB to bytes
                        hugepages[key] = value
                        hugepages["size_human"] = self._bytes_to_human(value)
                    else:
                        hugepages[key] = value
            
            # Calculate used hugepages
            if "total" in hugepages and "free" in hugepages:
                hugepages["used"] = hugepages["total"] - hugepages["free"]
            
            # Calculate total memory reserved for hugepages
            if "total" in hugepages and "size" in hugepages:
                total_size = hugepages["total"] * hugepages["size"]
                hugepages["total_size"] = total_size
                hugepages["total_size_human"] = self._bytes_to_human(total_size)
            
            return hugepages
        except Exception as e:
            logger.error(f"Error getting hugepages info: {e}")
            return {}
