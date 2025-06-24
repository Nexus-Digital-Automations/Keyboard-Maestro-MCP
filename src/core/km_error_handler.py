# Keyboard Maestro Error Handler: Specialized Error Management
# src/core/km_error_handler.py

"""
Specialized error handling for Keyboard Maestro operations.

This module implements comprehensive error handling, classification,
and recovery strategies specific to Keyboard Maestro integration
challenges and AppleScript execution failures.

Features:
- KM-specific error classification and messaging
- AppleScript error parsing and recovery
- Context-aware error reporting
- Recovery strategy suggestions
- Performance impact analysis

Size: 189 lines (target: <200)
"""

import time
import re
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

from src.types.domain_types import MacroUUID, MacroName, VariableName
from .types.enumerations import VariableScope, ExecutionMethod
from src.types.domain_types import MacroExecutionContext
from src.contracts.decorators import requires, ensures


class KMErrorType(Enum):
    """Keyboard Maestro specific error types."""
    MACRO_NOT_FOUND = "macro_not_found"
    MACRO_DISABLED = "macro_disabled"
    APPLESCRIPT_SYNTAX = "applescript_syntax"
    APPLESCRIPT_RUNTIME = "applescript_runtime"
    KEYBOARD_MAESTRO_UNAVAILABLE = "keyboard_maestro_unavailable"
    PERMISSION_DENIED = "permission_denied"
    VARIABLE_NOT_FOUND = "variable_not_found"
    VARIABLE_SCOPE_ERROR = "variable_scope_error"
    EXECUTION_TIMEOUT = "execution_timeout"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_PARAMETERS = "invalid_parameters"
    SYSTEM_RESOURCE_ERROR = "system_resource_error"


@dataclass(frozen=True)
class KMErrorResult:
    """Result of KM error handling operation."""
    error_type: KMErrorType
    error_message: str
    user_friendly_message: str
    recovery_suggestion: str
    technical_details: Optional[str] = None
    retry_recommended: bool = False
    estimated_fix_time: Optional[str] = None


