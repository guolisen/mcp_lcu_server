# MCP Linux Common Utility Server

The Model Context Protocol (MCP) Linux Common Utility (LCU) Server is a Python-based server that provides access to various Linux system operations and information through the Model Context Protocol.

## Features

- **CPU Operations**: CPU information, usage, load average, etc.
- **Memory Operations**: Memory and swap information, usage statistics.
- **Process/Thread Operations**: Process listing, information, and management.
- **Storage Operations**: Disk, volume, and partition information.
- **Filesystem Operations**: File creation, deletion, updating, and information.
- **Hardware Operations**: Hardware detection and information.
- **Network Operations**: Interface information, connectivity testing, and data transfer.
- **Monitoring Operations**: System status monitoring and health checks.

## Installation

### Prerequisites

- Python 3.10 or higher
- Linux operating system

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mcp_lcu_server.git
   cd mcp_lcu_server
   ```

2. Install the package:
   ```
   pip install -e .
   ```

## Configuration

The server can be configured using a YAML configuration file. By default, it looks for the configuration file in the following locations:

- `./config.yaml`
- `./config/config.yaml`
- `/etc/mcp-lcu-server/config.yaml`
- `~/.config/mcp-lcu-server/config.yaml`

You can also specify a custom configuration file path using the `--config` command-line option.

### Configuration File Example

```yaml
server:
  name: mcp-lcu-server
  transport: both  # stdio, sse, or both
  port: 8000
  host: 127.0.0.1

monitoring:
  enabled: true
  interval: 30  # seconds
  metrics:
    - cpu
    - memory
    - disk
    - network

filesystem:
  allowed_paths:
    - /
  max_file_size: 10485760  # 10MB

network:
  allow_downloads: true
  allow_uploads: true
  max_download_size: 104857600  # 100MB
  max_upload_size: 10485760  # 10MB
  allowed_domains:
    - "*"  # Allow all domains

process:
  allow_kill: false
  allowed_users: []
```

## Usage

### Starting the Server

You can start the server using the command-line interface:

```
mcp-lcu-server [OPTIONS]
```

Available options:

- `--config`, `-c`: Path to the configuration file
- `--transport`, `-t`: Transport type (stdio, sse, or both)
- `--port`, `-p`: Port for SSE transport
- `--host`, `-h`: Host for SSE transport
- `--debug`, `-d`: Enable debug logging

### Transport Types

The server supports the following transport types:

- `stdio`: Standard input/output transport
- `sse`: Server-Sent Events transport

### Examples

Start the server with stdio transport:
```
mcp-lcu-server --transport stdio
```

Start the server with SSE transport on port 8000:
```
mcp-lcu-server --transport sse --port 8000
```

Start the server with both transports:
```
mcp-lcu-server --transport both
```

## API Documentation

### Tools

The server provides various tools for interacting with the Linux system:

#### CPU Tools
- `get_cpu_info`: Get detailed CPU information
- `get_cpu_usage`: Get CPU usage percentage
- `get_load_average`: Get system load average
- `analyze_cpu_performance`: Analyze CPU performance

#### Memory Tools
- `get_memory_info`: Get detailed memory information
- `get_memory_usage`: Get memory usage
- `get_swap_info`: Get swap information
- `analyze_memory_performance`: Analyze memory performance

#### Process Tools
- `list_processes`: List all processes
- `get_process_info`: Get detailed information about a process
- `search_processes`: Search for processes
- `analyze_top_processes`: Analyze top processes by CPU and memory usage

#### Storage Tools
- `list_disks`: List physical disks
- `list_partitions`: List disk partitions
- `get_disk_usage`: Get disk usage
- `analyze_storage_usage`: Analyze storage usage

#### Filesystem Tools
- `list_directory`: List contents of a directory
- `read_file`: Read file contents
- `write_file`: Write content to a file
- `delete_file`: Delete a file or directory
- `copy_file`: Copy a file or directory
- `move_file`: Move a file or directory
- `search_files`: Search for files matching a pattern
- `search_file_contents`: Search for files containing a pattern

#### Hardware Tools
- `get_system_info`: Get general system information
- `get_cpu_info`: Get CPU information
- `get_memory_info`: Get memory information
- `get_storage_info`: Get storage information
- `get_pci_devices`: Get PCI device information
- `get_usb_devices`: Get USB device information
- `analyze_hardware`: Analyze hardware configuration

#### Network Tools
- `get_network_interfaces`: Get network interfaces information
- `get_network_connections`: Get network connections
- `get_network_stats`: Get network statistics
- `ping_host`: Ping a host
- `traceroute_host`: Trace route to a host
- `http_get_request`: Perform HTTP GET request
- `download_file_from_url`: Download a file from a URL
- `upload_file_to_url`: Upload a file to a URL
- `analyze_network`: Analyze network configuration and connectivity

#### Monitoring Tools
- `get_system_status`: Get system status
- `check_system_health`: Check system health
- `monitor_resources`: Monitor resource usage
- `get_system_uptime`: Get system uptime
- `get_system_load`: Get system load
- `analyze_system_performance`: Analyze system performance

### Resources

The server also provides various resources that can be accessed via MCP:

#### System Resources
- `linux://system/info`: System information
- `linux://system/cpu`: CPU information
- `linux://system/memory`: Memory information
- `linux://system/uptime`: System uptime

#### Monitoring Resources
- `linux://monitoring/status`: System status
- `linux://monitoring/health`: System health
- `linux://monitoring/resources`: Resource usage

#### Filesystem Resources
- `linux://fs/dir/{path}`: Directory listing
- `linux://fs/info/{path}`: File information
- `linux://fs/file/{path}`: File contents
- `linux://fs/usage/{path}`: Directory usage analysis

#### Network Resources
- `linux://network/interfaces`: Network interfaces
- `linux://network/connections`: Network connections
- `linux://network/stats`: Network statistics
- `linux://network/ping/{host}`: Ping a host
- `linux://network/traceroute/{host}`: Trace route to a host
- `linux://network/analysis`: Network analysis

## Security Considerations

The server provides access to various system operations, which can be potentially dangerous if misused. Make sure to:

- Configure the allowed paths for filesystem operations
- Configure the allowed domains for network operations
- Restrict the ability to kill processes
- Run the server with appropriate permissions

## License

This project is licensed under the MIT License - see the LICENSE file for details.
