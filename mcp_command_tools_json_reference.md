# MCP Command Tools JSON Reference

This document provides a detailed reference for the JSON response structure returned by command tools in the MCP (Model Context Protocol) interface.

## Command Execution Result

When executing a command using the `command_execute` tool, the following JSON structure is returned:

```json
{
  "id": "cmd_1744711661_6",                   // Unique command identifier
  "command": "/bin/bash /tmp/tmp9b37bcf5.sh", // The executed command
  "success": true,                            // Whether command succeeded (return code 0)
  "stdout": "Hello!!!\nHello!!!\n...",        // Standard output from the command
  "stderr": "",                               // Standard error output
  "return_code": 0,                           // Command's exit code
  "error": null,                              // Error message (if any)
  "completed": true,                          // Whether command completed execution
  "start_time": "2025-04-15T10:15:00.123456", // When command started
  "duration": 0.125,                          // Execution time in seconds
  "timeout": 60,                              // Timeout value in seconds
  "shell": true,                              // Whether shell was used
  "cwd": "/root/code"                         // Working directory
}
```

## Property Descriptions

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier for the command, generated using timestamp and counter in the format `cmd_TIMESTAMP_COUNTER`. Used to track and reference the command, especially for long-running commands. |
| `command` | string | The actual command string that was executed. Provides a record of what was run. |
| `success` | boolean | Indicates if the command completed successfully (return code 0). `true` for successful execution, `false` otherwise. |
| `stdout` | string | Standard output captured from the command execution. Contains the text output that would normally be displayed in the terminal. May be truncated if it exceeds the configured `max_output_size`. |
| `stderr` | string | Standard error output captured from the command. Contains error messages and warnings that would normally be displayed in the terminal. May be truncated if it exceeds the configured `max_output_size`. |
| `return_code` | integer | Exit code returned by the command. Typically, 0 indicates success, while non-zero values indicate various error conditions. |
| `error` | string or null | Error message if something went wrong during execution. `null` if no errors occurred. |
| `completed` | boolean | Indicates if the command finished execution. `true` if completed, `false` if still running or terminated abnormally. |
| `start_time` | string | ISO format timestamp when the command started executing. Useful for tracking when commands were run. |
| `duration` | number | How long the command took to execute in seconds. Useful for performance monitoring. |
| `timeout` | integer | Maximum time allowed for command execution in seconds. If the command exceeds this time, it will be terminated. |
| `shell` | boolean | Whether the command was executed in a shell environment. When `true`, shell features like pipes, redirections, and environment variables are available. |
| `cwd` | string or null | Working directory where the command was executed. `null` if the default directory was used. |

## Script Execution Result

When executing a script using the `command_execute_script` tool, the response includes all fields from the command execution result, plus:

```json
{
  // ... all fields from command execution result
  "script_path": "/tmp/tmp9b37bcf5.sh",       // Path to the temporary script file
  "interpreter": "/bin/bash"                  // Path to the interpreter used
}
```

| Property | Type | Description |
|----------|------|-------------|
| `script_path` | string | Path to the temporary script file created to execute the script content. |
| `interpreter` | string | Path to the interpreter used to execute the script (e.g., "/bin/bash", "/usr/bin/python3"). |

## Command Status Result

When checking the status of a command using the `command_get_status` tool:

```json
{
  "found": true,                              // Whether the command was found
  "status": {                                 // Command status (if found)
    // ... all fields from execution result
  }
}
```

| Property | Type | Description |
|----------|------|-------------|
| `found` | boolean | Indicates if the requested command was found in the running or completed commands. |
| `status` | object | If the command was found, contains all fields from the execution result. |
| `error` | string | If the command was not found or an error occurred, contains an error message. |

## Command History Result

When retrieving command history using the `command_list_history` tool:

```json
{
  "count": 2,                                 // Number of history entries
  "history": [                                // Array of command history entries
    {
      "id": "cmd_1744711661_5",               // Command ID
      "command": "ls -la",                    // Command that was executed
      "start_time": "2025-04-15T10:14:50.123456", // When command started
      "cwd": "/root/code"                     // Working directory
    },
    // ... more history entries
  ]
}
```

| Property | Type | Description |
|----------|------|-------------|
| `count` | integer | Number of history entries returned. |
| `history` | array | List of command history entries, each containing basic information about a previously executed command. |

## Error Response

When an error occurs during tool execution:

```json
{
  "success": false,                           // Indicates failure
  "error": "Command execution is disabled",   // Error message
  "command": "rm -rf /"                       // The command (if applicable)
}
```

| Property | Type | Description |
|----------|------|-------------|
| `success` | boolean | Always `false` for error responses. |
| `error` | string | Description of what went wrong. |
| `command` | string | The command that caused the error (if applicable). |

## Implementation Details

The command execution system includes several safeguards:

1. **Command validation**: Commands are validated against allowed and blocked patterns.
2. **Timeout handling**: Commands are terminated if they exceed the specified timeout.
3. **Output size limits**: Command output is truncated if it exceeds the configured maximum size.
4. **Sudo restrictions**: Sudo commands can be disabled for security.
5. **Script execution control**: Script execution can be disabled separately from regular commands.

These features ensure secure and reliable command execution in the MCP environment.
