#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Network operations module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import time
import socket
import logging
import requests
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, BinaryIO, IO

import psutil

logger = logging.getLogger(__name__)


class NetworkOperations:
    """Class for network operations on Linux systems."""
    
    def __init__(self, 
                allow_downloads: bool = True, 
                allow_uploads: bool = True,
                max_download_size: int = 100 * 1024 * 1024,  # 100MB
                max_upload_size: int = 10 * 1024 * 1024,  # 10MB
                allowed_domains: Optional[List[str]] = None):
        """Initialize network operations.
        
        Args:
            allow_downloads: Whether to allow file downloads
            allow_uploads: Whether to allow file uploads
            max_download_size: Maximum download size in bytes
            max_upload_size: Maximum upload size in bytes
            allowed_domains: List of allowed domains for network operations
        """
        self.allow_downloads = allow_downloads
        self.allow_uploads = allow_uploads
        self.max_download_size = max_download_size
        self.max_upload_size = max_upload_size
        self.allowed_domains = allowed_domains or ["*"]
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interfaces information.
        
        Returns:
            List of dictionaries with network interface information
        """
        try:
            # Get network interfaces using psutil
            interfaces = []
            
            # Get network addresses
            net_addrs = psutil.net_if_addrs()
            
            # Get network statistics
            net_stats = psutil.net_if_stats()
            
            # Get network I/O counters
            net_io = psutil.net_io_counters(pernic=True)
            
            # Process each interface
            for interface_name, addrs in net_addrs.items():
                interface_info = {
                    "name": interface_name,
                    "addresses": [],
                    "stats": {},
                    "io_counters": {}
                }
                
                # Process addresses
                for addr in addrs:
                    address_info = {
                        "family": self._get_address_family_name(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                        "ptp": addr.ptp
                    }
                    interface_info["addresses"].append(address_info)
                
                # Add statistics if available
                if interface_name in net_stats:
                    stats = net_stats[interface_name]
                    interface_info["stats"] = {
                        "isup": stats.isup,
                        "duplex": stats.duplex,
                        "speed": stats.speed,
                        "mtu": stats.mtu
                    }
                
                # Add I/O counters if available
                if interface_name in net_io:
                    counters = net_io[interface_name]
                    interface_info["io_counters"] = {
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
                
                interfaces.append(interface_info)
            
            return interfaces
        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}")
            return []
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """Get network connections.
        
        Returns:
            List of dictionaries with network connection information
        """
        try:
            # Get network connections using psutil
            connections = []
            
            # Get all network connections
            net_conns = psutil.net_connections()
            
            # Process each connection
            for conn in net_conns:
                # Create connection info
                conn_info = {
                    "fd": conn.fd,
                    "family": self._get_address_family_name(conn.family),
                    "type": self._get_socket_type_name(conn.type),
                    "laddr": {
                        "ip": conn.laddr.ip if conn.laddr else None,
                        "port": conn.laddr.port if conn.laddr else None
                    },
                    "raddr": {
                        "ip": conn.raddr.ip if conn.raddr else None,
                        "port": conn.raddr.port if conn.raddr else None
                    },
                    "status": conn.status,
                    "pid": conn.pid
                }
                
                # Add process name if available
                if conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        conn_info["process"] = {
                            "name": process.name(),
                            "exe": process.exe(),
                            "cmdline": process.cmdline()
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                connections.append(conn_info)
            
            return connections
        except Exception as e:
            logger.error(f"Error getting network connections: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics.
        
        Returns:
            Dictionary with network statistics
        """
        try:
            # Get network statistics using psutil
            
            # Get network I/O counters
            io_counters = psutil.net_io_counters()
            
            # Create statistics dictionary
            stats = {
                "bytes_sent": io_counters.bytes_sent,
                "bytes_recv": io_counters.bytes_recv,
                "packets_sent": io_counters.packets_sent,
                "packets_recv": io_counters.packets_recv,
                "errin": io_counters.errin,
                "errout": io_counters.errout,
                "dropin": io_counters.dropin,
                "dropout": io_counters.dropout,
                "bytes_sent_human": self._bytes_to_human(io_counters.bytes_sent),
                "bytes_recv_human": self._bytes_to_human(io_counters.bytes_recv)
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting network statistics: {e}")
            return {}
    
    def ping(self, host: str, count: int = 4, timeout: int = 10) -> Dict[str, Any]:
        """Ping a host.
        
        Args:
            host: Host to ping
            count: Number of ping packets
            timeout: Timeout in seconds
        
        Returns:
            Dictionary with ping results
        """
        try:
            # Check if host is allowed
            if not self._is_domain_allowed(host):
                raise ValueError(f"Domain {host} is not allowed")
            
            # Use the ping command to ping the host
            if self._is_command_available("ping"):
                # Build the ping command
                cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
                
                # Execute the ping command
                start_time = time.time()
                output = subprocess.check_output(cmd, universal_newlines=True)
                end_time = time.time()
                
                # Parse the output
                # Example output:
                # PING google.com (142.250.185.78) 56(84) bytes of data.
                # 64 bytes from muc11s21-in-f14.1e100.net (142.250.185.78): icmp_seq=1 ttl=115 time=14.8 ms
                # 64 bytes from muc11s21-in-f14.1e100.net (142.250.185.78): icmp_seq=2 ttl=115 time=14.7 ms
                # 64 bytes from muc11s21-in-f14.1e100.net (142.250.185.78): icmp_seq=3 ttl=115 time=14.8 ms
                # 64 bytes from muc11s21-in-f14.1e100.net (142.250.185.78): icmp_seq=4 ttl=115 time=14.7 ms
                #
                # --- google.com ping statistics ---
                # 4 packets transmitted, 4 received, 0% packet loss, time 3004ms
                # rtt min/avg/max/mdev = 14.694/14.756/14.848/0.060 ms
                
                # Extract the IP address
                ip_match = re.search(r"PING\s+.*\s+\((.*?)\)", output)
                ip = ip_match.group(1) if ip_match else None
                
                # Extract ping statistics
                stats_match = re.search(r"(\d+) packets transmitted, (\d+) received, (\d+)% packet loss", output)
                if stats_match:
                    transmitted = int(stats_match.group(1))
                    received = int(stats_match.group(2))
                    packet_loss = float(stats_match.group(3))
                else:
                    transmitted = 0
                    received = 0
                    packet_loss = 100
                
                # Extract round-trip times
                rtt_match = re.search(r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", output)
                if rtt_match:
                    rtt_min = float(rtt_match.group(1))
                    rtt_avg = float(rtt_match.group(2))
                    rtt_max = float(rtt_match.group(3))
                    rtt_mdev = float(rtt_match.group(4))
                else:
                    rtt_min = 0
                    rtt_avg = 0
                    rtt_max = 0
                    rtt_mdev = 0
                
                # Create results dictionary
                results = {
                    "host": host,
                    "ip": ip,
                    "transmitted": transmitted,
                    "received": received,
                    "packet_loss": packet_loss,
                    "time": end_time - start_time,
                    "rtt": {
                        "min": rtt_min,
                        "avg": rtt_avg,
                        "max": rtt_max,
                        "mdev": rtt_mdev
                    }
                }
                
                return results
            else:
                # Fallback to simple socket connection if ping is not available
                # This is not as accurate as ping but can at least check if host is reachable
                
                # Resolve hostname to IP address
                start_time = time.time()
                ip = socket.gethostbyname(host)
                
                # Try to connect to port 80
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(timeout)
                    s.connect((ip, 80))
                    s.close()
                    received = 1
                except Exception:
                    received = 0
                
                end_time = time.time()
                
                # Create results dictionary
                results = {
                    "host": host,
                    "ip": ip,
                    "transmitted": 1,
                    "received": received,
                    "packet_loss": 0 if received else 100,
                    "time": end_time - start_time,
                    "rtt": {
                        "min": 0,
                        "avg": 0,
                        "max": 0,
                        "mdev": 0
                    }
                }
                
                return results
        except Exception as e:
            logger.error(f"Error pinging host {host}: {e}")
            return {
                "host": host,
                "error": str(e)
            }
    
    def traceroute(self, host: str, max_hops: int = 30, timeout: int = 30) -> Dict[str, Any]:
        """Trace route to a host.
        
        Args:
            host: Host to trace route to
            max_hops: Maximum number of hops
            timeout: Timeout in seconds
        
        Returns:
            Dictionary with traceroute results
        """
        try:
            # Check if host is allowed
            if not self._is_domain_allowed(host):
                raise ValueError(f"Domain {host} is not allowed")
            
            # Use the traceroute command if available
            if self._is_command_available("traceroute"):
                # Build the traceroute command
                cmd = ["traceroute", "-m", str(max_hops), "-w", str(timeout), host]
                
                # Execute the traceroute command
                start_time = time.time()
                output = subprocess.check_output(cmd, universal_newlines=True)
                end_time = time.time()
                
                # Parse the output
                # Example output:
                # traceroute to google.com (142.250.185.78), 30 hops max, 60 byte packets
                #  1  _gateway (192.168.1.1)  2.179 ms  2.158 ms  2.139 ms
                #  2  213.135.255.249 (213.135.255.249)  13.287 ms  13.271 ms  13.254 ms
                #  3  be6.cr3-fra1.ip.twelve99.net (213.248.68.141)  13.750 ms  10.749 ms  10.730 ms
                #  4  bu-ether11.cr2-fra5.ip.twelve99.net (213.155.130.150)  10.713 ms  10.695 ms  15.691 ms
                #  5  google-ic-345384-fra5-b9.ip.twelve99.net (62.115.148.7)  12.679 ms  12.661 ms  12.645 ms
                #  6  108.170.252.193 (108.170.252.193)  12.628 ms  12.616 ms  17.844 ms
                #  7  142.250.227.54 (142.250.227.54)  14.788 ms 142.250.239.64 (142.250.239.64)  14.772 ms 142.250.239.120 (142.250.239.120)  14.756 ms
                #  8  muc11s21-in-f14.1e100.net (142.250.185.78)  14.740 ms  15.723 ms  15.709 ms
                
                # Extract the target IP address
                ip_match = re.search(r"traceroute to\s+.*\s+\((.*?)\)", output)
                ip = ip_match.group(1) if ip_match else None
                
                # Extract hops
                hops = []
                
                # Split the output into lines and skip the first line (header)
                lines = output.strip().split("\n")[1:]
                
                for line in lines:
                    # Extract hop number
                    hop_match = re.match(r"\s*(\d+)\s+", line)
                    if not hop_match:
                        continue
                    
                    hop_number = int(hop_match.group(1))
                    
                    # Extract hop details
                    hop_details = line[len(hop_match.group(0)):].strip()
                    
                    # Extract hostnames and IP addresses
                    hosts = []
                    rtt_values = []
                    
                    # Match host (hostname/IP) and RTT values
                    host_rtt_matches = re.finditer(r"([^ ]+)\s+\(([^)]+)\)\s+([\d.]+) ms", hop_details)
                    for match in host_rtt_matches:
                        hostname = match.group(1)
                        host_ip = match.group(2)
                        rtt = float(match.group(3))
                        
                        # Add host to hosts list if not already present
                        host_entry = {"hostname": hostname, "ip": host_ip}
                        if host_entry not in hosts:
                            hosts.append(host_entry)
                        
                        # Add RTT value
                        rtt_values.append(rtt)
                    
                    # If no hostname found, check for timeouts or errors
                    if not hosts:
                        # Check for timeout (* * *)
                        if "*" in hop_details:
                            hosts = [{"hostname": "*", "ip": "*"}]
                            rtt_values = []
                    
                    # Calculate average RTT
                    avg_rtt = sum(rtt_values) / len(rtt_values) if rtt_values else None
                    
                    # Create hop entry
                    hop = {
                        "number": hop_number,
                        "hosts": hosts,
                        "rtt_values": rtt_values,
                        "avg_rtt": avg_rtt
                    }
                    
                    hops.append(hop)
                
                # Create results dictionary
                results = {
                    "host": host,
                    "ip": ip,
                    "hops": hops,
                    "max_hops": max_hops,
                    "time": end_time - start_time
                }
                
                return results
            else:
                # Fallback to manual traceroute using Python sockets
                # This is not as accurate as the traceroute command but can provide basic functionality
                
                # Resolve hostname to IP address
                target_ip = socket.gethostbyname(host)
                
                # Create results dictionary
                results = {
                    "host": host,
                    "ip": target_ip,
                    "hops": [],
                    "max_hops": max_hops,
                    "time": 0
                }
                
                # Perform traceroute
                start_time = time.time()
                
                for ttl in range(1, max_hops + 1):
                    # Create a UDP socket
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    s.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
                    s.settimeout(timeout)
                    
                    # Create a raw socket to receive ICMP packets
                    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                    recv_socket.settimeout(timeout)
                    
                    # Bind the receive socket
                    recv_socket.bind(("", 0))
                    
                    # Send a UDP packet to an unlikely port
                    port = 33434 + ttl
                    s.sendto(b"", (host, port))
                    
                    # Try to receive the ICMP packet
                    curr_addr = None
                    curr_host = None
                    rtt_values = []
                    
                    try:
                        # Record send time
                        send_time = time.time()
                        
                        # Receive packet
                        _, curr_addr = recv_socket.recvfrom(512)
                        curr_addr = curr_addr[0]
                        
                        # Calculate RTT
                        rtt = (time.time() - send_time) * 1000
                        rtt_values.append(rtt)
                        
                        # Try to resolve hostname
                        try:
                            curr_host = socket.gethostbyaddr(curr_addr)[0]
                        except socket.herror:
                            curr_host = curr_addr
                    except socket.timeout:
                        pass
                    finally:
                        s.close()
                        recv_socket.close()
                    
                    # Create hop entry
                    if curr_addr:
                        hop = {
                            "number": ttl,
                            "hosts": [{"hostname": curr_host, "ip": curr_addr}],
                            "rtt_values": rtt_values,
                            "avg_rtt": sum(rtt_values) / len(rtt_values) if rtt_values else None
                        }
                    else:
                        hop = {
                            "number": ttl,
                            "hosts": [{"hostname": "*", "ip": "*"}],
                            "rtt_values": [],
                            "avg_rtt": None
                        }
                    
                    results["hops"].append(hop)
                    
                    # If we reached the target, break
                    if curr_addr == target_ip:
                        break
                
                end_time = time.time()
                results["time"] = end_time - start_time
                
                return results
        except Exception as e:
            logger.error(f"Error tracing route to host {host}: {e}")
            return {
                "host": host,
                "error": str(e)
            }
    
    def http_get(self, url: str, 
                timeout: int = 30, 
                follow_redirects: bool = True,
                headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform HTTP GET request.
        
        Args:
            url: URL to request
            timeout: Request timeout in seconds
            follow_redirects: Whether to follow redirects
            headers: HTTP headers to include in the request
        
        Returns:
            Dictionary with HTTP response information
        """
        try:
            # Parse URL
            parsed_url = urllib.parse.urlparse(url)
            
            # Check if domain is allowed
            if not self._is_domain_allowed(parsed_url.netloc):
                raise ValueError(f"Domain {parsed_url.netloc} is not allowed")
            
            # Set default headers if not provided
            if headers is None:
                headers = {
                    "User-Agent": "Python/MCP-LCU-Server"
                }
            
            # Perform HTTP GET request
            start_time = time.time()
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=follow_redirects,
                headers=headers,
                stream=True  # Stream to avoid downloading large responses
            )
            end_time = time.time()
            
            # Get response headers
            response_headers = dict(response.headers)
            
            # Get content length
            content_length = int(response_headers.get("Content-Length", 0))
            
            # Check if content length exceeds maximum download size
            if content_length > self.max_download_size:
                response.close()
                raise ValueError(f"Content length {self._bytes_to_human(content_length)} exceeds maximum allowed size {self._bytes_to_human(self.max_download_size)}")
            
            # Get response content (limited to max download size)
            max_content_size = min(content_length or self.max_download_size, self.max_download_size)
            content = response.content[:max_content_size]
            
            # Get response text if it's not too large and appears to be text
            response_text = None
            content_type = response_headers.get("Content-Type", "")
            if (len(content) <= 1024 * 1024) and content_type and ("text/" in content_type or "application/json" in content_type):
                try:
                    response_text = content.decode("utf-8")
                except UnicodeDecodeError:
                    response_text = None
            
            # Create response information
            response_info = {
                "url": response.url,
                "status_code": response.status_code,
                "reason": response.reason,
                "headers": response_headers,
                "content_length": len(content),
                "content_length_human": self._bytes_to_human(len(content)),
                "time": end_time - start_time,
                "text": response_text,
                "redirects": [r.url for r in response.history]
            }
            
            return response_info
        except Exception as e:
            logger.error(f"Error performing HTTP GET request to {url}: {e}")
            return {
                "url": url,
                "error": str(e)
            }
    
    def download_file(self, url: str, 
                     destination: str, 
                     timeout: int = 300,
                     headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Download a file from a URL.
        
        Args:
            url: URL to download from
            destination: Local file path to save the downloaded file
            timeout: Download timeout in seconds
            headers: HTTP headers to include in the request
        
        Returns:
            Dictionary with download information
        """
        try:
            # Check if downloads are allowed
            if not self.allow_downloads:
                raise ValueError("File downloads are not allowed")
            
            # Parse URL
            parsed_url = urllib.parse.urlparse(url)
            
            # Check if domain is allowed
            if not self._is_domain_allowed(parsed_url.netloc):
                raise ValueError(f"Domain {parsed_url.netloc} is not allowed")
            
            # Set default headers if not provided
            if headers is None:
                headers = {
                    "User-Agent": "Python/MCP-LCU-Server"
                }
            
            # Ensure destination directory exists
            destination_dir = os.path.dirname(destination)
            if destination_dir and not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            
            # Start download
            start_time = time.time()
            
            response = requests.get(
                url,
                timeout=timeout,
                headers=headers,
                stream=True
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Get content length
            content_length = int(response.headers.get("Content-Length", 0))
            
            # Check if content length exceeds maximum download size
            if content_length > self.max_download_size:
                response.close()
                raise ValueError(f"Content length {self._bytes_to_human(content_length)} exceeds maximum allowed size {self._bytes_to_human(self.max_download_size)}")
            
            # Download file in chunks
            downloaded_size = 0
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Check if downloaded size exceeds maximum
                        if downloaded_size > self.max_download_size:
                            f.close()
                            os.remove(destination)
                            response.close()
                            raise ValueError(f"Downloaded size {self._bytes_to_human(downloaded_size)} exceeds maximum allowed size {self._bytes_to_human(self.max_download_size)}")
            
            end_time = time.time()
            
            # Get file information
            file_stats = os.stat(destination)
            
            # Create download information
            download_info = {
                "url": url,
                "destination": destination,
                "size": file_stats.st_size,
                "size_human": self._bytes_to_human(file_stats.st_size),
                "time": end_time - start_time,
                "speed": file_stats.st_size / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                "speed_human": self._bytes_to_human(file_stats.st_size / (end_time - start_time)) + "/s" if (end_time - start_time) > 0 else "0 B/s"
            }
            
            return download_info
        except Exception as e:
            logger.error(f"Error downloading file from {url} to {destination}: {e}")
            return {
                "url": url,
                "destination": destination,
                "error": str(e)
            }
    
    def upload_file(self, source: str, 
                   url: str, 
                   timeout: int = 300,
                   field_name: str = "file",
                   additional_fields: Optional[Dict[str, str]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload a file to a URL.
        
        Args:
            source: Local file path to upload
            url: URL to upload to
            timeout: Upload timeout in seconds
            field_name: Form field name for the file
            additional_fields: Additional form fields to include in the upload
            headers: HTTP headers to include in the request
        
        Returns:
            Dictionary with upload information
        """
        try:
            # Check if uploads are allowed
            if not self.allow_uploads:
                raise ValueError("File uploads are not allowed")
            
            # Check if source file exists
            if not os.path.exists(source):
                raise FileNotFoundError(f"Source file {source} not found")
            
            # Parse URL
            parsed_url = urllib.parse.urlparse(url)
            
            # Check if domain is allowed
            if not self._is_domain_allowed(parsed_url.netloc):
                raise ValueError(f"Domain {parsed_url.netloc} is not allowed")
            
            # Check file size
            file_size = os.path.getsize(source)
            if file_size > self.max_upload_size:
                raise ValueError(f"File size {self._bytes_to_human(file_size)} exceeds maximum allowed size {self._bytes_to_human(self.max_upload_size)}")
            
            # Set default headers if not provided
            if headers is None:
                headers = {
                    "User-Agent": "Python/MCP-LCU-Server"
                }
            
            # Start upload
            start_time = time.time()
            
            # Create file objects for upload
            files = {field_name: open(source, "rb")}
            
            # Add additional fields
            data = additional_fields or {}
            
            # Perform the upload
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=timeout
            )
            
            # Close file objects
            for file_obj in files.values():
                file_obj.close()
            
            end_time = time.time()
            
            # Create upload information
            upload_info = {
                "url": url,
                "source": source,
                "size": file_size,
                "size_human": self._bytes_to_human(file_size),
                "status_code": response.status_code,
                "reason": response.reason,
                "time": end_time - start_time,
                "speed": file_size / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                "speed_human": self._bytes_to_human(file_size / (end_time - start_time)) + "/s" if (end_time - start_time) > 0 else "0 B/s"
            }
            
            # Add response text if not too large
            if len(response.text) <= 1024 * 10:  # 10KB max
                upload_info["response"] = response.text
            
            return upload_info
        except Exception as e:
            logger.error(f"Error uploading file {source} to {url}: {e}")
            return {
                "url": url,
                "source": source,
                "error": str(e)
            }
    
    def _is_domain_allowed(self, domain: str) -> bool:
        """Check if a domain is allowed.
        
        Args:
            domain: Domain to check
        
        Returns:
            Whether the domain is allowed
        """
        # If no domains are specified, all domains are allowed
        if not self.allowed_domains:
            return True
        
        # Check if wildcard is allowed
        if "*" in self.allowed_domains:
            return True
        
        # Check if domain is in allowed domains
        return domain in self.allowed_domains
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available.
        
        Args:
            command: Command to check
        
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
    
    def _get_address_family_name(self, family: int) -> str:
        """Get the name of an address family.
        
        Args:
            family: Address family constant
        
        Returns:
            Address family name
        """
        if family == socket.AF_INET:
            return "IPv4"
        elif family == socket.AF_INET6:
            return "IPv6"
        elif family == socket.AF_UNIX:
            return "UNIX"
        else:
            return f"Unknown ({family})"
    
    def _get_socket_type_name(self, socktype: int) -> str:
        """Get the name of a socket type.
        
        Args:
            socktype: Socket type constant
        
        Returns:
            Socket type name
        """
        if socktype == socket.SOCK_STREAM:
            return "TCP"
        elif socktype == socket.SOCK_DGRAM:
            return "UDP"
        elif socktype == socket.SOCK_RAW:
            return "RAW"
        else:
            return f"Unknown ({socktype})"
    
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
