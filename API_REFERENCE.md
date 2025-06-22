# MCP API Reference: Keyboard Maestro MCP Server

## Overview

The Keyboard Maestro MCP Server provides a comprehensive Model Context Protocol (MCP) API for automating macOS workflows through Keyboard Maestro. This document provides detailed reference information for all available tools, request/response formats, authentication requirements, and usage examples.

## API Architecture

### **MCP Protocol Compliance**

The server implements the Model Context Protocol (MCP) specification with the following transport layers:

```yaml
Supported Transports:
  - STDIO: Standard input/output for local AI assistant integration
  - HTTP: RESTful API for remote client connections
  - WebSocket: Real-time bidirectional communication

Protocol Version: MCP 1.0
Server Capabilities:
  - tools: Full tool execution support
  - resources: Dynamic resource discovery
  - prompts: Template-based prompt generation
  - logging: Comprehensive operation logging
```

### **Tool Categories**

The API is organized into logical categories for comprehensive automation coverage:

| Category | Tool Count | Description |
|----------|------------|-------------|
| **Macro Management** | 8 tools | CRUD operations for Keyboard Maestro macros |
| **Macro Execution** | 4 tools | Execute macros with various methods and timeouts |
| **Variable Management** | 6 tools | Manage Keyboard Maestro variables across all scopes |
| **Dictionary Management** | 5 tools | JSON dictionary import/export and manipulation |
| **Clipboard Operations** | 4 tools | Multi-format clipboard read/write operations |
| **File Operations** | 6 tools | File system automation and management |
| **Application Control** | 5 tools | Launch, quit, and control applications |
| **Window Management** | 7 tools | Window positioning, resizing, and focus control |
| **Interface Automation** | 8 tools | Mouse clicks, keyboard input, UI element interaction |
| **OCR Operations** | 4 tools | Text extraction and image-to-text conversion |
| **Image Recognition** | 5 tools | Template matching and visual automation |
| **Communication Tools** | 6 tools | Email, SMS, and notification operations |
| **System Health** | 3 tools | Performance monitoring and health checks |

**Total API Surface: 51+ MCP Tools**

## Authentication & Authorization

### **Permission Requirements**

The server requires specific macOS permissions for operation:

```yaml
Required Permissions:
  accessibility: true          # UI automation and macro execution
  automation: true            # Application control and AppleScript
  full_disk_access: false     # Optional for advanced file operations
  screen_recording: false     # Optional for OCR and image recognition
  microphone: false          # Optional for voice automation features
  camera: false              # Optional for camera-based automation

Permission Validation:
  - Permissions checked at startup and periodically during operation
  - Graceful degradation when optional permissions are unavailable
  - Clear error messages with permission grant instructions
```

### **Security Context**

Each tool operation includes security validation:

```python
# Security context for all operations
SecurityContext {
  user_id: str                 # Authenticated user identifier
  session_id: str              # Unique session identifier
  capability_level: enum       # READ_ONLY, BASIC, ADVANCED, ADMIN
  permitted_operations: set    # Allowed tool operations
  resource_limits: dict        # CPU, memory, timeout constraints
  audit_enabled: bool          # Whether operations are logged
}
```

## Tool Reference Documentation

### **Macro Management Tools**

#### **km_create_macro**

Create a new Keyboard Maestro macro with comprehensive configuration.

**Parameters:**
```typescript
{
  name: string;                    // Macro name (1-255 characters)
  group_uuid?: string;             // Target group UUID (optional)
  enabled?: boolean;               // Whether macro is enabled (default: true)
  color?: string;                  // Macro color (hex or name, optional)
  notes?: string;                  // Macro description (optional)
  triggers?: TriggerConfig[];      // Trigger configurations (optional)
  actions?: ActionConfig[];        // Action configurations (optional)
}
```

**Response:**
```typescript
{
  success: boolean;
  macro_uuid?: string;             // Created macro UUID
  name?: string;                   // Confirmed macro name
  group_uuid?: string;             // Parent group UUID
  created_at?: string;             // ISO timestamp of creation
  error?: string;                  // Error message if failed
  error_code?: string;             // Specific error code
  suggestion?: string;             // Recovery suggestion
}
```

