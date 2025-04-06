#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP resources for network operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
import os
from typing import Dict, List, Optional, Any
from urllib.parse import quote, unquote

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.network import NetworkOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


class NetworkResources:
    """Manager for network resources as MCP resources."""
    
    def __init__(self, config: Config):
        """Initialize network resources.
        
        Args:
            config: Server configuration
        """
        # Get network configuration from config
        allow_downloads = config.network.allow_downloads
        allow_uploads = config.network.allow_uploads
        max_download_size = config.network.max_download_size
        max_upload_size = config.network.max_upload_size
        allowed_domains = config.network.allowed_domains
        
        # Create network operations instance
        self.net_ops = NetworkOperations(
            allow_downloads=allow_downloads,
            allow_uploads=allow_uploads,
            max_download_size=max_download_size,
            max_upload_size=max_upload_size,
            allowed_domains=allowed_domains
        )
    
    def register_resources(self, mcp: FastMCP) -> None:
        """Register all network resource templates and static resources."""
        
        # Network interfaces resource
        @mcp.resource("linux://network/interfaces", 
                     name="Network Interfaces", 
                     description="Get network interfaces information",
                     mime_type="application/json")
        def get_network_interfaces() -> str:
            """Get network interfaces information."""
            try:
                interfaces = self.net_ops.get_interfaces()
                return json.dumps(interfaces, indent=2)
            except Exception as e:
                logger.error(f"Error getting network interfaces: {e}")
                return json.dumps({"error": str(e)})
        
        # Network connections resource
        @mcp.resource("linux://network/connections", 
                     name="Network Connections", 
                     description="Get network connections",
                     mime_type="application/json")
        def get_network_connections() -> str:
            """Get network connections."""
            try:
                connections = self.net_ops.get_connections()
                return json.dumps(connections, indent=2)
            except Exception as e:
                logger.error(f"Error getting network connections: {e}")
                return json.dumps({"error": str(e)})
        
        # Network statistics resource
        @mcp.resource("linux://network/stats", 
                     name="Network Statistics", 
                     description="Get network statistics",
                     mime_type="application/json")
        def get_network_stats() -> str:
            """Get network statistics."""
            try:
                stats = self.net_ops.get_stats()
                return json.dumps(stats, indent=2)
            except Exception as e:
                logger.error(f"Error getting network statistics: {e}")
                return json.dumps({"error": str(e)})
        
        # Ping host resource
        @mcp.resource("linux://network/ping/{host}",
                     name="Ping Host",
                     description="Ping a host",
                     mime_type="application/json")
        def ping_host(host: str) -> str:
            """Ping a host."""
            try:
                # URL decode host
                decoded_host = unquote(host)
                
                results = self.net_ops.ping(decoded_host)
                return json.dumps(results, indent=2)
            except Exception as e:
                logger.error(f"Error pinging host {host}: {e}")
                return json.dumps({"error": str(e)})
        
        # Traceroute host resource
        @mcp.resource("linux://network/traceroute/{host}",
                     name="Traceroute Host",
                     description="Trace route to a host",
                     mime_type="application/json")
        def traceroute_host(host: str) -> str:
            """Trace route to a host."""
            try:
                # URL decode host
                decoded_host = unquote(host)
                
                results = self.net_ops.traceroute(decoded_host)
                return json.dumps(results, indent=2)
            except Exception as e:
                logger.error(f"Error tracing route to host {host}: {e}")
                return json.dumps({"error": str(e)})
        
        # Network analysis resource
        @mcp.resource("linux://network/analysis",
                     name="Network Analysis",
                     description="Analyze network configuration and connectivity",
                     mime_type="application/json")
        def analyze_network() -> str:
            """Analyze network configuration and connectivity."""
            try:
                # Get network interfaces
                interfaces = self.net_ops.get_interfaces()
                
                # Get network connections
                connections = self.net_ops.get_connections()
                
                # Get network statistics
                stats = self.net_ops.get_stats()
                
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
                    ping_result = self.net_ops.ping("8.8.8.8", count=1, timeout=5)
                    
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


def register_network_resources(mcp: FastMCP, config: Config) -> None:
    """Register network resources with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create the resources manager
    resources = NetworkResources(config)
    
    # Register the resources
    resources.register_resources(mcp)
