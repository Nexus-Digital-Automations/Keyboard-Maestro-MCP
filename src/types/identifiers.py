# src/types/identifiers.py (Target: <200 lines)
"""
Branded identifier types for the Keyboard Maestro MCP Server.

This module implements type-driven development principles with branded types
to prevent primitive obsession and enforce domain constraints for all
identifier types used throughout the system.
"""

from typing import NewType, Union, Optional
from uuid import UUID
from dataclasses import dataclass
import re
import uuid


# Branded Identifier Types - Prevent primitive obsession
MacroUUID = NewType('MacroUUID', UUID)
MacroName = NewType('MacroName', str)
GroupUUID = NewType('GroupUUID', UUID)
GroupName = NewType('GroupName', str)
VariableName = NewType('VariableName', str)
TriggerID = NewType('TriggerID', str)
ActionID = NewType('ActionID', str)
ApplicationBundleID = NewType('ApplicationBundleID', str)
ExecutionID = NewType('ExecutionID', str)
PluginID = NewType('PluginID', str)


# Validation Functions with Comprehensive Error Reporting
def create_macro_uuid(uuid_str: str) -> MacroUUID:
    """Create validated macro UUID with error handling.
    
    Args:
        uuid_str: String representation of UUID
        
    Returns:
        MacroUUID: Validated macro UUID
        
    Raises:
        ValueError: If UUID format is invalid
    """
    try:
        return MacroUUID(UUID(uuid_str))
    except ValueError as e:
        raise ValueError(f"Invalid macro UUID format: {uuid_str}") from e


def create_macro_name(name: str) -> MacroName:
    """Create validated macro name following Keyboard Maestro conventions.
    
    Args:
        name: Proposed macro name
        
    Returns:
        MacroName: Validated macro name
        
    Raises:
        ValueError: If name violates constraints
    """
    if not name or len(name) > 255:
        raise ValueError("Macro name must be 1-255 characters")
    
    # Allow alphanumeric, spaces, hyphens, underscores, and periods
    if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name):
        raise ValueError("Macro name contains invalid characters")
    
    return MacroName(name)


def create_group_uuid(uuid_str: str) -> GroupUUID:
    """Create validated group UUID.
    
    Args:
        uuid_str: String representation of UUID
        
    Returns:
        GroupUUID: Validated group UUID
        
    Raises:
        ValueError: If UUID format is invalid
    """
    try:
        return GroupUUID(UUID(uuid_str))
    except ValueError as e:
        raise ValueError(f"Invalid group UUID format: {uuid_str}") from e


def create_variable_name(name: str) -> VariableName:
    """Create validated variable name following Keyboard Maestro conventions.
    
    Args:
        name: Proposed variable name
        
    Returns:
        VariableName: Validated variable name
        
    Raises:
        ValueError: If name violates constraints
    """
    if not name or len(name) > 255:
        raise ValueError("Variable name must be 1-255 characters")
    
    # Follow identifier conventions: start with letter or underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError("Variable name must follow identifier conventions")
    
    return VariableName(name)


def create_application_bundle_id(bundle_id: str) -> ApplicationBundleID:
    """Create validated application bundle identifier.
    
    Args:
        bundle_id: Application bundle identifier
        
    Returns:
        ApplicationBundleID: Validated bundle identifier
        
    Raises:
        ValueError: If bundle ID format is invalid
    """
    if not bundle_id:
        raise ValueError("Bundle ID cannot be empty")
    
    # Bundle IDs typically follow reverse domain notation
    if not re.match(r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+$', bundle_id):
        raise ValueError("Bundle ID must follow reverse domain notation")
    
    return ApplicationBundleID(bundle_id)


def create_execution_id() -> ExecutionID:
    """Create unique execution identifier.
    
    Returns:
        ExecutionID: Unique execution identifier
    """
    return ExecutionID(str(uuid.uuid4()))


# Composite Identifier Types for Complex Lookups
@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup.
    
    This type enables flexible macro identification while maintaining
    type safety and providing context for resolution.
    """
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        """Check if identifier uses UUID."""
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        """Check if identifier uses name."""
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        """Check if identifier requires group context for resolution."""
        return self.is_name() and self.group_context is None


@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context.
    
    Provides complete variable identification including scope
    and instance information for proper resolution.
    """
    name: VariableName
    scope: 'VariableScope'  # Forward reference to avoid circular import
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        """Check if variable is in global scope."""
        from .enumerations import VariableScope
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        """Check if variable is in local scope."""
        from .enumerations import VariableScope
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        """Check if variable is password type."""
        from .enumerations import VariableScope
        return self.scope == VariableScope.PASSWORD
    
    def requires_instance_id(self) -> bool:
        """Check if variable requires instance ID."""
        from .enumerations import VariableScope
        return self.scope == VariableScope.INSTANCE


# Helper Functions for Identifier Validation
def is_valid_macro_identifier(identifier: Union[str, UUID]) -> bool:
    """Check if value can be used as macro identifier.
    
    Args:
        identifier: Potential macro identifier
        
    Returns:
        bool: True if valid identifier format
    """
    if isinstance(identifier, str):
        try:
            create_macro_name(identifier)
            return True
        except ValueError:
            return False
    elif isinstance(identifier, UUID):
        return True
    return False


def is_valid_variable_name_format(name: str) -> bool:
    """Check if name follows variable naming conventions.
    
    Args:
        name: Potential variable name
        
    Returns:
        bool: True if valid format
    """
    try:
        create_variable_name(name)
        return True
    except ValueError:
        return False
