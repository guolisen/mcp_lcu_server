#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Storage operations module for Linux systems.
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


class StorageOperations:
    """Class for storage operations on Linux systems."""
    
    def __init__(self):
        """Initialize storage operations."""
        pass
    
    def list_disks(self) -> List[Dict[str, Any]]:
        """List physical disks.
        
        Returns:
            List of dictionaries with disk information
        """
        try:
            disks = []
            
            # Get disk names from /dev/disk/by-id
            disk_by_id_path = "/dev/disk/by-id"
            if os.path.exists(disk_by_id_path):
                for link in os.listdir(disk_by_id_path):
                    # Skip partitions and virtual devices
                    if "part" in link or link.startswith(("md-", "dm-", "lvm-", "wwn-")):
                        continue
                    
                    # Skip CD-ROM and other non-disk devices
                    if link.startswith(("usb-", "ata-")):
                        # Get the real device name
                        try:
                            link_path = os.path.join(disk_by_id_path, link)
                            real_path = os.path.realpath(link_path)
                            device_name = os.path.basename(real_path)
                            
                            # Check if it's a disk
                            if re.match(r"^(sd[a-z]+|nvme\d+n\d+|hd[a-z]+|vd[a-z]+|xvd[a-z]+)$", device_name):
                                # Get disk information
                                disk_info = self._get_disk_info(device_name, link)
                                if disk_info:
                                    disks.append(disk_info)
                        except Exception as e:
                            logger.error(f"Error getting disk info for {link}: {e}")
            
            # Get disks from /sys/block if the above method didn't find any
            if not disks:
                for device in os.listdir("/sys/block"):
                    # Check if it's a disk
                    if re.match(r"^(sd[a-z]+|nvme\d+n\d+|hd[a-z]+|vd[a-z]+|xvd[a-z]+)$", device):
                        # Get disk information
                        disk_info = self._get_disk_info(device)
                        if disk_info:
                            disks.append(disk_info)
            
            return disks
        except Exception as e:
            logger.error(f"Error listing disks: {e}")
            return []
    
    def list_partitions(self) -> List[Dict[str, Any]]:
        """List partitions.
        
        Returns:
            List of dictionaries with partition information
        """
        try:
            partitions = []
            
            # Get partitions from psutil
            disk_partitions = psutil.disk_partitions(all=True)
            
            for partition in disk_partitions:
                # Get partition information
                try:
                    partition_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "opts": partition.opts,
                    }
                    
                    # Add maxfile and maxpath if they exist
                    if hasattr(partition, 'maxfile'):
                        partition_info["maxfile"] = partition.maxfile
                    if hasattr(partition, 'maxpath'):
                        partition_info["maxpath"] = partition.maxpath
                    
                    # Get usage information if mounted
                    if os.path.ismount(partition.mountpoint):
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            partition_info.update({
                                "total": usage.total,
                                "used": usage.used,
                                "free": usage.free,
                                "percent": usage.percent,
                                "total_human": self._bytes_to_human(usage.total),
                                "used_human": self._bytes_to_human(usage.used),
                                "free_human": self._bytes_to_human(usage.free),
                            })
                        except (PermissionError, OSError):
                            # Skip if we can't get usage information
                            pass
                    
                    # Try to get additional information from /dev/disk/by-*
                    partition_name = os.path.basename(partition.device)
                    
                    # Get UUID
                    try:
                        by_uuid_path = "/dev/disk/by-uuid"
                        if os.path.exists(by_uuid_path):
                            for uuid in os.listdir(by_uuid_path):
                                real_path = os.path.realpath(os.path.join(by_uuid_path, uuid))
                                if os.path.basename(real_path) == partition_name:
                                    partition_info["uuid"] = uuid
                                    break
                    except Exception:
                        pass
                    
                    # Get label
                    try:
                        by_label_path = "/dev/disk/by-label"
                        if os.path.exists(by_label_path):
                            for label in os.listdir(by_label_path):
                                real_path = os.path.realpath(os.path.join(by_label_path, label))
                                if os.path.basename(real_path) == partition_name:
                                    partition_info["label"] = label
                                    break
                    except Exception:
                        pass
                    
                    # Get partition type
                    try:
                        by_part_path = "/dev/disk/by-partlabel"
                        if os.path.exists(by_part_path):
                            for part_label in os.listdir(by_part_path):
                                real_path = os.path.realpath(os.path.join(by_part_path, part_label))
                                if os.path.basename(real_path) == partition_name:
                                    partition_info["partlabel"] = part_label
                                    break
                    except Exception:
                        pass
                    
                    partitions.append(partition_info)
                except Exception as e:
                    logger.error(f"Error getting partition info for {partition.device}: {e}")
            
            return partitions
        except Exception as e:
            logger.error(f"Error listing partitions: {e}")
            return []
    
    def list_volumes(self) -> List[Dict[str, Any]]:
        """List logical volumes.
        
        Returns:
            List of dictionaries with volume information
        """
        try:
            volumes = []
            
            # Check if LVM is installed
            if self._is_command_available("lvs"):
                # Get logical volumes
                try:
                    output = subprocess.check_output(["lvs", "--noheadings", "--units", "b", "--separator", "|"], 
                                                   universal_newlines=True)
                    for line in output.strip().split("\n"):
                        if line:
                            parts = line.strip().split("|")
                            if len(parts) >= 6:
                                volume_name = parts[0].strip()
                                volume_group = parts[1].strip()
                                size_str = parts[3].strip()
                                size = int(size_str.rstrip("B")) if size_str.endswith("B") else 0
                                
                                volume_info = {
                                    "name": volume_name,
                                    "vg": volume_group,
                                    "device": f"/dev/{volume_group}/{volume_name}",
                                    "attributes": parts[2].strip(),
                                    "size": size,
                                    "size_human": self._bytes_to_human(size),
                                }
                                
                                # Try to get UUID and other information
                                try:
                                    dev_path = f"/dev/{volume_group}/{volume_name}"
                                    by_uuid_path = "/dev/disk/by-uuid"
                                    if os.path.exists(by_uuid_path):
                                        for uuid in os.listdir(by_uuid_path):
                                            real_path = os.path.realpath(os.path.join(by_uuid_path, uuid))
                                            if real_path == dev_path:
                                                volume_info["uuid"] = uuid
                                                break
                                except Exception:
                                    pass
                                
                                volumes.append(volume_info)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error getting logical volumes: {e}")
            
            # Add MD arrays (software RAID)
            if self._is_command_available("mdadm"):
                try:
                    # Get MD arrays
                    if os.path.exists("/proc/mdstat"):
                        with open("/proc/mdstat", "r") as f:
                            content = f.read()
                        
                        # Parse MD arrays
                        for match in re.finditer(r"^(md\d+) : ([^\n]+)", content, re.MULTILINE):
                            md_name = match.group(1)
                            md_info = match.group(2)
                            
                            # Get detailed information
                            try:
                                output = subprocess.check_output(["mdadm", "--detail", f"/dev/{md_name}"], 
                                                               universal_newlines=True)
                                
                                md_volume = {
                                    "name": md_name,
                                    "device": f"/dev/{md_name}",
                                    "type": "md",
                                }
                                
                                # Parse output
                                level_match = re.search(r"Raid Level : ([^\n]+)", output)
                                if level_match:
                                    md_volume["raid_level"] = level_match.group(1).strip()
                                
                                size_match = re.search(r"Array Size : ([^\n]+)", output)
                                if size_match:
                                    size_str = size_match.group(1).strip()
                                    # Try to convert size to bytes
                                    try:
                                        size_parts = size_str.split()
                                        if len(size_parts) > 0:
                                            size = float(size_parts[0])
                                            if "KB" in size_str:
                                                size *= 1024
                                            elif "MB" in size_str:
                                                size *= 1024 * 1024
                                            elif "GB" in size_str:
                                                size *= 1024 * 1024 * 1024
                                            elif "TB" in size_str:
                                                size *= 1024 * 1024 * 1024 * 1024
                                            md_volume["size"] = int(size)
                                            md_volume["size_human"] = self._bytes_to_human(md_volume["size"])
                                    except Exception:
                                        md_volume["size_str"] = size_str
                                
                                state_match = re.search(r"State : ([^\n]+)", output)
                                if state_match:
                                    md_volume["state"] = state_match.group(1).strip()
                                
                                uuid_match = re.search(r"UUID : ([^\n]+)", output)
                                if uuid_match:
                                    md_volume["uuid"] = uuid_match.group(1).strip()
                                
                                volumes.append(md_volume)
                            except subprocess.CalledProcessError:
                                # Skip if we can't get detailed information
                                pass
                except Exception as e:
                    logger.error(f"Error getting MD arrays: {e}")
            
            return volumes
        except Exception as e:
            logger.error(f"Error listing volumes: {e}")
            return []
    
    def get_disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """Get disk usage for a path.
        
        Args:
            path: Path to get disk usage for
        
        Returns:
            Dictionary with disk usage information
        """
        try:
            # Check if path exists
            if not os.path.exists(path):
                return {"error": f"Path {path} does not exist"}
            
            # Get disk usage
            usage = psutil.disk_usage(path)
            
            # Create result
            result = {
                "path": path,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
                "total_human": self._bytes_to_human(usage.total),
                "used_human": self._bytes_to_human(usage.used),
                "free_human": self._bytes_to_human(usage.free),
            }
            
            # Get filesystem and device
            partitions = psutil.disk_partitions(all=True)
            for partition in partitions:
                if path.startswith(partition.mountpoint):
                    result["device"] = partition.device
                    result["fstype"] = partition.fstype
                    result["mountpoint"] = partition.mountpoint
                    break
            
            return result
        except Exception as e:
            logger.error(f"Error getting disk usage for {path}: {e}")
            return {"error": str(e)}
    
    def get_disk_io_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get disk I/O statistics.
        
        Returns:
            Dictionary with disk I/O statistics
        """
        try:
            # Get disk I/O statistics
            io_stats = psutil.disk_io_counters(perdisk=True)
            
            # Format result
            result = {}
            for disk, stats in io_stats.items():
                result[disk] = {
                    "read_count": stats.read_count,
                    "write_count": stats.write_count,
                    "read_bytes": stats.read_bytes,
                    "write_bytes": stats.write_bytes,
                    "read_time": stats.read_time,
                    "write_time": stats.write_time,
                    "read_merged_count": getattr(stats, "read_merged_count", 0),
                    "write_merged_count": getattr(stats, "write_merged_count", 0),
                    "busy_time": getattr(stats, "busy_time", 0),
                    "read_bytes_human": self._bytes_to_human(stats.read_bytes),
                    "write_bytes_human": self._bytes_to_human(stats.write_bytes),
                }
            
            return result
        except Exception as e:
            logger.error(f"Error getting disk I/O statistics: {e}")
            return {}
    
    def get_disk_smart_info(self, device: str) -> Dict[str, Any]:
        """Get SMART information for a disk.
        
        Args:
            device: Disk device (e.g., sda, nvme0n1)
        
        Returns:
            Dictionary with SMART information
        """
        try:
            # Check if device exists
            if not os.path.exists(f"/dev/{device}"):
                return {"error": f"Device /dev/{device} does not exist"}
            
            # Check if smartctl is available
            if not self._is_command_available("smartctl"):
                return {"error": "smartctl is not available"}
            
            # Get SMART information
            try:
                output = subprocess.check_output(["smartctl", "-a", f"/dev/{device}"], 
                                               universal_newlines=True)
                
                # Parse output
                result = {
                    "device": device,
                    "raw_output": output,
                }
                
                # Parse model and serial
                model_match = re.search(r"Device Model:\s+(.+)", output)
                if model_match:
                    result["model"] = model_match.group(1).strip()
                
                serial_match = re.search(r"Serial Number:\s+(.+)", output)
                if serial_match:
                    result["serial"] = serial_match.group(1).strip()
                
                # Parse SMART status
                smart_status_match = re.search(r"SMART overall-health self-assessment test result: (.+)", output)
                if smart_status_match:
                    result["smart_status"] = smart_status_match.group(1).strip()
                
                # Parse temperature
                temp_match = re.search(r"Temperature:\s+(\d+) Celsius", output)
                if temp_match:
                    result["temperature"] = int(temp_match.group(1))
                
                # Parse power on hours
                power_on_match = re.search(r"Power_On_Hours[^:]*:\s+\d+\s+(\d+)", output)
                if power_on_match:
                    result["power_on_hours"] = int(power_on_match.group(1))
                
                # Parse attributes
                attributes = []
                attribute_section = re.search(r"SMART Attributes Data Structure revision.*?\n(.*?)\n\n", output, re.DOTALL)
                if attribute_section:
                    for line in attribute_section.group(1).strip().split("\n"):
                        if re.match(r"^\s*\d+", line):
                            parts = line.strip().split()
                            if len(parts) >= 10:
                                try:
                                    attribute = {
                                        "id": int(parts[0]),
                                        "name": parts[1],
                                        "value": int(parts[3]),
                                        "worst": int(parts[4]),
                                        "threshold": int(parts[5]),
                                        "raw_value": parts[9],
                                    }
                                    attributes.append(attribute)
                                except Exception:
                                    pass
                
                if attributes:
                    result["attributes"] = attributes
                
                return result
            except subprocess.CalledProcessError as e:
                return {"error": f"Error getting SMART info: {e.output}"}
        except Exception as e:
            logger.error(f"Error getting SMART info: {e}")
            return {"error": str(e)}
    
    def _get_disk_info(self, device_name: str, link_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get disk information.
        
        Args:
            device_name: Disk device name (e.g., sda, nvme0n1)
            link_name: Link name in /dev/disk/by-id
        
        Returns:
            Dictionary with disk information
        """
        try:
            # Create disk info dictionary
            disk_info = {
                "name": device_name,
                "device": f"/dev/{device_name}",
            }
            
            # Add link name
            if link_name:
                disk_info["id"] = link_name
            
            # Get disk size from sysfs
            size_file = f"/sys/block/{device_name}/size"
            if os.path.exists(size_file):
                with open(size_file, "r") as f:
                    size_blocks = int(f.read().strip())
                    disk_info["size"] = size_blocks * 512  # 512 bytes per block
                    disk_info["size_human"] = self._bytes_to_human(disk_info["size"])
            
            # Get disk model from sysfs
            model_file = f"/sys/block/{device_name}/device/model"
            if os.path.exists(model_file):
                with open(model_file, "r") as f:
                    disk_info["model"] = f.read().strip()
            
            # Get disk vendor from sysfs
            vendor_file = f"/sys/block/{device_name}/device/vendor"
            if os.path.exists(vendor_file):
                with open(vendor_file, "r") as f:
                    disk_info["vendor"] = f.read().strip()
            
            # Get disk serial number from sysfs
            serial_file = f"/sys/block/{device_name}/device/serial"
            if os.path.exists(serial_file):
                with open(serial_file, "r") as f:
                    disk_info["serial"] = f.read().strip()
            
            # Get disk removable flag from sysfs
            removable_file = f"/sys/block/{device_name}/removable"
            if os.path.exists(removable_file):
                with open(removable_file, "r") as f:
                    disk_info["removable"] = f.read().strip() == "1"
            
            # Get disk rotational flag from sysfs
            rotational_file = f"/sys/block/{device_name}/queue/rotational"
            if os.path.exists(rotational_file):
                with open(rotational_file, "r") as f:
                    disk_info["rotational"] = f.read().strip() == "1"
            
            # Get disk partitions
            partitions = []
            for partition in os.listdir(f"/sys/block/{device_name}"):
                if partition.startswith(device_name) and os.path.isdir(f"/sys/block/{device_name}/{partition}"):
                    partitions.append(partition)
            
            if partitions:
                disk_info["partitions"] = partitions
                disk_info["partition_count"] = len(partitions)
            
            return disk_info
        except Exception as e:
            logger.error(f"Error getting disk info for {device_name}: {e}")
            return None
    
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
