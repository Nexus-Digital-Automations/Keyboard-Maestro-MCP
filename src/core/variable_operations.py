"""Core variable operation logic with immutability patterns and type safety.

This module implements the foundational variable operation logic for Keyboard Maestro
variables, dictionaries, and clipboard operations. Following ADDER+ principles with
type-driven development, immutability patterns, and comprehensive contract validation.

Key Features:
- Type-safe variable operations with branded types
- Immutable data structures for variable state
- Pure transformation functions for data manipulation
- Comprehensive scope enforcement and validation
- Contract-driven development with preconditions/postconditions
"""

from dataclasses import dataclass, replace
from typing import Dict, Optional, Set, FrozenSet, Tuple, List, Any, Union
from enum import Enum
import json
import uuid
from datetime import datetime

from src.types.domain_types import VariableName, VariableValue
from src.types.enumerations import VariableScope
from src.types.results import Result, OperationError, ErrorType
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_variable_name


class VariableOperationType(Enum):
    """Types of variable operations."""
    GET = "get"
    SET = "set"
    DELETE = "delete"
    LIST = "list"
    EXISTS = "exists"


@dataclass(frozen=True)
class VariableMetadata:
    """Immutable metadata for variables."""
    name: VariableName
    scope: VariableScope
    instance_id: Optional[str]
    created_at: datetime
    modified_at: datetime
    is_password: bool
    
    def with_modification_time(self, new_time: datetime) -> 'VariableMetadata':
        """Create new metadata with updated modification time."""
        return replace(self, modified_at=new_time)
    
    def is_scoped_variable(self) -> bool:
        """Check if variable requires scope context."""
        return self.scope != VariableScope.GLOBAL
    
    def requires_instance_id(self) -> bool:
        """Check if variable requires instance ID."""
        return self.scope == VariableScope.INSTANCE


@dataclass(frozen=True)
class VariableEntry:
    """Immutable variable entry with metadata."""
    metadata: VariableMetadata
    value: Optional[VariableValue]
    
    def with_value(self, new_value: Optional[VariableValue]) -> 'VariableEntry':
        """Create new entry with updated value and modification time."""
        new_metadata = self.metadata.with_modification_time(datetime.now())
        return replace(self, metadata=new_metadata, value=new_value)
    
    def is_password_variable(self) -> bool:
        """Check if this is a password variable."""
        return self.metadata.is_password
    
    def is_accessible_in_scope(self, requested_scope: VariableScope,
                              instance_id: Optional[str] = None) -> bool:
        """Check if variable is accessible in the requested scope."""
        if self.metadata.scope != requested_scope:
            return False
        
        if self.metadata.requires_instance_id():
            return self.metadata.instance_id == instance_id
        
        return True


@dataclass(frozen=True)
class VariableSnapshot:
    """Immutable snapshot of variable state."""
    variables: FrozenSet[VariableEntry]
    snapshot_time: datetime
    
    def get_variable(self, name: VariableName, scope: VariableScope,
                    instance_id: Optional[str] = None) -> Optional[VariableEntry]:
        """Get variable entry from snapshot."""
        for entry in self.variables:
            if (entry.metadata.name == name and 
                entry.is_accessible_in_scope(scope, instance_id)):
                return entry
        return None
    
    def has_variable(self, name: VariableName, scope: VariableScope,
                    instance_id: Optional[str] = None) -> bool:
        """Check if variable exists in snapshot."""
        return self.get_variable(name, scope, instance_id) is not None
    
    def filter_by_scope(self, scope: VariableScope) -> FrozenSet[VariableEntry]:
        """Get all variables in specified scope."""
        return frozenset(
            entry for entry in self.variables
            if entry.metadata.scope == scope
        )


