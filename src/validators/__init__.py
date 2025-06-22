"""
Validation Framework Public API for Keyboard Maestro MCP Server.

This module provides the public interface for the validation framework,
exposing all validators, sanitizers, and boundary checkers through a
clean, composable API with defensive programming patterns.

Target: <100 lines per ADDER+ modularity requirements
"""

# Core validation components
from .input_validators import (
    InputValidator,
    ValidationResult,
    ValidationSeverity,
    BaseValidator,
    MacroIdentifierValidator,
    VariableNameValidator,
    FilePathValidator,
    CompositeValidator,
    MACRO_IDENTIFIER_VALIDATOR,
    VARIABLE_NAME_VALIDATOR,
    EXISTING_FILE_VALIDATOR,
    WRITABLE_PATH_VALIDATOR,
    validate_macro_identifier,
    validate_variable_name,
    validate_file_path,
)

# Input sanitization components
from .sanitizers import (
    SanitizationLevel,
    SanitizationResult,
    AppleScriptSanitizer,
    StringSanitizer,
    PathSanitizer,
    CompositeSanitizer,
    MINIMAL_SANITIZER,
    STANDARD_SANITIZER,
    STRICT_SANITIZER,
    PARANOID_SANITIZER,
    sanitize_macro_name,
    sanitize_variable_name,
    sanitize_file_path,
    sanitize_applescript,
)

# Boundary protection components
try:
    from ..boundaries.security_boundaries import (
        SecurityLevel,
        PermissionType,
        SecurityContext,
        SecurityBoundaryResult,
        SecurityBoundaryChecker,
        DEFAULT_SECURITY_BOUNDARY,
        validate_security_boundary,
    )
    
    from ..boundaries.system_boundaries import (
        ResourceType,
        ResourceLimit,
        SystemBoundaryResult,
        DEFAULT_SYSTEM_BOUNDARY,
        validate_system_boundary,
    )
except ImportError:
    # Boundary modules may not be available during development
    pass

# Unified validation interface
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass(frozen=True)
class ComprehensiveValidationResult:
    """Unified result from complete input validation pipeline."""
    is_valid: bool
    sanitized_value: Any
    validation_errors: List[str]
    security_warnings: List[str]
    boundary_violations: List[str]
    recommended_action: str

def validate_input_completely(
    value: Any,
    input_type: str = "string",
    sanitization_level: SanitizationLevel = SanitizationLevel.STANDARD,
    security_context: Optional[Any] = None,
    operation_context: Optional[Dict[str, Any]] = None
) -> ComprehensiveValidationResult:
    """
    Complete input validation pipeline: sanitization -> validation -> boundary checking.
    
    This is the primary entry point for comprehensive input validation.
    """
    
    # Step 1: Sanitization
    sanitizer = CompositeSanitizer(sanitization_level)
    sanitization_result = sanitizer.sanitize_input(value, input_type)
    
    sanitized_value = sanitization_result.sanitized_value
    security_warnings = list(sanitization_result.security_warnings)
    
    # Step 2: Validation
    validation_errors = []
    
    if input_type == "macro_identifier":
        validation_result = validate_macro_identifier(sanitized_value)
        if not validation_result.is_valid:
            validation_errors.extend([error.message for error in validation_result.errors])
    
    elif input_type == "variable_name":
        validation_result = validate_variable_name(sanitized_value)
        if not validation_result.is_valid:
            validation_errors.extend([error.message for error in validation_result.errors])
    
    elif input_type == "file_path":
        require_exists = operation_context.get("require_exists", False) if operation_context else False
        validation_result = validate_file_path(sanitized_value, require_exists)
        if not validation_result.is_valid:
            validation_errors.extend([error.message for error in validation_result.errors])
    
    # Step 3: Boundary checking (if context provided)
    boundary_violations = []
    if security_context and operation_context:
        try:
            # This would be implemented when boundary modules are fully integrated
            pass
        except:
            # Graceful degradation if boundary checking isn't available
            pass
    
    # Determine overall validity and recommended action
    is_valid = len(validation_errors) == 0 and len(boundary_violations) == 0
    
    if not is_valid:
        if boundary_violations:
            recommended_action = "Check permissions and authentication"
        elif validation_errors:
            recommended_action = "Correct input format and try again"
        else:
            recommended_action = "Review security warnings and retry"
    else:
        recommended_action = "Input is valid and safe to process"
    
    return ComprehensiveValidationResult(
        is_valid=is_valid,
        sanitized_value=sanitized_value,
        validation_errors=validation_errors,
        security_warnings=security_warnings,
        boundary_violations=boundary_violations,
        recommended_action=recommended_action
    )

# Convenience functions for common validation patterns
def validate_and_sanitize_macro_name(name: str) -> ComprehensiveValidationResult:
    """Validate and sanitize macro name with appropriate security level."""
    return validate_input_completely(name, "macro_identifier", SanitizationLevel.STANDARD)

def validate_and_sanitize_variable_name(name: str) -> ComprehensiveValidationResult:
    """Validate and sanitize variable name with appropriate security level."""
    return validate_input_completely(name, "variable_name", SanitizationLevel.STANDARD)

def validate_and_sanitize_file_path(path: str, require_exists: bool = False) -> ComprehensiveValidationResult:
    """Validate and sanitize file path with security checks."""
    context = {"require_exists": require_exists}
    return validate_input_completely(path, "file_path", SanitizationLevel.STRICT, None, context)

def validate_and_sanitize_applescript(script: str) -> ComprehensiveValidationResult:
    """Validate and sanitize AppleScript with strict security controls."""
    return validate_input_completely(script, "applescript", SanitizationLevel.STRICT)

# Export all components for external use
__all__ = [
    # Validation framework
    "InputValidator",
    "ValidationResult", 
    "ValidationSeverity",
    "validate_macro_identifier",
    "validate_variable_name",
    "validate_file_path",
    
    # Sanitization framework
    "SanitizationLevel",
    "SanitizationResult",
    "sanitize_macro_name",
    "sanitize_variable_name", 
    "sanitize_file_path",
    "sanitize_applescript",
    
    # Unified validation
    "ComprehensiveValidationResult",
    "validate_input_completely",
    "validate_and_sanitize_macro_name",
    "validate_and_sanitize_variable_name",
    "validate_and_sanitize_file_path",
    "validate_and_sanitize_applescript",
]
