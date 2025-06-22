# src/types/__init__.py (Target: <100 lines)
"""
Type System Public API for Keyboard Maestro MCP Server.

This module provides a clean, organized interface to the complete type system
following type-driven development principles with branded types, domain modeling,
and immutable structures.
"""

# Core Branded Identifier Types
from .identifiers import (
    MacroUUID, MacroName, GroupUUID, GroupName, VariableName,
    TriggerID, ActionID, ApplicationBundleID, ExecutionID, PluginID,
    create_macro_uuid, create_macro_name, create_group_uuid,
    create_variable_name, create_application_bundle_id, create_execution_id,
    MacroIdentifier, VariableIdentifier,
    is_valid_macro_identifier, is_valid_variable_name_format
)

# Branded Value Types
from .values import (
    MacroExecutionTimeout, VariableValue, TriggerValue,
    ScreenCoordinate, PixelColor, ConfidenceScore, ProcessID, FilePath,
    create_execution_timeout, create_confidence_score, create_screen_coordinate,
    create_file_path, ScreenCoordinates, ScreenArea, ColorRGB, NetworkEndpoint
)

# Domain Enumeration Types
from .enumerations import (
    MacroState, MacroLifecycleState, ExecutionMethod, VariableScope, TriggerType, ActionType,
    ApplicationOperation, FileOperation, ClickType, ExecutionStatus,
    ErrorType, LogLevel, TransportType,
    VALID_VARIABLE_SCOPES, VALID_LIFECYCLE_STATES, SUPPORTED_EXECUTION_METHODS,
    TERMINAL_EXECUTION_STATES, RECOVERABLE_ERROR_TYPES
)

# Core Domain Types
from .domain_types import (
    MacroMetadata, TriggerConfiguration, ActionConfiguration,
    MacroDefinition, VariableDefinition, ExecutionContext,
    OperationError, OCRTextExtraction,
    create_macro_metadata, create_execution_context
)

# Type Groups for Convenient Import
IDENTIFIER_TYPES = (
    MacroUUID, MacroName, GroupUUID, GroupName, VariableName,
    TriggerID, ActionID, ApplicationBundleID, ExecutionID, PluginID
)

VALUE_TYPES = (
    MacroExecutionTimeout, VariableValue, TriggerValue,
    ScreenCoordinate, PixelColor, ConfidenceScore, ProcessID, FilePath
)

STRUCTURED_VALUE_TYPES = (
    ScreenCoordinates, ScreenArea, ColorRGB, NetworkEndpoint
)

ENUMERATION_TYPES = (
    MacroState, MacroLifecycleState, ExecutionMethod, VariableScope, TriggerType, ActionType,
    ApplicationOperation, FileOperation, ClickType, ExecutionStatus,
    ErrorType, LogLevel, TransportType
)

DOMAIN_ENTITY_TYPES = (
    MacroMetadata, TriggerConfiguration, ActionConfiguration,
    MacroDefinition, VariableDefinition, ExecutionContext,
    OperationError, OCRTextExtraction
)

COMPOSITE_TYPES = (
    MacroIdentifier, VariableIdentifier
)

# Factory Functions
TYPE_FACTORIES = (
    create_macro_uuid, create_macro_name, create_group_uuid,
    create_variable_name, create_application_bundle_id, create_execution_id,
    create_execution_timeout, create_confidence_score, create_screen_coordinate,
    create_file_path, create_macro_metadata, create_execution_context
)

# Validation Functions  
TYPE_VALIDATORS = (
    is_valid_macro_identifier, is_valid_variable_name_format
)

# All exported types for comprehensive type checking
__all__ = [
    # Identifier Types
    'MacroUUID', 'MacroName', 'GroupUUID', 'GroupName', 'VariableName',
    'TriggerID', 'ActionID', 'ApplicationBundleID', 'ExecutionID', 'PluginID',
    'MacroIdentifier', 'VariableIdentifier',
    
    # Value Types
    'MacroExecutionTimeout', 'VariableValue', 'TriggerValue',
    'ScreenCoordinate', 'PixelColor', 'ConfidenceScore', 'ProcessID', 'FilePath',
    'ScreenCoordinates', 'ScreenArea', 'ColorRGB', 'NetworkEndpoint',
    
    # Enumeration Types
    'MacroState', 'MacroLifecycleState', 'ExecutionMethod', 'VariableScope', 'TriggerType', 'ActionType',
    'ApplicationOperation', 'FileOperation', 'ClickType', 'ExecutionStatus',
    'ErrorType', 'LogLevel', 'TransportType',
    
    # Domain Types
    'MacroMetadata', 'TriggerConfiguration', 'ActionConfiguration',
    'MacroDefinition', 'VariableDefinition', 'ExecutionContext',
    'OperationError', 'OCRTextExtraction',
    
    # Factory Functions
    'create_macro_uuid', 'create_macro_name', 'create_group_uuid',
    'create_variable_name', 'create_application_bundle_id', 'create_execution_id',
    'create_execution_timeout', 'create_confidence_score', 'create_screen_coordinate',
    'create_file_path', 'create_macro_metadata', 'create_execution_context',
    
    # Validation Functions
    'is_valid_macro_identifier', 'is_valid_variable_name_format',
    
    # Constants
    'VALID_VARIABLE_SCOPES', 'VALID_LIFECYCLE_STATES', 'SUPPORTED_EXECUTION_METHODS',
    'TERMINAL_EXECUTION_STATES', 'RECOVERABLE_ERROR_TYPES'
]
