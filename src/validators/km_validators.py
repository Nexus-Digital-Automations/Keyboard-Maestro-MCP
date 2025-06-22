# Keyboard Maestro Validation: Domain-Specific Validators
# src/validators/km_validators.py

"""
Keyboard Maestro specific validation functions and utilities.

This module implements comprehensive validation for Keyboard Maestro
domain objects, AppleScript commands, and system operations with
security-focused input sanitization and constraint checking.

Features:
- Macro identifier and name validation
- AppleScript security validation and sanitization
- Variable name and scope validation
- System operation boundary checking
- Comprehensive error reporting with recovery guidance

Size: 195 lines (target: <200)
"""

import re
import uuid
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass

from src.types.domain_types import MacroUUID, VariableName, GroupUUID
from src.types.enumerations import VariableScope, MacroState
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_string


@dataclass
class ValidationResult:
    """Result of validation operation with detailed feedback."""
    is_valid: bool
    error_message: Optional[str] = None
    suggestions: List[str] = None
    sanitized_value: Optional[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class KMValidator:
    """Keyboard Maestro validation utilities."""
    
    def __init__(self):
        """Initialize validator with default settings."""
        self._strict_mode = True
    
    def validate_macro_name(self, name: str) -> ValidationResult:
        """Validate macro name follows Keyboard Maestro conventions."""
        if not isinstance(name, str):
            return ValidationResult(
                is_valid=False,
                error_message="Macro name must be a string",
                suggestions=["Provide a string value for macro name"]
            )
        
        if len(name.strip()) == 0:
            return ValidationResult(
                is_valid=False,
                error_message="Macro name cannot be empty",
                suggestions=["Provide a non-empty macro name"]
            )
        
        if len(name) > KM_MAX_NAME_LENGTH:
            return ValidationResult(
                is_valid=False,
                error_message=f"Macro name too long (max {KM_MAX_NAME_LENGTH} characters)",
                suggestions=[f"Shorten macro name to {KM_MAX_NAME_LENGTH} characters or less"]
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_variable_name(self, name: str) -> ValidationResult:
        """Validate variable name format."""
        if not isinstance(name, str):
            return ValidationResult(
                is_valid=False,
                error_message="Variable name must be a string"
            )
        
        if not KM_VARIABLE_NAME_PATTERN.match(name):
            return ValidationResult(
                is_valid=False,
                error_message="Variable name must start with letter/underscore and contain only alphanumeric characters and underscores",
                suggestions=["Use format like 'myVariable' or 'my_variable'"]
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_script_safety(self, script: str) -> ValidationResult:
        """Validate AppleScript for security issues."""
        if not isinstance(script, str):
            return ValidationResult(
                is_valid=False,
                error_message="Script must be a string"
            )
        
        for pattern in DANGEROUS_APPLESCRIPT_PATTERNS:
            if pattern.search(script):
                return ValidationResult(
                    is_valid=False,
                    error_message="Script contains potentially dangerous commands",
                    suggestions=["Remove dangerous shell commands or system access"]
                )
        
        return ValidationResult(is_valid=True)


# Keyboard Maestro naming patterns and constraints
KM_MACRO_NAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1f]+$')
KM_VARIABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
KM_MAX_NAME_LENGTH = 255
KM_MAX_VARIABLE_LENGTH = 1000

# AppleScript security patterns (dangerous commands to block)
DANGEROUS_APPLESCRIPT_PATTERNS = [
    re.compile(r'\bdo\s+shell\s+script\b', re.IGNORECASE),
    re.compile(r'\bsudo\b', re.IGNORECASE),
    re.compile(r'\brm\s+-rf\b', re.IGNORECASE),
    re.compile(r'\beval\b', re.IGNORECASE),
    re.compile(r'\bexec\b', re.IGNORECASE),
    re.compile(r'\bsystem\s+events\b.*\bkey\s+code\b', re.IGNORECASE),
    re.compile(r'\bdelete\s+(file|folder)\b', re.IGNORECASE),
]

# Allowed AppleScript applications for security
ALLOWED_APPLESCRIPT_APPS = {
    'Keyboard Maestro Engine',
    'Keyboard Maestro',
    'System Events',
    'Finder',
    'Safari',
    'Mail',
    'TextEdit',
    'Calculator',
}


@requires(lambda name: is_valid_string(name))
@ensures(lambda result: isinstance(result, ValidationResult))
def validate_macro_name(name: str) -> ValidationResult:
    """Validate Keyboard Maestro macro name.
    
    Preconditions:
    - Name must be a valid string
    
    Postconditions:
    - Returns ValidationResult with validation details
    """
    if not name.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Macro name cannot be empty",
            suggestions=["Provide a descriptive macro name"]
        )
    
    if len(name) > KM_MAX_NAME_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=f"Macro name too long (max {KM_MAX_NAME_LENGTH} characters)",
            suggestions=[f"Shorten name to {KM_MAX_NAME_LENGTH} characters or less"]
        )
    
    if not KM_MACRO_NAME_PATTERN.match(name):
        return ValidationResult(
            is_valid=False,
            error_message="Macro name contains invalid characters",
            suggestions=[
                "Remove special characters: < > : \" / \\ | ? *",
                "Avoid control characters and unprintable characters"
            ]
        )
    
    return ValidationResult(
        is_valid=True,
        sanitized_value=name.strip()
    )


