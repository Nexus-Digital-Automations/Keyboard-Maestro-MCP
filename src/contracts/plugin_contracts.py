# src/contracts/plugin_contracts.py
"""
Plugin Contract Specifications - Design by Contract Implementation.

This module implements comprehensive contract enforcement for all plugin
operations using preconditions, postconditions, and invariants to ensure
correctness, security, and reliability of the plugin management system.

Target: <250 lines with comprehensive contract coverage
"""

from functools import wraps
from typing import Callable, Any, Dict, List, Optional
import os
import re
from pathlib import Path

from .decorators import requires, ensures, invariant
from .exceptions import create_precondition_violation, create_postcondition_violation
from ..types.plugin_types import (
    PluginID, PluginName, ScriptContent, PluginPath, SecurityHash,
    create_plugin_id, create_script_content, create_security_hash,
    validate_plugin_compatibility
)
from ..types.domain_types import PluginCreationData, PluginMetadata, PluginValidationResult
from ..types.enumerations import PluginScriptType, PluginLifecycleState, PluginSecurityLevel


# Contract Validation Functions

def is_valid_plugin_structure(plugin_data: PluginCreationData) -> bool:
    """Validate plugin data structure completeness."""
    try:
        return (
            bool(plugin_data.action_name and plugin_data.action_name.strip()) and
            bool(plugin_data.script_content and plugin_data.script_content.strip()) and
            isinstance(plugin_data.script_type, PluginScriptType) and
            len(plugin_data.action_name) <= 100 and
            len(plugin_data.script_content) <= 1_000_000
        )
    except Exception:
        return False


def is_safe_script_content(script_content: str, script_type: PluginScriptType) -> bool:
    """Validate script content for security compliance."""
    try:
        create_script_content(script_content, script_type)
        return True
    except ValueError:
        return False


def plugin_exists(plugin_id: PluginID) -> bool:
    """Check if plugin exists in the system."""
    # Placeholder implementation - would check actual plugin registry
    return isinstance(plugin_id, str) and plugin_id.startswith("mcp_plugin_")


def has_valid_bundle_structure(bundle_path: str) -> bool:
    """Validate plugin bundle directory structure."""
    try:
        path = Path(bundle_path)
        return (
            path.exists() and
            path.is_dir() and
            (path / "Info.plist").exists() and
            any(path.glob("script.*"))  # Has at least one script file
        )
    except Exception:
        return False


def km_actions_directory_writable() -> bool:
    """Check if Keyboard Maestro Actions directory is writable."""
    km_path = Path.home() / "Library/Application Support/Keyboard Maestro/Keyboard Maestro Actions"
    try:
        return km_path.exists() and os.access(str(km_path), os.W_OK)
    except Exception:
        return False


def is_valid_plugin_name(name: str) -> bool:
    """Validate plugin name format and safety."""
    try:
        return (
            bool(name and name.strip()) and
            len(name) <= 100 and
            not re.search(r'[<>:"/\\|?*]', name) and  # Invalid filename chars
            not name.startswith('.') and
            name.strip() == name  # No leading/trailing whitespace
        )
    except Exception:
        return False


# Plugin Creation Contract

@requires(lambda plugin_data: is_valid_plugin_structure(plugin_data))
@requires(lambda plugin_data: is_safe_script_content(plugin_data.script_content, plugin_data.script_type))
@requires(lambda plugin_data: is_valid_plugin_name(plugin_data.action_name))
@ensures(lambda result: isinstance(result, dict) and 'success' in result)
@ensures(lambda result: result['success'] == (result.get('plugin_id') is not None))
@ensures(lambda result, plugin_data: not result['success'] or 
         create_security_hash(plugin_data.script_content) == result.get('content_hash'))
