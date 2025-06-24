# src/boundaries/__init__.py
"""
Security Boundaries Public API for Keyboard Maestro MCP Server.

This module provides a clean interface to the comprehensive boundary protection
system including security validators, plugin boundaries, and multi-layered
defensive programming patterns.

Key Exports:
- Plugin security boundaries and validation
- General security boundary management
- Boundary validation results and contexts
- Convenience functions for boundary checking
"""

# Core Security Boundaries
from .security_boundaries import (
    SecurityContext,
    SecurityBoundaryResult,
    ComprehensiveSecurityBoundary,
    DEFAULT_SECURITY_BOUNDARY
)

# System Boundaries
from .system_boundaries import (
    SystemBoundaryManager,
    validate_system_permissions,
    check_resource_limits,
    validate_file_operations,
    DEFAULT_SYSTEM_BOUNDARY
)

# Keyboard Maestro Boundaries
from .km_boundaries import (
    BoundaryViolationType,
    KMBoundaryValidator,
    validate_km_integration,
    check_applescript_permissions,
    validate_macro_operations,
    DEFAULT_KM_BOUNDARY
)

# Plugin Security Boundaries
from .plugin_boundaries import (
    ComprehensivePluginBoundary,
    PluginSecurityValidator,
    ScriptContentSecurityValidator,
    PluginInstallationBoundary,
    PluginSecurityAnalysis,
    PluginThreatType,
    SecurityPattern,
    validate_plugin_security,
    validate_plugin_installation_security,
    DEFAULT_PLUGIN_BOUNDARY
)

# Permission Management
from .permission_checker import (
    PermissionChecker,
    validate_operation_permissions,
    check_user_permissions,
    DEFAULT_PERMISSION_CHECKER
)

# Convenience Functions

def validate_all_boundaries(operation_context: dict) -> SecurityBoundaryResult:
    """Validate operation against all relevant security boundaries.
    
    Args:
        operation_context: Context containing operation details
        
    Returns:
        Consolidated boundary validation result
    """
    return DEFAULT_SECURITY_MANAGER.validate_comprehensive_boundaries(operation_context)


def create_plugin_security_context(plugin_data) -> SecurityContext:
    """Create security context for plugin operations.
    
    Args:
        plugin_data: Plugin creation or execution data
        
    Returns:
        Security context for plugin operations
    """
    return DEFAULT_PLUGIN_BOUNDARY.create_security_context(plugin_data)


def validate_comprehensive_security(operation_type: str, **kwargs) -> SecurityBoundaryResult:
    """Validate operation against appropriate security boundaries.
    
    Args:
        operation_type: Type of operation being performed
        **kwargs: Operation-specific parameters
        
    Returns:
        Security validation result
    """
    if operation_type == "plugin_creation":
        return DEFAULT_PLUGIN_BOUNDARY.validate_plugin_creation(kwargs.get('plugin_data'))
    elif operation_type == "plugin_installation":
        return DEFAULT_PLUGIN_BOUNDARY.validate_plugin_installation(
            kwargs.get('plugin_id'), 
            kwargs.get('bundle_path'), 
            kwargs.get('target_dir')
        )
    elif operation_type == "system_operation":
        return DEFAULT_SYSTEM_BOUNDARY.validate_system_operation(kwargs)
    elif operation_type == "km_integration":
        return DEFAULT_KM_BOUNDARY.validate_km_operation(kwargs)
    else:
        return DEFAULT_SECURITY_MANAGER.validate_generic_operation(operation_type, kwargs)


# Package information
__version__ = "1.0.0"
__author__ = "Keyboard Maestro MCP Server"
__description__ = "Security Boundary Protection System"

# Public API exports
__all__ = [
    # Core Security Boundaries
    'SecurityContext', 'SecurityBoundaryResult', 'ComprehensiveSecurityBoundary',
    'BoundaryViolationType', 'DEFAULT_SECURITY_BOUNDARY',
    
    # System Boundaries
    'SystemBoundaryManager', 'validate_system_permissions', 'check_resource_limits',
    'validate_file_operations', 'DEFAULT_SYSTEM_BOUNDARY',
    
    # Keyboard Maestro Boundaries
    'KMBoundaryValidator', 'validate_km_integration', 'check_applescript_permissions',
    'validate_macro_operations', 'DEFAULT_KM_BOUNDARY',
    
    # Plugin Security Boundaries
    'ComprehensivePluginBoundary', 'PluginSecurityValidator', 'ScriptContentSecurityValidator',
    'PluginInstallationBoundary', 'PluginSecurityAnalysis', 'PluginThreatType', 'SecurityPattern',
    'validate_plugin_security', 'validate_plugin_installation_security', 'DEFAULT_PLUGIN_BOUNDARY',
    
    # Permission Management
    'PermissionChecker', 'validate_operation_permissions', 'check_user_permissions',
    'DEFAULT_PERMISSION_CHECKER',
    
    # Convenience Functions
    'validate_all_boundaries', 'create_plugin_security_context', 'validate_comprehensive_security'
]
