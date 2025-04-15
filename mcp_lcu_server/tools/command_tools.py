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
            JSON string with command execution result
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
            JSON string with script execution result
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
            JSON string with command status
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
            JSON string with command history
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