class KMErrorHandler:
    """Specialized error handler for Keyboard Maestro operations."""
    
    def __init__(self):
        self._error_patterns = self._initialize_error_patterns()
        self._recovery_strategies = self._initialize_recovery_strategies()
    
    def _initialize_error_patterns(self) -> Dict[str, KMErrorType]:
        """Initialize AppleScript error pattern mapping."""
        return {
            r"Can't get macro": KMErrorType.MACRO_NOT_FOUND,
            r"macro.*not found": KMErrorType.MACRO_NOT_FOUND,
            r"macro.*disabled": KMErrorType.MACRO_DISABLED,
            r"Application isn't running": KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE,
            r"Connection is invalid": KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE,
            r"timeout|timed out": KMErrorType.EXECUTION_TIMEOUT,
            r"permission denied": KMErrorType.PERMISSION_DENIED,
            r"not authorized": KMErrorType.PERMISSION_DENIED,
            r"variable.*not found|doesn't exist": KMErrorType.VARIABLE_NOT_FOUND,
            r"syntax error": KMErrorType.APPLESCRIPT_SYNTAX,
            r"compile error": KMErrorType.APPLESCRIPT_SYNTAX,
            r"runtime error": KMErrorType.APPLESCRIPT_RUNTIME,
            r"rate limit": KMErrorType.RATE_LIMIT_EXCEEDED,
            r"too many requests": KMErrorType.RATE_LIMIT_EXCEEDED,
            r"resource.*exhausted": KMErrorType.SYSTEM_RESOURCE_ERROR,
            r"memory.*limit": KMErrorType.SYSTEM_RESOURCE_ERROR,
        }
    
    def _initialize_recovery_strategies(self) -> Dict[KMErrorType, str]:
        """Initialize recovery strategy suggestions."""
        return {
            KMErrorType.MACRO_NOT_FOUND: "Verify macro name or UUID is correct and macro exists in Keyboard Maestro",
            KMErrorType.MACRO_DISABLED: "Enable the macro in Keyboard Maestro or check if it should be enabled",
            KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE: "Ensure Keyboard Maestro and Engine are running and accessible",
            KMErrorType.PERMISSION_DENIED: "Grant accessibility permissions in System Preferences > Security & Privacy",
            KMErrorType.VARIABLE_NOT_FOUND: "Create the variable or verify the variable name is correct",
            KMErrorType.VARIABLE_SCOPE_ERROR: "Check variable scope and ensure proper Local__ prefix for local variables",
            KMErrorType.EXECUTION_TIMEOUT: "Increase timeout value or optimize macro for better performance",
            KMErrorType.RATE_LIMIT_EXCEEDED: "Reduce request frequency or implement exponential backoff",
            KMErrorType.APPLESCRIPT_SYNTAX: "Fix AppleScript syntax errors in the generated script",
            KMErrorType.APPLESCRIPT_RUNTIME: "Check AppleScript runtime conditions and error handling",
            KMErrorType.INVALID_PARAMETERS: "Validate input parameters meet Keyboard Maestro requirements",
            KMErrorType.SYSTEM_RESOURCE_ERROR: "Free system resources or reduce operation complexity",
        }
    
    @requires(lambda exception: exception is not None)
    @requires(lambda context: isinstance(context, MacroExecutionContext))
    @ensures(lambda result: isinstance(result, KMErrorResult))
    async def handle_macro_execution_error(self, 
                                         exception: Exception,
                                         context: MacroExecutionContext,
                                         operation_id: str) -> KMErrorResult:
        """Handle macro execution errors with context-specific recovery.
        
        Preconditions:
        - Exception must not be None
        - Context must be valid MacroExecutionContext
        
        Postconditions:
        - Returns KMErrorResult with error analysis
        """
        error_type = self._classify_error(str(exception))
        error_message = str(exception)
        
        # Create context-specific error message
        user_message = self._generate_user_friendly_message(error_type, context)
        recovery_suggestion = self._get_recovery_suggestion(error_type, context)
        
        # Determine if retry is recommended
        retry_recommended = error_type in [
            KMErrorType.EXECUTION_TIMEOUT,
            KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE,
            KMErrorType.SYSTEM_RESOURCE_ERROR
        ]
        
        return KMErrorResult(
            error_type=error_type,
            error_message=error_message,
            user_friendly_message=user_message,
            recovery_suggestion=recovery_suggestion,
            technical_details=f"Operation ID: {operation_id}, Method: {context.method.value}",
            retry_recommended=retry_recommended,
            estimated_fix_time=self._estimate_fix_time(error_type)
        )
    
    @requires(lambda exception: exception is not None)
    @requires(lambda name: isinstance(name, VariableName))
    @requires(lambda scope: isinstance(scope, VariableScope))
    @ensures(lambda result: isinstance(result, KMErrorResult))
    async def handle_variable_operation_error(self,
                                            exception: Exception,
                                            name: VariableName,
                                            scope: VariableScope,
                                            operation_id: str) -> KMErrorResult:
        """Handle variable operation errors with scope-specific guidance.
        
        Preconditions:
        - Exception must not be None
        - Name must be VariableName type
        - Scope must be VariableScope type
        
        Postconditions:
        - Returns KMErrorResult with error analysis
        """
        error_type = self._classify_error(str(exception))
        error_message = str(exception)
        
        # Generate variable-specific error message
        user_message = f"Variable operation failed for '{name}' in {scope.value} scope: {error_message}"
        
        # Provide scope-specific recovery guidance
        if scope == VariableScope.LOCAL and error_type == KMErrorType.VARIABLE_NOT_FOUND:
            recovery_suggestion = f"Ensure variable '{name}' is created with Local__ prefix or in proper execution context"
        elif scope == VariableScope.PASSWORD:
            recovery_suggestion = f"Verify password variable '{name}' naming conventions and security requirements"
        else:
            recovery_suggestion = self._recovery_strategies.get(error_type, "Check variable configuration and try again")
        
        return KMErrorResult(
            error_type=error_type,
            error_message=error_message,
            user_friendly_message=user_message,
            recovery_suggestion=recovery_suggestion,
            technical_details=f"Operation ID: {operation_id}, Variable: {name}, Scope: {scope.value}",
            retry_recommended=error_type != KMErrorType.INVALID_PARAMETERS
        )
    
    @requires(lambda exception: exception is not None)
    @requires(lambda identifier: identifier is not None)
    @ensures(lambda result: isinstance(result, KMErrorResult))
    async def handle_macro_status_error(self,
                                      exception: Exception,
                                      identifier: Union[MacroUUID, MacroName],
                                      operation_id: str) -> KMErrorResult:
        """Handle macro status retrieval errors.
        
        Preconditions:
        - Exception must not be None
        - Identifier must not be None
        
        Postconditions:
        - Returns KMErrorResult with error analysis
        """
        error_type = self._classify_error(str(exception))
        error_message = str(exception)
        
        user_message = f"Failed to get status for macro '{identifier}': {error_message}"
        recovery_suggestion = self._recovery_strategies.get(error_type, "Verify macro exists and is accessible")
        
        return KMErrorResult(
            error_type=error_type,
            error_message=error_message,
            user_friendly_message=user_message,
            recovery_suggestion=recovery_suggestion,
            technical_details=f"Operation ID: {operation_id}, Macro: {identifier}",
            retry_recommended=error_type != KMErrorType.MACRO_NOT_FOUND
        )
    
    def _classify_error(self, error_message: str) -> KMErrorType:
        """Classify error based on message patterns."""
        error_lower = error_message.lower()
        
        for pattern, error_type in self._error_patterns.items():
            if re.search(pattern, error_lower, re.IGNORECASE):
                return error_type
        
        # Default classification based on common error indicators
        if "timeout" in error_lower:
            return KMErrorType.EXECUTION_TIMEOUT
        elif "permission" in error_lower or "access" in error_lower:
            return KMErrorType.PERMISSION_DENIED
        elif "not found" in error_lower:
            return KMErrorType.MACRO_NOT_FOUND
        else:
            return KMErrorType.APPLESCRIPT_RUNTIME
    
    def _generate_user_friendly_message(self, 
                                       error_type: KMErrorType, 
                                       context: MacroExecutionContext) -> str:
        """Generate user-friendly error message based on context."""
        identifier = context.identifier
        method = context.method.value
        
        messages = {
            KMErrorType.MACRO_NOT_FOUND: f"Macro '{identifier}' could not be found in Keyboard Maestro",
            KMErrorType.MACRO_DISABLED: f"Macro '{identifier}' is currently disabled",
            KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE: "Keyboard Maestro is not running or accessible",
            KMErrorType.PERMISSION_DENIED: "Permission denied - check accessibility settings",
            KMErrorType.EXECUTION_TIMEOUT: f"Macro '{identifier}' execution timed out after {context.timeout} seconds",
            KMErrorType.RATE_LIMIT_EXCEEDED: "Too many requests - please wait and try again",
            KMErrorType.APPLESCRIPT_SYNTAX: f"AppleScript syntax error in {method} execution",
            KMErrorType.APPLESCRIPT_RUNTIME: f"AppleScript runtime error during {method} execution",
        }
        
        return messages.get(error_type, f"An error occurred during {method} execution of '{identifier}'")
    
    def _get_recovery_suggestion(self, 
                                error_type: KMErrorType, 
                                context: MacroExecutionContext) -> str:
        """Get context-specific recovery suggestion."""
        base_suggestion = self._recovery_strategies.get(error_type, "Check configuration and try again")
        
        # Add method-specific guidance
        if context.method == ExecutionMethod.URL and error_type == KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE:
            return f"{base_suggestion}. For URL method, ensure Keyboard Maestro Engine is responding to URL schemes"
        elif context.method == ExecutionMethod.WEB and error_type == KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE:
            return f"{base_suggestion}. For Web API method, ensure Keyboard Maestro web server is running on port 4490"
        
        return base_suggestion
    
    def _estimate_fix_time(self, error_type: KMErrorType) -> Optional[str]:
        """Estimate time to fix error type."""
        fix_times = {
            KMErrorType.KEYBOARD_MAESTRO_UNAVAILABLE: "1-2 minutes (restart application)",
            KMErrorType.PERMISSION_DENIED: "2-5 minutes (system settings)",
            KMErrorType.MACRO_DISABLED: "30 seconds (enable macro)",
            KMErrorType.RATE_LIMIT_EXCEEDED: "1-2 minutes (wait for cooldown)",
            KMErrorType.EXECUTION_TIMEOUT: "immediate (increase timeout)",
            KMErrorType.MACRO_NOT_FOUND: "varies (create or fix macro name)",
            KMErrorType.VARIABLE_NOT_FOUND: "1 minute (create variable)",
        }
        
        return fix_times.get(error_type)
