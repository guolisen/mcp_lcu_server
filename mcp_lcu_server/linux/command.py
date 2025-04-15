#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 15, 2025
#
# Description: Command execution module for Linux systems.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import re
import time
import signal
import select
import logging
import subprocess
import threading
import tempfile
import shlex
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class CommandOperations:
    """Class for command execution operations on Linux systems."""
    
    def __init__(self, 
                enabled: bool = True,
                allowed_commands: Optional[List[str]] = None,
                blocked_commands: Optional[List[str]] = None,
                timeout: int = 60,
                max_output_size: int = 1024 * 1024,  # 1MB
                allow_sudo: bool = False,
                allow_scripts: bool = True):
        """Initialize command operations.
        
        Args:
            enabled: Whether command execution is enabled
            allowed_commands: List of allowed command patterns (regex)
            blocked_commands: List of blocked command patterns (regex)
            timeout: Default timeout for command execution in seconds
            max_output_size: Maximum size of command output in bytes
            allow_sudo: Whether to allow sudo commands
            allow_scripts: Whether to allow script execution
        """
        self.enabled = enabled
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.allow_sudo = allow_sudo
        self.allow_scripts = allow_scripts
        
        # Compile allowed command patterns
        self.allowed_patterns = []
        if allowed_commands:
            for pattern in allowed_commands:
                if pattern == "*":
                    # Special case: allow all commands
                    self.allowed_patterns = [re.compile(".*")]
                    break
                try:
                    self.allowed_patterns.append(re.compile(pattern))
                except re.error as e:
                    logger.error(f"Invalid allowed command pattern '{pattern}': {e}")
        
        # Compile blocked command patterns
        self.blocked_patterns = []
        if blocked_commands:
            for pattern in blocked_commands:
                try:
                    self.blocked_patterns.append(re.compile(pattern))
                except re.error as e:
                    logger.error(f"Invalid blocked command pattern '{pattern}': {e}")
        
        # Command history
        self.command_history = []
        self.max_history_size = 100
        
        # Running commands
        self.running_commands = {}
        self._command_id_counter = 0
        self._command_id_lock = threading.Lock()
    
    def execute_command(self, 
                       command: str, 
                       timeout: Optional[int] = None, 
                       shell: bool = True,
                       cwd: Optional[str] = None,
                       env: Optional[Dict[str, str]] = None,
                       capture_output: bool = True) -> Dict[str, Any]:
        """Execute a command and return the result.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds (None for default)
            shell: Whether to use shell
            cwd: Working directory
            env: Environment variables
            capture_output: Whether to capture output
        
        Returns:
            Dictionary with command execution result
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Command execution is disabled",
                "command": command
            }
        
        # Validate command
        validation_result = self._validate_command(command)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["reason"],
                "command": command
            }
        
        # Generate command ID
        command_id = self._generate_command_id()
        
        # Use default timeout if not specified
        if timeout is None:
            timeout = self.timeout
        
        # Prepare result dictionary
        result = {
            "id": command_id,
            "command": command,
            "start_time": datetime.now().isoformat(),
            "timeout": timeout,
            "shell": shell,
            "cwd": cwd,
            "success": False,
            "completed": False,
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "error": None,
            "duration": 0
        }
        
        # Add to history
        self._add_to_history({
            "id": command_id,
            "command": command,
            "start_time": result["start_time"],
            "cwd": cwd
        })
        
        # Add to running commands
        self.running_commands[command_id] = result
        
        try:
            # Start time
            start_time = time.time()
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=shell,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Capture output with size limit
            if capture_output:
                stdout_data, stderr_data = self._capture_output_with_limit(process, self.max_output_size, timeout)
                result["stdout"] = stdout_data
                result["stderr"] = stderr_data
            else:
                # Wait for process to complete
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Kill process on timeout
                    process.kill()
                    process.wait()
                    result["error"] = f"Command timed out after {timeout} seconds"
            
            # Get return code
            result["return_code"] = process.returncode
            result["success"] = process.returncode == 0
            
            # Calculate duration
            result["duration"] = time.time() - start_time
            
            # Mark as completed
            result["completed"] = True
            
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing command '{command}': {error_msg}")
            
            # Update result with error
            result["error"] = error_msg
            result["completed"] = True
            result["duration"] = time.time() - start_time
            
            return result
        finally:
            # Remove from running commands
            if command_id in self.running_commands:
                del self.running_commands[command_id]
    
    def execute_script(self, 
                      script_content: str, 
                      interpreter: str = "/bin/bash",
                      timeout: Optional[int] = None,
                      cwd: Optional[str] = None,
                      env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a script and return the result.
        
        Args:
            script_content: Content of the script
            interpreter: Path to the interpreter
            timeout: Timeout in seconds (None for default)
            cwd: Working directory
            env: Environment variables
        
        Returns:
            Dictionary with script execution result
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Command execution is disabled",
                "interpreter": interpreter
            }
        
        if not self.allow_scripts:
            return {
                "success": False,
                "error": "Script execution is disabled",
                "interpreter": interpreter
            }
        
        # Validate interpreter
        if not os.path.exists(interpreter):
            return {
                "success": False,
                "error": f"Interpreter not found: {interpreter}",
                "interpreter": interpreter
            }
        
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
                script_path = script_file.name
                script_file.write(script_content)
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Execute script
            command = f"{interpreter} {script_path}"
            result = self.execute_command(
                command=command,
                timeout=timeout,
                shell=True,
                cwd=cwd,
                env=env
            )
            
            # Add script info to result
            result["script_path"] = script_path
            result["interpreter"] = interpreter
            
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing script with interpreter '{interpreter}': {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "interpreter": interpreter
            }
        finally:
            # Clean up temporary script file
            try:
                if 'script_path' in locals():
                    os.unlink(script_path)
            except Exception as e:
                logger.error(f"Error cleaning up script file: {e}")
    
    def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running command.
        
        Args:
            command_id: Command ID
        
        Returns:
            Dictionary with command status or None if not found
        """
        return self.running_commands.get(command_id)
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get command execution history.
        
        Args:
            limit: Maximum number of history entries to return
        
        Returns:
            List of dictionaries with command history
        """
        return self.command_history[-limit:]
    
    def _validate_command(self, command: str) -> Dict[str, Any]:
        """Validate a command against allowed and blocked patterns.
        
        Args:
            command: Command to validate
        
        Returns:
            Dictionary with validation result
        """
        # Check for sudo
        if not self.allow_sudo and (command.startswith("sudo ") or "sudo " in command):
            return {
                "valid": False,
                "reason": "Sudo commands are not allowed"
            }
        
        # Check against blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(command):
                return {
                    "valid": False,
                    "reason": f"Command matches blocked pattern: {pattern.pattern}"
                }
        
        # Check against allowed patterns
        if self.allowed_patterns:
            for pattern in self.allowed_patterns:
                if pattern.search(command):
                    return {
                        "valid": True,
                        "reason": ""
                    }
            
            # No allowed pattern matched
            return {
                "valid": False,
                "reason": "Command does not match any allowed pattern"
            }
        
        # No allowed patterns specified, allow all
        return {
            "valid": True,
            "reason": ""
        }
    
    def _generate_command_id(self) -> str:
        """Generate a unique command ID.
        
        Returns:
            Command ID
        """
        with self._command_id_lock:
            self._command_id_counter += 1
            return f"cmd_{int(time.time())}_{self._command_id_counter}"
    
    def _add_to_history(self, command_info: Dict[str, Any]) -> None:
        """Add a command to the history.
        
        Args:
            command_info: Command information
        """
        self.command_history.append(command_info)
        
        # Trim history if needed
        if len(self.command_history) > self.max_history_size:
            self.command_history = self.command_history[-self.max_history_size:]
    
    def _capture_output_with_limit(self, 
                                 process: subprocess.Popen, 
                                 max_size: int, 
                                 timeout: int) -> Tuple[str, str]:
        """Capture process output with size limit.
        
        Args:
            process: Subprocess.Popen instance
            max_size: Maximum output size in bytes
            timeout: Timeout in seconds
        
        Returns:
            Tuple of (stdout, stderr)
        """
        stdout_chunks = []
        stderr_chunks = []
        stdout_size = 0
        stderr_size = 0
        
        # Start time
        start_time = time.time()
        
        # Read output
        while process.poll() is None:
            # Check timeout
            if timeout and time.time() - start_time > timeout:
                process.kill()
                process.wait()
                if stdout_size >= max_size:
                    stdout_chunks.append("\n... output truncated (size limit reached) ...")
                if stderr_size >= max_size:
                    stderr_chunks.append("\n... output truncated (size limit reached) ...")
                break
            
            # Read stdout
            if process.stdout:
                ready_to_read = select.select([process.stdout], [], [], 0.1)[0]
                if ready_to_read:
                    stdout_chunk = process.stdout.read(1024)
                    if stdout_chunk:
                        if stdout_size < max_size:
                            stdout_chunks.append(stdout_chunk)
                            stdout_size += len(stdout_chunk)
            
            # Read stderr
            if process.stderr:
                ready_to_read = select.select([process.stderr], [], [], 0.1)[0]
                if ready_to_read:
                    stderr_chunk = process.stderr.read(1024)
                    if stderr_chunk:
                        if stderr_size < max_size:
                            stderr_chunks.append(stderr_chunk)
                            stderr_size += len(stderr_chunk)
        
        # Read any remaining output
        if process.stdout:
            stdout_chunk = process.stdout.read()
            if stdout_chunk and stdout_size < max_size:
                stdout_chunks.append(stdout_chunk)
                stdout_size += len(stdout_chunk)
        
        if process.stderr:
            stderr_chunk = process.stderr.read()
            if stderr_chunk and stderr_size < max_size:
                stderr_chunks.append(stderr_chunk)
                stderr_size += len(stderr_chunk)
        
        # Join chunks
        stdout = "".join(stdout_chunks)
        stderr = "".join(stderr_chunks)
        
        return stdout, stderr
