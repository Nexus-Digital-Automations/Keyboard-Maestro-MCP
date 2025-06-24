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

# Plugin Type System
from .plugin_types import (
    PluginID, PluginName, PluginBundleID, ScriptContent, PluginPath, SecurityHash,
    PluginSecurityContext, PluginResourceLimits, PluginIdentifier,
    create_plugin_id, create_plugin_name, create_script_content, create_security_hash,
    create_memory_limit, create_timeout_seconds, create_risk_score,
    plugin_id_to_bundle_id, validate_plugin_compatibility
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
    PluginScriptType, PluginOutputHandling, PluginLifecycleState, PluginSecurityLevel,
    VALID_VARIABLE_SCOPES, VALID_LIFECYCLE_STATES, SUPPORTED_EXECUTION_METHODS,
    TERMINAL_EXECUTION_STATES, RECOVERABLE_ERROR_TYPES
)

# Core Domain Types
from .domain_types import (
    MacroMetadata, TriggerConfiguration, ActionConfiguration,
    MacroDefinition, VariableDefinition, ExecutionContext,
    OperationError, OCRTextExtraction,
    PluginCreationData, PluginMetadata, PluginValidationResult, PluginParameter,
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
    
    # Plugin Identifier Types
    'PluginID', 'PluginName', 'PluginBundleID', 'ScriptContent', 'PluginPath', 'SecurityHash',
    'PluginSecurityContext', 'PluginResourceLimits', 'PluginIdentifier',
    
    # Value Types
    'MacroExecutionTimeout', 'VariableValue', 'TriggerValue',
    'ScreenCoordinate', 'PixelColor', 'ConfidenceScore', 'ProcessID', 'FilePath',
    'ScreenCoordinates', 'ScreenArea', 'ColorRGB', 'NetworkEndpoint',
    
    # Enumeration Types
    'MacroState', 'MacroLifecycleState', 'ExecutionMethod', 'VariableScope', 'TriggerType', 'ActionType',
    'ApplicationOperation', 'FileOperation', 'ClickType', 'ExecutionStatus',
    'ErrorType', 'LogLevel', 'TransportType',
    'PluginScriptType', 'PluginOutputHandling', 'PluginLifecycleState', 'PluginSecurityLevel',
    
    # Domain Types
    'MacroMetadata', 'TriggerConfiguration', 'ActionConfiguration',
    'MacroDefinition', 'VariableDefinition', 'ExecutionContext',
    'OperationError', 'OCRTextExtraction',
    'PluginCreationData', 'PluginMetadata', 'PluginValidationResult', 'PluginParameter',
    
    # Factory Functions
    'create_macro_uuid', 'create_macro_name', 'create_group_uuid',
    'create_variable_name', 'create_application_bundle_id', 'create_execution_id',
    'create_execution_timeout', 'create_confidence_score', 'create_screen_coordinate',
    'create_file_path', 'create_macro_metadata', 'create_execution_context',
    
    # Plugin Factory Functions
    'create_plugin_id', 'create_plugin_name', 'create_script_content', 'create_security_hash',
    'create_memory_limit', 'create_timeout_seconds', 'create_risk_score',
    'plugin_id_to_bundle_id', 'validate_plugin_compatibility',
    
    # Validation Functions
    'is_valid_macro_identifier', 'is_valid_variable_name_format',
    
    # Constants
    'VALID_VARIABLE_SCOPES', 'VALID_LIFECYCLE_STATES', 'SUPPORTED_EXECUTION_METHODS',
    'TERMINAL_EXECUTION_STATES', 'RECOVERABLE_ERROR_TYPES'
]
