#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: MCP server for Linux Common Utilities.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import asyncio
import logging
import sys
import threading
import signal
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from mcp_lcu_server.config import Config, load_config
from mcp_lcu_server.linux.cpu import CPUOperations
from mcp_lcu_server.linux.memory import MemoryOperations
from mcp_lcu_server.linux.process import ProcessOperations
from mcp_lcu_server.linux.command import CommandOperations
# Import tool registration functions
from mcp_lcu_server.tools.cpu_tools import register_cpu_tools
from mcp_lcu_server.tools.memory_tools import register_memory_tools
from mcp_lcu_server.tools.process_tools import register_process_tools
from mcp_lcu_server.tools.storage_tools import register_storage_tools
from mcp_lcu_server.tools.filesystem_tools import register_filesystem_tools
from mcp_lcu_server.tools.hardware_tools import register_hardware_tools
from mcp_lcu_server.tools.network_tools import register_network_tools
from mcp_lcu_server.tools.monitoring_tools import register_monitoring_tools
from mcp_lcu_server.tools.command_tools import register_command_tools
from mcp_lcu_server.tools.user_tools import register_user_tools
from mcp_lcu_server.prompts.analysis_prompts import register_analysis_prompts
from mcp_lcu_server.resources.system_resources import register_system_resources
from mcp_lcu_server.resources.monitoring_resources import register_monitoring_resources
from mcp_lcu_server.resources.filesystem_resources import register_filesystem_resources
from mcp_lcu_server.resources.network_resources import register_network_resources

logger = logging.getLogger(__name__)


def create_server(config: Optional[Config] = None) -> FastMCP:
    """Create an MCP server for Linux Common Utilities.
    
    Args:
        config: Server configuration. If None, loads configuration from file.
    
    Returns:
        MCP server.
    """
    # Load configuration if not provided
    if config is None:
        config = load_config()
    
    # Create the MCP server with initialization timeout
    mcp = FastMCP(
        config.server.name,
        host=config.server.host,
        port=config.server.port,
        settings={
            "initialization_timeout": 10.0,  # 10 second timeout
            "log_level": "debug"
        }  
    )
    
    # Register tools - monitor calls during registration to debug
    try:
        logger.debug("Registering CPU tools")
        register_cpu_tools(mcp)
    except Exception as e:
        logger.error(f"Error registering CPU tools: {e}")
    
    try: 
        logger.debug("Registering memory tools")
        register_memory_tools(mcp)
    except Exception as e:
        logger.error(f"Error registering memory tools: {e}")
    
    try:
        logger.debug("Registering process tools")
        register_process_tools(mcp, config)
    except Exception as e:
        logger.error(f"Error registering process tools: {e}")
    
    try:
        logger.debug("Registering storage tools")
        register_storage_tools(mcp)
    except Exception as e:
        logger.error(f"Error registering storage tools: {e}")
    
    try:
        logger.debug("Registering filesystem tools")
        register_filesystem_tools(mcp, config)
    except Exception as e:
        logger.error(f"Error registering filesystem tools: {e}")
    
    try:
        logger.debug("Registering hardware tools")
        register_hardware_tools(mcp)
    except Exception as e:
        logger.error(f"Error registering hardware tools: {e}")
    
    try:
        logger.debug("Registering network tools")
        register_network_tools(mcp, config)
    except Exception as e:
        logger.error(f"Error registering network tools: {e}")
    
    try:
        logger.debug("Registering monitoring tools")
        register_monitoring_tools(mcp, config)
    except Exception as e:
        logger.error(f"Error registering monitoring tools: {e}")
    
    try:
        logger.debug("Registering command tools")
        register_command_tools(mcp, config)
    except Exception as e:
        logger.error(f"Error registering command tools: {e}")
    
    try:
        logger.debug("Registering user tools")
        register_user_tools(mcp, config)
    except Exception as e:
        logger.error(f"Error registering user tools: {e}")
    
    # Register prompts
    register_analysis_prompts(mcp)
    
    # Register resources
    register_system_resources(mcp)
    register_monitoring_resources(mcp, config)
    register_filesystem_resources(mcp, config)
    register_network_resources(mcp, config)
    
    return mcp


def run_server_stdio(mcp: FastMCP) -> None:
    """Run the MCP server with stdio transport.
    
    Args:
        mcp: MCP server.
    """
    logger.info("Starting MCP server with stdio transport")
    mcp.run(transport="stdio")


def run_server_sse(mcp: FastMCP, host: str, port: int) -> threading.Thread:
    """Run the MCP server with SSE transport in a separate thread.
    
    Args:
        mcp: MCP server.
        host: Host for SSE transport.
        port: Port for SSE transport.
    
    Returns:
        Thread object.
    """
    def _run_server():
        logger.info(f"Starting MCP server with SSE transport on {host}:{port}")
        mcp.run(transport="sse")
    
    thread = threading.Thread(target=_run_server, daemon=True)
    thread.start()
    return thread


def run_server(config: Optional[Config] = None,
              transport: Optional[str] = None,
              port: Optional[int] = None,
              host: Optional[str] = None) -> None:
    """Run the MCP server.
    
    Args:
        config: Server configuration. If None, loads configuration from file.
        transport: Transport type. If None, uses the value from the configuration.
        port: Port for SSE transport. If None, uses the value from the configuration.
        host: Host for SSE transport. If None, uses the value from the configuration.
    """
    # Load configuration if not provided
    if config is None:
        config = load_config()
    
    # Override configuration with provided values
    if transport is not None:
        config.server.transport = transport
    
    if port is not None:
        config.server.port = port
    
    if host is not None:
        config.server.host = host
    
    # Create the MCP server
    mcp = create_server(config)
    
    # Run the server
    try:
        if config.server.transport == "stdio":
            # Run with stdio transport
            run_server_stdio(mcp)
        elif config.server.transport == "sse":
            # Run with SSE transport
            thread = run_server_sse(mcp, config.server.host, config.server.port)
            
            # Wait for keyboard interrupt
            signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
            try:
                while thread.is_alive():
                    thread.join(1)
            except KeyboardInterrupt:
                logger.info("Stopping MCP server")
                sys.exit(0)
        else:
            logger.error(f"Invalid transport type: {config.server.transport}")
            logger.info("Supported transport types are 'stdio' and 'sse'")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Stopping MCP server")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        sys.exit(1)