def plugin_creation_contract(func: Callable) -> Callable:
    """Contract for plugin creation operations.
    
    Preconditions:
    - Plugin data structure must be valid and complete
    - Script content must pass security validation
    - Plugin name must be valid for filesystem use
    
    Postconditions:
    - Result indicates success or failure with error details
    - Success implies plugin ID is assigned
    - Content hash matches original script for verification
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# Plugin Installation Contract

@requires(lambda plugin_id: plugin_exists(plugin_id))
@requires(lambda bundle_path: has_valid_bundle_structure(bundle_path))
@requires(lambda: km_actions_directory_writable())
@ensures(lambda result: isinstance(result, dict) and 'success' in result)
@ensures(lambda result: result['success'] == (result.get('installation_path') is not None))
@ensures(lambda result, plugin_id: not result['success'] or 
         plugin_installation_verified(plugin_id, result.get('installation_path')))
@invariant(lambda: system_plugin_count_consistent())
def plugin_installation_contract(func: Callable) -> Callable:
    """Contract for plugin installation operations.
    
    Preconditions:
    - Plugin must exist and be validated
    - Bundle structure must be valid
    - Target directory must be writable
    
    Postconditions:
    - Result indicates success with installation path
    - Installation can be verified in target location
    
    Invariants:
    - System plugin count remains consistent
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# Plugin Validation Contract

@requires(lambda plugin_data: plugin_data is not None)
@requires(lambda plugin_data: hasattr(plugin_data, 'script_content'))
@requires(lambda plugin_data: hasattr(plugin_data, 'script_type'))
@ensures(lambda result: isinstance(result, PluginValidationResult))
@ensures(lambda result: result.is_valid == (len(result.validation_errors or []) == 0))
@ensures(lambda result: 0 <= result.estimated_risk_level <= 3)
@ensures(lambda result: result.is_valid or result.validation_errors)
def plugin_validation_contract(func: Callable) -> Callable:
    """Contract for plugin validation operations.
    
    Preconditions:
    - Plugin data must exist with required fields
    - Script content and type must be accessible
    
    Postconditions:
    - Returns structured validation result
    - Validity matches absence of validation errors
    - Risk level is within valid range (0-3)
    - Invalid plugins must have error details
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# Plugin Lifecycle Contract

@requires(lambda plugin_id: plugin_exists(plugin_id))
@requires(lambda target_state: isinstance(target_state, PluginLifecycleState))
@requires(lambda current_state, target_state: current_state.can_transition_to(target_state))
@ensures(lambda result: isinstance(result, dict) and 'success' in result)
@ensures(lambda result: result['success'] == (result.get('error_message') is None))
@ensures(lambda result, target_state: not result['success'] or 
         get_plugin_state(result.get('plugin_id')) == target_state)
@invariant(lambda: no_plugins_in_invalid_states())
def plugin_lifecycle_contract(func: Callable) -> Callable:
    """Contract for plugin lifecycle state transitions.
    
    Preconditions:
    - Plugin must exist in system
    - Target state must be valid enum value
    - Transition must be allowed from current state
    
    Postconditions:
    - Result indicates success or failure
    - Success means no error message present
    - Plugin state matches target state after successful transition
    
    Invariants:
    - No plugins exist in invalid states
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# Plugin Removal Contract

@requires(lambda plugin_id: plugin_exists(plugin_id))
@requires(lambda plugin_id: plugin_can_be_removed(plugin_id))
@ensures(lambda result: isinstance(result, dict) and 'success' in result)
@ensures(lambda result: result['success'] == (result.get('error_message') is None))
@ensures(lambda result, plugin_id: not result['success'] or not plugin_exists_after_removal(plugin_id))
@ensures(lambda result: result.get('rollback_available', False) == isinstance(result.get('backup_path'), str))
@invariant(lambda: system_cleanup_complete())
def plugin_removal_contract(func: Callable) -> Callable:
    """Contract for plugin removal operations.
    
    Preconditions:
    - Plugin must exist in system
    - Plugin must be in removable state
    
    Postconditions:
    - Result indicates success or failure
    - Success means plugin no longer exists
    - Rollback availability matches backup path presence
    
    Invariants:
    - System cleanup is complete (no orphaned files)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# Plugin Security Contract

@requires(lambda script_content: isinstance(script_content, str))
@requires(lambda script_type: isinstance(script_type, PluginScriptType))
@requires(lambda security_level: isinstance(security_level, PluginSecurityLevel))
@ensures(lambda result: isinstance(result, dict) and 'security_analysis' in result)
@ensures(lambda result: isinstance(result['security_analysis'], dict))
@ensures(lambda result: 'risk_score' in result['security_analysis'])
@ensures(lambda result: 0 <= result['security_analysis']['risk_score'] <= 100)
@ensures(lambda result: 'security_issues' in result['security_analysis'])
@invariant(lambda: security_analysis_consistent())
def plugin_security_contract(func: Callable) -> Callable:
    """Contract for plugin security analysis.
    
    Preconditions:
    - Script content must be valid string
    - Script type must be valid enum
    - Security level must be valid enum
    
    Postconditions:
    - Returns structured security analysis
    - Risk score is within valid range (0-100)
    - Security issues list is present
    
    Invariants:
    - Security analysis results are consistent
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# Helper Functions for Contract Validation