@requires(lambda identifier: identifier is not None)
@ensures(lambda result: isinstance(result, ValidationResult))
def validate_macro_identifier(identifier: str) -> ValidationResult:
    """Validate macro identifier (name or UUID).
    
    Preconditions:
    - Identifier must not be None
    
    Postconditions:
    - Returns ValidationResult with validation details
    """
    if not identifier or not identifier.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Macro identifier cannot be empty",
            suggestions=["Provide macro name or UUID"]
        )
    
    identifier = identifier.strip()
    
    # Check if it's a UUID
    try:
        uuid.UUID(identifier)
        return ValidationResult(
            is_valid=True,
            sanitized_value=identifier
        )
    except ValueError:
        pass
    
    # Validate as macro name
    return validate_macro_name(identifier)


@requires(lambda name: is_valid_string(name))
@ensures(lambda result: isinstance(result, ValidationResult))
def validate_variable_name(name: str, scope: VariableScope = VariableScope.GLOBAL) -> ValidationResult:
    """Validate Keyboard Maestro variable name.
    
    Preconditions:
    - Name must be a valid string
    
    Postconditions:
    - Returns ValidationResult with validation details
    """
    if not name.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Variable name cannot be empty",
            suggestions=["Provide a valid variable name"]
        )
    
    clean_name = name.strip()
    
    if len(clean_name) > KM_MAX_VARIABLE_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=f"Variable name too long (max {KM_MAX_VARIABLE_LENGTH} characters)",
            suggestions=[f"Shorten name to {KM_MAX_VARIABLE_LENGTH} characters or less"]
        )
    
    # Handle local variable prefix
    if clean_name.startswith('Local__'):
        if scope != VariableScope.LOCAL:
            return ValidationResult(
                is_valid=False,
                error_message="Local__ prefix requires LOCAL scope",
                suggestions=["Use LOCAL scope for Local__ prefixed variables"]
            )
        actual_name = clean_name[7:]  # Remove Local__ prefix
    else:
        actual_name = clean_name
    
    # Validate variable name pattern
    if not KM_VARIABLE_NAME_PATTERN.match(actual_name):
        return ValidationResult(
            is_valid=False,
            error_message="Invalid variable name format",
            suggestions=[
                "Use only letters, numbers, and underscores",
                "Start with letter or underscore",
                "Follow Keyboard Maestro naming conventions"
            ]
        )
    
    # Check password variable requirements
    if scope == VariableScope.PASSWORD:
        if not any(keyword in clean_name.lower() for keyword in ['password', 'pw', 'secret', 'key']):
            return ValidationResult(
                is_valid=False,
                error_message="Password variables should contain 'password', 'pw', 'secret', or 'key'",
                suggestions=["Include password-related keyword in variable name"]
            )
    
    return ValidationResult(
        is_valid=True,
        sanitized_value=clean_name
    )