**Example:**
```json
{
  "name": "Daily Backup Automation",
  "group_uuid": "E8F7A123-4567-8901-2345-6789ABCDEF01",
  "enabled": true,
  "color": "blue",
  "notes": "Automated daily backup of important documents",
  "triggers": [
    {
      "type": "time_based",
      "parameters": {
        "time": "18:00",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
      },
      "enabled": true
    }
  ]
}
```

#### **km_get_macro_info**

Retrieve detailed information about a specific macro.

**Parameters:**
```typescript
{
  identifier: string;              // Macro name or UUID
  include_actions?: boolean;       // Include action details (default: false)
  include_triggers?: boolean;      // Include trigger details (default: false)
}
```

**Response:**
```typescript
{
  success: boolean;
  macro?: {
    uuid: string;                  // Macro UUID
    name: string;                  // Macro name
    group_uuid?: string;           // Parent group UUID
    enabled: boolean;              // Enabled status
    color?: string;                // Macro color
    notes?: string;                // Macro notes
    created_at: string;            // ISO timestamp
    modified_at: string;           // ISO timestamp
    trigger_count: number;         // Number of triggers
    action_count: number;          // Number of actions
    triggers?: TriggerConfig[];    // Trigger details (if requested)
    actions?: ActionConfig[];      // Action details (if requested)
  };
  error?: string;
  error_code?: string;
}
```

#### **km_list_macros**

List macros with filtering and pagination support.

**Parameters:**
```typescript
{
  group_uuid?: string;             // Filter by group (optional)
  enabled_only?: boolean;          // Only enabled macros (default: false)
  name_pattern?: string;           // Regex pattern for name filtering
  limit?: number;                  // Maximum results (default: 100, max: 1000)
  offset?: number;                 // Pagination offset (default: 0)
}
```

**Response:**
```typescript
{
  success: boolean;
  macros?: Array<{
    uuid: string;
    name: string;
    group_uuid?: string;
    enabled: boolean;
    color?: string;
    trigger_count: number;
    action_count: number;
    modified_at: string;
  }>;
  total_count?: number;            // Total matching macros
  returned_count?: number;         // Number returned in this response
  has_more?: boolean;              // Whether more results available
  error?: string;
  error_code?: string;
}
```

### **Macro Execution Tools**

#### **km_execute_macro**

Execute a Keyboard Maestro macro with default settings.

**Parameters:**
```typescript
{
  identifier: string;              // Macro name or UUID
  trigger_value?: string;          // Optional parameter for parameterized macros
}
```

**Response:**
```typescript
{
  success: boolean;
  status?: string;                 // SUCCESS, FAILED, TIMEOUT, CANCELLED
  execution_time?: number;         // Execution time in seconds
  macro_uuid?: string;             // Executed macro UUID
  error?: string;                  // Error details if failed
  error_code?: string;             // Specific error code
}
```

**Example:**
```json
{
  "identifier": "Daily Backup Automation",
  "trigger_value": "/Users/john/Documents"
}
```

#### **km_execute_macro_with_timeout**

Execute a macro with custom timeout settings.

**Parameters:**
```typescript
{
  identifier: string;              // Macro name or UUID
  timeout: number;                 // Maximum execution time (1-300 seconds)
  trigger_value?: string;          // Optional parameter value
}
```

**Response:**
```typescript
{
  success: boolean;
  status?: string;                 // Execution status
  execution_time?: number;         // Actual execution time
  timeout_used?: number;           // Timeout setting used
  timed_out?: boolean;             // Whether execution timed out
  macro_uuid?: string;             // Executed macro UUID
  error?: string;
  error_code?: string;
}
```

#### **km_execute_macro_via_method**

Execute a macro using a specific execution method.

**Parameters:**
```typescript
{
  identifier: string;              // Macro name or UUID
  method: string;                  // applescript, url, web_api, remote
  trigger_value?: string;          // Optional parameter value
  timeout?: number;                // Timeout in seconds (default: 30)
}
```

