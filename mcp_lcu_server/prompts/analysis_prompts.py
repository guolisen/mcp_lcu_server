#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025, Lewis Guo. All rights reserved.
# Author: Lewis Guo <guolisen@gmail.com>
# Created: April 06, 2025
#
# Description: Analysis prompts for the MCP Linux Common Utility server.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent

logger = logging.getLogger(__name__)


def register_analysis_prompts(mcp: FastMCP) -> None:
    """Register analysis prompts with the MCP server.
    
    Args:
        mcp: MCP server
    """
    
    @mcp.prompt(name="system_overview")
    def system_overview(system_info: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for system overview analysis.
        
        Args:
            system_info: Optional system information.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if system_info:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the Linux system information:\n\n{system_info}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# System Overview Analysis\n\nYou are an expert Linux system administrator tasked with analyzing a Linux system.\n\n## Available Tools and Resources\n\nYou have access to various tools and resources from the MCP Linux Common Utility server:\n\n- CPU tools: get_cpu_info, get_cpu_usage, get_cpu_times, get_load_average, analyze_cpu_performance\n- Memory tools: get_memory_info, get_memory_usage, get_swap_info, analyze_memory_performance\n- Process tools: list_processes, get_process_info, analyze_top_processes\n- Storage tools: list_disks, list_partitions, get_disk_usage, analyze_storage_usage\n- Monitoring tools: get_system_status, check_system_health, analyze_system_performance\n\n## Instructions\n\n1. Examine the system specifications (CPU, memory, storage).\n2. Analyze the current system status and usage.\n3. Identify any potential issues or bottlenecks.\n4. Provide recommendations based on the analysis.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- System Specifications\n- Current Status\n- Issues and Bottlenecks (if any)\n- Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="cpu_performance_analysis")
    def cpu_performance_analysis(cpu_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for CPU performance analysis.
        
        Args:
            cpu_data: Optional CPU performance data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if cpu_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the CPU performance data:\n\n{cpu_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# CPU Performance Analysis\n\nYou are an expert Linux system performance analyst specialized in CPU analysis.\n\n## Available Tools and Resources\n\nYou have access to various CPU-related tools from the MCP Linux Common Utility server:\n\n- get_cpu_info: Get detailed CPU information\n- get_cpu_usage: Get CPU usage percentage\n- get_cpu_times: Get CPU time spent in various modes\n- get_load_average: Get system load average\n- get_cpu_stats: Get CPU statistics (ctx_switches, interrupts, etc.)\n- analyze_cpu_performance: Comprehensive CPU performance analysis\n\n## Instructions\n\n1. Examine the CPU specifications and capabilities.\n2. Analyze the current CPU usage, load, and patterns.\n3. Identify any performance issues, bottlenecks, or abnormal behavior.\n4. Examine process CPU usage if available.\n5. Provide recommendations to optimize CPU performance.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- CPU Specifications\n- Current Utilization\n- Performance Analysis\n- Issues and Bottlenecks (if any)\n- Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="memory_performance_analysis")
    def memory_performance_analysis(memory_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for memory performance analysis.
        
        Args:
            memory_data: Optional memory performance data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if memory_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the memory performance data:\n\n{memory_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Memory Performance Analysis\n\nYou are an expert Linux system performance analyst specialized in memory analysis.\n\n## Available Tools and Resources\n\nYou have access to various memory-related tools from the MCP Linux Common Utility server:\n\n- get_memory_info: Get detailed memory information\n- get_memory_usage: Get memory usage\n- get_swap_info: Get detailed swap information\n- get_swap_usage: Get swap usage\n- get_memory_stats: Get comprehensive memory statistics\n- analyze_memory_performance: Comprehensive memory performance analysis\n\n## Instructions\n\n1. Examine the memory specifications and configuration.\n2. Analyze the current memory usage, distribution, and patterns.\n3. Evaluate swap usage and activity.\n4. Identify any memory pressure, leaks, or abnormal behavior.\n5. Provide recommendations to optimize memory performance.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Memory Specifications\n- Current Utilization\n- Swap Analysis\n- Performance Analysis\n- Issues and Bottlenecks (if any)\n- Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="storage_performance_analysis")
    def storage_performance_analysis(storage_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for storage performance analysis.
        
        Args:
            storage_data: Optional storage performance data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if storage_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the storage performance data:\n\n{storage_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Storage Performance Analysis\n\nYou are an expert Linux system performance analyst specialized in storage analysis.\n\n## Available Tools and Resources\n\nYou have access to various storage-related tools from the MCP Linux Common Utility server:\n\n- list_disks: List physical disks\n- list_partitions: List partitions\n- list_volumes: List logical volumes\n- get_disk_usage: Get disk usage for a path\n- get_disk_io_stats: Get disk I/O statistics\n- analyze_storage_usage: Comprehensive storage usage analysis\n\n## Instructions\n\n1. Examine the disk and storage specifications.\n2. Analyze the current disk usage, partitioning, and filesystem organization.\n3. Evaluate I/O performance and patterns.\n4. Identify any storage bottlenecks, space issues, or abnormal behavior.\n5. Provide recommendations to optimize storage performance.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Storage Specifications\n- Current Utilization\n- I/O Performance\n- Issues and Bottlenecks (if any)\n- Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="process_analysis")
    def process_analysis(process_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for process analysis.
        
        Args:
            process_data: Optional process data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if process_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the process data:\n\n{process_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Process Analysis\n\nYou are an expert Linux system performance analyst specialized in process analysis.\n\n## Available Tools and Resources\n\nYou have access to various process-related tools from the MCP Linux Common Utility server:\n\n- list_processes: List all processes\n- get_process_info: Get detailed information about a process\n- list_threads: List threads for a process\n- search_processes: Search for processes\n- get_process_tree: Get process tree\n- analyze_top_processes: Analyze top processes by CPU and memory usage\n\n## Instructions\n\n1. Examine the process landscape on the system.\n2. Identify resource-intensive processes (CPU, memory).\n3. Analyze process relationships and dependencies.\n4. Detect any abnormal process behavior, zombies, or runaway processes.\n5. Provide recommendations based on the analysis.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Process Overview\n- Resource-Intensive Processes\n- Process Relationships\n- Abnormal Behavior (if any)\n- Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="system_health_analysis")
    def system_health_analysis(health_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for system health analysis.
        
        Args:
            health_data: Optional health data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if health_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the system health data:\n\n{health_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# System Health Analysis\n\nYou are an expert Linux system administrator tasked with performing a health check on a Linux system.\n\n## Available Tools and Resources\n\nYou have access to various monitoring tools from the MCP Linux Common Utility server:\n\n- get_system_status: Get system status\n- check_system_health: Check system health\n- get_cpu_metrics: Get CPU metrics\n- get_memory_metrics: Get memory metrics\n- get_disk_metrics: Get disk metrics\n- get_network_metrics: Get network metrics\n- analyze_system_performance: Analyze system performance\n\n## Instructions\n\n1. Assess the overall system health status.\n2. Identify any critical issues that require immediate attention.\n3. Evaluate resource utilization and performance metrics.\n4. Analyze historical trends and patterns if available.\n5. Provide actionable recommendations to improve system health.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Overall Health Status\n- Critical Issues (if any)\n- Resource Utilization\n- Trends and Patterns\n- Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="network_analysis")
    def network_analysis(network_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for network analysis.
        
        Args:
            network_data: Optional network data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if network_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the network data:\n\n{network_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Network Analysis\n\nYou are an expert Linux network administrator tasked with analyzing the network configuration and performance of a Linux system.\n\n## Available Tools and Resources\n\nYou have access to various network-related information from the MCP Linux Common Utility server.\n\n## Instructions\n\n1. Examine the network interfaces, their configuration, and status.\n2. Analyze IP addressing, routing, and connectivity.\n3. Evaluate network performance metrics and utilization.\n4. Identify any network issues, bottlenecks, or security concerns.\n5. Provide recommendations to optimize network performance and security.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Network Configuration\n- Current Utilization\n- Performance Analysis\n- Issues and Concerns (if any)\n- Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="system_troubleshooting")
    def system_troubleshooting(issue_description: Optional[str] = None, system_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for system troubleshooting.
        
        Args:
            issue_description: Description of the issue.
            system_data: System data related to the issue.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if issue_description:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Issue Description:\n\n{issue_description}"
                    )
                )
            )
            
        if system_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"System Data:\n\n{system_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Linux System Troubleshooting\n\nYou are an expert Linux troubleshooter tasked with diagnosing and resolving issues on a Linux system.\n\n## Available Tools and Resources\n\nYou have access to various tools and resources from the MCP Linux Common Utility server.\n\n## Instructions\n\n1. Analyze the issue description and system data to identify potential causes.\n2. Investigate key areas relevant to the reported problem (e.g., CPU, memory, storage, processes).\n3. Formulate a hypothesis about the root cause.\n4. Suggest diagnostic steps to confirm the root cause.\n5. Provide specific, actionable solutions to resolve the issue.\n6. Include preventive measures to avoid similar issues in the future.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Issue Summary\n- Initial Assessment\n- Potential Causes\n- Diagnostic Steps\n- Recommended Solutions\n- Preventive Measures\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read."
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="security_audit")
    def security_audit(security_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for security audit.
        
        Args:
            security_data: Optional security data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if security_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the security data:\n\n{security_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Linux Security Audit\n\nYou are an expert Linux security auditor tasked with evaluating the security posture of a Linux system.\n\n## Available Tools and Resources\n\nYou have access to various tools and resources from the MCP Linux Common Utility server.\n\n## Instructions\n\n1. Analyze the system configuration for security weaknesses.\n2. Evaluate user accounts, permissions, and authentication mechanisms.\n3. Assess network services, open ports, and firewall configuration.\n4. Identify potential security vulnerabilities and risks.\n5. Provide recommendations to enhance security posture.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Security Overview\n- User and Permission Analysis\n- Network Security\n- Vulnerabilities and Risks\n- Security Recommendations\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read.\n\nFor each recommendation, include:\n- The specific issue addressed\n- The recommended action\n- The potential security impact\n- The priority level (Critical, High, Medium, Low)"
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="performance_optimization")
    def performance_optimization(system_data: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for performance optimization.
        
        Args:
            system_data: Optional system data.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if system_data:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Here is the system data:\n\n{system_data}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Linux Performance Optimization\n\nYou are an expert Linux performance engineer tasked with optimizing a Linux system for maximum performance.\n\n## Available Tools and Resources\n\nYou have access to various tools and resources from the MCP Linux Common Utility server.\n\n## Instructions\n\n1. Evaluate the current system performance across key areas (CPU, memory, storage, network).\n2. Identify performance bottlenecks and inefficiencies.\n3. Analyze resource utilization patterns and workload characteristics.\n4. Provide specific, actionable optimization recommendations.\n5. Prioritize recommendations based on expected performance impact.\n\nPresent your analysis in a clear, structured format with sections for:\n\n- Current Performance Assessment\n- Identified Bottlenecks\n- Optimization Recommendations\n- Implementation Plan\n\nUse appropriate formatting (headings, bullet points) to ensure the analysis is easy to read.\n\nFor each recommendation, include:\n- The specific performance issue addressed\n- The recommended changes (be specific with commands or configuration)\n- The expected performance improvement\n- The priority level (Critical, High, Medium, Low)"
                )
            )
        )
        
        return messages
    
    @mcp.prompt(name="command_assistant")
    def command_assistant(task_description: Optional[str] = None) -> List[PromptMessage]:
        """Create a prompt for command assistant.
        
        Args:
            task_description: Description of the task.
        
        Returns:
            List of prompt messages.
        """
        messages = []
        
        # Add context if provided
        if task_description:
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Task Description:\n\n{task_description}"
                    )
                )
            )
        
        # Add the main prompt
        messages.append(
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text="# Linux Command Assistant\n\nYou are an expert Linux command-line assistant helping users construct effective commands for their task.\n\n## Instructions\n\n1. Analyze the task description to understand what the user wants to accomplish.\n2. Consider the most appropriate commands, tools, and options to address the task.\n3. Construct command examples that effectively accomplish the task.\n4. Explain the command structure, options, and expected output.\n5. Provide alternatives where appropriate.\n\nPresent your response in a clear, structured format with sections for:\n\n- Task Analysis\n- Recommended Command(s)\n- Command Explanation\n- Alternatives (if applicable)\n- Additional Tips\n\nUse appropriate formatting (headings, code blocks) to ensure the response is easy to understand.\n\nInclude safety considerations for destructive operations, and suggest using flags like `--dry-run` or temporary directories where appropriate."
                )
            )
        )
        
        return messages
