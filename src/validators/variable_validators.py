"""Variable validation and scope checking with type safety enforcement.

This module provides comprehensive validation for Keyboard Maestro variables,
dictionaries, and clipboard operations. Implements ADDER+ defensive programming
patterns with type-driven validation and scope enforcement.

Key Features:
- Variable name and value validation with Keyboard Maestro conventions
- Scope enforcement for global, local, instance, and password variables
- Dictionary structure and JSON format validation
- Clipboard content and format validation
- Type-safe validation patterns with branded types
"""

from typing import Optional, Dict, Any, List, Set
import re
import json
from dataclasses import dataclass

from src.types.domain_types import VariableName, VariableValue
from .types.enumerations import VariableScope
from src.types.results import Result, OperationError, ErrorType
from src.contracts.decorators import requires, ensures


@dataclass(frozen=True)
class ValidationError:
    """Detailed validation error information."""
    field: str
    value: Any
    rule: str
    message: str
    suggestion: str


class VariableNameValidator:
    """Validates variable names according to Keyboard Maestro conventions."""
    
    # Keyboard Maestro variable naming patterns
    VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    PASSWORD_INDICATORS = {'password', 'pw', 'pass', 'secret', 'key'}
    RESERVED_PREFIXES = {'local__', 'instance__', 'kmvar_'}
    
    @classmethod
    @requires(lambda name: isinstance(name, str))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_name(cls, name: str) -> Result[VariableName]:
        """Validate variable name format and conventions."""
        # Length validation
        if not name:
            return Result.failure(ValidationError(
                field="name",
                value=name,
                rule="non_empty",
                message="Variable name cannot be empty",
                suggestion="Provide a non-empty variable name"
            ))
        
        if len(name) > 255:
            return Result.failure(ValidationError(
                field="name",
                value=name,
                rule="max_length",
                message="Variable name exceeds maximum length of 255 characters",
                suggestion="Use a shorter variable name"
            ))
        
        # Format validation
        if not cls.VALID_NAME_PATTERN.match(name):
            return Result.failure(ValidationError(
                field="name",
                value=name,
                rule="format",
                message="Variable name must start with letter or underscore, contain only alphanumeric and underscore",
                suggestion="Use format: [a-zA-Z_][a-zA-Z0-9_]*"
            ))
        
        # Reserved prefix check
        name_lower = name.lower()
        for prefix in cls.RESERVED_PREFIXES:
            if name_lower.startswith(prefix):
                return Result.failure(ValidationError(
                    field="name",
                    value=name,
                    rule="reserved_prefix",
                    message=f"Variable name uses reserved prefix '{prefix}'",
                    suggestion="Choose a different name without reserved prefixes"
                ))
        
        return Result.success(VariableName(name))
    
    @classmethod
    def is_password_variable_name(cls, name: str) -> bool:
        """Check if name indicates password variable."""
        name_lower = name.lower()
        return any(indicator in name_lower for indicator in cls.PASSWORD_INDICATORS)
    
    @classmethod
    def suggest_password_name(cls, base_name: str) -> str:
        """Suggest password variable name from base name."""
        if not cls.is_password_variable_name(base_name):
            return f"{base_name}_password"
        return base_name


class VariableScopeValidator:
    """Validates variable scope requirements and constraints."""
    
    @staticmethod
    @requires(lambda scope: isinstance(scope, VariableScope))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_scope_requirements(
        scope: VariableScope,
        instance_id: Optional[str] = None,
        is_password: bool = False
    ) -> Result[bool]:
        """Validate scope-specific requirements."""
        # Instance scope validation
        if scope == VariableScope.INSTANCE:
            if instance_id is None:
                return Result.failure(ValidationError(
                    field="instance_id",
                    value=instance_id,
                    rule="required",
                    message="Instance variables require instance_id parameter",
                    suggestion="Provide instance_id for instance-scoped variables"
                ))
            
            if not isinstance(instance_id, str) or not instance_id.strip():
                return Result.failure(ValidationError(
                    field="instance_id",
                    value=instance_id,
                    rule="format",
                    message="Instance ID must be non-empty string",
                    suggestion="Provide valid instance identifier"
                ))
        
        # Password scope validation
        if scope == VariableScope.PASSWORD and not is_password:
            return Result.failure(ValidationError(
                field="scope",
                value=scope,
                rule="consistency",
                message="Variable marked as password scope but is_password is False",
                suggestion="Set is_password=True for password scope variables"
            ))
        
        # Local scope context validation
        if scope == VariableScope.LOCAL:
            # Local variables should only be used within execution context
            # This is a warning rather than error for flexibility
            pass
        
        return Result.success(True)
    
    @staticmethod
    def get_scope_display_name(scope: VariableScope) -> str:
        """Get human-readable scope name."""
        scope_names = {
            VariableScope.GLOBAL: "Global",
            VariableScope.LOCAL: "Local",
            VariableScope.INSTANCE: "Instance",
            VariableScope.PASSWORD: "Password"
        }
        return scope_names.get(scope, "Unknown")


