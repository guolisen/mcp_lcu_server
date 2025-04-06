#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Configuration module for the MCP Linux Common Utility server.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import yaml
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    """Server configuration."""
    
    name: str = "mcp-lcu-server"
    transport: str = "stdio"  # "stdio" or "sse"
    port: int = 8000
    host: str = "127.0.0.1"
    
    @validator("transport")
    def validate_transport(cls, v):
        if v not in ["stdio", "sse"]:
            raise ValueError(f"Invalid transport: {v}. Must be one of: stdio, sse")
        return v


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    
    enabled: bool = True
    interval: int = 30  # seconds
    metrics: List[str] = Field(default=["cpu", "memory", "disk", "network"])
    
    @validator("interval")
    def validate_interval(cls, v):
        if v < 1:
            raise ValueError(f"Monitoring interval must be at least 1 second, got {v}")
        return v
    
    @validator("metrics")
    def validate_metrics(cls, v):
        valid_metrics = ["cpu", "memory", "disk", "network", "process"]
        for metric in v:
            if metric not in valid_metrics:
                raise ValueError(f"Invalid metric: {metric}. Must be one of: {', '.join(valid_metrics)}")
        return v


class FilesystemConfig(BaseModel):
    """Filesystem operations configuration."""
    
    allowed_paths: List[str] = Field(default=["/"])
    max_file_size: int = 1024 * 1024 * 10  # 10MB
    
    @validator("max_file_size")
    def validate_max_file_size(cls, v):
        if v < 0:
            raise ValueError(f"Max file size must be non-negative, got {v}")
        return v


class NetworkConfig(BaseModel):
    """Network operations configuration."""
    
    allow_downloads: bool = True
    allow_uploads: bool = True
    max_download_size: int = 1024 * 1024 * 100  # 100MB
    max_upload_size: int = 1024 * 1024 * 10  # 10MB
    allowed_domains: List[str] = Field(default=["*"])
    
    @validator("max_download_size", "max_upload_size")
    def validate_max_sizes(cls, v):
        if v < 0:
            raise ValueError(f"Max size must be non-negative, got {v}")
        return v


class ProcessConfig(BaseModel):
    """Process operations configuration."""
    
    allow_kill: bool = False
    allowed_users: List[str] = Field(default=[])


class Config(BaseSettings):
    """Main configuration."""
    
    server: ServerConfig = Field(default_factory=ServerConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    filesystem: FilesystemConfig = Field(default_factory=FilesystemConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    process: ProcessConfig = Field(default_factory=ProcessConfig)
    
    model_config = SettingsConfigDict(
        env_prefix="MCP_LCU_SERVER_",
        env_nested_delimiter="__",
    )


def find_config_file() -> Optional[Path]:
    """Find the configuration file."""
    # Check environment variable
    env_config = os.environ.get("MCP_LCU_SERVER_CONFIG")
    if env_config:
        config_path = Path(env_config)
        if config_path.exists():
            return config_path
    
    # Check common locations
    common_locations = [
        Path("./config.yaml"),
        Path("./config/config.yaml"),
        Path("/etc/mcp-lcu-server/config.yaml"),
        Path.home() / ".config" / "mcp-lcu-server" / "config.yaml",
    ]
    
    for location in common_locations:
        if location.exists():
            return location
    
    return None


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from file and environment variables."""
    config = Config()
    
    # Load from file if provided
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
    else:
        path = find_config_file()
    
    # Load from file if found
    if path:
        with open(path, "r") as f:
            file_config = yaml.safe_load(f)
            if file_config:
                # Update config with file values
                for section, values in file_config.items():
                    if hasattr(config, section) and isinstance(values, dict):
                        section_model = getattr(config, section)
                        for key, value in values.items():
                            if hasattr(section_model, key):
                                setattr(section_model, key, value)
    
    return config
