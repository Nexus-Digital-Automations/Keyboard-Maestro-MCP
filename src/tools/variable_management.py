"""Variable management MCP tools with type safety and immutability patterns.

This module provides comprehensive MCP tools for Keyboard Maestro variable operations
including CRUD operations, scope management, and secure password variable handling.
Implements ADDER+ principles with contract-driven development and defensive programming.

Key Features:
- Complete variable CRUD operations with scope enforcement
- Type-safe variable operations with branded types
- Password variable security with memory-only handling
- Instance and local variable scope management
- Contract-driven validation and error handling
"""

from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

from fastmcp import FastMCP
from src.types.domain_types import VariableName, VariableValue
from .types.enumerations import VariableScope
from src.types.results import Result, OperationError, ErrorType
from src.core.variable_operations import VariableOperations, VariableEntry, VariableMetadata, VariableSnapshot
from src.validators.variable_validators import VariableNameValidator, VariableScopeValidator, VariableValueValidator
from src.pure.data_transformations import VariableTransformations, FormatTransformations
from src.core.km_interface import KeyboardMaestroInterface
from src.contracts.decorators import requires, ensures
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def register_variable_tools(mcp: FastMCP, km_interface: KeyboardMaestroInterface) -> None:
    """Register all variable management MCP tools."""
    
    @mcp.tool()
    @requires(lambda name: isinstance(name, str) and len(name) > 0)
    @requires(lambda scope: scope in ['global', 'local', 'instance', 'password'])
    @ensures(lambda result: isinstance(result, dict))
    async def km_get_variable(
        name: str,
        scope: str = 'global',
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Keyboard Maestro variable value with scope enforcement.
        
        Retrieves variable value from specified scope with comprehensive validation
        and type safety. Supports all variable scopes including password variables.
        
        Args:
            name: Variable name following Keyboard Maestro conventions
            scope: Variable scope (global, local, instance, password)
            instance_id: Required for instance-scoped variables
            
        Returns:
            Dict containing variable value, metadata, and operation status
        """
        try:
            # Validate variable name
            name_result = VariableNameValidator.validate_name(name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            variable_name = name_result.unwrap()
            variable_scope = VariableScope(scope)
            
            # Validate scope requirements
            scope_result = VariableScopeValidator.validate_scope_requirements(
                variable_scope, instance_id
            )
            if scope_result.is_failure:
                return {
                    'success': False,
                    'error': scope_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': scope_result._error.suggestion
                }
            
            # Get variable through Keyboard Maestro interface
            variable_result = await km_interface.get_variable(
                variable_name, variable_scope, instance_id
            )
            
            if variable_result.is_failure:
                return {
                    'success': False,
                    'error': variable_result._error.message,
                    'error_type': variable_result._error.error_type.value,
                    'suggestion': variable_result._error.recovery_suggestion
                }
            
            variable_entry = variable_result.unwrap()
            
            # Handle non-existent variable
            if variable_entry is None:
                return {
                    'success': True,
                    'exists': False,
                    'name': name,
                    'scope': scope,
                    'value': None
                }
            
            # Return variable data (exclude actual value for password variables)
            response = {
                'success': True,
                'exists': True,
                'name': variable_entry.metadata.name,
                'scope': variable_entry.metadata.scope.value,
                'created_at': variable_entry.metadata.created_at.isoformat(),
                'modified_at': variable_entry.metadata.modified_at.isoformat(),
                'is_password': variable_entry.metadata.is_password
            }
            
            # Include value for non-password variables
            if not variable_entry.is_password_variable():
                response['value'] = variable_entry.value
            else:
                response['value'] = '<password_protected>'
            
            # Include instance context if applicable
            if variable_entry.metadata.instance_id:
                response['instance_id'] = variable_entry.metadata.instance_id
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting variable {name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check variable name and scope parameters'
            }
    
    @mcp.tool()
    @requires(lambda name: isinstance(name, str) and len(name) > 0)
    @requires(lambda scope: scope in ['global', 'local', 'instance', 'password'])
    @ensures(lambda result: isinstance(result, dict))
    async def km_set_variable(
        name: str,
        value: str,
        scope: str = 'global',
        instance_id: Optional[str] = None,
        is_password: bool = False
    ) -> Dict[str, Any]:
        """Set Keyboard Maestro variable value with validation and scope enforcement.
        
        Sets variable value in specified scope with comprehensive validation,
        type safety, and security handling for password variables.
        
        Args:
            name: Variable name following Keyboard Maestro conventions
            value: Variable value to set
            scope: Variable scope (global, local, instance, password)
            instance_id: Required for instance-scoped variables
            is_password: Whether this is a password variable
            
        Returns:
            Dict containing operation status and variable metadata
        """
        try:
            # Validate variable name
            name_result = VariableNameValidator.validate_name(name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            variable_name = name_result.unwrap()
            variable_scope = VariableScope(scope)
            
            # Auto-detect password variables if not explicitly set
            if not is_password and variable_scope == VariableScope.PASSWORD:
                is_password = True
            elif not is_password:
                is_password = VariableNameValidator.is_password_variable_name(name)
            
            # Validate scope requirements
            scope_result = VariableScopeValidator.validate_scope_requirements(
                variable_scope, instance_id, is_password
            )
            if scope_result.is_failure:
                return {
                    'success': False,
                    'error': scope_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': scope_result._error.suggestion
                }
            
            # Validate variable value
            value_result = VariableValueValidator.validate_value(value, is_password)
            if value_result.is_failure:
                return {
                    'success': False,
                    'error': value_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': value_result._error.suggestion
                }
            
            variable_value = value_result.unwrap()
            
            # Set variable through Keyboard Maestro interface
            set_result = await km_interface.set_variable(
                variable_name, variable_value, variable_scope, instance_id, is_password
            )
            
            if set_result.is_failure:
                return {
                    'success': False,
                    'error': set_result._error.message,
                    'error_type': set_result._error.error_type.value,
                    'suggestion': set_result._error.recovery_suggestion
                }
            
            # Return success response
            response = {
                'success': True,
                'name': name,
                'scope': scope,
                'is_password': is_password,
                'modified_at': datetime.now().isoformat()
            }
            
            # Include instance context if applicable
            if instance_id:
                response['instance_id'] = instance_id
            
            # Don't echo back password values
            if not is_password:
                response['value'] = value
            else:
                response['value'] = '<password_set>'
            
            return response
            
        except Exception as e:
            logger.error(f"Error setting variable {name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check variable name, value, and scope parameters'
            }
    
    @mcp.tool()
    @requires(lambda name: isinstance(name, str) and len(name) > 0)
    @requires(lambda scope: scope in ['global', 'local', 'instance', 'password'])
    @ensures(lambda result: isinstance(result, dict))
    async def km_delete_variable(
        name: str,
        scope: str = 'global',
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete Keyboard Maestro variable with scope enforcement.
        
        Deletes variable from specified scope with validation and confirmation.
        Provides safety checks for password variables and important system variables.
        
        Args:
            name: Variable name to delete
            scope: Variable scope (global, local, instance, password)
            instance_id: Required for instance-scoped variables
            
        Returns:
            Dict containing operation status and deletion confirmation
        """
        try:
            # Validate variable name
            name_result = VariableNameValidator.validate_name(name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            variable_name = name_result.unwrap()
            variable_scope = VariableScope(scope)
            
            # Validate scope requirements
            scope_result = VariableScopeValidator.validate_scope_requirements(
                variable_scope, instance_id
            )
            if scope_result.is_failure:
                return {
                    'success': False,
                    'error': scope_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': scope_result._error.suggestion
                }
            
            # Check if variable exists before deletion
            exists_result = await km_interface.get_variable(
                variable_name, variable_scope, instance_id
            )
            
            if exists_result.is_success and exists_result.unwrap() is None:
                return {
                    'success': True,
                    'existed': False,
                    'name': name,
                    'scope': scope,
                    'message': 'Variable did not exist'
                }
            
            # Delete variable through Keyboard Maestro interface
            delete_result = await km_interface.delete_variable(
                variable_name, variable_scope, instance_id
            )
            
            if delete_result.is_failure:
                return {
                    'success': False,
                    'error': delete_result._error.message,
                    'error_type': delete_result._error.error_type.value,
                    'suggestion': delete_result._error.recovery_suggestion
                }
            
            return {
                'success': True,
                'existed': True,
                'name': name,
                'scope': scope,
                'deleted_at': datetime.now().isoformat(),
                'message': 'Variable deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting variable {name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check variable name and scope parameters'
            }
    
    @mcp.tool()
    @requires(lambda scope: scope in ['global', 'local', 'instance', 'password', 'all'])
    @ensures(lambda result: isinstance(result, dict))
    async def km_list_variables(
        scope: str = 'global',
        name_pattern: Optional[str] = None,
        include_password: bool = False,
        limit: int = 100
    ) -> Dict[str, Any]:
        """List Keyboard Maestro variables with filtering and scope selection.
        
        Retrieves list of variables from specified scope(s) with optional filtering
        by name pattern. Provides comprehensive metadata while respecting security.
        
        Args:
            scope: Variable scope to list (global, local, instance, password, all)
            name_pattern: Optional regex pattern to filter variable names
            include_password: Whether to include password variables in listing
            limit: Maximum number of variables to return
            
        Returns:
            Dict containing variable list with metadata and summary statistics
        """
        try:
            # Get variable snapshot from Keyboard Maestro interface
            if scope == 'all':
                snapshot_result = await km_interface.get_all_variables_snapshot()
            else:
                variable_scope = VariableScope(scope)
                snapshot_result = await km_interface.get_variables_by_scope(variable_scope)
            
            if snapshot_result.is_failure:
                return {
                    'success': False,
                    'error': snapshot_result._error.message,
                    'error_type': snapshot_result._error.error_type.value,
                    'suggestion': snapshot_result._error.recovery_suggestion
                }
            
            snapshot = snapshot_result.unwrap()
            
            # Apply name pattern filtering if specified
            variables = snapshot.variables
            if name_pattern:
                variables = VariableTransformations.filter_variables_by_pattern(
                    snapshot, name_pattern, use_regex=True
                )
            
            # Filter password variables if not included
            if not include_password:
                variables = frozenset(
                    var for var in variables
                    if not var.is_password_variable()
                )
            
            # Apply limit
            limited_variables = list(variables)[:limit]
            
            # Build response with variable information
            variable_list = []
            for var in limited_variables:
                var_info = {
                    'name': var.metadata.name,
                    'scope': var.metadata.scope.value,
                    'created_at': var.metadata.created_at.isoformat(),
                    'modified_at': var.metadata.modified_at.isoformat(),
                    'is_password': var.metadata.is_password
                }
                
                # Include value for non-password variables
                if not var.is_password_variable():
                    var_info['value'] = var.value
                    var_info['value_length'] = len(var.value) if var.value else 0
                else:
                    var_info['value'] = '<password_protected>'
                    var_info['value_length'] = None
                
                # Include instance context if applicable
                if var.metadata.instance_id:
                    var_info['instance_id'] = var.metadata.instance_id
                
                variable_list.append(var_info)
            
            # Generate summary statistics
            summary = VariableTransformations.create_variable_summary(snapshot)
            
            return {
                'success': True,
                'variables': variable_list,
                'total_found': len(variables),
                'total_returned': len(variable_list),
                'scope_filter': scope,
                'name_pattern': name_pattern,
                'include_password': include_password,
                'summary': summary,
                'snapshot_time': snapshot.snapshot_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error listing variables: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check scope and pattern parameters'
            }
    
    @mcp.tool()
    @requires(lambda name: isinstance(name, str) and len(name) > 0)
    @requires(lambda scope: scope in ['global', 'local', 'instance', 'password'])
    @ensures(lambda result: isinstance(result, dict))
    async def km_variable_exists(
        name: str,
        scope: str = 'global',
        instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if Keyboard Maestro variable exists in specified scope.
        
        Quick existence check for variables without retrieving values.
        Useful for conditional logic and validation workflows.
        
        Args:
            name: Variable name to check
            scope: Variable scope (global, local, instance, password)
            instance_id: Required for instance-scoped variables
            
        Returns:
            Dict containing existence status and basic metadata
        """
        try:
            # Validate variable name
            name_result = VariableNameValidator.validate_name(name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            variable_name = name_result.unwrap()
            variable_scope = VariableScope(scope)
            
            # Check existence through Keyboard Maestro interface
            exists_result = await km_interface.variable_exists(
                variable_name, variable_scope, instance_id
            )
            
            if exists_result.is_failure:
                return {
                    'success': False,
                    'error': exists_result._error.message,
                    'error_type': exists_result._error.error_type.value,
                    'suggestion': exists_result._error.recovery_suggestion
                }
            
            exists = exists_result.unwrap()
            
            response = {
                'success': True,
                'exists': exists,
                'name': name,
                'scope': scope
            }
            
            if instance_id:
                response['instance_id'] = instance_id
            
            return response
            
        except Exception as e:
            logger.error(f"Error checking variable existence {name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check variable name and scope parameters'
            }
