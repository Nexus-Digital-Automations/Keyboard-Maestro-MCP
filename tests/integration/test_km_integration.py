# Keyboard Maestro Integration Tests: Comprehensive System Testing
# tests/integration/test_km_integration.py

"""
Integration tests for Keyboard Maestro MCP integration layer.

This test suite validates the complete integration between the MCP server
and Keyboard Maestro, including connection pooling, boundary validation,
error handling, and end-to-end operation workflows.

Features:
- Complete integration workflow testing
- AppleScript connection pool validation
- Boundary protection verification
- Error handling and recovery testing
- Performance and reliability validation

Size: 241 lines (target: <250)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.core.km_interface import KeyboardMaestroInterface, MockKMInterface, MacroExecutionContext
from src.core.applescript_pool import AppleScriptConnectionPool, PoolConfiguration
from src.validators.km_validators import KMValidator
from src.boundaries.km_boundaries import KMBoundaryGuard
from src.core.km_error_handler import KMErrorHandler
from src.types.domain_types import MacroName, VariableName
from src.types.enumerations import ExecutionMethod, VariableScope


class TestKMIntegrationWorkflow:
    """Test complete Keyboard Maestro integration workflows."""
    
    @pytest.fixture
    async def km_interface(self):
        """Create KM interface with mock dependencies."""
        pool_config = PoolConfiguration(max_connections=2, min_connections=1)
        connection_pool = Mock(spec=AppleScriptConnectionPool)
        validator = Mock(spec=KMValidator)
        error_handler = Mock(spec=KMErrorHandler)
        boundary_guard = Mock(spec=KMBoundaryGuard)
        
        # Configure mocks for successful operations
        validator.is_valid_macro_identifier.return_value = True
        validator.is_valid_variable_name.return_value = True
        validator.is_safe_variable_value.return_value = True
        
        boundary_guard.validate_macro_execution = AsyncMock(return_value=Mock(allowed=True))
        boundary_guard.validate_variable_access = AsyncMock(return_value=Mock(allowed=True))
        boundary_guard.validate_variable_modification = AsyncMock(return_value=Mock(allowed=True))
        
        interface = KeyboardMaestroInterface(
            connection_pool=connection_pool,
            validator=validator,
            error_handler=error_handler,
            boundary_guard=boundary_guard
        )
        
        return interface
    
    @pytest.mark.asyncio
    async def test_macro_execution_workflow(self, km_interface):
        """Test complete macro execution workflow."""
        # Arrange
        context = MacroExecutionContext(
            identifier=MacroName("test_macro"),
            trigger_value="test_value",
            method=ExecutionMethod.APPLESCRIPT,
            timeout=30
        )
        
        # Mock connection pool behavior
        mock_connection = Mock()
        mock_connection.execute_script = AsyncMock(return_value={
            'success': True,
            'output': 'Macro executed successfully',
            'error': None
        })
        
        km_interface.connection_pool.get_connection.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        km_interface.connection_pool.get_connection.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Act
        with patch('src.utils.applescript_utils.AppleScriptBuilder') as mock_builder:
            mock_builder.return_value.build_macro_execution_script.return_value = 'tell application "Keyboard Maestro Engine"'
            
            result = await km_interface.execute_macro(context)
        
        # Assert
        assert result.success is True
        assert result.result == 'Macro executed successfully'
        assert result.execution_time >= 0
        assert result.operation_id.startswith('km_op_')
        
        # Verify boundary validation was called
        km_interface.boundary_guard.validate_macro_execution.assert_called_once_with(context)
        
        # Verify connection pool was used
        km_interface.connection_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_variable_operations_workflow(self, km_interface):
        """Test complete variable operations workflow."""
        # Arrange
        var_name = VariableName("test_variable")
        var_value = "test_value"
        scope = VariableScope.GLOBAL
        
        # Mock connection behavior
        mock_connection = Mock()
        mock_connection.execute_script = AsyncMock(return_value={
            'success': True,
            'output': var_value,
            'error': None
        })
        
        km_interface.connection_pool.get_connection.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        km_interface.connection_pool.get_connection.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Act - Set variable
        with patch('src.utils.applescript_utils.AppleScriptBuilder') as mock_builder:
            mock_builder.return_value.build_set_variable_script.return_value = 'setvariable script'
            
            set_result = await km_interface.set_variable(var_name, var_value, scope)
        
        # Assert set operation
        assert set_result.success is True
        assert "set successfully" in set_result.result
        
        # Act - Get variable
        with patch('src.utils.applescript_utils.AppleScriptBuilder') as mock_builder:
            mock_builder.return_value.build_get_variable_script.return_value = 'getvariable script'
            
            get_result = await km_interface.get_variable(var_name, scope)
        
        # Assert get operation
        assert get_result.success is True
        assert get_result.result == var_value
        
        # Verify boundary validations were called
        assert km_interface.boundary_guard.validate_variable_modification.call_count >= 1
        assert km_interface.boundary_guard.validate_variable_access.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, km_interface):
        """Test error handling workflow."""
        # Arrange
        context = MacroExecutionContext(identifier=MacroName("failing_macro"))
        
        # Mock connection to fail
        mock_connection = Mock()
        mock_connection.execute_script = AsyncMock(return_value={
            'success': False,
            'output': None,
            'error': 'Macro not found'
        })
        
        km_interface.connection_pool.get_connection.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        km_interface.connection_pool.get_connection.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Mock error handler
        from src.core.km_error_handler import KMErrorResult, KMErrorType
        mock_error_result = KMErrorResult(
            error_type=KMErrorType.MACRO_NOT_FOUND,
            error_message="Macro not found",
            user_friendly_message="The specified macro could not be found",
            recovery_suggestion="Check macro name and try again"
        )
        km_interface.error_handler.handle_macro_execution_error = AsyncMock(return_value=mock_error_result)
        
        # Act
        with patch('src.utils.applescript_utils.AppleScriptBuilder'):
            result = await km_interface.execute_macro(context)
        
        # Assert
        assert result.success is False
        assert "Macro not found" in result.error_details
        assert result.execution_time >= 0
        
        # Verify error handler was called
        km_interface.error_handler.handle_macro_execution_error.assert_called_once()


class TestAppleScriptConnectionPool:
    """Test AppleScript connection pool behavior."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_lifecycle(self):
        """Test connection pool initialization and shutdown."""
        # Arrange
        config = PoolConfiguration(max_connections=2, min_connections=1)
        pool = AppleScriptConnectionPool(config)
        
        # Act - Initialize
        await pool.initialize()
        
        # Assert initialization
        assert pool.status.value == 'active'
        assert pool.total_connections >= config.min_connections
        
        # Act - Get connection
        async with pool.get_connection() as connection:
            assert connection is not None
            assert connection.is_available
        
        # Act - Shutdown
        await pool.shutdown()
        
        # Assert shutdown
        assert pool.status.value == 'shutdown'
        assert pool.total_connections == 0
    
    @pytest.mark.asyncio
    async def test_connection_pool_resource_management(self):
        """Test connection pool resource management."""
        # Arrange
        config = PoolConfiguration(max_connections=2, min_connections=1)
        pool = AppleScriptConnectionPool(config)
        await pool.initialize()
        
        try:
            # Act - Get multiple connections
            connections = []
            for _ in range(config.max_connections):
                conn_context = pool.get_connection()
                connection = await conn_context.__aenter__()
                connections.append((conn_context, connection))
            
            # Assert all connections acquired
            assert len(connections) == config.max_connections
            assert pool.available_connections == 0
            
            # Act - Release connections
            for conn_context, connection in connections:
                await conn_context.__aexit__(None, None, None)
            
            # Assert connections released
            assert pool.available_connections == config.max_connections
            
        finally:
            await pool.shutdown()


