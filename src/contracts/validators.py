# Contract Validation Functions Framework
# Target: <250 lines - Core validation functions for contract enforcement

"""
Contract validation functions for comprehensive input and state validation.

This module provides reusable validation functions for contract enforcement
including macro identifiers, variables, coordinates, system operations, and
business logic validation. All validators return structured results with
detailed error information for contract violation reporting.

Key Features:
- Comprehensive domain-specific validators for Keyboard Maestro operations  
- Type-safe validation with branded type integration
- Detailed error reporting with recovery suggestions
- Composable validation patterns for complex business rules
- Integration with contract decorators and exception framework
"""

import re
import os
import uuid
from typing import Any, List, Dict, Optional, Set, Union
from uuid import UUID
from pathlib import Path

# Import domain types and exceptions
from src.types.identifiers import (
    MacroUUID, MacroName, VariableName, GroupUUID, TriggerID, ActionID
)
from src.types.values import (
    ScreenCoordinates, ScreenArea, ConfidenceScore
)
from src.types.enumerations import (
    VariableScope, ExecutionMethod, TriggerType, ActionType, 
    ApplicationOperation, FileOperation, ClickType
)
from src.contracts.exceptions import (
    ViolationContext, ViolationType, create_precondition_violation
)


# Keyboard Maestro Domain Validators

def is_valid_string(value: Any, min_length: int = 1, max_length: int = 1000) -> bool:
    """Validate string meets basic requirements."""
    if not isinstance(value, str):
        return False
    return min_length <= len(value) <= max_length


def is_valid_macro_identifier(identifier: Any) -> bool:
    """Validate macro identifier format (UUID or name string)."""
    if isinstance(identifier, UUID):
        return True
    if isinstance(identifier, str):
        # Valid name: 1-255 characters, alphanumeric plus common symbols
        return (len(identifier) > 0 and 
                len(identifier) <= 255 and
                re.match(r'^[a-zA-Z0-9_\s\-\.]+$', identifier) is not None)
    return False


def is_valid_macro_name(name: Any) -> bool:
    """Validate macro name follows Keyboard Maestro conventions."""
    if not isinstance(name, str):
        return False
    
    # Keyboard Maestro macro name rules
    return (1 <= len(name) <= 255 and
            re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name) is not None and
            not name.isspace())  # Not just whitespace


def is_valid_variable_name(name: Any) -> bool:
    """Validate variable name follows Keyboard Maestro naming conventions."""
    if not isinstance(name, str):
        return False
    
    # Keyboard Maestro variable naming rules: identifier-like format
    return (1 <= len(name) <= 255 and
            re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) is not None)


def is_valid_group_name(name: Any) -> bool:
    """Validate macro group name format."""
    if not isinstance(name, str):
        return False
    
    # Similar to macro names but slightly more restrictive
    return (1 <= len(name) <= 255 and
            re.match(r'^[a-zA-Z0-9_\s\-]+$', name) is not None and
            not name.isspace())


def is_positive_number(value: Any) -> bool:
    """Validate that value is a positive number."""
    if not isinstance(value, (int, float)):
        return False
    return value > 0


def is_valid_timeout(timeout: Any) -> bool:
    """Validate timeout value for operations."""
    if not isinstance(timeout, (int, float)):
        return False
    # Timeout should be positive and reasonable (up to 10 minutes)
    return 0 < timeout <= 600


def is_valid_execution_timeout(timeout: Any) -> bool:
    """Validate macro execution timeout value."""
    if not isinstance(timeout, (int, float)):
        return False
    
    # Reasonable timeout range: 1 second to 5 minutes
    return 1 <= timeout <= 300


def is_valid_threshold_config(config: Any) -> bool:
    """Validate performance threshold configuration."""
    if not isinstance(config, dict):
        return False
    
    required_fields = {'cpu_threshold', 'memory_threshold', 'disk_threshold'}
    if not all(field in config for field in required_fields):
        return False
    
    # Validate threshold values (percentages 0-100)
    for field in required_fields:
        value = config[field]
        if not isinstance(value, (int, float)):
            return False
        if not 0 <= value <= 100:
            return False
    
    return True


def is_valid_execution_method(method: Any) -> bool:
    """Validate macro execution method."""
    if not isinstance(method, ExecutionMethod):
        return False
    return method in ExecutionMethod


def validate_variable_scope(scope: Any, instance_id: Optional[str] = None) -> bool:
    """Validate variable scope with context requirements."""
    if not isinstance(scope, VariableScope):
        return False
    
    # Instance scope requires instance ID
    if scope == VariableScope.INSTANCE:
        return instance_id is not None and len(instance_id) > 0
    
    return True


# Screen and Coordinate Validators

