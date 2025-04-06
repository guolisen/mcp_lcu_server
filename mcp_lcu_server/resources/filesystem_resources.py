#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP resources for filesystem operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
import os
from typing import Dict, List, Optional, Any
from urllib.parse import quote, unquote

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.filesystem import FilesystemOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


class FilesystemResources:
    """Manager for filesystem resources as MCP resources."""
    
    def __init__(self, config: Config):
        """Initialize filesystem resources.
        
        Args:
            config: Server configuration
        """
        # Get allowed paths from config
        allowed_paths = config.filesystem.allowed_paths if hasattr(config.filesystem, "allowed_paths") else None
        max_file_size = getattr(config.filesystem, "max_file_size", 10 * 1024 * 1024)  # Default to 10MB
        
        # Create filesystem operations instance
        self.fs_ops = FilesystemOperations(allowed_paths=allowed_paths, max_file_size=max_file_size)
    
    def register_resources(self, mcp: FastMCP) -> None:
        """Register all filesystem resource templates and static resources."""
        
        # Directory listing resource
        @mcp.resource("linux://fs/dir/{path}", 
                     name="Directory Listing", 
                     description="List contents of a directory",
                     mime_type="application/json")
        def list_directory(path: str) -> str:
            """List contents of a directory."""
            try:
                # URL decode path
                decoded_path = unquote(path)
                
                # List directory
                contents = self.fs_ops.list_directory(decoded_path, recursive=False)
                return json.dumps(contents, indent=2)
            except Exception as e:
                logger.error(f"Error listing directory {path}: {e}")
                return json.dumps({"error": str(e)})
        
        # Recursive directory listing resource
        @mcp.resource("linux://fs/dir/{path}/recursive", 
                     name="Recursive Directory Listing", 
                     description="List contents of a directory recursively",
                     mime_type="application/json")
        def list_directory_recursive(path: str) -> str:
            """List contents of a directory recursively."""
            try:
                # URL decode path
                decoded_path = unquote(path)
                
                # List directory recursively
                contents = self.fs_ops.list_directory(decoded_path, recursive=True)
                return json.dumps(contents, indent=2)
            except Exception as e:
                logger.error(f"Error listing directory {path} recursively: {e}")
                return json.dumps({"error": str(e)})
        
        # File info resource
        @mcp.resource("linux://fs/info/{path}", 
                     name="File Information", 
                     description="Get information about a file or directory",
                     mime_type="application/json")
        def get_file_info(path: str) -> str:
            """Get information about a file or directory."""
            try:
                # URL decode path
                decoded_path = unquote(path)
                
                # Get file information
                file_info = self.fs_ops.get_file_info(decoded_path)
                return json.dumps(file_info, indent=2)
            except Exception as e:
                logger.error(f"Error getting file info for {path}: {e}")
                return json.dumps({"error": str(e)})
        
        # File contents resource
        @mcp.resource("linux://fs/file/{path}", 
                     name="File Contents", 
                     description="Get contents of a file",
                     mime_type="text/plain")
        def get_file_contents(path: str) -> str:
            """Get contents of a file."""
            try:
                # URL decode path
                decoded_path = unquote(path)
                
                # Get file information to check MIME type
                file_info = self.fs_ops.get_file_info(decoded_path)
                
                # Check if file exists and is a regular file
                if "error" in file_info:
                    return json.dumps({"error": file_info["error"]})
                
                if file_info.get("type") != "file":
                    return json.dumps({"error": f"Path {decoded_path} is not a file"})
                
                # Check if file is binary
                mime_type = file_info.get("mime_type", "")
                is_binary = not (mime_type.startswith("text/") or 
                               mime_type in ["application/json", "application/xml", 
                                           "application/javascript"])
                
                # Read file contents
                result = self.fs_ops.read_file(decoded_path, binary=is_binary)
                
                # Handle error dictionary
                if isinstance(result, dict) and "error" in result:
                    return json.dumps(result)
                
                # Return content
                if is_binary and isinstance(result, bytes):
                    return f"Binary file: {len(result)} bytes"
                
                return result
            except Exception as e:
                logger.error(f"Error getting file contents for {path}: {e}")
                return json.dumps({"error": str(e)})
        
        # Directory usage analysis resource
        @mcp.resource("linux://fs/usage/{path}", 
                     name="Directory Usage Analysis", 
                     description="Analyze directory usage",
                     mime_type="application/json")
        def analyze_directory_usage(path: str) -> str:
            """Analyze directory usage."""
            try:
                # URL decode path
                decoded_path = unquote(path)
                
                # Check if path exists
                file_info = self.fs_ops.get_file_info(decoded_path)
                if "error" in file_info:
                    return json.dumps({"error": file_info["error"]})
                
                # Check if path is a directory
                if file_info.get("type") != "directory":
                    return json.dumps({"error": f"Path {decoded_path} is not a directory"})
                
                # Get directory contents
                contents = self.fs_ops.list_directory(decoded_path, recursive=True)
                
                # Calculate sizes by type
                total_size = 0
                type_sizes = {
                    "file": 0,
                    "directory": 0,
                    "symlink": 0,
                    "other": 0
                }
                
                # Count items by type
                item_counts = {
                    "file": 0,
                    "directory": 0,
                    "symlink": 0,
                    "other": 0
                }
                
                # Count by extension
                extension_counts = {}
                extension_sizes = {}
                
                for item in contents:
                    item_type = item.get("type", "other")
                    item_size = item.get("size", 0)
                    
                    # Update total size
                    total_size += item_size
                    
                    # Update type sizes and counts
                    if item_type in type_sizes:
                        type_sizes[item_type] += item_size
                        item_counts[item_type] += 1
                    else:
                        type_sizes["other"] += item_size
                        item_counts["other"] += 1
                    
                    # Update extension counts and sizes
                    if item_type == "file":
                        ext = item.get("extension", "").lower() or "no_extension"
                        
                        if ext not in extension_counts:
                            extension_counts[ext] = 0
                            extension_sizes[ext] = 0
                        
                        extension_counts[ext] += 1
                        extension_sizes[ext] += item_size
                
                # Prepare extension statistics
                extension_stats = []
                for ext, count in extension_counts.items():
                    extension_stats.append({
                        "extension": ext,
                        "count": count,
                        "size": extension_sizes[ext],
                        "size_human": self.fs_ops._bytes_to_human(extension_sizes[ext]),
                        "percent": (extension_sizes[ext] / total_size * 100) if total_size > 0 else 0
                    })
                
                # Sort extension statistics by size (descending)
                extension_stats.sort(key=lambda x: x["size"], reverse=True)
                
                # Prepare result
                result = {
                    "path": decoded_path,
                    "total_size": total_size,
                    "total_size_human": self.fs_ops._bytes_to_human(total_size),
                    "item_count": sum(item_counts.values()),
                    "item_counts": item_counts,
                    "type_sizes": {
                        t: {
                            "size": s,
                            "size_human": self.fs_ops._bytes_to_human(s),
                            "percent": (s / total_size * 100) if total_size > 0 else 0
                        }
                        for t, s in type_sizes.items()
                    },
                    "extension_stats": extension_stats[:20]  # Top 20 extensions
                }
                
                return json.dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Error analyzing directory usage for {path}: {e}")
                return json.dumps({"error": str(e)})


def register_filesystem_resources(mcp: FastMCP, config: Config) -> None:
    """Register filesystem resources with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create the resources manager
    resources = FilesystemResources(config)
    
    # Register the resources
    resources.register_resources(mcp)
