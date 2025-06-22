"""
Macro execution MCP tools with comprehensive error handling.

This module provides MCP tools for executing Keyboard Maestro macros
through various interfaces with contract-driven validation.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP
from fastmcp.tools import tool

from src.types.domain_types import MacroIdentifier, ExecutionMethod
from src.core.macro_operations import MacroOperations, MacroOperationStatus
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_macro_identifier, is_valid_timeout
from src.validators.macro_validators import ValidationResult

logger = logging.getLogger(__name__)


class MacroExecutionTools:
    """MCP tools for macro execution operations."""
    
    def __init__(self, macro_operations: MacroOperations):
        """Initialize with macro operations dependency."""
        self.macro_operations = macro_operations
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register all macro execution tools with the MCP server."""
        mcp_server.tool()(self.execute_macro)
        mcp_server.tool()(self.execute_macro_with_timeout)
        mcp_server.tool()(self.execute_macro_via_method)
        mcp_server.tool()(self.test_macro_execution)
        
        logger.info("Macro execution tools registered")
    
    async def execute_macro(
        self,
        identifier: str,
        trigger_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a Keyboard Maestro macro using default settings.
        
        Args:
            identifier: Macro name or UUID
            trigger_value: Optional parameter value for parameterized macros
            
        Returns:
            Execution result with status and details
        """
        try:
            # Validate input
            if not is_valid_macro_identifier(identifier):
                return {
                    "success": False,
                    "error": "Invalid macro identifier",
                    "error_code": "INVALID_IDENTIFIER"
                }
            
            # Execute macro
            result = await self.macro_operations.execute_macro(
                identifier=identifier,
                trigger_value=trigger_value,
                method=ExecutionMethod.APPLESCRIPT,
                timeout=30
            )
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "error": result.error_details if result.error_details else None,
                "macro_uuid": result.macro_uuid
            }
            
        except Exception as e:
            logger.error(f"Macro execution failed: {e}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            }
    
    async def execute_macro_with_timeout(
        self,
        identifier: str,
        timeout: int,
        trigger_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a macro with custom timeout settings.
        
        Args:
            identifier: Macro name or UUID
            timeout: Maximum execution time in seconds (1-300)
            trigger_value: Optional parameter value
            
        Returns:
            Execution result with timing information
        """
        try:
            # Validate timeout
            if not is_valid_timeout(timeout):
                return {
                    "success": False,
                    "error": "Invalid timeout value (must be 1-300 seconds)",
                    "error_code": "INVALID_TIMEOUT"
                }
            
            # Execute with timeout
            result = await self.macro_operations.execute_macro(
                identifier=identifier,
                trigger_value=trigger_value,
                method=ExecutionMethod.APPLESCRIPT,
                timeout=timeout
            )
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "timeout_used": timeout,
                "timed_out": result.status == MacroOperationStatus.TIMEOUT,
                "error": result.error_details,
                "macro_uuid": result.macro_uuid
            }
            
        except Exception as e:
            logger.error(f"Timed macro execution failed: {e}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            }
    
    async def execute_macro_via_method(
        self,
        identifier: str,
        method: str,
        trigger_value: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a macro using a specific execution method.
        
        Args:
            identifier: Macro name or UUID
            method: Execution method (applescript, url, web_api, remote)
            trigger_value: Optional parameter value
            timeout: Maximum execution time in seconds
            
        Returns:
            Execution result with method information
        """
        try:
            # Validate and convert method
            method_map = {
                "applescript": ExecutionMethod.APPLESCRIPT,
                "url": ExecutionMethod.URL,
                "web_api": ExecutionMethod.WEB_API,
                "remote": ExecutionMethod.REMOTE
            }
            
            execution_method = method_map.get(method.lower())
            if not execution_method:
                return {
                    "success": False,
                    "error": f"Unsupported execution method: {method}",
                    "error_code": "INVALID_METHOD",
                    "supported_methods": list(method_map.keys())
                }
            
            # Execute via specified method
            result = await self.macro_operations.execute_macro(
                identifier=identifier,
                trigger_value=trigger_value,
                method=execution_method,
                timeout=timeout
            )
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "execution_method": method,
                "execution_time": result.execution_time,
                "error": result.error_details,
                "macro_uuid": result.macro_uuid
            }
            
        except Exception as e:
            logger.error(f"Method-specific execution failed: {e}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "error_code": "EXECUTION_ERROR"
            }
    
    async def test_macro_execution(
        self,
        identifier: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Test macro execution readiness without actually running it.
        
        Args:
            identifier: Macro name or UUID to test
            dry_run: If True, only validate without executing
            
        Returns:
            Test results and readiness status
        """
        try:
            # Validate identifier
            if not is_valid_macro_identifier(identifier):
                return {
                    "ready": False,
                    "error": "Invalid macro identifier",
                    "error_code": "INVALID_IDENTIFIER"
                }
            
            # Check if macro exists
            macro_info = await self.macro_operations.get_macro_info(identifier)
            if not macro_info:
                return {
                    "ready": False,
                    "error": "Macro not found",
                    "error_code": "MACRO_NOT_FOUND"
                }
            
            # Check if macro is enabled
            if not macro_info.enabled:
                return {
                    "ready": False,
                    "error": "Macro is disabled",
                    "error_code": "MACRO_DISABLED",
                    "macro_info": {
                        "name": macro_info.name,
                        "uuid": macro_info.uuid,
                        "enabled": macro_info.enabled
                    }
                }
            
            test_results = {
                "ready": True,
                "macro_info": {
                    "name": macro_info.name,
                    "uuid": macro_info.uuid,
                    "enabled": macro_info.enabled,
                    "group_uuid": macro_info.group_uuid,
                    "trigger_count": macro_info.trigger_count,
                    "action_count": macro_info.action_count
                },
                "execution_methods": ["applescript", "url", "web_api", "remote"]
            }
            
            # Perform actual test execution if not dry run
            if not dry_run:
                test_result = await self.macro_operations.execute_macro(
                    identifier=identifier,
                    timeout=5  # Short timeout for testing
                )
                
                test_results["test_execution"] = {
                    "success": test_result.status == MacroOperationStatus.SUCCESS,
                    "status": test_result.status.value,
                    "execution_time": test_result.execution_time,
                    "error": test_result.error_details
                }
            
            return test_results
            
        except Exception as e:
            logger.error(f"Macro test failed: {e}")
            return {
                "ready": False,
                "error": f"Test failed: {str(e)}",
                "error_code": "TEST_ERROR"
            }


def register_macro_execution_tools(mcp_server: FastMCP, macro_operations: MacroOperations) -> None:
    """
    Register macro execution tools with the FastMCP server.
    
    This is a convenience function for registering all execution tools.
    """
    execution_tools = MacroExecutionTools(macro_operations)
    execution_tools.register_tools(mcp_server)
    
    logger.info("All macro execution tools registered successfully")
