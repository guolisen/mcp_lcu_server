#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for network operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.network import NetworkOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


def register_network_tools(mcp: FastMCP, config: Config) -> None:
    """Register network tools with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Get network configuration from config
    allow_downloads = config.network.allow_downloads
    allow_uploads = config.network.allow_uploads
    max_download_size = config.network.max_download_size
    max_upload_size = config.network.max_upload_size
    allowed_domains = config.network.allowed_domains
    
    # Create network operations instance
    net_ops = NetworkOperations(
        allow_downloads=allow_downloads,
        allow_uploads=allow_uploads,
        max_download_size=max_download_size,
        max_upload_size=max_upload_size,
        allowed_domains=allowed_domains
    )
    
    @mcp.tool()
    def get_network_interfaces() -> str:
        """Get network interfaces information.
        
        Returns:
            JSON string with network interfaces information
        """
        logger.info("Getting network interfaces information")
        
        try:
            interfaces = net_ops.get_interfaces()
            return json.dumps(interfaces, indent=2)
        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_network_connections() -> str:
        """Get network connections.
        
        Returns:
            JSON string with network connections information
        """
        logger.info("Getting network connections")
        
        try:
            connections = net_ops.get_connections()
            return json.dumps(connections, indent=2)
        except Exception as e:
            logger.error(f"Error getting network connections: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_network_stats() -> str:
        """Get network statistics.
        
        Returns:
            JSON string with network statistics
        """
        logger.info("Getting network statistics")
        
        try:
            stats = net_ops.get_stats()
            return json.dumps(stats, indent=2)
        except Exception as e:
            logger.error(f"Error getting network statistics: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def ping_host(host: str, count: int = 4, timeout: int = 10) -> str:
        """Ping a host.
        
        Args:
            host: Host to ping
            count: Number of ping packets
            timeout: Timeout in seconds
        
        Returns:
            JSON string with ping results
        """
        logger.info(f"Pinging host {host} (count={count}, timeout={timeout})")
        
        try:
            results = net_ops.ping(host, count, timeout)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Error pinging host {host}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def traceroute_host(host: str, max_hops: int = 30, timeout: int = 30) -> str:
        """Trace route to a host.
        
        Args:
            host: Host to trace route to
            max_hops: Maximum number of hops
            timeout: Timeout in seconds
        
        Returns:
            JSON string with traceroute results
        """
        logger.info(f"Tracing route to host {host} (max_hops={max_hops}, timeout={timeout})")
        
        try:
            results = net_ops.traceroute(host, max_hops, timeout)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Error tracing route to host {host}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def http_get_request(url: str, 
                        timeout: int = 30, 
                        follow_redirects: bool = True) -> str:
        """Perform HTTP GET request.
        
        Args:
            url: URL to request
            timeout: Request timeout in seconds
            follow_redirects: Whether to follow redirects
        
        Returns:
            JSON string with HTTP response information
        """
        logger.info(f"Performing HTTP GET request to {url} (timeout={timeout}, follow_redirects={follow_redirects})")
        
        try:
            response_info = net_ops.http_get(url, timeout, follow_redirects)
            return json.dumps(response_info, indent=2)
        except Exception as e:
            logger.error(f"Error performing HTTP GET request to {url}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def download_file_from_url(url: str, 
                              destination: str, 
                              timeout: int = 300) -> str:
        """Download a file from a URL.
        
        Args:
            url: URL to download from
            destination: Local file path to save the downloaded file
            timeout: Download timeout in seconds
        
        Returns:
            JSON string with download information
        """
        logger.info(f"Downloading file from {url} to {destination} (timeout={timeout})")
        
        try:
            # Check if downloads are allowed
            if not allow_downloads:
                return json.dumps({
                    "error": "File downloads are not allowed"
                })
            
            download_info = net_ops.download_file(url, destination, timeout)
            return json.dumps(download_info, indent=2)
        except Exception as e:
            logger.error(f"Error downloading file from {url} to {destination}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def upload_file_to_url(source: str, 
                          url: str, 
                          timeout: int = 300,
                          field_name: str = "file") -> str:
        """Upload a file to a URL.
        
        Args:
            source: Local file path to upload
            url: URL to upload to
            timeout: Upload timeout in seconds
            field_name: Form field name for the file
        
        Returns:
            JSON string with upload information
        """
        logger.info(f"Uploading file {source} to {url} (timeout={timeout}, field_name={field_name})")
        
        try:
            # Check if uploads are allowed
            if not allow_uploads:
                return json.dumps({
                    "error": "File uploads are not allowed"
                })
            
            upload_info = net_ops.upload_file(source, url, timeout, field_name)
            return json.dumps(upload_info, indent=2)
        except Exception as e:
            logger.error(f"Error uploading file {source} to {url}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def analyze_network() -> str:
        """Analyze network configuration and connectivity.
        
        This function analyzes the network configuration and connectivity
        of the system and provides insights and recommendations.
        
        Returns:
            JSON string with network analysis
        """
        logger.info("Analyzing network configuration and connectivity")
        
        try:
            # Get network interfaces
            interfaces = net_ops.get_interfaces()
            
            # Get network connections
            connections = net_ops.get_connections()
            
            # Get network statistics
            stats = net_ops.get_stats()
            
            # Create analysis result
            analysis = {
                "summary": {
                    "interfaces": len(interfaces),
                    "connections": len(connections),
                    "bytes_sent": stats.get("bytes_sent_human", "0 B"),
                    "bytes_received": stats.get("bytes_recv_human", "0 B")
                },
                "interfaces_up": [],
                "active_connections": 0,
                "listening_ports": []
            }
            
            # Add up interfaces
            for interface in interfaces:
                if interface.get("stats", {}).get("isup", False):
                    # Add interface to up interfaces
                    interface_info = {
                        "name": interface.get("name", "unknown"),
                        "addresses": []
                    }
                    
                    # Add IP addresses
                    for addr in interface.get("addresses", []):
                        if addr.get("family") in ["IPv4", "IPv6"] and addr.get("address"):
                            interface_info["addresses"].append({
                                "family": addr.get("family"),
                                "address": addr.get("address")
                            })
                    
                    # Add to up interfaces if it has addresses
                    if interface_info["addresses"]:
                        analysis["interfaces_up"].append(interface_info)
            
            # Count active connections and listening ports
            for conn in connections:
                # Check if connection is established
                if conn.get("status") == "ESTABLISHED":
                    analysis["active_connections"] += 1
                
                # Check if connection is listening
                if conn.get("status") == "LISTEN":
                    # Get local port
                    local_port = conn.get("laddr", {}).get("port")
                    if local_port:
                        # Add to listening ports if not already present
                        if local_port not in [p.get("port") for p in analysis["listening_ports"]]:
                            # Add process information if available
                            process_info = conn.get("process", {})
                            
                            analysis["listening_ports"].append({
                                "port": local_port,
                                "protocol": conn.get("type", "unknown"),
                                "process_name": process_info.get("name", "unknown"),
                                "process_pid": conn.get("pid", None)
                            })
            
            # Test internet connectivity
            internet_connectivity = {
                "status": "unknown",
                "message": "Internet connectivity test not performed"
            }
            
            try:
                # Try to ping a well-known host
                ping_result = net_ops.ping("8.8.8.8", count=1, timeout=5)
                
                # Check if ping was successful
                if ping_result.get("received", 0) > 0:
                    internet_connectivity = {
                        "status": "connected",
                        "message": "Internet connection is available"
                    }
                else:
                    internet_connectivity = {
                        "status": "disconnected",
                        "message": "Internet connection is not available"
                    }
            except Exception:
                internet_connectivity = {
                    "status": "error",
                    "message": "Error testing internet connectivity"
                }
            
            # Add internet connectivity to analysis
            analysis["internet_connectivity"] = internet_connectivity
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing network: {e}")
            return json.dumps({"error": str(e)})