**Response:**
```typescript
{
  success: boolean;
  status?: string;                 // Execution status
  execution_method?: string;       // Method used for execution
  execution_time?: number;         // Execution time
  macro_uuid?: string;             // Executed macro UUID
  supported_methods?: string[];    // Available methods (on error)
  error?: string;
  error_code?: string;
}
```

### **Variable Management Tools**

#### **km_get_variable**

Get Keyboard Maestro variable value with scope enforcement.

**Parameters:**
```typescript
{
  name: string;                    // Variable name
  scope?: string;                  // global, local, instance, password (default: global)
  instance_id?: string;            // Required for instance-scoped variables
}
```

**Response:**
```typescript
{
  success: boolean;
  exists?: boolean;                // Whether variable exists
  name?: string;                   // Variable name
  scope?: string;                  // Variable scope
  value?: string;                  // Variable value (masked for passwords)
  created_at?: string;             // ISO timestamp
  modified_at?: string;            // ISO timestamp
  is_password?: boolean;           // Whether this is a password variable
  instance_id?: string;            // Instance ID (for instance variables)
  error?: string;
  error_code?: string;
}
```

**Example:**
```json
{
  "name": "BackupLocation",
  "scope": "global"
}
```

#### **km_set_variable**

Set Keyboard Maestro variable value with validation and scope enforcement.

**Parameters:**
```typescript
{
  name: string;                    // Variable name
  value: string;                   // Variable value
  scope?: string;                  // global, local, instance, password (default: global)
  instance_id?: string;            // Required for instance-scoped variables
  is_password?: boolean;           // Whether this is a password variable
}
```

**Response:**
```typescript
{
  success: boolean;
  name?: string;                   // Variable name
  scope?: string;                  // Variable scope
  value?: string;                  // Set value (masked for passwords)
  is_password?: boolean;           // Password variable status
  modified_at?: string;            // ISO timestamp
  instance_id?: string;            // Instance ID (if applicable)
  error?: string;
  error_code?: string;
}
```

#### **km_list_variables**

List Keyboard Maestro variables with filtering and scope selection.

**Parameters:**
```typescript
{
  scope?: string;                  // global, local, instance, password, all (default: global)
  name_pattern?: string;           // Regex pattern for name filtering
  include_password?: boolean;      // Include password variables (default: false)
  limit?: number;                  // Maximum results (default: 100)
}
```

**Response:**
```typescript
{
  success: boolean;
  variables?: Array<{
    name: string;
    scope: string;
    value: string;                 // Masked for password variables
    value_length?: number;         // Length of value (null for passwords)
    created_at: string;
    modified_at: string;
    is_password: boolean;
    instance_id?: string;
  }>;
  total_found?: number;            // Total matching variables
  total_returned?: number;         // Number returned
  scope_filter?: string;           // Applied scope filter
  name_pattern?: string;           // Applied name pattern
  summary?: {                      // Summary statistics
    total_variables: number;
    by_scope: Record<string, number>;
    password_variables: number;
  };
  snapshot_time?: string;          // When data was collected
  error?: string;
  error_code?: string;
}
```

### **File Operations Tools**

#### **km_read_file**

Read file contents with encoding and size validation.

**Parameters:**
```typescript
{
  file_path: string;               // Absolute file path
  encoding?: string;               // utf-8, ascii, latin1 (default: utf-8)
  max_size_mb?: number;            // Maximum file size (default: 10MB)
}
```

**Response:**
```typescript
{
  success: boolean;
  content?: string;                // File contents
  file_path?: string;              // Confirmed file path
  file_size_bytes?: number;        // File size in bytes
  encoding_used?: string;          // Encoding used for reading
  modified_at?: string;            // File modification timestamp
  error?: string;
  error_code?: string;
}
```

#### **km_write_file**

Write content to file with backup and validation.

**Parameters:**
```typescript
{
  file_path: string;               // Absolute file path
  content: string;                 // Content to write
  encoding?: string;               // utf-8, ascii, latin1 (default: utf-8)
  create_backup?: boolean;         // Create backup of existing file (default: true)
  overwrite?: boolean;             // Allow overwriting existing file (default: false)
}
```

