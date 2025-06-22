"""
Core Input Validation Framework for Keyboard Maestro MCP Server.

This module implements comprehensive input validation with composable validators,
type safety, defensive programming patterns, and detailed error reporting.
All external inputs must pass through these validators before processing.

Target: <250 lines per ADDER+ modularity requirements
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Protocol, TypeVar, Union, Literal, Dict
from enum import Enum
import re
import uuid
import os.path
from pathlib import Path

# Import type system components (assuming they exist from Task 1.1/1.2)
try:
    from ..types.domain_types import MacroUUID, MacroName, VariableName, GroupUUID
    from ..types.enumerations import VariableScope, ExecutionMethod, TriggerType
    from ..types.results import Result, OperationError, ErrorType
    from ..contracts.decorators import requires, ensures
    from ..contracts.exceptions import ValidationError
except ImportError:
    # Fallback types for development
    MacroUUID = str
    MacroName = str
    VariableName = str
    GroupUUID = str
    
    class VariableScope(Enum):
        GLOBAL = "global"
        LOCAL = "local"
        PASSWORD = "password"
    
    class ErrorType(Enum):
        VALIDATION_ERROR = "validation_error"
    
    @dataclass
    class OperationError:
        error_type: ErrorType
        message: str
    
    @dataclass
    class Result:
        _value: Any = None
        _error: Any = None
        
        @classmethod
        def success(cls, value): return cls(_value=value)
        
        @classmethod  
        def failure(cls, error): return cls(_error=error)
        
        @property
        def is_success(self): return self._value is not None

T = TypeVar('T')

class ValidationSeverity(Enum):
    """Validation error severity levels for progressive enforcement."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass(frozen=True)
class ValidationResult:
    """Comprehensive validation result with detailed error information."""
    is_valid: bool
    errors: List[OperationError]
    warnings: List[str]
    sanitized_value: Optional[Any] = None
    validation_metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success(cls, value: Any = None, warnings: List[str] = None) -> 'ValidationResult':
        """Create successful validation result."""
        return cls(
            is_valid=True,
            errors=[],
            warnings=warnings or [],
            sanitized_value=value
        )
    
    @classmethod
    def failure(cls, errors: List[OperationError], warnings: List[str] = None) -> 'ValidationResult':
        """Create failed validation result."""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or []
        )

