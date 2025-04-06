#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP tools for filesystem operations.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.filesystem import FilesystemOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


def register_filesystem_tools(mcp: FastMCP, config: Config) -> None:
    """Register filesystem tools with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Get allowed paths from config
    allowed_paths = config.filesystem.allowed_paths if hasattr(config.filesystem, "allowed_paths") else None
    max_file_size = getattr(config.filesystem, "max_file_size", 10 * 1024 * 1024)  # Default to 10MB
    
    # Create filesystem operations instance
    fs_ops = FilesystemOperations(allowed_paths=allowed_paths, max_file_size=max_file_size)
    
    @mcp.tool()
    def list_directory(path: str, recursive: bool = False) -> str:
        """List contents of a directory.
        
        Args:
            path: Directory path
            recursive: Whether to list contents recursively
        
        Returns:
            JSON string with directory contents
        """
        logger.info(f"Listing directory {path} (recursive={recursive})")
        
        try:
            result = fs_ops.list_directory(path, recursive)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def get_file_info(path: str) -> str:
        """Get file information.
        
        Args:
            path: File path
        
        Returns:
            JSON string with file information
        """
        logger.info(f"Getting file info for {path}")
        
        try:
            result = fs_ops.get_file_info(path)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def read_file(path: str, binary: bool = False) -> str:
        """Read file contents.
        
        Args:
            path: File path
            binary: Whether to read file in binary mode
        
        Returns:
            File contents or JSON string with error
        """
        logger.info(f"Reading file {path} (binary={binary})")
        
        try:
            result = fs_ops.read_file(path, binary)
            
            # Handle error dictionary
            if isinstance(result, dict) and "error" in result:
                return json.dumps(result, indent=2)
            
            # Convert binary result to hex string
            if binary and isinstance(result, bytes):
                result = result.hex()
            
            return result
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def write_file(path: str, content: str, mode: str = "w", make_executable: bool = False) -> str:
        """Write content to a file.
        
        Args:
            path: File path
            content: Content to write
            mode: File mode (w, a, wb, ab)
            make_executable: Whether to make the file executable
        
        Returns:
            JSON string with operation result
        """
        logger.info(f"Writing to file {path} (mode={mode}, make_executable={make_executable})")
        
        try:
            # Convert content to bytes if mode is binary
            if "b" in mode and isinstance(content, str):
                if content.startswith("0x"):
                    # Hex string
                    content_bytes = bytes.fromhex(content[2:])
                else:
                    # Try to decode from hex
                    try:
                        content_bytes = bytes.fromhex(content)
                    except ValueError:
                        # Use UTF-8 encoding
                        content_bytes = content.encode("utf-8")
            else:
                content_bytes = content
            
            result = fs_ops.write_file(path, content_bytes, mode, make_executable)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error writing to file {path}: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def delete_file(path: str) -> str:
        """Delete a file or directory.
        
        Args:
            path: File or directory path
        
        Returns:
            JSON string with operation result
        """
        logger.info(f"Deleting file or directory {path}")
        
        try:
            result = fs_ops.delete_file(path)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def copy_file(source: str, destination: str) -> str:
        """Copy a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
        
        Returns:
            JSON string with operation result
        """
        logger.info(f"Copying {source} to {destination}")
        
        try:
            result = fs_ops.copy_file(source, destination)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def move_file(source: str, destination: str) -> str:
        """Move a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
        
        Returns:
            JSON string with operation result
        """
        logger.info(f"Moving {source} to {destination}")
        
        try:
            result = fs_ops.move_file(source, destination)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def create_directory(path: str, mode: int = 0o755) -> str:
        """Create a directory.
        
        Args:
            path: Directory path
            mode: Directory mode
        
        Returns:
            JSON string with operation result
        """
        logger.info(f"Creating directory {path} (mode={mode})")
        
        try:
            result = fs_ops.create_directory(path, mode)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def create_symlink(source: str, destination: str) -> str:
        """Create a symbolic link.
        
        Args:
            source: Source path
            destination: Destination path (symlink)
        
        Returns:
            JSON string with operation result
        """
        logger.info(f"Creating symlink {destination} -> {source}")
        
        try:
            result = fs_ops.create_symlink(source, destination)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error creating symlink {destination} -> {source}: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    @mcp.tool()
    def search_files(directory: str, 
                    pattern: str, 
                    recursive: bool = True,
                    case_sensitive: bool = False,
                    max_results: int = 100) -> str:
        """Search for files matching a pattern.
        
        Args:
            directory: Directory to search in
            pattern: Search pattern (regular expression)
            recursive: Whether to search recursively
            case_sensitive: Whether the search is case-sensitive
            max_results: Maximum number of results to return
        
        Returns:
            JSON string with search results
        """
        logger.info(f"Searching for files in {directory} with pattern {pattern} "
                    f"(recursive={recursive}, case_sensitive={case_sensitive}, "
                    f"max_results={max_results})")
        
        try:
            result = fs_ops.search_files(directory, pattern, recursive, case_sensitive, max_results)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error searching for files in {directory} with pattern {pattern}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def search_file_contents(directory: str, 
                            pattern: str, 
                            file_pattern: str = "*", 
                            recursive: bool = True,
                            case_sensitive: bool = False,
                            max_results: int = 100) -> str:
        """Search for files containing a pattern.
        
        Args:
            directory: Directory to search in
            pattern: Search pattern (regular expression)
            file_pattern: File pattern to match (glob pattern)
            recursive: Whether to search recursively
            case_sensitive: Whether the search is case-sensitive
            max_results: Maximum number of results to return
        
        Returns:
            JSON string with search results
        """
        logger.info(f"Searching for file contents in {directory} with pattern {pattern} "
                    f"(file_pattern={file_pattern}, recursive={recursive}, "
                    f"case_sensitive={case_sensitive}, max_results={max_results})")
        
        try:
            result = fs_ops.search_file_contents(directory, pattern, file_pattern, 
                                              recursive, case_sensitive, max_results)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error searching for file contents in {directory} with pattern {pattern}: {e}")
            return json.dumps({"error": str(e)})
    
    @mcp.tool()
    def analyze_directory_usage(path: str) -> str:
        """Analyze directory usage and provide statistics.
        
        Args:
            path: Directory path
        
        Returns:
            JSON string with directory usage analysis
        """
        logger.info(f"Analyzing directory usage for {path}")
        
        try:
            # Check if path exists
            file_info = fs_ops.get_file_info(path)
            if "error" in file_info:
                return json.dumps({"error": file_info["error"]})
            
            # Check if path is a directory
            if file_info.get("type") != "directory":
                return json.dumps({"error": f"Path {path} is not a directory"})
            
            # Get directory contents
            contents = fs_ops.list_directory(path, recursive=True)
            
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
                    "size_human": fs_ops._bytes_to_human(extension_sizes[ext]),
                    "percent": (extension_sizes[ext] / total_size * 100) if total_size > 0 else 0
                })
            
            # Sort extension statistics by size (descending)
            extension_stats.sort(key=lambda x: x["size"], reverse=True)
            
            # Prepare result
            result = {
                "path": path,
                "total_size": total_size,
                "total_size_human": fs_ops._bytes_to_human(total_size),
                "item_count": sum(item_counts.values()),
                "item_counts": item_counts,
                "type_sizes": {
                    t: {
                        "size": s,
                        "size_human": fs_ops._bytes_to_human(s),
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