**Response:**
```typescript
{
  success: boolean;
  file_path?: string;              // Written file path
  bytes_written?: number;          // Number of bytes written
  backup_created?: boolean;        // Whether backup was created
  backup_path?: string;            // Backup file path (if created)
  encoding_used?: string;          // Encoding used for writing
  written_at?: string;             // Write operation timestamp
  error?: string;
  error_code?: string;
}
```

### **Application Control Tools**

#### **km_launch_application**

Launch an application with wait and focus options.

**Parameters:**
```typescript
{
  application: string;             // Application name or bundle ID
  wait_for_launch?: boolean;       // Wait for app to finish launching (default: true)
  bring_to_front?: boolean;        // Bring app to front (default: true)
  timeout?: number;                // Launch timeout in seconds (default: 30)
}
```

**Response:**
```typescript
{
  success: boolean;
  application?: string;            // Application identifier used
  bundle_id?: string;              // Application bundle ID
  process_id?: number;             // Application process ID
  launch_time?: number;            // Time taken to launch (seconds)
  was_already_running?: boolean;   // Whether app was already running
  brought_to_front?: boolean;      // Whether app was brought to front
  error?: string;
  error_code?: string;
}
```

### **Window Management Tools**

#### **km_set_window_position**

Set window position and size with validation.

**Parameters:**
```typescript
{
  application?: string;            // Target application (default: frontmost)
  window_title?: string;           // Target window title (default: frontmost)
  x: number;                       // X coordinate
  y: number;                       // Y coordinate
  width?: number;                  // Window width (optional)
  height?: number;                 // Window height (optional)
}
```

**Response:**
```typescript
{
  success: boolean;
  application?: string;            // Target application
  window_title?: string;           // Target window title
  previous_position?: {            // Previous window position
    x: number;
    y: number;
    width: number;
    height: number;
  };
  new_position?: {                 // New window position
    x: number;
    y: number;
    width: number;
    height: number;
  };
  error?: string;
  error_code?: string;
}
```

### **OCR Operations Tools**

#### **km_extract_text_from_screen**

Extract text from screen region using OCR.

**Parameters:**
```typescript
{
  x: number;                       // Top-left X coordinate
  y: number;                       // Top-left Y coordinate
  width: number;                   // Capture width
  height: number;                  // Capture height
  language?: string;               // OCR language (default: auto-detect)
  confidence_threshold?: number;   // Minimum confidence (0.0-1.0, default: 0.7)
}
```

**Response:**
```typescript
{
  success: boolean;
  extracted_text?: string;         // Extracted text content
  confidence_score?: number;       // Overall confidence score
  language_detected?: string;      // Detected language
  capture_region?: {               // Confirmed capture region
    x: number;
    y: number;
    width: number;
    height: number;
  };
  word_count?: number;             // Number of words extracted
  processing_time?: number;        // OCR processing time (seconds)
  error?: string;
  error_code?: string;
}
```

### **System Health Tools**

#### **km_get_system_health**

Get comprehensive system health and performance metrics.

**Parameters:**
```typescript
{
  include_detailed_metrics?: boolean;  // Include detailed performance data (default: false)
}
```

**Response:**
```typescript
{
  success: boolean;
  health_status?: string;          // HEALTHY, DEGRADED, UNHEALTHY
  overall_score?: number;          // Health score (0-100)
  km_engine_status?: string;       // Keyboard Maestro Engine status
  system_metrics?: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
    available_memory_mb: number;
  };
  performance_metrics?: {
    avg_response_time_ms: number;
    operations_per_second: number;
    success_rate_percent: number;
    error_count_last_hour: number;
  };
  recommendations?: Array<{
    priority: string;              // low, medium, high, critical
    category: string;              // performance, security, maintenance
    issue: string;                 // Issue description
    recommendation: string;        // Recommended action
    impact: string;                // Expected impact
  }>;
  last_updated?: string;           // ISO timestamp
  error?: string;
  error_code?: string;
}
```

## Request/Response Format Specifications

### **Standard Request Format**

All MCP tool requests follow this structure:

```json
{
  "jsonrpc": "2.0",
  "id": "request-id-12345",
  "method": "tools/call",
  "params": {
    "name": "km_execute_macro",
    "arguments": {
      "identifier": "Daily Backup Automation",
      "timeout": 60
    }
  }
}
```

