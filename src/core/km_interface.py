# Keyboard Maestro Interface Abstraction
# Implements high-level interface for Keyboard Maestro operations with contract-driven development

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
from uuid import UUID, uuid4

from src.types.domain_types import MacroUUID, MacroName, VariableName, GroupUUID, MacroExecutionContext
from src.types.enumerations import ExecutionMethod, VariableScope, MacroState
from src.contracts.decorators import requires, ensures
from src.contracts.exceptions import PreconditionViolation, PostconditionViolation
from src.validators.km_validators import KMValidator
from src.core.applescript_pool import AppleScriptConnectionPool
from src.core.km_error_handler import KMErrorHandler
from src.boundaries.km_boundaries import KMBoundaryGuard

@dataclass(frozen=True)
class KMOperationResult:
    """Immutable result for Keyboard Maestro operations."""
    success: bool
    result: Optional[Any] = None
    error_details: Optional[str] = None
    execution_time: float = 0.0
    operation_id: str = ""
    
    def __post_init__(self):
        """Validate result structure consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.result is not None:
            raise ValueError("Failed result cannot have return value")

@dataclass(frozen=True)
class KMInterface(ABC):
    """Abstract interface for Keyboard Maestro operations."""
    
    @abstractmethod
    async def execute_macro(self, context: MacroExecutionContext) -> KMOperationResult:
        """Execute macro with comprehensive error handling."""
        pass
    
    @abstractmethod
    async def get_variable(self, name: VariableName, scope: VariableScope = VariableScope.GLOBAL) -> KMOperationResult:
        """Retrieve variable value with scope enforcement."""
        pass
    
    @abstractmethod
    async def set_variable(self, name: VariableName, value: str, scope: VariableScope = VariableScope.GLOBAL) -> KMOperationResult:
        """Set variable value with validation."""
        pass
    
    @abstractmethod
    async def get_macro_status(self, identifier: Union[MacroUUID, MacroName]) -> KMOperationResult:
        """Get macro status and properties."""
        pass

class KeyboardMaestroInterface(KMInterface):
    """Production implementation of Keyboard Maestro interface."""
    
    def __init__(self, 
                 connection_pool: AppleScriptConnectionPool,
                 validator: KMValidator,
                 error_handler: KMErrorHandler,
                 boundary_guard: KMBoundaryGuard):
        self.connection_pool = connection_pool
        self.validator = validator
        self.error_handler = error_handler
        self.boundary_guard = boundary_guard
        self._operation_counter = 0
    
    @requires(lambda self, context: isinstance(context, MacroExecutionContext))
    @requires(lambda self, context: self.validator.is_valid_macro_identifier(context.identifier))
    @requires(lambda self, context: 0 < context.timeout <= 300)
    @ensures(lambda result: isinstance(result, KMOperationResult))
    @ensures(lambda result: result.success or result.error_details is not None)
    async def execute_macro(self, context: MacroExecutionContext) -> KMOperationResult:
        """Execute Keyboard Maestro macro with comprehensive validation and error handling.
        
        Preconditions:
        - Context must be valid MacroExecutionContext
        - Macro identifier must be valid (non-empty string or UUID)
        - Timeout must be between 1 and 300 seconds
        
        Postconditions:
        - Returns valid KMOperationResult
        - Success or error details provided
        """
        operation_id = self._generate_operation_id()
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate operation boundaries
            boundary_result = await self.boundary_guard.validate_macro_execution(context)
            if not boundary_result.allowed:
                return KMOperationResult(
                    success=False,
                    error_details=f"Boundary violation: {boundary_result.reason}",
                    execution_time=0.0,
                    operation_id=operation_id
                )
            
            # Execute macro through connection pool
            async with self.connection_pool.get_connection() as connection:
                result = await self._execute_macro_with_connection(connection, context)
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                return KMOperationResult(
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    operation_id=operation_id
                )
                
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Handle error through specialized error handler
            error_result = await self.error_handler.handle_macro_execution_error(
                e, context, operation_id
            )
            
            return KMOperationResult(
                success=False,
                error_details=error_result.error_message,
                execution_time=execution_time,
                operation_id=operation_id
            )
    
    @requires(lambda self, name: isinstance(name, VariableName))
    @requires(lambda self, name, scope: scope in VariableScope)
    @ensures(lambda result: isinstance(result, KMOperationResult))
    @ensures(lambda result: result.success or result.error_details is not None)
    async def get_variable(self, name: VariableName, scope: VariableScope = VariableScope.GLOBAL) -> KMOperationResult:
        """Retrieve variable value with scope enforcement and validation.
        
        Preconditions:
        - Variable name must be valid VariableName type
        - Scope must be valid VariableScope enumeration
        
        Postconditions:
        - Returns valid KMOperationResult
        - Success or error details provided
        """
        operation_id = self._generate_operation_id()
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate variable name and scope
            if not self.validator.is_valid_variable_name(name):
                return KMOperationResult(
                    success=False,
                    error_details=f"Invalid variable name: {name}",
                    execution_time=0.0,
                    operation_id=operation_id
                )
            
            # Validate scope access
            scope_result = await self.boundary_guard.validate_variable_access(name, scope)
            if not scope_result.allowed:
                return KMOperationResult(
                    success=False,
                    error_details=f"Scope access denied: {scope_result.reason}",
                    execution_time=0.0,
                    operation_id=operation_id
                )
            
            # Get variable through connection pool
            async with self.connection_pool.get_connection() as connection:
                value = await self._get_variable_with_connection(connection, name, scope)
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                return KMOperationResult(
                    success=True,
                    result=value,
                    execution_time=execution_time,
                    operation_id=operation_id
                )
                
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            error_result = await self.error_handler.handle_variable_operation_error(
                e, name, scope, operation_id
            )
            
            return KMOperationResult(
                success=False,
                error_details=error_result.error_message,
                execution_time=execution_time,
                operation_id=operation_id
            )
    
    @requires(lambda self, name: isinstance(name, VariableName))
    @requires(lambda self, name, value: isinstance(value, str))
    @requires(lambda self, name, value, scope: scope in VariableScope)
    @ensures(lambda result: isinstance(result, KMOperationResult))
    @ensures(lambda result: result.success or result.error_details is not None)
    async def set_variable(self, name: VariableName, value: str, scope: VariableScope = VariableScope.GLOBAL) -> KMOperationResult:
        """Set variable value with comprehensive validation and scope enforcement.
        
        Preconditions:
        - Variable name must be valid VariableName type
        - Value must be string type
        - Scope must be valid VariableScope enumeration
        
        Postconditions:
        - Returns valid KMOperationResult
        - Success or error details provided
        """
        operation_id = self._generate_operation_id()
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate variable name
            if not self.validator.is_valid_variable_name(name):
                return KMOperationResult(
                    success=False,
                    error_details=f"Invalid variable name: {name}",
                    execution_time=0.0,
                    operation_id=operation_id
                )
            
            # Validate variable value content
            if not self.validator.is_safe_variable_value(value):
                return KMOperationResult(
                    success=False,
                    error_details="Variable value contains unsafe content",
                    execution_time=0.0,
                    operation_id=operation_id
                )
            
            # Validate scope access for modification
            scope_result = await self.boundary_guard.validate_variable_modification(name, value, scope)
            if not scope_result.allowed:
                return KMOperationResult(
                    success=False,
                    error_details=f"Variable modification denied: {scope_result.reason}",
                    execution_time=0.0,
                    operation_id=operation_id
                )
            
            # Set variable through connection pool
            async with self.connection_pool.get_connection() as connection:
                await self._set_variable_with_connection(connection, name, value, scope)
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                return KMOperationResult(
                    success=True,
                    result=f"Variable '{name}' set successfully",
                    execution_time=execution_time,
                    operation_id=operation_id
                )
                
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            error_result = await self.error_handler.handle_variable_operation_error(
                e, name, scope, operation_id
            )
            
            return KMOperationResult(
                success=False,
                error_details=error_result.error_message,
                execution_time=execution_time,
                operation_id=operation_id
            )
    
    @requires(lambda self, identifier: self.validator.is_valid_macro_identifier(identifier))
    @ensures(lambda result: isinstance(result, KMOperationResult))
    async def get_macro_status(self, identifier: Union[MacroUUID, MacroName]) -> KMOperationResult:
        """Get macro status and properties with validation.
        
        Preconditions:
        - Identifier must be valid macro identifier
        
        Postconditions:
        - Returns valid KMOperationResult
        """
        operation_id = self._generate_operation_id()
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.connection_pool.get_connection() as connection:
                status = await self._get_macro_status_with_connection(connection, identifier)
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                return KMOperationResult(
                    success=True,
                    result=status,
                    execution_time=execution_time,
                    operation_id=operation_id
                )
                
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            error_result = await self.error_handler.handle_macro_status_error(
                e, identifier, operation_id
            )
            
            return KMOperationResult(
                success=False,
                error_details=error_result.error_message,
                execution_time=execution_time,
                operation_id=operation_id
            )
    
    def _generate_operation_id(self) -> str:
        """Generate unique operation identifier."""
        self._operation_counter += 1
        return f"km_op_{self._operation_counter}_{uuid4().hex[:8]}"
    
    async def _execute_macro_with_connection(self, 
                                           connection: 'AppleScriptConnection', 
                                           context: MacroExecutionContext) -> str:
        """Execute macro using connection with method-specific handling."""
        if context.method == ExecutionMethod.APPLESCRIPT:
            return await self._execute_macro_applescript(connection, context)
        elif context.method == ExecutionMethod.URL:
            return await self._execute_macro_url(context)
        elif context.method == ExecutionMethod.WEB:
            return await self._execute_macro_web(context)
        else:
            raise ValueError(f"Unsupported execution method: {context.method}")
    
    async def _execute_macro_applescript(self, 
                                       connection: 'AppleScriptConnection',
                                       context: MacroExecutionContext) -> str:
        """Execute macro via AppleScript."""
        from src.utils.applescript_utils import AppleScriptBuilder
        
        builder = AppleScriptBuilder()
        script = builder.build_macro_execution_script(
            identifier=context.identifier,
            trigger_value=context.trigger_value,
            context_variables=context.context_variables
        )
        
        result = await connection.execute_script(script, timeout=context.timeout)
        
        if not result['success']:
            raise RuntimeError(f"AppleScript execution failed: {result['error']}")
        
        return result['output'] or "Macro executed successfully"
    
    async def _execute_macro_url(self, context: MacroExecutionContext) -> str:
        """Execute macro via URL scheme."""
        from src.utils.applescript_utils import URLSchemeExecutor
        
        executor = URLSchemeExecutor()
        result = await executor.execute_macro_url(
            identifier=context.identifier,
            trigger_value=context.trigger_value,
            timeout=context.timeout
        )
        
        return result
    
    async def _execute_macro_web(self, context: MacroExecutionContext) -> str:
        """Execute macro via web API."""
        from src.utils.applescript_utils import WebAPIExecutor
        
        executor = WebAPIExecutor()
        result = await executor.execute_macro_web(
            identifier=context.identifier,
            trigger_value=context.trigger_value,
            timeout=context.timeout
        )
        
        return result
    
    async def _get_variable_with_connection(self, 
                                          connection: 'AppleScriptConnection',
                                          name: VariableName, 
                                          scope: VariableScope) -> Optional[str]:
        """Get variable value using AppleScript connection."""
        from src.utils.applescript_utils import AppleScriptBuilder
        
        builder = AppleScriptBuilder()
        script = builder.build_get_variable_script(name, scope)
        
        result = await connection.execute_script(script, timeout=10.0)
        
        if not result['success']:
            if "variable does not exist" in result['error'].lower():
                return None  # Variable doesn't exist
            raise RuntimeError(f"Failed to get variable: {result['error']}")
        
        return result['output']
    
    async def _set_variable_with_connection(self, 
                                          connection: 'AppleScriptConnection',
                                          name: VariableName, 
                                          value: str, 
                                          scope: VariableScope) -> None:
        """Set variable value using AppleScript connection."""
        from src.utils.applescript_utils import AppleScriptBuilder
        
        builder = AppleScriptBuilder()
        script = builder.build_set_variable_script(name, value, scope)
        
        result = await connection.execute_script(script, timeout=10.0)
        
        if not result['success']:
            raise RuntimeError(f"Failed to set variable: {result['error']}")
    
    async def _get_macro_status_with_connection(self, 
                                              connection: 'AppleScriptConnection',
                                              identifier: Union[MacroUUID, MacroName]) -> Dict[str, Any]:
        """Get macro status using AppleScript connection."""
        from src.utils.applescript_utils import AppleScriptBuilder
        
        builder = AppleScriptBuilder()
        script = builder.build_macro_status_script(identifier)
        
        result = await connection.execute_script(script, timeout=10.0)
        
        if not result['success']:
            raise RuntimeError(f"Failed to get macro status: {result['error']}")
        
        # Parse status information from AppleScript output
        status_data = self._parse_macro_status_output(result['output'])
        return status_data
    
    def _parse_macro_status_output(self, output: str) -> Dict[str, Any]:
        """Parse macro status output from AppleScript."""
        # Simplified parsing - in production would use structured output
        lines = output.strip().split('\n') if output else []
        
        status = {
            'exists': False,
            'enabled': False,
            'name': None,
            'uuid': None,
            'group': None,
            'last_used': None
        }
        
        for line in lines:
            if 'exists:' in line.lower():
                status['exists'] = 'true' in line.lower()
            elif 'enabled:' in line.lower():
                status['enabled'] = 'true' in line.lower()
            elif 'name:' in line.lower():
                status['name'] = line.split(':', 1)[1].strip()
            elif 'uuid:' in line.lower():
                status['uuid'] = line.split(':', 1)[1].strip()
        
        return status


class MockKMInterface(KMInterface):
    """Mock implementation for testing purposes."""
    
    def __init__(self):
        self._variables = {}
        self._macros = {
            'test_macro': {'name': 'test_macro', 'enabled': True},
            'disabled_macro': {'name': 'disabled_macro', 'enabled': False}
        }
    
    async def execute_macro(self, context: MacroExecutionContext) -> KMOperationResult:
        """Mock macro execution."""
        identifier = str(context.identifier)
        
        if identifier in self._macros:
            return KMOperationResult(
                success=True,
                result=f"Mock execution of {identifier}",
                execution_time=0.1,
                operation_id=f"mock_{identifier}"
            )
        else:
            return KMOperationResult(
                success=False,
                error_details=f"Macro not found: {identifier}",
                execution_time=0.0,
                operation_id=f"mock_{identifier}"
            )
    
    async def get_variable(self, name: VariableName, scope: VariableScope = VariableScope.GLOBAL) -> KMOperationResult:
        """Mock variable retrieval."""
        key = f"{scope.value}:{name}"
        value = self._variables.get(key)
        
        return KMOperationResult(
            success=True,
            result=value,
            execution_time=0.01,
            operation_id=f"mock_get_{name}"
        )
    
    async def set_variable(self, name: VariableName, value: str, scope: VariableScope = VariableScope.GLOBAL) -> KMOperationResult:
        """Mock variable assignment."""
        key = f"{scope.value}:{name}"
        self._variables[key] = value
        
        return KMOperationResult(
            success=True,
            result=f"Variable {name} set to {value}",
            execution_time=0.01,
            operation_id=f"mock_set_{name}"
        )
    
    async def get_macro_status(self, identifier: Union[MacroUUID, MacroName]) -> KMOperationResult:
        """Mock macro status retrieval."""
        identifier_str = str(identifier)
        macro = self._macros.get(identifier_str)
        
        if macro:
            return KMOperationResult(
                success=True,
                result=macro,
                execution_time=0.01,
                operation_id=f"mock_status_{identifier_str}"
            )
        else:
            return KMOperationResult(
                success=False,
                error_details=f"Macro not found: {identifier_str}",
                execution_time=0.01,
                operation_id=f"mock_status_{identifier_str}"
            )