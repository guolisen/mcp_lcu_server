#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Filesystem operations module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import stat
import shutil
import logging
import datetime
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, BinaryIO

logger = logging.getLogger(__name__)


class FilesystemOperations:
    """Class for filesystem operations on Linux systems."""
    
    def __init__(self, allowed_paths: Optional[List[str]] = None, max_file_size: int = 10 * 1024 * 1024):
        """Initialize filesystem operations.
        
        Args:
            allowed_paths: List of allowed paths (if None, all paths are allowed)
            max_file_size: Maximum file size in bytes (default: 10MB)
        """
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths] if allowed_paths else None
        self.max_file_size = max_file_size
    
    def list_directory(self, path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """List contents of a directory.
        
        Args:
            path: Directory path
            recursive: Whether to list contents recursively
        
        Returns:
            List of dictionaries with file information
        """
        try:
            # Normalize path
            norm_path = self._normalize_path(path)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_path):
                raise PermissionError(f"Access to path {path} is not allowed")
            
            # Check if path exists
            if not os.path.exists(norm_path):
                raise FileNotFoundError(f"Path {path} does not exist")
            
            # Check if path is a directory
            if not os.path.isdir(norm_path):
                raise NotADirectoryError(f"Path {path} is not a directory")
            
            return self._list_directory_internal(norm_path, recursive)
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return []
    
    def _list_directory_internal(self, path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """Internal method to list directory contents.
        
        Args:
            path: Directory path
            recursive: Whether to list contents recursively
        
        Returns:
            List of dictionaries with file information
        """
        result = []
        
        try:
            # List directory contents
            for entry in os.scandir(path):
                # Get file information
                entry_info = self._get_file_info(entry.path)
                
                # Add to result
                result.append(entry_info)
                
                # Recurse into subdirectories if requested
                if recursive and entry.is_dir() and not entry.is_symlink():
                    for subentry in self._list_directory_internal(entry.path, recursive):
                        result.append(subentry)
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
        
        return result
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file information.
        
        Args:
            path: File path
        
        Returns:
            Dictionary with file information
        """
        try:
            # Normalize path
            norm_path = self._normalize_path(path)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_path):
                raise PermissionError(f"Access to path {path} is not allowed")
            
            # Check if path exists
            if not os.path.exists(norm_path):
                raise FileNotFoundError(f"Path {path} does not exist")
            
            return self._get_file_info(norm_path)
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return {"error": str(e)}
    
    def _get_file_info(self, path: str) -> Dict[str, Any]:
        """Internal method to get file information.
        
        Args:
            path: File path
        
        Returns:
            Dictionary with file information
        """
        try:
            # Get stat information
            file_stat = os.stat(path, follow_symlinks=False)
            
            # Get file type
            file_type = self._get_file_type(file_stat.st_mode)
            
            # Check if path is a symlink
            is_symlink = os.path.islink(path)
            symlink_target = os.readlink(path) if is_symlink else None
            
            # Get file size
            file_size = file_stat.st_size
            
            # Get file timestamps
            atime = datetime.datetime.fromtimestamp(file_stat.st_atime)
            mtime = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            ctime = datetime.datetime.fromtimestamp(file_stat.st_ctime)
            
            # Get file permissions
            file_mode = file_stat.st_mode
            permissions = self._format_permissions(file_mode)
            
            # Get file owner and group
            try:
                import pwd
                import grp
                owner = pwd.getpwuid(file_stat.st_uid).pw_name
                group = grp.getgrgid(file_stat.st_gid).gr_name
            except (ImportError, KeyError):
                owner = str(file_stat.st_uid)
                group = str(file_stat.st_gid)
            
            # Get file extension
            _, ext = os.path.splitext(path)
            if ext:
                ext = ext[1:]  # Remove leading dot
            
            # Get MIME type
            mime_type = self._get_mime_type(path)
            
            # Create result
            result = {
                "name": os.path.basename(path),
                "path": path,
                "type": file_type,
                "size": file_size,
                "size_human": self._bytes_to_human(file_size),
                "permissions": permissions,
                "mode": file_mode,
                "owner": owner,
                "group": group,
                "atime": atime.isoformat(),
                "mtime": mtime.isoformat(),
                "ctime": ctime.isoformat(),
                "extension": ext,
                "mime_type": mime_type,
                "is_symlink": is_symlink,
            }
            
            # Add symlink target if applicable
            if is_symlink:
                result["symlink_target"] = symlink_target
            
            return result
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return {
                "name": os.path.basename(path),
                "path": path,
                "error": str(e)
            }
    
    def read_file(self, path: str, binary: bool = False) -> Union[str, bytes, Dict[str, Any]]:
        """Read file contents.
        
        Args:
            path: File path
            binary: Whether to read file in binary mode
        
        Returns:
            File contents as string, bytes, or error dictionary
        """
        try:
            # Normalize path
            norm_path = self._normalize_path(path)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_path):
                raise PermissionError(f"Access to path {path} is not allowed")
            
            # Check if file exists
            if not os.path.exists(norm_path):
                raise FileNotFoundError(f"File {path} does not exist")
            
            # Check if path is a file
            if not os.path.isfile(norm_path):
                raise IsADirectoryError(f"Path {path} is not a file")
            
            # Check file size
            file_size = os.path.getsize(norm_path)
            if file_size > self.max_file_size:
                raise ValueError(f"File size {self._bytes_to_human(file_size)} exceeds maximum allowed size {self._bytes_to_human(self.max_file_size)}")
            
            # Read file contents
            mode = "rb" if binary else "r"
            with open(norm_path, mode) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return {"error": str(e)}
    
    def write_file(self, path: str, 
                  content: Union[str, bytes], 
                  mode: str = "w",
                  make_executable: bool = False) -> Dict[str, Any]:
        """Write content to a file.
        
        Args:
            path: File path
            content: Content to write
            mode: File mode (w, a, wb, ab)
            make_executable: Whether to make the file executable
        
        Returns:
            Dictionary with operation result
        """
        try:
            # Normalize path
            norm_path = self._normalize_path(path)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_path):
                raise PermissionError(f"Access to path {path} is not allowed")
            
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(norm_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            # Write file contents
            with open(norm_path, mode) as f:
                f.write(content)
            
            # Make file executable if requested
            if make_executable:
                current_mode = os.stat(norm_path).st_mode
                os.chmod(norm_path, current_mode | 0o111)  # Add execute permission
            
            # Get file information
            file_info = self._get_file_info(norm_path)
            
            return {
                "success": True,
                "message": f"File {path} written successfully",
                "file_info": file_info
            }
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file or directory.
        
        Args:
            path: File or directory path
        
        Returns:
            Dictionary with operation result
        """
        try:
            # Normalize path
            norm_path = self._normalize_path(path)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_path):
                raise PermissionError(f"Access to path {path} is not allowed")
            
            # Check if file exists
            if not os.path.exists(norm_path):
                raise FileNotFoundError(f"Path {path} does not exist")
            
            # Get file information before deletion
            file_info = self._get_file_info(norm_path)
            
            # Delete file or directory
            if os.path.isdir(norm_path) and not os.path.islink(norm_path):
                shutil.rmtree(norm_path)
            else:
                os.remove(norm_path)
            
            return {
                "success": True,
                "message": f"{'Directory' if file_info['type'] == 'directory' else 'File'} {path} deleted successfully",
                "file_info": file_info
            }
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
        
        Returns:
            Dictionary with operation result
        """
        try:
            # Normalize paths
            norm_source = self._normalize_path(source)
            norm_dest = self._normalize_path(destination)
            
            # Check if paths are allowed
            if not self._is_path_allowed(norm_source):
                raise PermissionError(f"Access to source path {source} is not allowed")
            
            if not self._is_path_allowed(norm_dest):
                raise PermissionError(f"Access to destination path {destination} is not allowed")
            
            # Check if source exists
            if not os.path.exists(norm_source):
                raise FileNotFoundError(f"Source path {source} does not exist")
            
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(norm_dest)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            # Copy file or directory
            if os.path.isdir(norm_source) and not os.path.islink(norm_source):
                shutil.copytree(norm_source, norm_dest)
            else:
                shutil.copy2(norm_source, norm_dest)
            
            # Get file information
            source_info = self._get_file_info(norm_source)
            dest_info = self._get_file_info(norm_dest)
            
            return {
                "success": True,
                "message": f"{'Directory' if source_info['type'] == 'directory' else 'File'} {source} copied to {destination} successfully",
                "source_info": source_info,
                "destination_info": dest_info
            }
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
        
        Returns:
            Dictionary with operation result
        """
        try:
            # Normalize paths
            norm_source = self._normalize_path(source)
            norm_dest = self._normalize_path(destination)
            
            # Check if paths are allowed
            if not self._is_path_allowed(norm_source):
                raise PermissionError(f"Access to source path {source} is not allowed")
            
            if not self._is_path_allowed(norm_dest):
                raise PermissionError(f"Access to destination path {destination} is not allowed")
            
            # Check if source exists
            if not os.path.exists(norm_source):
                raise FileNotFoundError(f"Source path {source} does not exist")
            
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(norm_dest)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            # Get file information before moving
            source_info = self._get_file_info(norm_source)
            
            # Move file or directory
            shutil.move(norm_source, norm_dest)
            
            # Get file information after moving
            dest_info = self._get_file_info(norm_dest)
            
            return {
                "success": True,
                "message": f"{'Directory' if source_info['type'] == 'directory' else 'File'} {source} moved to {destination} successfully",
                "source_info": source_info,
                "destination_info": dest_info
            }
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_directory(self, path: str, mode: int = 0o755) -> Dict[str, Any]:
        """Create a directory.
        
        Args:
            path: Directory path
            mode: Directory mode
        
        Returns:
            Dictionary with operation result
        """
        try:
            # Normalize path
            norm_path = self._normalize_path(path)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_path):
                raise PermissionError(f"Access to path {path} is not allowed")
            
            # Create directory
            os.makedirs(norm_path, mode=mode, exist_ok=True)
            
            # Get directory information
            dir_info = self._get_file_info(norm_path)
            
            return {
                "success": True,
                "message": f"Directory {path} created successfully",
                "directory_info": dir_info
            }
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_symlink(self, source: str, destination: str) -> Dict[str, Any]:
        """Create a symbolic link.
        
        Args:
            source: Source path
            destination: Destination path (symlink)
        
        Returns:
            Dictionary with operation result
        """
        try:
            # Normalize paths
            norm_source = self._normalize_path(source)
            norm_dest = self._normalize_path(destination)
            
            # Check if paths are allowed
            if not self._is_path_allowed(norm_dest):
                raise PermissionError(f"Access to destination path {destination} is not allowed")
            
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(norm_dest)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            # Create symlink
            os.symlink(norm_source, norm_dest)
            
            # Get symlink information
            symlink_info = self._get_file_info(norm_dest)
            
            return {
                "success": True,
                "message": f"Symlink {destination} -> {source} created successfully",
                "symlink_info": symlink_info
            }
        except Exception as e:
            logger.error(f"Error creating symlink {destination} -> {source}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_files(self, directory: str, 
                    pattern: str, 
                    recursive: bool = True,
                    case_sensitive: bool = False,
                    max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for files matching a pattern.
        
        Args:
            directory: Directory to search in
            pattern: Search pattern (regular expression)
            recursive: Whether to search recursively
            case_sensitive: Whether the search is case-sensitive
            max_results: Maximum number of results to return
        
        Returns:
            List of dictionaries with file information
        """
        try:
            # Normalize directory path
            norm_dir = self._normalize_path(directory)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_dir):
                raise PermissionError(f"Access to directory {directory} is not allowed")
            
            # Check if directory exists
            if not os.path.exists(norm_dir):
                raise FileNotFoundError(f"Directory {directory} does not exist")
            
            # Check if path is a directory
            if not os.path.isdir(norm_dir):
                raise NotADirectoryError(f"Path {directory} is not a directory")
            
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            
            results = []
            
            # Walk directory tree
            for root, dirs, files in os.walk(norm_dir):
                # Check if we should skip this directory
                if not recursive and root != norm_dir:
                    continue
                
                # Check if we've reached the maximum number of results
                if len(results) >= max_results:
                    break
                
                # Check directories
                for dir_name in dirs:
                    # Check if we've reached the maximum number of results
                    if len(results) >= max_results:
                        break
                    
                    # Check if directory name matches pattern
                    if regex.search(dir_name):
                        dir_path = os.path.join(root, dir_name)
                        
                        # Get directory information
                        dir_info = self._get_file_info(dir_path)
                        results.append(dir_info)
                
                # Check files
                for file_name in files:
                    # Check if we've reached the maximum number of results
                    if len(results) >= max_results:
                        break
                    
                    # Check if file name matches pattern
                    if regex.search(file_name):
                        file_path = os.path.join(root, file_name)
                        
                        # Get file information
                        file_info = self._get_file_info(file_path)
                        results.append(file_info)
            
            return results
        except Exception as e:
            logger.error(f"Error searching for files in {directory} with pattern {pattern}: {e}")
            return []
    
    def search_file_contents(self, directory: str, 
                            pattern: str, 
                            file_pattern: str = "*", 
                            recursive: bool = True,
                            case_sensitive: bool = False,
                            max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for files containing a pattern.
        
        Args:
            directory: Directory to search in
            pattern: Search pattern (regular expression)
            file_pattern: File pattern to match (glob pattern)
            recursive: Whether to search recursively
            case_sensitive: Whether the search is case-sensitive
            max_results: Maximum number of results to return
        
        Returns:
            List of dictionaries with search results
        """
        try:
            # Normalize directory path
            norm_dir = self._normalize_path(directory)
            
            # Check if path is allowed
            if not self._is_path_allowed(norm_dir):
                raise PermissionError(f"Access to directory {directory} is not allowed")
            
            # Check if directory exists
            if not os.path.exists(norm_dir):
                raise FileNotFoundError(f"Directory {directory} does not exist")
            
            # Check if path is a directory
            if not os.path.isdir(norm_dir):
                raise NotADirectoryError(f"Path {directory} is not a directory")
            
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            
            # Compile file pattern
            import fnmatch
            file_pattern_regex = re.compile(fnmatch.translate(file_pattern))
            
            results = []
            
            # Walk directory tree
            for root, dirs, files in os.walk(norm_dir):
                # Check if we should skip this directory
                if not recursive and root != norm_dir:
                    continue
                
                # Check if we've reached the maximum number of results
                if len(results) >= max_results:
                    break
                
                # Check files
                for file_name in files:
                    # Check if we've reached the maximum number of results
                    if len(results) >= max_results:
                        break
                    
                    # Check if file name matches file pattern
                    if not file_pattern_regex.match(file_name):
                        continue
                    
                    file_path = os.path.join(root, file_name)
                    
                    try:
                        # Check if file is a binary file
                        if self._is_binary_file(file_path):
                            continue
                        
                        # Read file contents
                        with open(file_path, "r") as f:
                            content = f.read()
                        
                        # Search for pattern in file contents
                        matches = regex.finditer(content)
                        
                        # Convert matches to line and column numbers
                        for match in matches:
                            # Get line number and column number
                            start_pos = match.start()
                            end_pos = match.end()
                            
                            # Get line and column
                            line_start = content.rfind("\n", 0, start_pos) + 1
                            line_end = content.find("\n", end_pos)
                            if line_end == -1:  # End of file
                                line_end = len(content)
                            
                            # Get line number (1-based)
                            line_number = content.count("\n", 0, start_pos) + 1
                            
                            # Get column number (1-based)
                            column_number = start_pos - line_start + 1
                            
                            # Get line content
                            line_content = content[line_start:line_end]
                            
                            # Add match to results
                            results.append({
                                "file": file_path,
                                "line": line_number,
                                "column": column_number,
                                "content": line_content,
                                "match": match.group(0)
                            })
                            
                            # Check if we've reached the maximum number of results
                            if len(results) >= max_results:
                                break
                    except Exception as e:
                        logger.error(f"Error searching in file {file_path}: {e}")
            
            return results
        except Exception as e:
            logger.error(f"Error searching for file contents in {directory} with pattern {pattern}: {e}")
            return []
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if a file is a binary file.
        
        Args:
            file_path: File path
        
        Returns:
            Whether the file is a binary file
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                return b"\0" in chunk
        except Exception:
            return False
    
    def _normalize_path(self, path: str) -> str:
        """Normalize a path.
        
        Args:
            path: Path to normalize
        
        Returns:
            Normalized path
        """
        # Convert to Path object and resolve
        return str(Path(path).expanduser().resolve())
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed.
        
        Args:
            path: Path to check
        
        Returns:
            Whether the path is allowed
        """
        # If no allowed paths are specified, all paths are allowed
        if self.allowed_paths is None:
            return True
        
        # Convert to Path object
        path_obj = Path(path)
        
        # Check if path is within any of the allowed paths
        for allowed_path in self.allowed_paths:
            try:
                path_obj.relative_to(allowed_path)
                return True
            except ValueError:
                continue
        
        return False
    
    def _get_file_type(self, mode: int) -> str:
        """Get file type from stat mode.
        
        Args:
            mode: File stat mode
        
        Returns:
            File type (file, directory, symlink, etc.)
        """
        if stat.S_ISDIR(mode):
            return "directory"
        elif stat.S_ISREG(mode):
            return "file"
        elif stat.S_ISLNK(mode):
            return "symlink"
        elif stat.S_ISFIFO(mode):
            return "fifo"
        elif stat.S_ISSOCK(mode):
            return "socket"
        elif stat.S_ISBLK(mode):
            return "block"
        elif stat.S_ISCHR(mode):
            return "character"
        else:
            return "unknown"
    
    def _format_permissions(self, mode: int) -> str:
        """Format file permissions in the style of `ls -l`.
        
        Args:
            mode: File stat mode
        
        Returns:
            String with file permissions
        """
        result = ""
        
        # File type
        if stat.S_ISDIR(mode):
            result += "d"
        elif stat.S_ISLNK(mode):
            result += "l"
        elif stat.S_ISFIFO(mode):
            result += "p"
        elif stat.S_ISSOCK(mode):
            result += "s"
        elif stat.S_ISBLK(mode):
            result += "b"
        elif stat.S_ISCHR(mode):
            result += "c"
        else:
            result += "-"
        
        # User permissions
        result += "r" if mode & 0o400 else "-"
        result += "w" if mode & 0o200 else "-"
        if mode & 0o4000:  # Setuid
            result += "s" if mode & 0o100 else "S"
        else:
            result += "x" if mode & 0o100 else "-"
        
        # Group permissions
        result += "r" if mode & 0o40 else "-"
        result += "w" if mode & 0o20 else "-"
        if mode & 0o2000:  # Setgid
            result += "s" if mode & 0o10 else "S"
        else:
            result += "x" if mode & 0o10 else "-"
        
        # Other permissions
        result += "r" if mode & 0o4 else "-"
        result += "w" if mode & 0o2 else "-"
        if mode & 0o1000:  # Sticky bit
            result += "t" if mode & 0o1 else "T"
        else:
            result += "x" if mode & 0o1 else "-"
        
        return result
    
    def _get_mime_type(self, path: str) -> str:
        """Get MIME type of a file.
        
        Args:
            path: File path
        
        Returns:
            MIME type
        """
        try:
            # Try to use file command
            if os.path.exists("/usr/bin/file"):
                try:
                    output = subprocess.check_output(
                        ["file", "--mime-type", "-b", path],
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    ).strip()
                    return output
                except subprocess.CalledProcessError:
                    pass
            
            # Fallback: Guess based on extension
            _, ext = os.path.splitext(path)
            if ext:
                ext = ext.lower()
                
                # Common MIME types
                mime_types = {
                    ".txt": "text/plain",
                    ".html": "text/html",
                    ".htm": "text/html",
                    ".css": "text/css",
                    ".js": "application/javascript",
                    ".json": "application/json",
                    ".xml": "application/xml",
                    ".csv": "text/csv",
                    ".pdf": "application/pdf",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".svg": "image/svg+xml",
                    ".mp3": "audio/mpeg",
                    ".mp4": "video/mp4",
                    ".zip": "application/zip",
                    ".tar": "application/x-tar",
                    ".gz": "application/gzip",
                    ".py": "text/x-python",
                    ".c": "text/x-c",
                    ".cpp": "text/x-c++",
                    ".h": "text/x-c",
                    ".hpp": "text/x-c++",
                    ".java": "text/x-java",
                    ".sh": "text/x-shellscript",
                    ".md": "text/markdown",
                    ".rst": "text/x-rst",
                }
                
                return mime_types.get(ext, "application/octet-stream")
            
            # If extension not found or no extension, check if it's a text file
            if not self._is_binary_file(path):
                return "text/plain"
            
            # Default for binary files
            return "application/octet-stream"
        except Exception as e:
            logger.error(f"Error getting MIME type for {path}: {e}")
            return "application/octet-stream"
    
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