### **Standard Response Format**

All MCP tool responses follow this structure:

```json
{
  "jsonrpc": "2.0",
  "id": "request-id-12345",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"status\": \"SUCCESS\", \"execution_time\": 2.34}"
      }
    ],
    "isError": false
  }
}
```

### **Error Response Format**

Error responses include detailed information for debugging:

```json
{
  "jsonrpc": "2.0",
  "id": "request-id-12345",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": false, \"error\": \"Macro not found\", \"error_code\": \"MACRO_NOT_FOUND\", \"suggestion\": \"Check macro name or UUID\"}"
      }
    ],
    "isError": true
  }
}
```

## Rate Limiting & Quotas

### **Default Rate Limits**

```yaml
Rate Limits (per client session):
  macro_execution: 100 requests/minute
  variable_operations: 500 requests/minute
  file_operations: 200 requests/minute
  system_queries: 1000 requests/minute
  health_checks: unlimited

Burst Allowance:
  - 2x rate limit for up to 30 seconds
  - Automatic throttling when limits exceeded
  - Priority queuing for critical operations

Resource Quotas:
  max_concurrent_operations: 25
  max_execution_time: 300 seconds
  max_file_size: 100MB
  max_response_size: 10MB
```

### **Rate Limit Headers**

HTTP clients receive rate limit information in response headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 45
```

## SDK Usage Examples

### **Python SDK Example**

```python
import asyncio
from mcp_client import MCPClient

async def automation_example():
    """Example automation workflow using the MCP client."""
    
    # Initialize MCP client
    client = MCPClient("stdio://km-mcp-server")
    await client.connect()
    
    try:
        # Create a new macro
        create_result = await client.call_tool("km_create_macro", {
            "name": "Automated Report Generation",
            "group_uuid": "E8F7A123-4567-8901-2345-6789ABCDEF01",
            "enabled": True,
            "notes": "Generate daily sales report"
        })
        
        if create_result["success"]:
            macro_uuid = create_result["macro_uuid"]
            print(f"Created macro: {macro_uuid}")
            
            # Set up variables for the macro
            await client.call_tool("km_set_variable", {
                "name": "ReportDate",
                "value": "2025-06-21",
                "scope": "global"
            })
            
            await client.call_tool("km_set_variable", {
                "name": "OutputPath",
                "value": "/Users/reports/daily/",
                "scope": "global"
            })
            
            # Execute the macro
            execution_result = await client.call_tool("km_execute_macro", {
                "identifier": macro_uuid,
                "timeout": 120
            })
            
            if execution_result["success"]:
                print(f"Macro executed successfully in {execution_result['execution_time']} seconds")
            else:
                print(f"Execution failed: {execution_result['error']}")
        
    finally:
        await client.disconnect()

# Run the example
asyncio.run(automation_example())
```

### **Node.js SDK Example**

```javascript
const { MCPClient } = require('@mcp/client');

async function windowManagementExample() {
    const client = new MCPClient({
        transport: 'stdio',
        command: 'km-mcp-server'
    });
    
    await client.connect();
    
    try {
        // Get current system health
        const health = await client.callTool('km_get_system_health', {
            include_detailed_metrics: true
        });
        
        console.log(`System health: ${health.health_status}`);
        console.log(`Performance score: ${health.overall_score}/100`);
        
        // Launch application and manage windows
        const launchResult = await client.callTool('km_launch_application', {
            application: 'TextEdit',
            bring_to_front: true,
            wait_for_launch: true
        });
        
        if (launchResult.success) {
            // Position the window
            await client.callTool('km_set_window_position', {
                application: 'TextEdit',
                x: 100,
                y: 100,
                width: 800,
                height: 600
            });
            
            // Write content to a file
            await client.callTool('km_write_file', {
                file_path: '/tmp/automation_test.txt',
                content: 'Hello from MCP automation!',
                create_backup: false,
                overwrite: true
            });
            
            console.log('Window management automation completed successfully');
        }
        
    } catch (error) {
        console.error('Automation failed:', error);
    } finally {
        await client.disconnect();
    }
}

