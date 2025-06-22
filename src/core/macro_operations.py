"""
Core macro operation logic with contract-driven development.

This module implements the core business logic for macro operations,
separated from MCP tool interfaces for clean architecture and testing.
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

from src.types import (
    MacroIdentifier, MacroUUID, MacroName, GroupUUID, ExecutionMethod
)
from src.types.domain_types import MacroExecutionResult, MacroCreationData, MacroModificationData
from src.contracts.decorators import requires, ensures
from src.contracts.validators import (
    is_valid_macro_identifier, is_valid_timeout, 
    is_valid_execution_method, is_valid_macro_structure
)
from src.validators.macro_validators import MacroValidator
from src.core.km_interface import KMInterface
from src.core.km_error_handler import KMErrorHandler

logger = logging.getLogger(__name__)


class MacroOperationStatus(Enum):
    """Status enumeration for macro operations."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class MacroInfo:
    """Complete macro information structure."""
    uuid: MacroUUID
    name: MacroName
    group_uuid: GroupUUID
    enabled: bool
    color: Optional[str] = None
    notes: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    last_used: Optional[str] = None
    trigger_count: int = 0
    action_count: int = 0


class MacroOperations:
    """Core macro operations with contract enforcement."""
    
    def __init__(self, km_interface: KMInterface, error_handler: KMErrorHandler):
        """Initialize macro operations with required dependencies."""
        self.km_interface = km_interface
        self.error_handler = error_handler
        self.validator = MacroValidator()
    
    @requires(lambda self, identifier: is_valid_macro_identifier(identifier))
    @requires(lambda self, identifier, timeout: is_valid_timeout(timeout))
    @requires(lambda self, identifier, timeout, method: is_valid_execution_method(method))
    @ensures(lambda result: result.status != MacroOperationStatus.SUCCESS or result.execution_time >= 0)
    async def execute_macro(
        self,
        identifier: MacroIdentifier,
        trigger_value: Optional[str] = None,
        method: ExecutionMethod = ExecutionMethod.APPLESCRIPT,
        timeout: int = 30
    ) -> MacroExecutionResult:
        """
        Execute a Keyboard Maestro macro with comprehensive error handling.
        
        Preconditions:
        - identifier must be valid (non-empty string or valid UUID)
        - timeout must be positive and reasonable (1-300 seconds)
        - method must be supported execution method
        
        Postconditions:
        - Result indicates success or provides detailed error information
        - Execution time is non-negative for successful operations
        """
        try:
            logger.info(f"Executing macro: {identifier} via {method.value}")
            
            # Validate macro exists
            if not await self._macro_exists(identifier):
                return MacroExecutionResult(
                    status=MacroOperationStatus.NOT_FOUND,
                    error_details=f"Macro not found: {identifier}",
                    execution_time=0
                )
            
            # Execute via appropriate method
            result = await self._execute_via_method(
                identifier, trigger_value, method, timeout
            )
            
            logger.info(f"Macro execution completed: {result.status.value}")
            return result
            
        except Exception as e:
            return await self.error_handler.handle_execution_error(e, identifier, method)
    
    @requires(lambda self, macro_data: is_valid_macro_structure(macro_data))
    @requires(lambda self, macro_data: len(macro_data.name) > 0)
    @ensures(lambda result: result.status != MacroOperationStatus.SUCCESS or result.macro_uuid is not None)
    async def create_macro(
        self,
        macro_data: MacroCreationData
    ) -> MacroExecutionResult:
        """
        Create a new Keyboard Maestro macro with validation.
        
        Preconditions:
        - macro_data must have valid structure and non-empty name
        - target group must exist if specified
        - macro name must be unique within target group
        
        Postconditions:
        - Success implies macro UUID is assigned
        - Failure provides specific error classification
        """
        try:
            logger.info(f"Creating macro: {macro_data.name}")
            
            # Validate creation data
            validation_result = await self.validator.validate_creation_data(macro_data)
            if not validation_result.is_valid:
                return MacroExecutionResult(
                    status=MacroOperationStatus.FAILED,
                    error_details=validation_result.error_message
                )
            
            # Create macro via Keyboard Maestro interface
            macro_uuid = await self.km_interface.create_macro(macro_data)
            
            logger.info(f"Macro created successfully: {macro_uuid}")
            return MacroExecutionResult(
                status=MacroOperationStatus.SUCCESS,
                macro_uuid=macro_uuid
            )
            
        except Exception as e:
            return await self.error_handler.handle_creation_error(e, macro_data)
    
    @requires(lambda self, macro_id: is_valid_macro_identifier(macro_id))
    async def get_macro_info(self, macro_id: MacroIdentifier) -> Optional[MacroInfo]:
        """Retrieve comprehensive macro information."""
        try:
            if not await self._macro_exists(macro_id):
                return None
            
            info_dict = await self.km_interface.get_macro_properties(macro_id)
            return MacroInfo(**info_dict)
            
        except Exception as e:
            logger.error(f"Failed to get macro info: {e}")
            return None
    
    @requires(lambda self, macro_id: is_valid_macro_identifier(macro_id))
    async def modify_macro(
        self,
        macro_id: MacroIdentifier,
        updates: MacroModificationData
    ) -> MacroExecutionResult:
        """Modify existing macro properties with validation."""
        try:
            logger.info(f"Modifying macro: {macro_id}")
            
            # Validate macro exists
            if not await self._macro_exists(macro_id):
                return MacroExecutionResult(
                    status=MacroOperationStatus.NOT_FOUND,
                    error_details=f"Macro not found: {macro_id}"
                )
            
            # Validate modification data
            validation_result = await self.validator.validate_modification_data(
                macro_id, updates
            )
            if not validation_result.is_valid:
                return MacroExecutionResult(
                    status=MacroOperationStatus.FAILED,
                    error_details=validation_result.error_message
                )
            
            # Apply modifications
            success = await self.km_interface.modify_macro(macro_id, updates)
            
            if success:
                logger.info(f"Macro modified successfully: {macro_id}")
                return MacroExecutionResult(status=MacroOperationStatus.SUCCESS)
            else:
                return MacroExecutionResult(
                    status=MacroOperationStatus.FAILED,
                    error_details="Modification failed"
                )
                
        except Exception as e:
            return await self.error_handler.handle_modification_error(e, macro_id, updates)
    
    async def list_macros(
        self,
        group_id: Optional[GroupUUID] = None,
        enabled_only: bool = False
    ) -> List[MacroInfo]:
        """List macros with optional filtering."""
        try:
            macro_list = await self.km_interface.list_macros(group_id, enabled_only)
            return [MacroInfo(**macro_dict) for macro_dict in macro_list]
            
        except Exception as e:
            logger.error(f"Failed to list macros: {e}")
            return []
    
    async def delete_macro(self, macro_id: MacroIdentifier) -> MacroExecutionResult:
        """Delete a macro with safety checks."""
        try:
            logger.info(f"Deleting macro: {macro_id}")
            
            if not await self._macro_exists(macro_id):
                return MacroExecutionResult(
                    status=MacroOperationStatus.NOT_FOUND,
                    error_details=f"Macro not found: {macro_id}"
                )
            
            success = await self.km_interface.delete_macro(macro_id)
            
            if success:
                logger.info(f"Macro deleted successfully: {macro_id}")
                return MacroExecutionResult(status=MacroOperationStatus.SUCCESS)
            else:
                return MacroExecutionResult(
                    status=MacroOperationStatus.FAILED,
                    error_details="Deletion failed"
                )
                
        except Exception as e:
            return await self.error_handler.handle_deletion_error(e, macro_id)
    
    # Private helper methods
    
    async def _macro_exists(self, identifier: MacroIdentifier) -> bool:
        """Check if macro exists in Keyboard Maestro."""
        try:
            return await self.km_interface.macro_exists(identifier)
        except Exception:
            return False
    
    async def _execute_via_method(
        self,
        identifier: MacroIdentifier,
        trigger_value: Optional[str],
        method: ExecutionMethod,
        timeout: int
    ) -> MacroExecutionResult:
        """Execute macro using specified method."""
        execution_methods = {
            ExecutionMethod.APPLESCRIPT: self.km_interface.execute_via_applescript,
            ExecutionMethod.URL: self.km_interface.execute_via_url,
            ExecutionMethod.WEB_API: self.km_interface.execute_via_web_api,
            ExecutionMethod.REMOTE: self.km_interface.execute_via_remote
        }
        
        execute_func = execution_methods.get(method)
        if not execute_func:
            return MacroExecutionResult(
                status=MacroOperationStatus.FAILED,
                error_details=f"Unsupported execution method: {method}"
            )
        
        return await execute_func(identifier, trigger_value, timeout)
