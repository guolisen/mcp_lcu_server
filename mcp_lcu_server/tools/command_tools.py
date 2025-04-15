#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 15, 2025
#
# Description: MCP tools for command execution.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.linux.command import CommandOperations
from mcp_lcu_server.config import Config

logger = logging.getLogger(__name__)


def register_command_tools(mcp: FastMCP, config: Config) -> None:
    """Register command execution tools with the MCP server.
    
    Args:
        mcp: MCP server.
        config: Server configuration.
    """
    # Create command operations instance with configuration
    command_ops = CommandOperations(
        enabled=config.command.enabled,
        allowed_commands=config.command.allowed_commands,
        blocked_commands=config.command.blocked_commands,
        timeout=config.command.timeout,
        max_output_size=config.command.max_output_size,
        allow_sudo=config.command.allow_sudo,
        allow_scripts=config.command.allow_scripts
    )
    
    @mcp.tool()
    def command_execute(command: str, 
                      timeout: Optional[int] = None, 
                      shell: bool = True,
                      cwd: Optional[str] = None,
                      capture_output: bool = True) -> str:
        """Execute a command and return the result.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds (None for default)
            shell: Whether to use shell
            cwd: Working directory
            capture_output: Whether to capture output
        
        Returns:
            JSON string with command execution result containing:
            {
                "id": "cmd_1744711661_6",                   # Unique command identifier (timestamp_counter format)
                "command": "/bin/bash /tmp/tmp9b37bcf5.sh", # The executed command
                "success": true,                            # Whether command succeeded (return code 0)
                "stdout": "Hello!!!\n...",                  # Standard output (may be truncated if exceeds max_output_size)
                "stderr": "",                               # Standard error output
                "return_code": 0,                           # Command's exit code (0 typically means success)
                "error": null,                              # Error message if an error occurred (null otherwise)
                "completed": true,                          # Whether command completed execution
                "start_time": "2025-04-15T10:15:00.123456", # ISO format timestamp when command started
                "duration": 0.125,                          # Execution time in seconds
                "timeout": 60,                              # Timeout value in seconds
                "shell": true,                              # Whether shell was used
                "cwd": "/root/code"                         # Working directory where command was executed
            }
            
            On error:
            {
                "success": false,                           # Indicates failure
                "error": "Command execution is disabled",   # Error message describing what went wrong
                "command": "rm -rf /"                       # The command that caused the error
            }
        """
        logger.info(f"Executing command: {command}")
        
        try:
            if not config.command.enabled:
                return json.dumps({
                    "success": False,
                    "error": "Command execution is disabled by configuration"
                })
            
            result = command_ops.execute_command(
                command=command,
                timeout=timeout,
                shell=shell,
                cwd=cwd,
                capture_output=capture_output
            )
            
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "command": command
            })
    
    @mcp.tool()
    def command_execute_script(script_content: str, 
                             interpreter: str = "/bin/bash",
                             timeout: Optional[int] = None,
                             cwd: Optional[str] = None) -> str:
        """Execute a script and return the result.
        
        Args:
            script_content: Content of the script
            interpreter: Path to the interpreter
            timeout: Timeout in seconds (None for default)
            cwd: Working directory
        
        Returns:
            JSON string with script execution result containing all fields from command_execute plus:
            {
                # ... all fields from command execution result
                "script_path": "/tmp/tmp9b37bcf5.sh",       # Path to the temporary script file
                "interpreter": "/bin/bash"                  # Path to the interpreter used
            }
            
            On error:
            {
                "success": false,                           # Indicates failure
                "error": "Script execution is disabled",    # Error message describing what went wrong
                "interpreter": "/bin/bash"                  # The interpreter that was specified
            }
        """
        logger.info(f"Executing script with interpreter: {interpreter}")
        
        try:
            if not config.command.enabled:
                return json.dumps({
                    "success": False,
                    "error": "Command execution is disabled by configuration"
                })
            
            if not config.command.allow_scripts:
                return json.dumps({
                    "success": False,
                    "error": "Script execution is disabled by configuration"
                })
            
            result = command_ops.execute_script(
                script_content=script_content,
                interpreter=interpreter,
                timeout=timeout,
                cwd=cwd
            )
            
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "interpreter": interpreter
            })
    
    @mcp.tool()
    def command_get_status(command_id: str) -> str:
        """Get status of a running command.
        
        Args:
            command_id: Command ID
        
        Returns:
            JSON string with command status:
            {
                "found": true,                              # Whether the command was found
                "status": {                                 # Command status if found
                    # ... all fields from command execution result
                    "id": "cmd_1744711661_6",
                    "command": "ls -la",
                    "success": true,
                    # ... other fields
                }
            }
            
            If command not found:
            {
                "found": false,                             # Indicates command was not found
                "error": "Command with ID cmd_1744711661_6 not found" # Error message
            }
        """
        logger.info(f"Getting status for command ID: {command_id}")
        
        try:
            status = command_ops.get_command_status(command_id)
            
            if status is None:
                return json.dumps({
                    "found": False,
                    "error": f"Command with ID {command_id} not found"
                })
            
            return json.dumps({
                "found": True,
                "status": status
            }, indent=2)
        except Exception as e:
            logger.error(f"Error getting command status: {e}")
            return json.dumps({
                "found": False,
                "error": str(e)
            })
    
    @mcp.tool()
    def command_list_history(limit: int = 10) -> str:
        """Get command execution history.
        
        Args:
            limit: Maximum number of history entries to return
        
        Returns:
            JSON string with command history:
            {
                "count": 2,                                 # Number of history entries returned
                "history": [                                # Array of command history entries
                    {
                        "id": "cmd_1744711661_5",           # Command ID
                        "command": "ls -la",                # Command that was executed
                        "start_time": "2025-04-15T10:14:50.123456", # When command started
                        "cwd": "/root/code"                 # Working directory
                    },
                    # ... more history entries
                ]
            }
            
            On error:
            {
                "count": 0,                                 # Zero entries
                "history": [],                              # Empty history array
                "error": "Error message"                    # Error message describing what went wrong
            }
        """
        logger.info(f"Listing command history (limit={limit})")
        
        try:
            history = command_ops.get_command_history(limit=limit)
            
            return json.dumps({
                "count": len(history),
                "history": history
            }, indent=2)
        except Exception as e:
            logger.error(f"Error listing command history: {e}")
            return json.dumps({
                "count": 0,
                "history": [],
                "error": str(e)
            })
