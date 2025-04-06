#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for hardware information.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.hardware import HardwareOperations

logger = logging.getLogger(__name__)


def register_hardware_tools(mcp: FastMCP) -> None:
    """Register hardware tools with the MCP server.
    
    Args:
        mcp: MCP server.
    """
    # Create hardware operations instance
    hw_ops = HardwareOperations()
    
    @mcp.tool()
    def get_system_info() -> str:
        """Get general system information.
        
        Returns:
            JSON string with system information
        """
        logger.info("Getting system information")
        
        try:
            system_info = hw_ops.get_system_info()
            return json.dumps(system_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting system information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_hardware_cpu_info() -> str:
        """Get CPU hardware information.
        
        Returns:
            JSON string with CPU hardware information
        """
        logger.info("Getting CPU hardware information")
        
        try:
            cpu_info = hw_ops.get_cpu_info()
            return json.dumps(cpu_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting CPU hardware information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_hardware_memory_info() -> str:
        """Get memory hardware information.
        
        Returns:
            JSON string with memory hardware information
        """
        logger.info("Getting memory hardware information")
        
        try:
            memory_info = hw_ops.get_memory_info()
            return json.dumps(memory_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting memory hardware information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_storage_info() -> str:
        """Get storage information.
        
        Returns:
            JSON string with storage information
        """
        logger.info("Getting storage information")
        
        try:
            storage_info = hw_ops.get_storage_info()
            return json.dumps(storage_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting storage information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_pci_devices() -> str:
        """Get information about PCI devices.
        
        Returns:
            JSON string with PCI device information
        """
        logger.info("Getting PCI device information")
        
        try:
            pci_devices = hw_ops.get_pci_devices()
            return json.dumps(pci_devices, indent=2)
        except Exception as e:
            logger.error(f"Error getting PCI device information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_usb_devices() -> str:
        """Get information about USB devices.
        
        Returns:
            JSON string with USB device information
        """
        logger.info("Getting USB device information")
        
        try:
            usb_devices = hw_ops.get_usb_devices()
            return json.dumps(usb_devices, indent=2)
        except Exception as e:
            logger.error(f"Error getting USB device information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_block_devices() -> str:
        """Get information about block devices.
        
        Returns:
            JSON string with block device information
        """
        logger.info("Getting block device information")
        
        try:
            block_devices = hw_ops.get_block_devices()
            return json.dumps(block_devices, indent=2)
        except Exception as e:
            logger.error(f"Error getting block device information: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def analyze_hardware() -> str:
        """Analyze hardware configuration and provide insights.
        
        This function analyzes the hardware configuration of the system 
        and provides insights and recommendations.
        
        Returns:
            JSON string with hardware analysis
        """
        logger.info("Analyzing hardware configuration")
        
        try:
            # Get system information
            system_info = hw_ops.get_system_info()
            
            # Get CPU information
            cpu_info = system_info.get("cpu", {})
            
            # Get memory information
            memory_info = system_info.get("memory", {})
            
            # Get storage information
            storage_info = hw_ops.get_storage_info()
            
            # Create analysis result
            analysis = {
                "summary": {
                    "hostname": system_info.get("hostname", "unknown"),
                    "os": system_info.get("os", {}).get("pretty_name", "Linux"),
                    "kernel": system_info.get("kernel", "unknown"),
                    "uptime": system_info.get("uptime", {}).get("formatted", "unknown"),
                    "cpu": {
                        "model": cpu_info.get("info", {}).get("model_name", "unknown"),
                        "cores": {
                            "physical": cpu_info.get("count", {}).get("physical", 0),
                            "logical": cpu_info.get("count", {}).get("logical", 0)
                        }
                    },
                    "memory": {
                        "total": memory_info.get("ram", {}).get("total_human", "unknown"),
                        "used_percent": memory_info.get("ram", {}).get("percent", 0)
                    }
                },
                "insights": []
            }
            
            # Add insights and recommendations
            insights = []
            
            # CPU insights
            if cpu_info:
                # Check CPU cores
                physical_cores = cpu_info.get("count", {}).get("physical", 0)
                logical_cores = cpu_info.get("count", {}).get("logical", 0)
                
                if physical_cores > 0 and logical_cores > 0:
                    # Check if hyperthreading is enabled
                    if logical_cores > physical_cores:
                        insights.append({
                            "component": "cpu",
                            "type": "info",
                            "message": f"Hyperthreading is enabled ({physical_cores} physical cores, {logical_cores} logical cores)"
                        })
                    else:
                        insights.append({
                            "component": "cpu",
                            "type": "info",
                            "message": f"Hyperthreading is not enabled ({physical_cores} physical cores, {logical_cores} logical cores)"
                        })
                
                # Check CPU temperature if available
                cpu_temps = cpu_info.get("temperatures", [])
                if cpu_temps:
                    # Get max temperature
                    max_temp = max([temp.get("current", 0) for temp in cpu_temps])
                    
                    if max_temp > 80:
                        insights.append({
                            "component": "cpu",
                            "type": "warning",
                            "message": f"CPU temperature is very high ({max_temp}°C)"
                        })
                    elif max_temp > 70:
                        insights.append({
                            "component": "cpu",
                            "type": "warning",
                            "message": f"CPU temperature is high ({max_temp}°C)"
                        })
            
            # Memory insights
            if memory_info:
                # Check memory usage
                memory_percent = memory_info.get("ram", {}).get("percent", 0)
                
                if memory_percent > 90:
                    insights.append({
                        "component": "memory",
                        "type": "warning",
                        "message": f"Memory usage is very high ({memory_percent}%)"
                    })
                elif memory_percent > 80:
                    insights.append({
                        "component": "memory",
                        "type": "info",
                        "message": f"Memory usage is high ({memory_percent}%)"
                    })
                
                # Check swap usage
                swap_percent = memory_info.get("swap", {}).get("percent", 0)
                
                if swap_percent > 50:
                    insights.append({
                        "component": "memory",
                        "type": "warning",
                        "message": f"Swap usage is high ({swap_percent}%)"
                    })
            
            # Storage insights
            if storage_info:
                # Check disk usage
                partitions = storage_info.get("partitions", [])
                
                for partition in partitions:
                    usage = partition.get("usage", {})
                    if usage:
                        percent = usage.get("percent", 0)
                        mountpoint = partition.get("mountpoint", "unknown")
                        
                        if percent > 90:
                            insights.append({
                                "component": "storage",
                                "type": "warning",
                                "message": f"Disk usage for {mountpoint} is very high ({percent}%)"
                            })
                        elif percent > 80:
                            insights.append({
                                "component": "storage",
                                "type": "info",
                                "message": f"Disk usage for {mountpoint} is high ({percent}%)"
                            })
            
            # Add insights to analysis
            analysis["insights"] = insights
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing hardware: {e}")
            return json.dumps({"error": str(e)})
