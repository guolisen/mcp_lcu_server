#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for storage information and operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.storage import StorageOperations

logger = logging.getLogger(__name__)


def register_storage_tools(mcp: FastMCP) -> None:
    """Register storage tools with the MCP server.
    
    Args:
        mcp: MCP server.
    """
    # Create storage operations instance
    storage_ops = StorageOperations()
    
    @mcp.tool()
    def storage_list_disks() -> str:
        """List physical disks.
        
        Returns:
            JSON string with list of disks and their properties
        """
        logger.info("Listing disks")
        
        try:
            disks = storage_ops.list_disks()
            return json.dumps(disks, indent=2)
        except Exception as e:
            logger.error(f"Error listing disks: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def storage_list_partitions() -> str:
        """List partitions.
        
        Returns:
            JSON string with list of partitions and their properties
        """
        logger.info("Listing partitions")
        
        try:
            partitions = storage_ops.list_partitions()
            return json.dumps(partitions, indent=2)
        except Exception as e:
            logger.error(f"Error listing partitions: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def storage_list_volumes() -> str:
        """List logical volumes (LVM, MD RAID, etc.).
        
        Returns:
            JSON string with list of volumes and their properties
        """
        logger.info("Listing volumes")
        
        try:
            volumes = storage_ops.list_volumes()
            return json.dumps(volumes, indent=2)
        except Exception as e:
            logger.error(f"Error listing volumes: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def storage_get_disk_usage(path: str = "/") -> str:
        """Get disk usage for a path.
        
        Args:
            path: Path to get disk usage for
        
        Returns:
            JSON string with disk usage information
        """
        logger.info(f"Getting disk usage for path: {path}")
        
        try:
            usage = storage_ops.get_disk_usage(path)
            return json.dumps(usage, indent=2)
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def storage_get_disk_io_stats() -> str:
        """Get disk I/O statistics.
        
        Returns:
            JSON string with disk I/O statistics
        """
        logger.info("Getting disk I/O statistics")
        
        try:
            stats = storage_ops.get_disk_io_stats()
            return json.dumps(stats, indent=2)
        except Exception as e:
            logger.error(f"Error getting disk I/O statistics: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def storage_get_disk_smart_info(device: str) -> str:
        """Get SMART information for a disk.
        
        Args:
            device: Disk device (e.g., sda, nvme0n1)
        
        Returns:
            JSON string with SMART information
        """
        logger.info(f"Getting SMART information for device: {device}")
        
        try:
            smart_info = storage_ops.get_disk_smart_info(device)
            return json.dumps(smart_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting SMART information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def storage_analyze_storage_usage() -> str:
        """Analyze storage usage across the system.
        
        This function provides a comprehensive analysis of storage usage:
        - Overall disk space usage
        - Largest directories and files
        - Filesystems nearing capacity
        - Inodes usage
        - Storage optimization recommendations
        
        Returns:
            JSON string with storage usage analysis
        """
        logger.info("Analyzing storage usage")
        
        try:
            # Get partitions and their usage
            partitions = storage_ops.list_partitions()
            
            # Filter mounted partitions with usage data
            mounted_partitions = [p for p in partitions if "total" in p and p["total"] > 0]
            
            # Identify filesystems nearing capacity
            critical_fs = []
            warning_fs = []
            normal_fs = []
            
            for partition in mounted_partitions:
                percent = partition.get("percent", 0)
                
                # Skip small/special filesystems
                if partition.get("total", 0) < 100 * 1024 * 1024:  # Smaller than 100MB
                    continue
                
                if percent >= 90:
                    critical_fs.append(partition)
                elif percent >= 75:
                    warning_fs.append(partition)
                else:
                    normal_fs.append(partition)
            
            # Calculate total storage
            total_storage = sum(p.get("total", 0) for p in mounted_partitions)
            used_storage = sum(p.get("used", 0) for p in mounted_partitions)
            free_storage = sum(p.get("free", 0) for p in mounted_partitions)
            
            # Generate recommendations
            recommendations = []
            
            if critical_fs:
                recommendations.append("Critical: The following filesystems are running out of space and need immediate attention: " + 
                                      ", ".join([f"{p['mountpoint']} ({p['percent']}%)" for p in critical_fs]))
            
            if warning_fs:
                recommendations.append("Warning: The following filesystems are nearing capacity and should be monitored: " + 
                                      ", ".join([f"{p['mountpoint']} ({p['percent']}%)" for p in warning_fs]))
            
            if len(critical_fs) + len(warning_fs) > 0:
                recommendations.append("Run 'du -sh /* | sort -hr' to identify large directories")
                recommendations.append("Consider removing temporary files, log files, or cached package data")
                
                # Suggest checking for large log files
                if any(p["mountpoint"] == "/var" for p in critical_fs + warning_fs):
                    recommendations.append("Check for large log files in /var/log")
                
                # Suggest checking for container/docker data
                if any(p["mountpoint"] == "/" or p["mountpoint"] == "/var" for p in critical_fs + warning_fs):
                    recommendations.append("Check for unused container images or volumes if Docker/Podman is used")
            
            # Create analysis report
            analysis = {
                "summary": {
                    "total_storage": total_storage,
                    "total_storage_human": storage_ops._bytes_to_human(total_storage),
                    "used_storage": used_storage,
                    "used_storage_human": storage_ops._bytes_to_human(used_storage),
                    "free_storage": free_storage,
                    "free_storage_human": storage_ops._bytes_to_human(free_storage),
                    "usage_percent": (used_storage / total_storage * 100) if total_storage > 0 else 0,
                    "critical_filesystems": len(critical_fs),
                    "warning_filesystems": len(warning_fs)
                },
                "filesystems": {
                    "critical": critical_fs,
                    "warning": warning_fs,
                    "normal": normal_fs
                },
                "recommendations": recommendations
            }
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing storage usage: {e}")
            return json.dumps({"error": str(e)})