@dataclass(frozen=True)
class DictionaryEntry:
    """Immutable dictionary entry."""
    name: str
    data: Dict[str, Any]
    created_at: datetime
    modified_at: datetime
    
    def with_key_value(self, key: str, value: Any) -> 'DictionaryEntry':
        """Create new dictionary entry with updated key-value pair."""
        new_data = dict(self.data)
        new_data[key] = value
        return replace(
            self,
            data=new_data,
            modified_at=datetime.now()
        )
    
    def without_key(self, key: str) -> 'DictionaryEntry':
        """Create new dictionary entry without specified key."""
        new_data = dict(self.data)
        new_data.pop(key, None)
        return replace(
            self,
            data=new_data,
            modified_at=datetime.now()
        )
    
    def get_keys(self) -> FrozenSet[str]:
        """Get all dictionary keys."""
        return frozenset(self.data.keys())
    
    def to_json(self) -> str:
        """Convert dictionary to JSON string."""
        return json.dumps(self.data, indent=2, sort_keys=True)


@dataclass(frozen=True)
class ClipboardEntry:
    """Immutable clipboard entry."""
    content: str
    format_type: str
    timestamp: datetime
    index: int
    
    def is_text_format(self) -> bool:
        """Check if entry contains text."""
        return self.format_type == "text"
    
    def is_image_format(self) -> bool:
        """Check if entry contains image."""
        return self.format_type == "image"
    
    def is_file_format(self) -> bool:
        """Check if entry contains file reference."""
        return self.format_type == "file"


@dataclass(frozen=True)
class ClipboardSnapshot:
    """Immutable clipboard state snapshot."""
    entries: Tuple[ClipboardEntry, ...]
    current_index: int
    max_history_size: int
    
    def get_current_entry(self) -> Optional[ClipboardEntry]:
        """Get the current clipboard entry."""
        if 0 <= self.current_index < len(self.entries):
            return self.entries[self.current_index]
        return None
    
    def add_entry(self, entry: ClipboardEntry) -> 'ClipboardSnapshot':
        """Create new snapshot with added entry."""
        # Add to front, maintain max history size
        new_entries = (entry,) + self.entries[:self.max_history_size - 1]
        return replace(
            self,
            entries=new_entries,
            current_index=0
        )
    
    def get_history_entries(self, count: int = 10) -> Tuple[ClipboardEntry, ...]:
        """Get recent clipboard entries."""
        return self.entries[:min(count, len(self.entries))]


