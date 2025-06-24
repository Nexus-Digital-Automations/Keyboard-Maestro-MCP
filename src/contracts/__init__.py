# Contract Framework Public API  
# Target: <100 lines - Clean exports for contract specification framework

"""
Public API for the Contract Specification Framework.

This module provides a clean interface to the comprehensive contract framework
including decorators, validators, exceptions, and invariants. Exports the most
commonly used functions and classes for easy import and usage throughout the
Keyboard Maestro MCP Server codebase.

Key Exports:
- Contract decorators: requires, ensures, invariant
- Validation functions: domain-specific validators
- Exception classes: contract violation hierarchy  
- Invariant checking: system invariant utilities
- Convenience functions: common contract patterns
"""

# Contract Decorators
from .decorators import (
    requires,
    ensures, 
    invariant,
    ContractState
)

# Contract Exceptions
from .exceptions import (
    ContractViolation,
    PreconditionViolation,
    PostconditionViolation,
    InvariantViolation,
    TypeSafetyViolation,
    SecurityBoundaryViolation,
    ViolationType,
    ViolationContext,
    create_precondition_violation,
    create_postcondition_violation,
    create_invariant_violation
)

# Core Validators
from .validators import (
    # Keyboard Maestro Domain Validators
    is_valid_macro_identifier,
    is_valid_macro_name,
    is_valid_variable_name,
    is_valid_group_name,
    is_valid_execution_timeout,
    validate_variable_scope,
    
    # Screen and Coordinate Validators
    is_valid_screen_coordinates,
    is_valid_screen_area,
    is_valid_confidence_score,
    
    # File System and Application Validators
    is_valid_file_path,
    file_exists_and_readable,
    directory_exists_and_writable,
    is_valid_application_identifier,
    
    # Security and Safety Validators
    is_safe_script_content,
    is_valid_email_address,
    is_valid_phone_number,
    
    # Business Logic Validators
    is_valid_macro_structure,
    name_is_unique_in_group,
    group_exists,
    macro_exists,
    
    # Composite Validators
    validate_macro_creation_data,
    validate_file_operation_data
)

# Plugin Contracts
from .plugin_contracts import (
    plugin_creation_contract,
    plugin_installation_contract,
    plugin_validation_contract,
    plugin_lifecycle_contract,
    plugin_removal_contract,
    plugin_security_contract,
    is_valid_plugin_structure,
    is_safe_script_content,
    plugin_exists,
    has_valid_bundle_structure,
    CONTRACT_ERROR_MESSAGES,
    get_contract_error_message
)

# System Invariants
from .invariants import (
    system_invariant_checker,
    InvariantDefinition,
    InvariantSeverity,
    check_macro_integrity,
    check_variable_scope,
    check_permission_boundaries,
    check_all_system_invariants
)


# Convenience contract creation functions

def macro_contract(name_validator=True, timeout_validator=True, existence_check=True):
    """Create standard macro operation contract decorators."""
    def decorator(func):
        # Apply multiple contract decorators for macro operations
        if name_validator:
            func = requires(lambda identifier: is_valid_macro_identifier(identifier))(func)
        if timeout_validator:
            func = requires(lambda timeout=30: is_valid_execution_timeout(timeout))(func)
        if existence_check:
            func = requires(lambda identifier: macro_exists(str(identifier)))(func)
        
        # Add postcondition for successful execution
        func = ensures(lambda result: result.success or result.error_details is not None)(func)
        
        return func
    return decorator


def variable_contract(name_validator=True, scope_validator=True):
    """Create standard variable operation contract decorators."""
    def decorator(func):
        if name_validator:
            func = requires(lambda name: is_valid_variable_name(name))(func)
        if scope_validator:
            func = requires(lambda scope, instance_id=None: validate_variable_scope(scope, instance_id))(func)
        
        # Add postcondition for scope compliance
        func = ensures(lambda result: result.scope_compliant)(func)
        
        return func
    return decorator


def file_operation_contract(path_validator=True, permission_check=True):
    """Create standard file operation contract decorators."""
    def decorator(func):
        if path_validator:
            func = requires(lambda path: is_valid_file_path(path))(func)
        if permission_check:
            func = requires(lambda path: file_exists_and_readable(path))(func)
        
        # Add postcondition for operation success
        func = ensures(lambda result: result.success or result.error_type is not None)(func)
        
        return func
    return decorator


def security_contract(script_safety=True, boundary_check=True):
    """Create security-focused contract decorators."""
    def decorator(func):
        if script_safety:
            func = requires(lambda script: is_safe_script_content(script))(func)
        if boundary_check:
            func = requires(lambda operation: check_permission_boundaries())(func)
        
        # Add security boundary invariant
        func = invariant(lambda: check_permission_boundaries())(func)
        
        return func
    return decorator


# Package version and metadata
__version__ = "1.0.0"
__author__ = "Keyboard Maestro MCP Server"
__description__ = "Contract Specification Framework for Design by Contract implementation"

# Public API - what gets exported when someone does "from src.contracts import *"
__all__ = [
    # Decorators
    'requires', 'ensures', 'invariant', 'ContractState',
    
    # Exceptions
    'ContractViolation', 'PreconditionViolation', 'PostconditionViolation',
    'InvariantViolation', 'TypeSafetyViolation', 'SecurityBoundaryViolation',
    'ViolationType', 'ViolationContext',
    
    # Exception Factories
    'create_precondition_violation', 'create_postcondition_violation', 'create_invariant_violation',
    
    # Core Validators
    'is_valid_macro_identifier', 'is_valid_macro_name', 'is_valid_variable_name',
    'is_valid_screen_coordinates', 'is_valid_file_path', 'is_safe_script_content',
    'validate_macro_creation_data', 'validate_file_operation_data',
    
    # Plugin Contracts
    'plugin_creation_contract', 'plugin_installation_contract', 'plugin_validation_contract',
    'plugin_lifecycle_contract', 'plugin_removal_contract', 'plugin_security_contract',
    'is_valid_plugin_structure', 'plugin_exists', 'has_valid_bundle_structure',
    'CONTRACT_ERROR_MESSAGES', 'get_contract_error_message',
    
    # Invariants
    'system_invariant_checker', 'InvariantDefinition', 'InvariantSeverity',
    'check_macro_integrity', 'check_variable_scope', 'check_permission_boundaries',
    'check_all_system_invariants',
    
    # Convenience Contracts
    'macro_contract', 'variable_contract', 'file_operation_contract', 'security_contract'
]
