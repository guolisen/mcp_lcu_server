#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP resources for Linux system information.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
import os
import re
import platform
import socket
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import quote, unquote

import psutil

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource

from mcp_lcu_server.linux.cpu import CPUOperations
from mcp_lcu_server.linux.memory import MemoryOperations
from mcp_lcu_server.linux.process import ProcessOperations
from mcp_lcu_server.linux.storage import StorageOperations

logger = logging.getLogger(__name__)


class SystemResources:
    """Manager for system resources as MCP resources."""
    
    def __init__(self):
        self.cpu_ops = CPUOperations()
        self.memory_ops = MemoryOperations()
        self.process_ops = ProcessOperations()
        self.storage_ops = StorageOperations()
        
    def register_resources(self, mcp: FastMCP) -> None:
        """Register all system resource templates and static resources."""
        
        # System overview resource
        @mcp.resource("linux://system", 
                     name="Linux System Information", 
                     description="Overall system information for the Linux host",
                     mime_type="application/json")
        def system_get_system_info() -> str:
            """Get overall system information."""
            try:
                system_info = self._get_system_info()
                return json.dumps(system_info, indent=2)
            except Exception as e:
                logger.error(f"Error getting system info: {e}")
                return json.dumps({"error": str(e)})
        
        # CPU information resource
        @mcp.resource("linux://cpu", 
                     name="CPU Information", 
                     description="Detailed CPU information for the Linux host",
                     mime_type="application/json")
        def system_get_system_cpu_info() -> str:
            """Get detailed CPU information."""
            try:
                cpu_info = self.cpu_ops.get_cpu_info()
                
                # Add current usage
                try:
                    cpu_info["current_usage"] = self.cpu_ops.get_cpu_usage(per_cpu=False)
                    cpu_info["per_cpu_usage"] = self.cpu_ops.get_cpu_usage(per_cpu=True)
                except Exception:
                    pass
                
                # Add load average
                try:
                    cpu_info["load_average"] = self.cpu_ops.get_load_average()
                except Exception:
                    pass
                
                return json.dumps(cpu_info, indent=2)
            except Exception as e:
                logger.error(f"Error getting CPU info: {e}")
                return json.dumps({"error": str(e)})
        
        # Memory information resource
        @mcp.resource("linux://memory", 
                     name="Memory Information", 
                     description="Detailed memory information for the Linux host",
                     mime_type="application/json")
        def system_get_system_memory_info() -> str:
            """Get detailed memory information."""
            try:
                memory_stats = self.memory_ops.get_memory_stats()
                return json.dumps(memory_stats, indent=2)
            except Exception as e:
                logger.error(f"Error getting memory info: {e}")
                return json.dumps({"error": str(e)})
        
        # Process information resource
        @mcp.resource("linux://processes", 
                     name="Process Information", 
                     description="Process listing for the Linux host",
                     mime_type="application/json")
        def system_get_process_info() -> str:
            """Get process listing."""
            try:
                processes = self.process_ops.list_processes(include_threads=False, include_username=True)
                return json.dumps(processes, indent=2)
            except Exception as e:
                logger.error(f"Error getting process info: {e}")
                return json.dumps({"error": str(e)})
        
        # Detailed process information resource
        @mcp.resource("linux://processes/{pid}",
                     name="Process Details",
                     description="Detailed information about a specific process",
                     mime_type="application/json")
        def system_get_process_details(pid: str) -> str:
            """Get detailed information about a specific process."""
            try:
                process_info = self.process_ops.get_process_info(int(pid))
                if not process_info:
                    return json.dumps({"error": f"Process with PID {pid} not found"})
                return json.dumps(process_info, indent=2)
            except Exception as e:
                logger.error(f"Error getting process details for PID {pid}: {e}")
                return json.dumps({"error": str(e)})
        
        # Storage information resource
        @mcp.resource("linux://storage", 
                     name="Storage Information", 
                     description="Storage information for the Linux host",
                     mime_type="application/json")
        def system_get_storage_info() -> str:
            """Get storage information."""
            try:
                storage_info = {
                    "disks": self.storage_ops.list_disks(),
                    "partitions": self.storage_ops.list_partitions(),
                    "volumes": self.storage_ops.list_volumes(),
                    "io_stats": self.storage_ops.get_disk_io_stats()
                }
                return json.dumps(storage_info, indent=2)
            except Exception as e:
                logger.error(f"Error getting storage info: {e}")
                return json.dumps({"error": str(e)})
        
        # Network information resource
        @mcp.resource("linux://network", 
                     name="Network Information", 
                     description="Network information for the Linux host",
                     mime_type="application/json")
        def system_get_network_info() -> str:
            """Get network information."""
            try:
                network_info = self._get_network_info()
                return json.dumps(network_info, indent=2)
            except Exception as e:
                logger.error(f"Error getting network info: {e}")
                return json.dumps({"error": str(e)})
        
        # Hardware information resource
        @mcp.resource("linux://hardware", 
                     name="Hardware Information", 
                     description="Hardware information for the Linux host",
                     mime_type="application/json")
        def system_get_hardware_info() -> str:
            """Get hardware information."""
            try:
                hardware_info = self._get_hardware_info()
                return json.dumps(hardware_info, indent=2)
            except Exception as e:
                logger.error(f"Error getting hardware info: {e}")
                return json.dumps({"error": str(e)})
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get overall system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            # Basic system information
            uname = platform.uname()
            boot_time = psutil.boot_time()
            boot_time_str = datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S')
            uptime_seconds = time.time() - boot_time
            uptime_str = self._format_uptime(uptime_seconds)
            
            system_info = {
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "system": uname.system,
                "release": uname.release,
                "version": uname.version,
                "architecture": uname.machine,
                "processor": uname.processor,
                "boot_time": boot_time,
                "boot_time_str": boot_time_str,
                "uptime_seconds": uptime_seconds,
                "uptime": uptime_str,
                "time": {
                    "timestamp": time.time(),
                    "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "timezone": time.tzname[0]
                }
            }
            
            # Add CPU summary
            try:
                cpu_info = self.cpu_ops.get_cpu_info()
                system_info["cpu"] = {
                    "brand": cpu_info.get("brand_raw", "Unknown"),
                    "architecture": cpu_info.get("architecture", "Unknown"),
                    "physical_cores": cpu_info.get("count", {}).get("physical", 0),
                    "logical_cores": cpu_info.get("count", {}).get("logical", 0),
                    "usage_percent": self.cpu_ops.get_cpu_usage(per_cpu=False)
                }
                
                # Add load average
                try:
                    system_info["cpu"]["load_average"] = self.cpu_ops.get_load_average()
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error getting CPU summary: {e}")
            
            # Add memory summary
            try:
                memory_info = self.memory_ops.get_memory_info()
                system_info["memory"] = {
                    "total": memory_info.get("total", 0),
                    "available": memory_info.get("available", 0),
                    "used": memory_info.get("used", 0),
                    "free": memory_info.get("free", 0),
                    "percent": memory_info.get("percent", 0),
                    "total_human": memory_info.get("total_human", "0 B"),
                    "available_human": memory_info.get("available_human", "0 B"),
                    "used_human": memory_info.get("used_human", "0 B"),
                    "free_human": memory_info.get("free_human", "0 B")
                }
            except Exception as e:
                logger.error(f"Error getting memory summary: {e}")
            
            # Add storage summary
            try:
                partitions = self.storage_ops.list_partitions()
                mounted_partitions = [p for p in partitions if "total" in p and p["total"] > 0]
                
                total_storage = sum(p.get("total", 0) for p in mounted_partitions)
                used_storage = sum(p.get("used", 0) for p in mounted_partitions)
                free_storage = sum(p.get("free", 0) for p in mounted_partitions)
                
                system_info["storage"] = {
                    "total": total_storage,
                    "used": used_storage,
                    "free": free_storage,
                    "percent": (used_storage / total_storage * 100) if total_storage > 0 else 0,
                    "total_human": self.storage_ops._bytes_to_human(total_storage),
                    "used_human": self.storage_ops._bytes_to_human(used_storage),
                    "free_human": self.storage_ops._bytes_to_human(free_storage)
                }
            except Exception as e:
                logger.error(f"Error getting storage summary: {e}")
            
            # Add network summary
            try:
                net_io = psutil.net_io_counters()
                system_info["network"] = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "bytes_sent_human": self._bytes_to_human(net_io.bytes_sent),
                    "bytes_recv_human": self._bytes_to_human(net_io.bytes_recv)
                }
            except Exception as e:
                logger.error(f"Error getting network summary: {e}")
            
            # Add processes summary
            try:
                processes = self.process_ops.list_processes()
                total_processes = len(processes)
                running_processes = sum(1 for p in processes if p.get("status") == "running")
                sleeping_processes = sum(1 for p in processes if p.get("status") == "sleeping")
                
                system_info["processes"] = {
                    "total": total_processes,
                    "running": running_processes,
                    "sleeping": sleeping_processes,
                    "other": total_processes - running_processes - sleeping_processes
                }
            except Exception as e:
                logger.error(f"Error getting processes summary: {e}")
            
            return system_info
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information.
        
        Returns:
            Dictionary with network information
        """
        try:
            network_info = {
                "interfaces": {},
                "connections": [],
                "stats": {}
            }
            
            # Get network interfaces
            if_addrs = psutil.net_if_addrs()
            if_stats = psutil.net_if_stats()
            
            for interface_name, addrs in if_addrs.items():
                # Get interface statistics
                stats = if_stats.get(interface_name, None)
                
                interface_info = {
                    "addresses": [],
                    "isup": stats.isup if stats else False,
                    "duplex": stats.duplex.name if stats and hasattr(stats, "duplex") else "unknown",
                    "speed": stats.speed if stats else 0,
                    "mtu": stats.mtu if stats else 0
                }
                
                # Add addresses
                for addr in addrs:
                    address_info = {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                        "ptp": addr.ptp
                    }
                    
                    # Add family name for common address families
                    if addr.family == socket.AF_INET:
                        address_info["family_name"] = "IPv4"
                    elif addr.family == socket.AF_INET6:
                        address_info["family_name"] = "IPv6"
                    elif addr.family == psutil.AF_LINK:
                        address_info["family_name"] = "MAC"
                    
                    interface_info["addresses"].append(address_info)
                
                network_info["interfaces"][interface_name] = interface_info
            
            # Get network connections
            try:
                connections = psutil.net_connections()
                
                for conn in connections:
                    try:
                        connection_info = {
                            "fd": conn.fd,
                            "family": conn.family,
                            "type": conn.type,
                            "status": conn.status,
                            "pid": conn.pid
                        }
                        
                        # Add family and type names
                        if conn.family == socket.AF_INET:
                            connection_info["family_name"] = "IPv4"
                        elif conn.family == socket.AF_INET6:
                            connection_info["family_name"] = "IPv6"
                        elif conn.family == socket.AF_UNIX:
                            connection_info["family_name"] = "UNIX"
                        
                        if conn.type == socket.SOCK_STREAM:
                            connection_info["type_name"] = "TCP"
                        elif conn.type == socket.SOCK_DGRAM:
                            connection_info["type_name"] = "UDP"
                        
                        # Add local address
                        if conn.laddr:
                            if hasattr(conn.laddr, "ip") and hasattr(conn.laddr, "port"):
                                connection_info["local_address"] = f"{conn.laddr.ip}:{conn.laddr.port}"
                            else:
                                connection_info["local_address"] = str(conn.laddr)
                        
                        # Add remote address
                        if conn.raddr:
                            if hasattr(conn.raddr, "ip") and hasattr(conn.raddr, "port"):
                                connection_info["remote_address"] = f"{conn.raddr.ip}:{conn.raddr.port}"
                            else:
                                connection_info["remote_address"] = str(conn.raddr)
                        
                        network_info["connections"].append(connection_info)
                    except Exception:
                        # Skip problematic connections
                        pass
            except Exception as e:
                logger.error(f"Error getting network connections: {e}")
            
            # Get network statistics
            try:
                net_io = psutil.net_io_counters(pernic=True)
                
                for interface_name, counters in net_io.items():
                    network_info["stats"][interface_name] = {
                        "bytes_sent": counters.bytes_sent,
                        "bytes_recv": counters.bytes_recv,
                        "packets_sent": counters.packets_sent,
                        "packets_recv": counters.packets_recv,
                        "errin": counters.errin,
                        "errout": counters.errout,
                        "dropin": counters.dropin,
                        "dropout": counters.dropout,
                        "bytes_sent_human": self._bytes_to_human(counters.bytes_sent),
                        "bytes_recv_human": self._bytes_to_human(counters.bytes_recv)
                    }
            except Exception as e:
                logger.error(f"Error getting network statistics: {e}")
            
            # Add routing table if available
            try:
                routing_table = self._get_routing_table()
                if routing_table:
                    network_info["routing_table"] = routing_table
            except Exception as e:
                logger.error(f"Error getting routing table: {e}")
            
            return network_info
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {"error": str(e)}
    
    def _get_routing_table(self) -> List[Dict[str, Any]]:
        """Get the routing table.
        
        Returns:
            List of dictionaries with routing table entries
        """
        try:
            # Check if route command is available
            if self._is_command_available("route"):
                output = subprocess.check_output(["route", "-n"], universal_newlines=True)
                
                # Parse routing table
                lines = output.strip().split("\n")
                if len(lines) <= 2:
                    return []
                
                # Skip header lines
                routes = []
                for line in lines[2:]:
                    parts = line.split()
                    if len(parts) >= 8:
                        route = {
                            "destination": parts[0],
                            "gateway": parts[1],
                            "netmask": parts[2],
                            "flags": parts[3],
                            "metric": int(parts[4]),
                            "ref": int(parts[5]),
                            "use": int(parts[6]),
                            "interface": parts[7]
                        }
                        routes.append(route)
                
                return routes
            
            return []
        except Exception as e:
            logger.error(f"Error getting routing table: {e}")
            return []
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information.
        
        Returns:
            Dictionary with hardware information
        """
        try:
            hardware_info = {
                "system": {},
                "devices": {}
            }
            
            # Get basic system information
            try:
                if self._is_command_available("dmidecode"):
                    # Run dmidecode as root to get system information
                    try:
                        output = subprocess.check_output(["sudo", "dmidecode", "-t", "system"], 
                                                       universal_newlines=True)
                        
                        # Parse system information
                        manufacturer_match = re.search(r"Manufacturer: (.+)", output)
                        if manufacturer_match:
                            hardware_info["system"]["manufacturer"] = manufacturer_match.group(1).strip()
                        
                        product_match = re.search(r"Product Name: (.+)", output)
                        if product_match:
                            hardware_info["system"]["product"] = product_match.group(1).strip()
                        
                        version_match = re.search(r"Version: (.+)", output)
                        if version_match:
                            hardware_info["system"]["version"] = version_match.group(1).strip()
                        
                        serial_match = re.search(r"Serial Number: (.+)", output)
                        if serial_match:
                            hardware_info["system"]["serial"] = serial_match.group(1).strip()
                    except Exception:
                        # Skip if dmidecode fails (e.g., not running as root)
                        pass
            except Exception as e:
                logger.error(f"Error getting system hardware info: {e}")
            
            # Get CPU information
            try:
                cpu_info = self.cpu_ops.get_cpu_info()
                hardware_info["cpu"] = cpu_info
            except Exception as e:
                logger.error(f"Error getting CPU hardware info: {e}")
            
            # Get disk information
            try:
                disks = self.storage_ops.list_disks()
                hardware_info["disks"] = disks
            except Exception as e:
                logger.error(f"Error getting disk hardware info: {e}")
            
            # Get PCI devices if lspci is available
            try:
                if self._is_command_available("lspci"):
                    output = subprocess.check_output(["lspci", "-mm"], universal_newlines=True)
                    
                    # Parse PCI devices
                    pci_devices = []
                    for line in output.strip().split("\n"):
                        try:
                            parts = line.strip().split('"')
                            if len(parts) >= 5:
                                device = {
                                    "slot": parts[0].strip(),
                                    "class": parts[1],
                                    "vendor": parts[3],
                                    "device": parts[5],
                                    "rev": parts[7] if len(parts) > 7 else ""
                                }
                                pci_devices.append(device)
                        except Exception:
                            # Skip problematic lines
                            pass
                    
                    if pci_devices:
                        hardware_info["devices"]["pci"] = pci_devices
            except Exception as e:
                logger.error(f"Error getting PCI devices: {e}")
            
            # Get USB devices if lsusb is available
            try:
                if self._is_command_available("lsusb"):
                    output = subprocess.check_output(["lsusb"], universal_newlines=True)
                    
                    # Parse USB devices
                    usb_devices = []
                    for line in output.strip().split("\n"):
                        try:
                            match = re.match(r"Bus (\d+) Device (\d+): ID ([0-9a-f]{4}):([0-9a-f]{4}) (.+)", line)
                            if match:
                                device = {
                                    "bus": match.group(1),
                                    "device": match.group(2),
                                    "vendor_id": match.group(3),
                                    "product_id": match.group(4),
                                    "description": match.group(5)
                                }
                                usb_devices.append(device)
                        except Exception:
                            # Skip problematic lines
                            pass
                    
                    if usb_devices:
                        hardware_info["devices"]["usb"] = usb_devices
            except Exception as e:
                logger.error(f"Error getting USB devices: {e}")
            
            return hardware_info
        except Exception as e:
            logger.error(f"Error getting hardware info: {e}")
            return {"error": str(e)}
    
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
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available.
        
        Args:
            command: Command name
        
        Returns:
            Whether the command is available
        """
        try:
            subprocess.run(["which", command], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            return True
        except subprocess.CalledProcessError:
            return False


def register_system_resources(mcp: FastMCP) -> None:
    """Register system resources with the MCP server.
    
    Args:
        mcp: MCP server.
    """
    # Create the resources manager
    resources = SystemResources()
    
    # Register the resources
    resources.register_resources(mcp)