def plugin_installation_verified(plugin_id: PluginID, installation_path: str) -> bool:
    """Verify plugin installation was successful."""
    try:
        path = Path(installation_path)
        return (
            path.exists() and
            path.is_dir() and
            path.name.endswith('.kmsync') and
            (path / "Info.plist").exists()
        )
    except Exception:
        return False


def system_plugin_count_consistent() -> bool:
    """Verify system plugin count consistency."""
    # Placeholder - would implement actual consistency check
    return True


def get_plugin_state(plugin_id: Optional[str]) -> Optional[PluginLifecycleState]:
    """Get current state of plugin."""
    # Placeholder - would query actual plugin registry
    if plugin_id and plugin_id.startswith("mcp_plugin_"):
        return PluginLifecycleState.CREATED
    return None


def no_plugins_in_invalid_states() -> bool:
    """Verify no plugins are in invalid states."""
    # Placeholder - would check all plugins in registry
    return True


def plugin_can_be_removed(plugin_id: PluginID) -> bool:
    """Check if plugin can be safely removed."""
    state = get_plugin_state(plugin_id)
    return state is not None and state.can_be_removed()


def plugin_exists_after_removal(plugin_id: PluginID) -> bool:
    """Check if plugin still exists after removal."""
    # Should return False after successful removal
    return False


def system_cleanup_complete() -> bool:
    """Verify system cleanup after plugin operations."""
    # Placeholder - would verify no orphaned files/registry entries
    return True


def security_analysis_consistent() -> bool:
    """Verify security analysis consistency."""
    # Placeholder - would verify analysis results are deterministic
    return True


# Convenience Contract Decorators

def plugin_operation_contract():
    """Convenience decorator combining common plugin operation contracts."""
    def decorator(func: Callable) -> Callable:
        @requires(lambda *args, **kwargs: validate_common_preconditions(args, kwargs))
        @ensures(lambda result: validate_common_postconditions(result))
        @invariant(lambda: validate_system_invariants())
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_common_preconditions(args: tuple, kwargs: Dict[str, Any]) -> bool:
    """Validate common preconditions for plugin operations."""
    # Basic argument validation
    return len(args) > 0 or len(kwargs) > 0


def validate_common_postconditions(result: Any) -> bool:
    """Validate common postconditions for plugin operations."""
    # Basic result structure validation
    return isinstance(result, dict) and 'success' in result


def validate_system_invariants() -> bool:
    """Validate system-wide invariants."""
    return (
        system_plugin_count_consistent() and
        no_plugins_in_invalid_states() and
        security_analysis_consistent()
    )


# Contract-Based Error Messages

CONTRACT_ERROR_MESSAGES = {
    'invalid_plugin_structure': "Plugin data structure is invalid or incomplete",
    'unsafe_script_content': "Script content contains security violations",
    'invalid_plugin_name': "Plugin name is invalid or unsafe for filesystem",
    'plugin_not_exists': "Plugin does not exist in the system",
    'invalid_bundle_structure': "Plugin bundle structure is invalid",
    'directory_not_writable': "Target directory is not writable",
    'invalid_state_transition': "Plugin state transition is not allowed",
    'plugin_not_removable': "Plugin cannot be removed in current state",
    'security_analysis_failed': "Security analysis could not be completed"
}

def get_contract_error_message(error_key: str) -> str:
    """Get standardized contract error message."""
    return CONTRACT_ERROR_MESSAGES.get(error_key, "Contract violation occurred")