def is_valid_screen_coordinates(coordinates: Any) -> bool:
    """Validate screen coordinates within bounds."""
    if not hasattr(coordinates, 'x') or not hasattr(coordinates, 'y'):
        return False
    
    try:
        x, y = coordinates.x, coordinates.y
        if not isinstance(x, int) or not isinstance(y, int):
            return False
        
        # Get screen bounds (simplified - would integrate with actual screen detection)
        screen_bounds = get_screen_bounds()
        return (0 <= x <= screen_bounds.width and 
                0 <= y <= screen_bounds.height)
    except Exception:
        return False


def is_valid_screen_area(area: Any) -> bool:
    """Validate screen area definition."""
    if not hasattr(area, 'top_left') or not hasattr(area, 'bottom_right'):
        return False
    
    try:
        # Validate individual coordinates
        if not is_valid_screen_coordinates(area.top_left):
            return False
        if not is_valid_screen_coordinates(area.bottom_right):
            return False
        
        # Validate area is well-formed
        return (area.bottom_right.x > area.top_left.x and
                area.bottom_right.y > area.top_left.y)
    except Exception:
        return False


def is_valid_confidence_score(score: Any) -> bool:
    """Validate confidence score range."""
    if not isinstance(score, (int, float)):
        return False
    
    return 0.0 <= score <= 1.0


# File System and Application Validators

def is_valid_file_path(path: Any) -> bool:
    """Validate file path format and accessibility."""
    if not isinstance(path, str):
        return False
    
    try:
        path_obj = Path(path)
        # Check if path is well-formed and within reasonable length
        return (len(path) <= 4096 and  # Reasonable path length limit
                path_obj.is_absolute() and  # Require absolute paths for security
                not any(part.startswith('.') for part in path_obj.parts[1:]))  # No hidden dirs
    except Exception:
        return False


def file_exists_and_readable(path: str) -> bool:
    """Validate file exists and is readable."""
    try:
        return os.path.exists(path) and os.access(path, os.R_OK)
    except Exception:
        return False


def directory_exists_and_writable(path: str) -> bool:
    """Validate directory exists and is writable."""
    try:
        return (os.path.exists(path) and 
                os.path.isdir(path) and 
                os.access(path, os.W_OK))
    except Exception:
        return False


def is_valid_application_identifier(identifier: Any) -> bool:
    """Validate application identifier (bundle ID or name)."""
    if not isinstance(identifier, str):
        return False
    
    if len(identifier) == 0 or len(identifier) > 255:
        return False
    
    # Bundle ID format: com.company.appname
    bundle_id_pattern = r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+){2,}$'
    if re.match(bundle_id_pattern, identifier):
        return True
    
    # Application name: alphanumeric with common symbols
    app_name_pattern = r'^[a-zA-Z0-9_\s\-\.]+$'
    return re.match(app_name_pattern, identifier) is not None


# Security and Safety Validators

def is_safe_script_content(script: str) -> bool:
    """Validate script content for security (AppleScript, shell, etc.)."""
    if not isinstance(script, str):
        return False
    
    if len(script.strip()) == 0:
        return False
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'rm\s+-rf',           # Dangerous file deletion
        r'sudo\s+',            # Privilege escalation
        r'eval\s*\(',          # Code injection
        r'exec\s*\(',          # Code execution
        r'system\s*\(',        # System command execution
        r'os\.system',         # Python system calls
        r'subprocess\.',       # Python subprocess
        r'shell_exec',         # PHP shell execution
        r'passthru',           # PHP command execution
        r'curl.*\|.*sh',       # Download and execute
        r'wget.*\|.*sh',       # Download and execute
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, script, re.IGNORECASE):
            return False
    
    return True


def is_valid_email_address(email: Any) -> bool:
    """Validate email address format."""
    if not isinstance(email, str):
        return False
    
    # Basic email validation pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return (len(email) <= 320 and  # RFC 5321 limit
            re.match(email_pattern, email) is not None)


def is_valid_phone_number(phone: Any) -> bool:
    """Validate phone number format."""
    if not isinstance(phone, str):
        return False
    
    # Remove common formatting characters
    clean_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    
    # Check for valid phone number patterns
    return (len(clean_phone) >= 10 and 
            len(clean_phone) <= 15 and
            clean_phone.isdigit())


# Numeric and Performance Validators

def is_positive_number(value: Any) -> bool:
    """Validate that value is a positive number."""
    if not isinstance(value, (int, float)):
        return False
    return value > 0


def is_valid_timeout(timeout: Any) -> bool:
    """Validate timeout value for operations."""
    if not isinstance(timeout, (int, float)):
        return False
    # Timeout should be positive and reasonable (max 5 minutes)
    return 0.1 <= timeout <= 300


def is_valid_threshold_config(config: Any) -> bool:
    """Validate performance threshold configuration."""
    if not isinstance(config, dict):
        return False
    
    required_fields = {'cpu_threshold', 'memory_threshold', 'response_time_threshold'}
    if not all(field in config for field in required_fields):
        return False
    
    # Validate threshold values
    cpu_threshold = config.get('cpu_threshold')
    memory_threshold = config.get('memory_threshold')
    response_time_threshold = config.get('response_time_threshold')
    
    # CPU threshold: 0-100%
    if not isinstance(cpu_threshold, (int, float)) or not (0 <= cpu_threshold <= 100):
        return False
    
    # Memory threshold: 0-100%
    if not isinstance(memory_threshold, (int, float)) or not (0 <= memory_threshold <= 100):
        return False
    
    # Response time threshold: positive number in seconds
    if not is_positive_number(response_time_threshold):
        return False
    
    return True