# Core Variable Operations
class VariableOperations:
    """Core variable operations with type safety and immutability."""
    
    @staticmethod
    @requires(lambda name: is_valid_variable_name(name))
    @requires(lambda scope: scope in VariableScope)
    @ensures(lambda result: result.is_success or result.is_failure)
    def create_variable_metadata(
        name: VariableName,
        scope: VariableScope,
        instance_id: Optional[str] = None,
        is_password: bool = False
    ) -> Result[VariableMetadata]:
        """Create variable metadata with validation."""
        try:
            # Check password variable naming convention
            if is_password and "password" not in name.lower() and "pw" not in name.lower():
                return Result.failure(OperationError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="Password variables must contain 'password' or 'pw' in name",
                    recovery_suggestion="Rename variable to include 'password' or 'pw'"
                ))
            
            # Validate instance ID requirement
            if scope == VariableScope.INSTANCE and instance_id is None:
                return Result.failure(OperationError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="Instance variables require instance ID",
                    recovery_suggestion="Provide instance_id parameter"
                ))
            
            now = datetime.now()
            metadata = VariableMetadata(
                name=name,
                scope=scope,
                instance_id=instance_id,
                created_at=now,
                modified_at=now,
                is_password=is_password
            )
            
            return Result.success(metadata)
            
        except Exception as e:
            return Result.failure(OperationError(
                error_type=ErrorType.SYSTEM_ERROR,
                message=f"Failed to create variable metadata: {str(e)}",
                recovery_suggestion="Check input parameters and try again"
            ))
    
    @staticmethod
    @requires(lambda snapshot: isinstance(snapshot, VariableSnapshot))
    @requires(lambda name: is_valid_variable_name(name))
    @ensures(lambda result: result.is_success or result.is_failure)
    def get_variable_from_snapshot(
        snapshot: VariableSnapshot,
        name: VariableName,
        scope: VariableScope,
        instance_id: Optional[str] = None
    ) -> Result[Optional[VariableEntry]]:
        """Get variable from snapshot with scope validation."""
        try:
            entry = snapshot.get_variable(name, scope, instance_id)
            return Result.success(entry)
            
        except Exception as e:
            return Result.failure(OperationError(
                error_type=ErrorType.SYSTEM_ERROR,
                message=f"Failed to retrieve variable: {str(e)}",
                recovery_suggestion="Check variable name and scope parameters"
            ))
    
    @staticmethod
    @requires(lambda dictionary_name: len(dictionary_name) > 0)
    @ensures(lambda result: result.is_success or result.is_failure)
    def create_dictionary_entry(
        dictionary_name: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Result[DictionaryEntry]:
        """Create new dictionary entry with validation."""
        try:
            if initial_data is None:
                initial_data = {}
            
            # Validate JSON serializability
            try:
                json.dumps(initial_data)
            except (TypeError, ValueError) as e:
                return Result.failure(OperationError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message=f"Dictionary data is not JSON serializable: {str(e)}",
                    recovery_suggestion="Ensure all values are JSON-compatible types"
                ))
            
            now = datetime.now()
            entry = DictionaryEntry(
                name=dictionary_name,
                data=initial_data.copy(),  # Defensive copy
                created_at=now,
                modified_at=now
            )
            
            return Result.success(entry)
            
        except Exception as e:
            return Result.failure(OperationError(
                error_type=ErrorType.SYSTEM_ERROR,
                message=f"Failed to create dictionary entry: {str(e)}",
                recovery_suggestion="Check dictionary name and initial data"
            ))
    
    @staticmethod
    @requires(lambda entry: isinstance(entry, DictionaryEntry))
    @requires(lambda json_data: isinstance(json_data, str))
    @ensures(lambda result: result.is_success or result.is_failure)
    def import_dictionary_from_json(
        entry: DictionaryEntry,
        json_data: str
    ) -> Result[DictionaryEntry]:
        """Import dictionary data from JSON string."""
        try:
            data = json.loads(json_data)
            
            if not isinstance(data, dict):
                return Result.failure(OperationError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="JSON data must be an object/dictionary",
                    recovery_suggestion="Ensure JSON contains a top-level object"
                ))
            
            return Result.success(replace(
                entry,
                data=data,
                modified_at=datetime.now()
            ))
            
        except json.JSONDecodeError as e:
            return Result.failure(OperationError(
                error_type=ErrorType.VALIDATION_ERROR,
                message=f"Invalid JSON format: {str(e)}",
                recovery_suggestion="Check JSON syntax and structure"
            ))
        except Exception as e:
            return Result.failure(OperationError(
                error_type=ErrorType.SYSTEM_ERROR,
                message=f"Failed to import dictionary: {str(e)}",
                recovery_suggestion="Check input data and try again"
            ))
    
    @staticmethod
    @requires(lambda content: isinstance(content, str))
    @requires(lambda format_type: format_type in ["text", "image", "file"])
    @ensures(lambda result: result.is_success or result.is_failure)
    def create_clipboard_entry(
        content: str,
        format_type: str,
        index: int = 0
    ) -> Result[ClipboardEntry]:
        """Create clipboard entry with validation."""
        try:
            if index < 0:
                return Result.failure(OperationError(
                    error_type=ErrorType.VALIDATION_ERROR,
                    message="Clipboard index must be non-negative",
                    recovery_suggestion="Use index >= 0"
                ))
            
            entry = ClipboardEntry(
                content=content,
                format_type=format_type,
                timestamp=datetime.now(),
                index=index
            )
            
            return Result.success(entry)
            
        except Exception as e:
            return Result.failure(OperationError(
                error_type=ErrorType.SYSTEM_ERROR,
                message=f"Failed to create clipboard entry: {str(e)}",
                recovery_suggestion="Check content and format parameters"
            ))