@requires(lambda script: is_valid_string(script))
@ensures(lambda result: isinstance(result, ValidationResult))
def validate_applescript_security(script: str) -> ValidationResult:
    """Validate AppleScript for security risks.
    
    Preconditions:
    - Script must be a valid string
    
    Postconditions:
    - Returns ValidationResult with security analysis
    """
    if not script.strip():
        return ValidationResult(
            is_valid=False,
            error_message="AppleScript cannot be empty",
            suggestions=["Provide valid AppleScript code"]
        )
    
    script_clean = script.strip()
    security_issues = []
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_APPLESCRIPT_PATTERNS:
        if pattern.search(script_clean):
            security_issues.append(f"Potentially dangerous command detected: {pattern.pattern}")
    
    # Check for unauthorized applications
    app_references = re.findall(r'tell\s+application\s+"([^"]+)"', script_clean, re.IGNORECASE)
    unauthorized_apps = [app for app in app_references if app not in ALLOWED_APPLESCRIPT_APPS]
    
    if unauthorized_apps:
        security_issues.append(f"Unauthorized applications: {', '.join(unauthorized_apps)}")
    
    # Check script length (prevent resource exhaustion)
    if len(script_clean) > 10000:
        security_issues.append("Script too long (max 10,000 characters)")
    
    if security_issues:
        return ValidationResult(
            is_valid=False,
            error_message="Security validation failed",
            suggestions=[
                "Remove dangerous commands and unauthorized application references",
                "Use only approved AppleScript operations",
                "Keep scripts concise and focused"
            ] + security_issues
        )
    
    return ValidationResult(
        is_valid=True,
        sanitized_value=script_clean
    )


def sanitize_applescript_string(value: str) -> str:
    """Sanitize string for safe use in AppleScript.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string safe for AppleScript
    """
    if not value:
        return ""
    
    # Escape quotes and backslashes
    sanitized = value.replace('\\', '\\\\').replace('"', '\\"')
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized


@requires(lambda file_path: is_valid_string(file_path))
@ensures(lambda result: isinstance(result, ValidationResult))
def validate_file_path(file_path: str) -> ValidationResult:
    """Validate file path for Keyboard Maestro operations.
    
    Preconditions:
    - File path must be a valid string
    
    Postconditions:
    - Returns ValidationResult with path validation
    """
    if not file_path.strip():
        return ValidationResult(
            is_valid=False,
            error_message="File path cannot be empty",
            suggestions=["Provide valid file path"]
        )
    
    clean_path = file_path.strip()
    
    # Check for dangerous paths
    dangerous_patterns = [
        r'\.\./',  # Directory traversal
        r'/etc/',  # System configuration
        r'/usr/bin/',  # System binaries
        r'/System/',  # System files
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, clean_path):
            return ValidationResult(
                is_valid=False,
                error_message=f"Dangerous path pattern detected: {pattern}",
                suggestions=["Use safe file paths in user directories"]
            )
    
    # Check path length
    if len(clean_path) > 1000:
        return ValidationResult(
            is_valid=False,
            error_message="File path too long (max 1000 characters)",
            suggestions=["Use shorter file path"]
        )
    
    return ValidationResult(
        is_valid=True,
        sanitized_value=clean_path
    )


def validate_macro_execution_context(context: Dict[str, Any]) -> ValidationResult:
    """Validate macro execution context and parameters.
    
    Args:
        context: Execution context dictionary
        
    Returns:
        Validation result with context analysis
    """
    required_fields = ['macro_identifier', 'execution_method']
    missing_fields = [field for field in required_fields if field not in context]
    
    if missing_fields:
        return ValidationResult(
            is_valid=False,
            error_message=f"Missing required fields: {', '.join(missing_fields)}",
            suggestions=[f"Provide {field}" for field in missing_fields]
        )
    
    # Validate macro identifier
    identifier_result = validate_macro_identifier(context['macro_identifier'])
    if not identifier_result.is_valid:
        return identifier_result
    
    # Validate execution method
    valid_methods = ['applescript', 'url', 'web', 'remote']
    if context['execution_method'] not in valid_methods:
        return ValidationResult(
            is_valid=False,
            error_message=f"Invalid execution method: {context['execution_method']}",
            suggestions=[f"Use one of: {', '.join(valid_methods)}"]
        )
    
    # Validate timeout if provided
    if 'timeout' in context:
        timeout = context['timeout']
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return ValidationResult(
                is_valid=False,
                error_message="Timeout must be positive number",
                suggestions=["Use positive timeout value in seconds"]
            )
    
    return ValidationResult(is_valid=True)