def is_valid_execution_method(method: Any) -> bool:
    """Validate execution method enum value."""
    from src.types.enumerations import ExecutionMethod
    
    if not isinstance(method, ExecutionMethod):
        return False
    
    # All enum values are valid
    return True


# Business Logic Validators

def is_valid_macro_structure(macro_data: Dict[str, Any]) -> bool:
    """Validate macro data structure completeness."""
    required_fields = {'name', 'triggers', 'actions'}
    
    # Check required fields present
    if not all(field in macro_data for field in required_fields):
        return False
    
    # Validate field types and constraints
    if not is_valid_macro_name(macro_data['name']):
        return False
    
    # Must have at least one trigger or action
    triggers = macro_data.get('triggers', [])
    actions = macro_data.get('actions', [])
    
    if not isinstance(triggers, list) or not isinstance(actions, list):
        return False
    
    return len(triggers) > 0 or len(actions) > 0


def name_is_unique_in_group(name: str, group_id: Optional[str]) -> bool:
    """Validate macro name uniqueness within group (simplified check)."""
    # In real implementation, would query Keyboard Maestro for existing names
    # For now, return True as placeholder
    return True


def group_exists(group_id: str) -> bool:
    """Validate that macro group exists (simplified check)."""
    # In real implementation, would query Keyboard Maestro for group existence
    # For now, return True as placeholder
    return True


def macro_exists(macro_id: str) -> bool:
    """Validate that macro exists (simplified check)."""
    # In real implementation, would query Keyboard Maestro for macro existence
    # For now, return True as placeholder
    return True


# Composite Validators

def validate_macro_creation_data(macro_data: Dict[str, Any]) -> List[str]:
    """Comprehensive validation for macro creation data."""
    violations = []
    
    if not is_valid_macro_structure(macro_data):
        violations.append("Invalid macro structure")
    
    if 'group_id' in macro_data and macro_data['group_id'] is not None:
        if not group_exists(macro_data['group_id']):
            violations.append("Target group does not exist")
    
    if not name_is_unique_in_group(macro_data['name'], 
                                   macro_data.get('group_id')):
        violations.append("Macro name not unique in target group")
    
    return violations


def validate_file_operation_data(operation: str, source: str, 
                                destination: Optional[str] = None) -> List[str]:
    """Comprehensive validation for file operations."""
    violations = []
    
    if not is_valid_file_path(source):
        violations.append("Invalid source path format")
    elif not file_exists_and_readable(source):
        violations.append("Source file does not exist or is not readable")
    
    if destination is not None:
        if not is_valid_file_path(destination):
            violations.append("Invalid destination path format")
        
        dest_dir = os.path.dirname(destination)
        if not directory_exists_and_writable(dest_dir):
            violations.append("Destination directory does not exist or is not writable")
    
    return violations


# Server Configuration Validators

def is_valid_server_configuration(config: Any) -> bool:
    """Validate server configuration object completeness and correctness."""
    if not hasattr(config, 'transport') or not hasattr(config, 'host'):
        return False
    if not hasattr(config, 'port') or not hasattr(config, 'max_concurrent_operations'):
        return False
    if not hasattr(config, 'operation_timeout') or not hasattr(config, 'auth_required'):
        return False
    if not hasattr(config, 'log_level') or not hasattr(config, 'development_mode'):
        return False
    
    # Validate transport type
    if config.transport not in ["stdio", "streamable-http", "websocket"]:
        return False
    
    # Validate port range for network transports
    if config.transport != "stdio" and not (1024 <= config.port <= 65535):
        return False
    
    # Validate operational parameters
    if config.max_concurrent_operations <= 0 or config.operation_timeout <= 0:
        return False
    
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.log_level.upper() not in valid_levels:
        return False
    
    return True


# Utility functions

def get_screen_bounds():
    """Get current screen bounds (simplified implementation)."""
    # In real implementation, would use AppKit/Cocoa to get actual screen bounds
    # For now, return common screen size as placeholder
    class ScreenBounds:
        width = 1920
        height = 1080
    
    return ScreenBounds()


def get_required_parameters(trigger_type: TriggerType) -> Set[str]:
    """Get required parameters for trigger type."""
    parameter_map = {
        TriggerType.HOTKEY: {'key', 'modifiers'},
        TriggerType.APPLICATION: {'application_identifier'},
        TriggerType.TIME: {'schedule'},
        TriggerType.SYSTEM: {'system_event'},
        TriggerType.FILE_FOLDER: {'path', 'file_event'},
    }
    
    return parameter_map.get(trigger_type, set())