windowManagementExample();
```

### **Claude Desktop Integration Example**

```json
{
  "mcpServers": {
    "keyboard-maestro": {
      "command": "/usr/local/bin/km-mcp-server",
      "args": ["--config", "/Users/claude/.km-mcp/config.yaml"],
      "env": {
        "KM_MCP_LOG_LEVEL": "INFO",
        "KM_MCP_PERFORMANCE_MODE": "balanced"
      }
    }
  }
}
```

## Error Codes Reference

### **Validation Errors**

| Code | Description | Recovery Action |
|------|-------------|-----------------|
| `INVALID_IDENTIFIER` | Invalid macro name or UUID format | Check identifier format and existence |
| `INVALID_TIMEOUT` | Timeout value outside valid range (1-300) | Use timeout between 1 and 300 seconds |
| `INVALID_SCOPE` | Invalid variable scope specified | Use: global, local, instance, password |
| `INVALID_PATH` | File path validation failed | Use absolute path within allowed directories |
| `INVALID_COORDINATES` | Screen coordinates out of bounds | Check screen resolution and coordinate values |

### **Permission Errors**

| Code | Description | Recovery Action |
|------|-------------|-----------------|
| `PERMISSION_DENIED` | Required macOS permission not granted | Grant permission in System Preferences |
| `ACCESSIBILITY_REQUIRED` | Accessibility permission needed | Enable Accessibility for the application |
| `AUTOMATION_REQUIRED` | Automation permission needed | Allow automation in Security & Privacy |
| `INSUFFICIENT_PRIVILEGES` | Operation requires higher privileges | Run with appropriate user permissions |

### **Execution Errors**

| Code | Description | Recovery Action |
|------|-------------|-----------------|
| `MACRO_NOT_FOUND` | Specified macro does not exist | Verify macro name/UUID and existence |
| `MACRO_DISABLED` | Macro is disabled | Enable macro in Keyboard Maestro |
| `EXECUTION_TIMEOUT` | Macro execution exceeded timeout | Increase timeout or optimize macro |
| `EXECUTION_FAILED` | Macro execution failed | Check macro logic and dependencies |
| `KM_ENGINE_UNAVAILABLE` | Keyboard Maestro Engine not running | Start Keyboard Maestro Engine |

### **System Errors**

| Code | Description | Recovery Action |
|------|-------------|-----------------|
| `SYSTEM_ERROR` | Unexpected system error occurred | Check logs and retry operation |
| `RESOURCE_EXHAUSTED` | System resources unavailable | Wait for resources or reduce load |
| `RATE_LIMIT_EXCEEDED` | Request rate limit exceeded | Wait and retry with backoff |
| `FILE_NOT_FOUND` | Specified file does not exist | Verify file path and existence |
| `NETWORK_ERROR` | Network operation failed | Check network connectivity |

## Best Practices

### **Performance Optimization**

1. **Batch Operations**: Use batch tools when available for multiple operations
2. **Appropriate Timeouts**: Set realistic timeouts based on macro complexity
3. **Resource Management**: Monitor system resources and adjust concurrent operations
4. **Caching**: Leverage variable caching for frequently accessed data
5. **Error Handling**: Implement comprehensive error handling and retry logic

### **Security Considerations**

1. **Input Validation**: Always validate inputs before API calls
2. **Permission Checks**: Verify required permissions before operations
3. **Secure Storage**: Use password variables for sensitive data
4. **Audit Logging**: Enable audit logging for compliance requirements
5. **Rate Limiting**: Respect rate limits to prevent service degradation

### **Integration Patterns**

1. **Health Checks**: Regular health monitoring for reliable automation
2. **Graceful Degradation**: Handle permission or resource limitations gracefully
3. **Retry Strategies**: Implement exponential backoff for transient failures
4. **Status Monitoring**: Track operation status and performance metrics
5. **Configuration Management**: Use environment-specific configurations

---

**API Reference Version**: 1.0.0  
**Last Updated**: June 21, 2025  
**Server Compatibility**: Keyboard Maestro MCP Server v1.0+  
**MCP Protocol Version**: 1.0