class TestBoundaryValidation:
    """Test boundary validation and protection."""
    
    @pytest.fixture
    def boundary_guard(self):
        """Create boundary guard with test configuration."""
        config = {
            'max_operations_per_minute': 5,
            'max_concurrent_operations': 2,
            'max_variable_size': 100,
            'max_execution_timeout': 60
        }
        return KMBoundaryGuard(config)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, boundary_guard):
        """Test rate limiting boundary validation."""
        # Arrange
        context = MacroExecutionContext(identifier=MacroName("test_macro"))
        
        # Act - Execute up to rate limit
        results = []
        for _ in range(6):  # One more than rate limit
            result = await boundary_guard.validate_macro_execution(context)
            results.append(result)
        
        # Assert rate limiting
        successful_operations = [r for r in results if r.allowed]
        rate_limited_operations = [r for r in results if not r.allowed]
        
        assert len(successful_operations) == 5  # Rate limit
        assert len(rate_limited_operations) == 1
        
        if rate_limited_operations:
            assert "rate limit" in rate_limited_operations[0].reason.lower()
    
    @pytest.mark.asyncio
    async def test_variable_size_limits(self, boundary_guard):
        """Test variable size boundary validation."""
        # Arrange
        var_name = VariableName("large_variable")
        large_value = "x" * 150  # Exceeds 100 char limit
        small_value = "x" * 50   # Within limit
        
        # Act
        large_result = await boundary_guard.validate_variable_modification(
            var_name, large_value, VariableScope.GLOBAL
        )
        small_result = await boundary_guard.validate_variable_modification(
            var_name, small_value, VariableScope.GLOBAL
        )
        
        # Assert
        assert not large_result.allowed
        assert "too large" in large_result.reason.lower()
        assert small_result.allowed


class TestMockKMInterface:
    """Test mock implementation for development and testing."""
    
    @pytest.fixture
    def mock_interface(self):
        """Create mock KM interface."""
        return MockKMInterface()
    
    @pytest.mark.asyncio
    async def test_mock_macro_execution(self, mock_interface):
        """Test mock macro execution."""
        # Arrange
        context = MacroExecutionContext(identifier=MacroName("test_macro"))
        
        # Act
        result = await mock_interface.execute_macro(context)
        
        # Assert
        assert result.success is True
        assert "Mock execution" in result.result
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_mock_variable_operations(self, mock_interface):
        """Test mock variable operations."""
        # Arrange
        var_name = VariableName("test_var")
        var_value = "test_value"
        
        # Act - Set and get variable
        set_result = await mock_interface.set_variable(var_name, var_value)
        get_result = await mock_interface.get_variable(var_name)
        
        # Assert
        assert set_result.success is True
        assert get_result.success is True
        assert get_result.result == var_value
    
    @pytest.mark.asyncio
    async def test_mock_error_scenarios(self, mock_interface):
        """Test mock error scenarios."""
        # Arrange
        context = MacroExecutionContext(identifier=MacroName("nonexistent_macro"))
        
        # Act
        result = await mock_interface.execute_macro(context)
        
        # Assert
        assert result.success is False
        assert "not found" in result.error_details