class VariableValueValidator:
    """Validates variable values and content."""
    
    MAX_VALUE_LENGTH = 1_000_000  # 1MB text limit
    
    @classmethod
    @requires(lambda value: value is None or isinstance(value, str))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_value(
        cls,
        value: Optional[str],
        is_password: bool = False
    ) -> Result[Optional[VariableValue]]:
        """Validate variable value content and constraints."""
        if value is None:
            return Result.success(None)
        
        # Length validation
        if len(value) > cls.MAX_VALUE_LENGTH:
            return Result.failure(ValidationError(
                field="value",
                value=f"<{len(value)} characters>",
                rule="max_length",
                message=f"Variable value exceeds maximum length of {cls.MAX_VALUE_LENGTH:,} characters",
                suggestion="Reduce value length or use file storage for large data"
            ))
        
        # Password value validation
        if is_password:
            if not value.strip():
                return Result.failure(ValidationError(
                    field="value",
                    value="<empty>",
                    rule="password_empty",
                    message="Password variables should not have empty values",
                    suggestion="Provide a meaningful password value"
                ))
        
        return Result.success(VariableValue(value))


class DictionaryValidator:
    """Validates dictionary structures and operations."""
    
    MAX_DICT_SIZE = 100_000  # Maximum serialized size
    MAX_KEY_LENGTH = 1000
    MAX_NESTING_DEPTH = 10
    
    @classmethod
    @requires(lambda name: isinstance(name, str))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_dictionary_name(cls, name: str) -> Result[str]:
        """Validate dictionary name format."""
        if not name or not name.strip():
            return Result.failure(ValidationError(
                field="dictionary_name",
                value=name,
                rule="non_empty",
                message="Dictionary name cannot be empty",
                suggestion="Provide a non-empty dictionary name"
            ))
        
        # Use similar validation as variable names
        if len(name) > 255:
            return Result.failure(ValidationError(
                field="dictionary_name",
                value=name,
                rule="max_length",
                message="Dictionary name exceeds maximum length of 255 characters",
                suggestion="Use a shorter dictionary name"
            ))
        
        return Result.success(name.strip())
    
    @classmethod
    @requires(lambda data: isinstance(data, dict))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_dictionary_data(cls, data: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """Validate dictionary data structure and content."""
        # Check JSON serializability
        try:
            serialized = json.dumps(data)
            if len(serialized) > cls.MAX_DICT_SIZE:
                return Result.failure(ValidationError(
                    field="data",
                    value=f"<{len(serialized)} bytes>",
                    rule="max_size",
                    message=f"Dictionary exceeds maximum size of {cls.MAX_DICT_SIZE:,} bytes",
                    suggestion="Reduce dictionary size or split into multiple dictionaries"
                ))
        except (TypeError, ValueError) as e:
            return Result.failure(ValidationError(
                field="data",
                value=str(data),
                rule="json_serializable",
                message=f"Dictionary data is not JSON serializable: {str(e)}",
                suggestion="Ensure all values are JSON-compatible types"
            ))
        
        # Validate keys
        for key in data.keys():
            if not isinstance(key, str):
                return Result.failure(ValidationError(
                    field="key",
                    value=key,
                    rule="string_type",
                    message="Dictionary keys must be strings",
                    suggestion="Convert non-string keys to strings"
                ))
            
            if len(key) > cls.MAX_KEY_LENGTH:
                return Result.failure(ValidationError(
                    field="key",
                    value=key,
                    rule="max_length",
                    message=f"Dictionary key exceeds maximum length of {cls.MAX_KEY_LENGTH} characters",
                    suggestion="Use shorter key names"
                ))
        
        # Check nesting depth
        def check_depth(obj, current_depth=0):
            if current_depth > cls.MAX_NESTING_DEPTH:
                return False
            if isinstance(obj, dict):
                return all(check_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                return all(check_depth(item, current_depth + 1) for item in obj)
            return True
        
        if not check_depth(data):
            return Result.failure(ValidationError(
                field="data",
                value="<nested structure>",
                rule="max_depth",
                message=f"Dictionary nesting exceeds maximum depth of {cls.MAX_NESTING_DEPTH}",
                suggestion="Flatten nested structures or reduce nesting depth"
            ))
        
        return Result.success(data)
    
    @classmethod
    @requires(lambda json_str: isinstance(json_str, str))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_json_import(cls, json_str: str) -> Result[Dict[str, Any], ValidationError]:
        """Validate JSON string for dictionary import."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return Result.failure(ValidationError(
                field="json_data",
                value=json_str[:100] + "..." if len(json_str) > 100 else json_str,
                rule="valid_json",
                message=f"Invalid JSON format: {str(e)}",
                suggestion="Check JSON syntax and structure"
            ))
        
        if not isinstance(data, dict):
            return Result.failure(ValidationError(
                field="json_data",
                value=str(type(data)),
                rule="object_type",
                message="JSON data must be an object/dictionary at root level",
                suggestion="Wrap data in object if needed: {\"data\": ...}"
            ))
        
        return cls.validate_dictionary_data(data)


class ClipboardValidator:
    """Validates clipboard content and operations."""
    
    SUPPORTED_FORMATS = {'text', 'image', 'file'}
    MAX_CONTENT_LENGTH = 10_000_000  # 10MB limit
    
    @classmethod
    @requires(lambda content: isinstance(content, str))
    @requires(lambda format_type: isinstance(format_type, str))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_clipboard_content(
        cls,
        content: str,
        format_type: str
    ) -> Result[bool, ValidationError]:
        """Validate clipboard content and format."""
        # Format validation
        if format_type not in cls.SUPPORTED_FORMATS:
            return Result.failure(ValidationError(
                field="format_type",
                value=format_type,
                rule="supported_format",
                message=f"Unsupported clipboard format: {format_type}",
                suggestion=f"Use one of: {', '.join(cls.SUPPORTED_FORMATS)}"
            ))
        
        # Content length validation
        if len(content) > cls.MAX_CONTENT_LENGTH:
            return Result.failure(ValidationError(
                field="content",
                value=f"<{len(content)} characters>",
                rule="max_length",
                message=f"Clipboard content exceeds maximum length of {cls.MAX_CONTENT_LENGTH:,} characters",
                suggestion="Reduce content size or use file storage"
            ))
        
        # Format-specific validation
        if format_type == "file":
            # For file format, content should be valid file path
            if not content.strip():
                return Result.failure(ValidationError(
                    field="content",
                    value=content,
                    rule="file_path",
                    message="File clipboard content cannot be empty",
                    suggestion="Provide valid file path"
                ))
        
        return Result.success(True)
    
    @classmethod
    @requires(lambda index: isinstance(index, int))
    @ensures(lambda result: result.is_success or result.is_failure)
    def validate_history_index(
        cls,
        index: int,
        max_history_size: int = 200
    ) -> Result[int]:
        """Validate clipboard history index."""
        if index < 0:
            return Result.failure(ValidationError(
                field="index",
                value=index,
                rule="non_negative",
                message="Clipboard history index must be non-negative",
                suggestion="Use index >= 0"
            ))
        
        if index >= max_history_size:
            return Result.failure(ValidationError(
                field="index",
                value=index,
                rule="within_bounds",
                message=f"Index {index} exceeds maximum history size of {max_history_size}",
                suggestion=f"Use index between 0 and {max_history_size - 1}"
            ))
        
        return Result.success(index)
