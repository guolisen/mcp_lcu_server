#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Hardware operations module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import logging
import subprocess
from typing import Dict, List, Optional, Union, Any

import psutil

logger = logging.getLogger(__name__)


class HardwareOperations:
    """Class for hardware operations on Linux systems."""
    
    def __init__(self):
        """Initialize hardware operations."""
        pass
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get general system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            # Get CPU information
            cpu_info = self.get_cpu_info()
            
            # Get memory information
            memory_info = self.get_memory_info()
            
            # Get system information using various commands
            system_info = {
                "hostname": self._get_hostname(),
                "kernel": self._get_kernel_version(),
                "os": self._get_os_info(),
                "uptime": self._get_uptime(),
                "cpu": cpu_info,
                "memory": memory_info,
                "boot_time": psutil.boot_time(),
            }
            
            return system_info
        except Exception as e:
            logger.error(f"Error getting system information: {e}")
            return {"error": str(e)}
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information.
        
        Returns:
            Dictionary with CPU information
        """
        try:
            # Get CPU information using psutil
            cpu_count_logical = psutil.cpu_count()
            cpu_count_physical = psutil.cpu_count(logical=False)
            
            # Get CPU frequency
            freq = psutil.cpu_freq()
            
            # Initialize CPU info dictionary
            cpu_info = {
                "count": {
                    "logical": cpu_count_logical,
                    "physical": cpu_count_physical
                },
                "frequency": {
                    "current": freq.current if freq else None,
                    "min": freq.min if freq and hasattr(freq, "min") else None,
                    "max": freq.max if freq and hasattr(freq, "max") else None
                }
            }
            
            # Try to get more detailed CPU information from /proc/cpuinfo
            if os.path.exists("/proc/cpuinfo"):
                cpuinfo = {}
                
                with open("/proc/cpuinfo", "r") as f:
                    content = f.read()
                
                # Get processor information for each CPU
                processors = re.split(r"\n\s*\n", content.strip())
                if processors:
                    # Get information from the first processor
                    processor = processors[0]
                    
                    # Extract CPU model
                    model_name = re.search(r"model name\s*:\s*(.+)", processor)
                    if model_name:
                        cpuinfo["model_name"] = model_name.group(1).strip()
                    
                    # Extract CPU vendor
                    vendor_id = re.search(r"vendor_id\s*:\s*(.+)", processor)
                    if vendor_id:
                        cpuinfo["vendor"] = vendor_id.group(1).strip()
                    
                    # Extract CPU architecture
                    cpu_family = re.search(r"cpu family\s*:\s*(.+)", processor)
                    if cpu_family:
                        cpuinfo["family"] = cpu_family.group(1).strip()
                    
                    # Extract CPU stepping
                    stepping = re.search(r"stepping\s*:\s*(.+)", processor)
                    if stepping:
                        cpuinfo["stepping"] = stepping.group(1).strip()
                    
                    # Extract CPU cache size
                    cache_size = re.search(r"cache size\s*:\s*(.+)", processor)
                    if cache_size:
                        cpuinfo["cache_size"] = cache_size.group(1).strip()
                    
                    # Extract CPU bogomips
                    bogomips = re.search(r"bogomips\s*:\s*(.+)", processor)
                    if bogomips:
                        cpuinfo["bogomips"] = bogomips.group(1).strip()
                    
                    # Add CPUInfo to CPU info dictionary
                    cpu_info["info"] = cpuinfo
            
            # Try to get CPU temperature if available
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    cpu_temps = []
                    
                    # Look for CPU temperatures
                    for name, entries in temps.items():
                        if any(name.lower().startswith(prefix) for prefix in ["cpu", "core", "package"]):
                            for entry in entries:
                                cpu_temps.append({
                                    "label": entry.label or name,
                                    "current": entry.current,
                                    "high": entry.high,
                                    "critical": entry.critical
                                })
                    
                    if cpu_temps:
                        cpu_info["temperatures"] = cpu_temps
            except Exception:
                pass
            
            return cpu_info
        except Exception as e:
            logger.error(f"Error getting CPU information: {e}")
            return {"error": str(e)}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information.
        
        Returns:
            Dictionary with memory information
        """
        try:
            # Get memory information using psutil
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Format memory information
            memory_info = {
                "ram": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "free": memory.free,
                    "percent": memory.percent,
                    "total_human": self._bytes_to_human(memory.total),
                    "available_human": self._bytes_to_human(memory.available),
                    "used_human": self._bytes_to_human(memory.used),
                    "free_human": self._bytes_to_human(memory.free)
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent,
                    "total_human": self._bytes_to_human(swap.total),
                    "used_human": self._bytes_to_human(swap.used),
                    "free_human": self._bytes_to_human(swap.free)
                }
            }
            
            # Try to get more detailed memory information from /proc/meminfo
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    content = f.read()
                
                # Extract additional memory information
                meminfo = {}
                
                # Extract Buffers
                buffers = re.search(r"Buffers:\s*(\d+)", content)
                if buffers:
                    meminfo["buffers"] = int(buffers.group(1)) * 1024
                
                # Extract Cached
                cached = re.search(r"Cached:\s*(\d+)", content)
                if cached:
                    meminfo["cached"] = int(cached.group(1)) * 1024
                
                # Extract SReclaimable
                slab_reclaimable = re.search(r"SReclaimable:\s*(\d+)", content)
                if slab_reclaimable:
                    meminfo["slab_reclaimable"] = int(slab_reclaimable.group(1)) * 1024
                
                # Extract SUnreclaim
                slab_unreclaimable = re.search(r"SUnreclaim:\s*(\d+)", content)
                if slab_unreclaimable:
                    meminfo["slab_unreclaimable"] = int(slab_unreclaimable.group(1)) * 1024
                
                # Extract Memory Types
                hugepages_total = re.search(r"HugePages_Total:\s*(\d+)", content)
                hugepages_free = re.search(r"HugePages_Free:\s*(\d+)", content)
                hugepages_size = re.search(r"Hugepagesize:\s*(\d+)", content)
                
                if hugepages_total and hugepages_free and hugepages_size:
                    meminfo["hugepages"] = {
                        "total": int(hugepages_total.group(1)),
                        "free": int(hugepages_free.group(1)),
                        "size": int(hugepages_size.group(1)) * 1024,
                        "size_human": self._bytes_to_human(int(hugepages_size.group(1)) * 1024)
                    }
                
                # Add meminfo to memory_info
                if meminfo:
                    memory_info["details"] = meminfo
            
            # Try to get memory hardware information from dmidecode
            try:
                if os.path.exists("/usr/sbin/dmidecode"):
                    # Run dmidecode to get memory hardware information
                    output = subprocess.check_output(["sudo", "dmidecode", "-t", "memory"],
                                                   universal_newlines=True,
                                                   stderr=subprocess.DEVNULL)
                    
                    # Parse memory modules
                    memory_devices = []
                    devices = re.split(r"Memory Device\n", output)
                    
                    for device in devices[1:]:  # Skip the first entry (header)
                        memory_device = {}
                        
                        # Extract size
                        size_match = re.search(r"Size: (.+)", device)
                        if size_match:
                            size = size_match.group(1).strip()
                            if size != "No Module Installed":
                                memory_device["size"] = size
                        
                        # Extract type
                        type_match = re.search(r"Type: (.+)", device)
                        if type_match:
                            memory_device["type"] = type_match.group(1).strip()
                        
                        # Extract speed
                        speed_match = re.search(r"Speed: (.+)", device)
                        if speed_match:
                            memory_device["speed"] = speed_match.group(1).strip()
                        
                        # Extract manufacturer
                        manufacturer_match = re.search(r"Manufacturer: (.+)", device)
                        if manufacturer_match:
                            memory_device["manufacturer"] = manufacturer_match.group(1).strip()
                        
                        # Extract serial number
                        serial_match = re.search(r"Serial Number: (.+)", device)
                        if serial_match:
                            memory_device["serial"] = serial_match.group(1).strip()
                        
                        # Extract part number
                        part_match = re.search(r"Part Number: (.+)", device)
                        if part_match:
                            memory_device["part"] = part_match.group(1).strip()
                        
                        # Add to devices list if it has a size
                        if "size" in memory_device:
                            memory_devices.append(memory_device)
                    
                    if memory_devices:
                        memory_info["devices"] = memory_devices
            except Exception:
                pass
            
            return memory_info
        except Exception as e:
            logger.error(f"Error getting memory information: {e}")
            return {"error": str(e)}
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information.
        
        Returns:
            Dictionary with storage information
        """
        try:
            # Get disk partitions using psutil
            partitions = psutil.disk_partitions(all=True)
            
            # Format partition information
            partition_info = []
            for partition in partitions:
                # Get usage information if mounted and accessible
                usage = None
                if partition.mountpoint and os.path.exists(partition.mountpoint):
                    try:
                        usage_data = psutil.disk_usage(partition.mountpoint)
                        usage = {
                            "total": usage_data.total,
                            "used": usage_data.used,
                            "free": usage_data.free,
                            "percent": usage_data.percent,
                            "total_human": self._bytes_to_human(usage_data.total),
                            "used_human": self._bytes_to_human(usage_data.used),
                            "free_human": self._bytes_to_human(usage_data.free)
                        }
                    except (PermissionError, OSError):
                        pass
                
                # Create partition entry
                part_entry = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "opts": partition.opts
                }
                
                # Add usage information if available
                if usage:
                    part_entry["usage"] = usage
                
                partition_info.append(part_entry)
            
            # Get disk I/O information using psutil
            io_counters = psutil.disk_io_counters(perdisk=True)
            
            # Format I/O information
            io_info = {}
            for disk, counters in io_counters.items():
                io_info[disk] = {
                    "read_count": counters.read_count,
                    "write_count": counters.write_count,
                    "read_bytes": counters.read_bytes,
                    "write_bytes": counters.write_bytes,
                    "read_time": counters.read_time,
                    "write_time": counters.write_time,
                    "read_bytes_human": self._bytes_to_human(counters.read_bytes),
                    "write_bytes_human": self._bytes_to_human(counters.write_bytes)
                }
            
            # Try to get physical disk information
            physical_disks = self._get_physical_disks()
            
            # Create storage information dictionary
            storage_info = {
                "partitions": partition_info,
                "io_counters": io_info
            }
            
            # Add physical disk information if available
            if physical_disks:
                storage_info["physical_disks"] = physical_disks
            
            return storage_info
        except Exception as e:
            logger.error(f"Error getting storage information: {e}")
            return {"error": str(e)}
    
    def get_pci_devices(self) -> List[Dict[str, Any]]:
        """Get information about PCI devices.
        
        Returns:
            List of dictionaries with PCI device information
        """
        try:
            pci_devices = []
            
            # Try to use lspci command
            if self._is_command_available("lspci"):
                # Run lspci command
                output = subprocess.check_output(["lspci", "-vmm"], universal_newlines=True)
                
                # Parse output
                devices = re.split(r"\n\n", output.strip())
                
                for device in devices:
                    # Extract device information
                    device_info = {}
                    
                    # Extract slot
                    slot_match = re.search(r"Slot:\s*(.+)", device)
                    if slot_match:
                        device_info["slot"] = slot_match.group(1).strip()
                    
                    # Extract class
                    class_match = re.search(r"Class:\s*(.+)", device)
                    if class_match:
                        device_info["class"] = class_match.group(1).strip()
                    
                    # Extract vendor
                    vendor_match = re.search(r"Vendor:\s*(.+)", device)
                    if vendor_match:
                        device_info["vendor"] = vendor_match.group(1).strip()
                    
                    # Extract device
                    device_match = re.search(r"Device:\s*(.+)", device)
                    if device_match:
                        device_info["device"] = device_match.group(1).strip()
                    
                    # Extract subsystem vendor
                    subsys_vendor_match = re.search(r"SVendor:\s*(.+)", device)
                    if subsys_vendor_match:
                        device_info["subsystem_vendor"] = subsys_vendor_match.group(1).strip()
                    
                    # Extract subsystem device
                    subsys_device_match = re.search(r"SDevice:\s*(.+)", device)
                    if subsys_device_match:
                        device_info["subsystem_device"] = subsys_device_match.group(1).strip()
                    
                    # Extract revision
                    rev_match = re.search(r"Rev:\s*(.+)", device)
                    if rev_match:
                        device_info["revision"] = rev_match.group(1).strip()
                    
                    # Add to list if we have enough information
                    if "slot" in device_info and "class" in device_info:
                        pci_devices.append(device_info)
            
            return pci_devices
        except Exception as e:
            logger.error(f"Error getting PCI devices: {e}")
            return []
    
    def get_usb_devices(self) -> List[Dict[str, Any]]:
        """Get information about USB devices.
        
        Returns:
            List of dictionaries with USB device information
        """
        try:
            usb_devices = []
            
            # Try to use lsusb command
            if self._is_command_available("lsusb"):
                # Run lsusb command
                output = subprocess.check_output(["lsusb"], universal_newlines=True)
                
                # Parse output
                for line in output.strip().split("\n"):
                    # Extract device information
                    match = re.match(r"Bus (\d+) Device (\d+): ID ([0-9a-f]{4}):([0-9a-f]{4}) (.+)", line)
                    if match:
                        device_info = {
                            "bus": match.group(1),
                            "device": match.group(2),
                            "vendor_id": match.group(3),
                            "product_id": match.group(4),
                            "description": match.group(5)
                        }
                        
                        usb_devices.append(device_info)
            
            return usb_devices
        except Exception as e:
            logger.error(f"Error getting USB devices: {e}")
            return []
    
    def get_block_devices(self) -> List[Dict[str, Any]]:
        """Get information about block devices.
        
        Returns:
            List of dictionaries with block device information
        """
        try:
            block_devices = []
            
            # Try to use lsblk command
            if self._is_command_available("lsblk"):
                # Run lsblk command with JSON output
                output = subprocess.check_output(["lsblk", "-J"], universal_newlines=True)
                
                # Parse JSON output
                import json
                try:
                    data = json.loads(output)
                    if "blockdevices" in data:
                        for device in data["blockdevices"]:
                            # Convert device dictionary to our format
                            device_info = {
                                "name": device.get("name", ""),
                                "size": device.get("size", ""),
                                "type": device.get("type", ""),
                                "mountpoint": device.get("mountpoint", ""),
                                "model": device.get("model", ""),
                                "vendor": device.get("vendor", ""),
                                "serial": device.get("serial", "")
                            }
                            
                            # Add children if available
                            if "children" in device:
                                device_info["children"] = []
                                for child in device["children"]:
                                    child_info = {
                                        "name": child.get("name", ""),
                                        "size": child.get("size", ""),
                                        "type": child.get("type", ""),
                                        "mountpoint": child.get("mountpoint", "")
                                    }
                                    device_info["children"].append(child_info)
                            
                            block_devices.append(device_info)
                    return block_devices
                except json.JSONDecodeError:
                    pass
            
            # Fallback to parsing /proc/partitions
            if os.path.exists("/proc/partitions"):
                with open("/proc/partitions", "r") as f:
                    lines = f.readlines()
                
                # Skip header lines
                for line in lines[2:]:
                    parts = line.strip().split()
                    if len(parts) == 4:
                        major, minor, blocks, name = parts
                        
                        # Skip partitions, get only disks
                        if not re.match(r"^(sd[a-z]+|hd[a-z]+|vd[a-z]+|nvme\d+n\d+)$", name):
                            continue
                        
                        # Create device information
                        device_info = {
                            "name": name,
                            "size": int(blocks) * 1024,
                            "size_human": self._bytes_to_human(int(blocks) * 1024)
                        }
                        
                        block_devices.append(device_info)
            
            return block_devices
        except Exception as e:
            logger.error(f"Error getting block devices: {e}")
            return []
    
    def _get_physical_disks(self) -> List[Dict[str, Any]]:
        """Get information about physical disks.
        
        Returns:
            List of dictionaries with physical disk information
        """
        try:
            physical_disks = []
            
            # Try to list disks using /sys/block
            if os.path.exists("/sys/block"):
                for entry in os.listdir("/sys/block"):
                    # Check if it's a disk
                    if re.match(r"^(sd[a-z]+|hd[a-z]+|vd[a-z]+|nvme\d+n\d+)$", entry):
                        disk_path = os.path.join("/sys/block", entry)
                        
                        # Get disk information
                        disk_info = {
                            "name": entry,
                            "device": f"/dev/{entry}"
                        }
                        
                        # Get size
                        size_path = os.path.join(disk_path, "size")
                        if os.path.exists(size_path):
                            with open(size_path, "r") as f:
                                size_blocks = int(f.read().strip())
                                size_bytes = size_blocks * 512  # 512 bytes per block
                                disk_info["size"] = size_bytes
                                disk_info["size_human"] = self._bytes_to_human(size_bytes)
                        
                        # Get vendor
                        vendor_path = os.path.join(disk_path, "device/vendor")
                        if os.path.exists(vendor_path):
                            with open(vendor_path, "r") as f:
                                disk_info["vendor"] = f.read().strip()
                        
                        # Get model
                        model_path = os.path.join(disk_path, "device/model")
                        if os.path.exists(model_path):
                            with open(model_path, "r") as f:
                                disk_info["model"] = f.read().strip()
                        
                        # Get serial
                        serial_path = os.path.join(disk_path, "device/serial")
                        if os.path.exists(serial_path):
                            with open(serial_path, "r") as f:
                                disk_info["serial"] = f.read().strip()
                        
                        # Get removable flag
                        removable_path = os.path.join(disk_path, "removable")
                        if os.path.exists(removable_path):
                            with open(removable_path, "r") as f:
                                disk_info["removable"] = f.read().strip() == "1"
                        
                        # Get rotational flag (HDD vs SSD)
                        rotational_path = os.path.join(disk_path, "queue/rotational")
                        if os.path.exists(rotational_path):
                            with open(rotational_path, "r") as f:
                                disk_info["rotational"] = f.read().strip() == "1"
                                disk_info["type"] = "HDD" if disk_info["rotational"] else "SSD"
                        
                        # Try to get SMART information if smartctl is available
                        if self._is_command_available("smartctl"):
                            try:
                                smart_output = subprocess.check_output(
                                    ["sudo", "smartctl", "-i", f"/dev/{entry}"],
                                    universal_newlines=True,
                                    stderr=subprocess.DEVNULL
                                )
                                
                                # Extract SMART information
                                smart_info = {}
                                
                                # Extract model family
                                model_family = re.search(r"Model Family:\s*(.+)", smart_output)
                                if model_family:
                                    smart_info["model_family"] = model_family.group(1).strip()
                                
                                # Extract device model
                                device_model = re.search(r"Device Model:\s*(.+)", smart_output)
                                if device_model:
                                    smart_info["device_model"] = device_model.group(1).strip()
                                
                                # Extract serial number
                                serial_number = re.search(r"Serial Number:\s*(.+)", smart_output)
                                if serial_number:
                                    smart_info["serial_number"] = serial_number.group(1).strip()
                                
                                # Extract firmware version
                                firmware = re.search(r"Firmware Version:\s*(.+)", smart_output)
                                if firmware:
                                    smart_info["firmware"] = firmware.group(1).strip()
                                
                                # Extract capacity
                                capacity = re.search(r"User Capacity:\s*(.+)", smart_output)
                                if capacity:
                                    smart_info["capacity"] = capacity.group(1).strip()
                                
                                # Extract SMART support
                                smart_support = re.search(r"SMART support is:\s*(.+)", smart_output)
                                if smart_support:
                                    smart_info["smart_support"] = smart_support.group(1).strip()
                                
                                if smart_info:
                                    disk_info["smart"] = smart_info
                            except Exception:
                                pass
                        
                        physical_disks.append(disk_info)
            
            return physical_disks
        except Exception as e:
            logger.error(f"Error getting physical disks: {e}")
            return []
    
    def _get_hostname(self) -> str:
        """Get hostname.
        
        Returns:
            Hostname
        """
        try:
            return os.uname().nodename
        except Exception:
            try:
                with open("/etc/hostname", "r") as f:
                    return f.read().strip()
            except Exception:
                try:
                    return subprocess.check_output(["hostname"], universal_newlines=True).strip()
                except Exception:
                    return "unknown"
    
    def _get_kernel_version(self) -> str:
        """Get kernel version.
        
        Returns:
            Kernel version
        """
        try:
            return os.uname().release
        except Exception:
            try:
                return subprocess.check_output(["uname", "-r"], universal_newlines=True).strip()
            except Exception:
                return "unknown"
    
    def _get_os_info(self) -> Dict[str, str]:
        """Get OS information.
        
        Returns:
            Dictionary with OS information
        """
        try:
            # Initialize OS info
            os_info = {
                "name": "Linux",
                "version": "",
                "id": "",
                "pretty_name": ""
            }
            
            # Try to get OS information from /etc/os-release
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            # Remove quotes
                            value = value.strip('"\'')
                            
                            if key == "NAME":
                                os_info["name"] = value
                            elif key == "VERSION":
                                os_info["version"] = value
                            elif key == "ID":
                                os_info["id"] = value
                            elif key == "PRETTY_NAME":
                                os_info["pretty_name"] = value
            
            # If pretty_name is empty, combine name and version
            if not os_info["pretty_name"] and os_info["name"]:
                os_info["pretty_name"] = f"{os_info['name']} {os_info['version']}".strip()
            
            return os_info
        except Exception:
            return {
                "name": "Linux",
                "version": "",
                "id": "",
                "pretty_name": "Linux"
            }
    
    def _get_uptime(self) -> Dict[str, Any]:
        """Get system uptime.
        
        Returns:
            Dictionary with uptime information
        """
        try:
            # Get uptime in seconds
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])
            
            # Calculate days, hours, minutes, and seconds
            days = int(uptime_seconds // (24 * 3600))
            uptime_seconds %= (24 * 3600)
            hours = int(uptime_seconds // 3600)
            uptime_seconds %= 3600
            minutes = int(uptime_seconds // 60)
            seconds = int(uptime_seconds % 60)
            
            # Format uptime string
            uptime_string = ""
            if days > 0:
                uptime_string += f"{days} day{'s' if days != 1 else ''}, "
            
            uptime_string += f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            return {
                "seconds": uptime_seconds,
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "formatted": uptime_string
            }
        except Exception:
            return {
                "seconds": 0,
                "days": 0,
                "hours": 0,
                "minutes": 0,
                "formatted": "unknown"
            }
    
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