class InputValidator(Protocol[T]):
    """Protocol for composable input validators with type safety."""
    
    @abstractmethod
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate input value with optional context information."""
        ...
    
    @abstractmethod
    def get_validation_rules(self) -> Dict[str, str]:
        """Get human-readable validation rules for documentation."""
        ...

class BaseValidator(ABC):
    """Base class for input validators with common functionality."""
    
    def __init__(self, name: str, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.name = name
        self.severity = severity
    
    def _create_error(self, message: str, field_name: str = "input", 
                     error_code: str = "VALIDATION_FAILED") -> OperationError:
        """Create standardized validation error."""
        return OperationError(
            error_type=ErrorType.VALIDATION_ERROR,
            message=f"{self.name}: {message}",
            details=f"Field '{field_name}' failed validation",
            recovery_suggestion=f"Ensure {field_name} meets the following criteria: {self.get_validation_rules()}",
            error_code=error_code
        )

class MacroIdentifierValidator(BaseValidator):
    """Validates macro identifiers (UUID or name format)."""
    
    def __init__(self):
        super().__init__("MacroIdentifierValidator")
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate macro identifier format and constraints."""
        if value is None:
            return ValidationResult.failure([
                self._create_error("Macro identifier cannot be None", "identifier")
            ])
        
        # Try UUID validation first
        if isinstance(value, str):
            try:
                uuid.UUID(value)
                return ValidationResult.success(value)
            except ValueError:
                # Not a UUID, check if valid name
                pass
        
        # Validate as macro name
        if not isinstance(value, str):
            return ValidationResult.failure([
                self._create_error(f"Expected string or UUID, got {type(value).__name__}", "identifier")
            ])
        
        if not (1 <= len(value) <= 255):
            return ValidationResult.failure([
                self._create_error("Macro name must be 1-255 characters", "identifier")
            ])
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return ValidationResult.failure([
                self._create_error("Macro name contains invalid characters", "identifier")
            ])
        
        return ValidationResult.success(value)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for macro identifiers."""
        return {
            "format": "Valid UUID string or macro name",
            "length": "1-255 characters for names",
            "characters": "Names: letters, numbers, spaces, hyphens, dots, underscores only"
        }

class VariableNameValidator(BaseValidator):
    """Validates Keyboard Maestro variable names."""
    
    def __init__(self):
        super().__init__("VariableNameValidator")
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate variable name following Keyboard Maestro conventions."""
        if not isinstance(value, str):
            return ValidationResult.failure([
                self._create_error(f"Expected string, got {type(value).__name__}", "variable_name")
            ])
        
        if not (1 <= len(value) <= 255):
            return ValidationResult.failure([
                self._create_error("Variable name must be 1-255 characters", "variable_name")
            ])
        
        # Keyboard Maestro variable naming conventions
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            return ValidationResult.failure([
                self._create_error(
                    "Variable name must start with letter/underscore, contain only letters/numbers/underscores",
                    "variable_name"
                )
            ])
        
        return ValidationResult.success(value)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for variable names."""
        return {
            "format": "Must start with letter or underscore",
            "characters": "Only letters, numbers, and underscores allowed",
            "length": "1-255 characters"
        }

class FilePathValidator(BaseValidator):
    """Validates file system paths for operations."""
    
    def __init__(self, require_exists: bool = False, require_readable: bool = False):
        super().__init__("FilePathValidator")
        self.require_exists = require_exists
        self.require_readable = require_readable
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate file path format and accessibility."""
        if not isinstance(value, str):
            return ValidationResult.failure([
                self._create_error(f"Expected string path, got {type(value).__name__}", "file_path")
            ])
        
        if not value.strip():
            return ValidationResult.failure([
                self._create_error("File path cannot be empty", "file_path")
            ])
        
        # Basic path validation
        try:
            path = Path(value).resolve()
        except (OSError, ValueError) as e:
            return ValidationResult.failure([
                self._create_error(f"Invalid path format: {str(e)}", "file_path")
            ])
        
        errors = []
        warnings = []
        
        # Existence check
        if self.require_exists and not path.exists():
            errors.append(self._create_error(f"Path does not exist: {value}", "file_path"))
        
        # Readability check  
        if self.require_readable and path.exists() and not os.access(str(path), os.R_OK):
            errors.append(self._create_error(f"Path is not readable: {value}", "file_path"))
        
        # Security warnings for suspicious paths
        if any(part.startswith('.') for part in path.parts[1:]):
            warnings.append(f"Path contains hidden directories: {value}")
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        
        return ValidationResult.success(str(path), warnings)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for file paths."""
        rules = {
            "format": "Valid file system path",
            "security": "No directory traversal patterns"
        }
        if self.require_exists:
            rules["existence"] = "Path must exist"
        if self.require_readable:
            rules["permissions"] = "Path must be readable"
        return rules

class CompositeValidator:
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[InputValidator], 
                 logic: Literal["AND", "OR"] = "AND", 
                 name: str = "CompositeValidator"):
        self.validators = validators
        self.logic = logic
        self.name = name
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate using composite logic."""
        results = [validator.validate(value, context) for validator in self.validators]
        
        if self.logic == "AND":
            # All validators must pass
            all_errors = []
            all_warnings = []
            
            for result in results:
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
            
            if all_errors:
                return ValidationResult.failure(all_errors, all_warnings)
            
            # Use sanitized value from last successful validator
            sanitized_value = value
            for result in results:
                if result.sanitized_value is not None:
                    sanitized_value = result.sanitized_value
            
            return ValidationResult.success(sanitized_value, all_warnings)
        
        else:  # OR logic
            # At least one validator must pass
            for result in results:
                if result.is_valid:
                    return result
            
            # All failed, combine errors
            all_errors = []
            for result in results:
                all_errors.extend(result.errors)
            
            return ValidationResult.failure(all_errors)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get combined validation rules."""
        combined_rules = {}
        for i, validator in enumerate(self.validators):
            validator_rules = validator.get_validation_rules()
            for key, value in validator_rules.items():
                combined_key = f"{self.logic.lower()}_{i}_{key}"
                combined_rules[combined_key] = value
        return combined_rules

# Pre-configured validator instances for common use cases
MACRO_IDENTIFIER_VALIDATOR = MacroIdentifierValidator()
VARIABLE_NAME_VALIDATOR = VariableNameValidator()
EXISTING_FILE_VALIDATOR = FilePathValidator(require_exists=True, require_readable=True)
WRITABLE_PATH_VALIDATOR = FilePathValidator(require_exists=False)

def validate_macro_identifier(value: Any) -> ValidationResult:
    """Convenience function for macro identifier validation."""
    return MACRO_IDENTIFIER_VALIDATOR.validate(value)

def validate_variable_name(value: Any) -> ValidationResult:
    """Convenience function for variable name validation."""
    return VARIABLE_NAME_VALIDATOR.validate(value)

def validate_file_path(value: Any, require_exists: bool = False) -> ValidationResult:
    """Convenience function for file path validation."""
    validator = FilePathValidator(require_exists=require_exists)
    return validator.validate(value)
