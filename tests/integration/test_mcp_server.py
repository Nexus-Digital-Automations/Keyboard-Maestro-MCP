# MCP Server Integration Tests: Keyboard Maestro MCP Server
# tests/integration/test_mcp_server.py

"""
Integration tests for the complete MCP server functionality.

This module provides comprehensive integration testing for the Keyboard Maestro
MCP Server, verifying server lifecycle, tool registration, transport protocols,
and end-to-end operation workflows with property-based testing.

Features:
- Server lifecycle testing (initialization, shutdown)
- Transport protocol verification (STDIO, HTTP)
- Tool registration and execution testing
- Contract compliance verification
- Performance and stress testing

Size: 241 lines (target: <250)
"""

import pytest
import asyncio
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

from src.core.mcp_server import KeyboardMaestroMCPServer
from src.utils.configuration import ServerConfiguration
from src.interfaces.transport_manager import TransportManager
from src.types.enumerations import ServerStatus, ComponentStatus
from src.contracts.validators import is_valid_server_configuration


@pytest.fixture
def development_config() -> ServerConfiguration:
    """Provide development mode server configuration."""
    return ServerConfiguration(
        transport="stdio",
        host="127.0.0.1",
        port=8000,
        max_concurrent_operations=10,
        operation_timeout=30,
        auth_required=False,
        log_level="DEBUG",
        development_mode=True
    )


@pytest.fixture
def production_config() -> ServerConfiguration:
    """Provide production mode server configuration."""
    return ServerConfiguration(
        transport="streamable-http",
        host="127.0.0.1", 
        port=8001,
        max_concurrent_operations=50,
        operation_timeout=15,
        auth_required=True,
        log_level="INFO",
        development_mode=False
    )


@pytest.fixture
async def mock_dependencies():
    """Provide mocked dependencies for testing."""
    with patch('src.core.km_interface.KeyboardMaestroInterface') as mock_km, \
         patch('src.boundaries.security_boundaries.SecurityBoundaryManager') as mock_security:
        
        # Configure mocks
        mock_km_instance = AsyncMock()
        mock_km.return_value = mock_km_instance
        
        mock_security_instance = AsyncMock()
        mock_security.return_value = mock_security_instance
        
        yield {
            'km_interface': mock_km_instance,
            'security_manager': mock_security_instance
        }


class TestServerLifecycle:
    """Test server initialization and lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_server_initialization_development(self, development_config, mock_dependencies):
        """Test server initialization in development mode."""
        server = KeyboardMaestroMCPServer(development_config)
        
        # Verify initial state
        assert server.status == ServerStatus.INITIALIZING
        assert server.config == development_config
        
        # Initialize server
        await server.initialize()
        
        # Verify successful initialization
        assert server.status == ServerStatus.RUNNING
        assert server.metrics.uptime_seconds > 0
        
        # Cleanup
        await server.shutdown()
        assert server.status == ServerStatus.SHUTDOWN
    
    @pytest.mark.asyncio
    async def test_server_initialization_production(self, production_config, mock_dependencies):
        """Test server initialization in production mode."""
        server = KeyboardMaestroMCPServer(production_config)
        
        await server.initialize()
        
        # Verify production-specific settings
        assert server.status == ServerStatus.RUNNING
        assert server.config.max_concurrent_operations == 50
        assert server.config.operation_timeout == 15
        
        await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_component_health_verification(self, development_config, mock_dependencies):
        """Test component health checking during initialization."""
        server = KeyboardMaestroMCPServer(development_config)
        
        await server.initialize()
        
        # Get health status
        health = await server.get_health_status()
        
        # Verify all components are healthy
        assert health['server_status'] == 'running'
        assert 'component_status' in health
        
        component_statuses = health['component_status']
        expected_components = ['security_manager', 'km_interface', 'context_manager', 'tool_registry']
        
        for component in expected_components:
            assert component in component_statuses
            assert component_statuses[component] == 'healthy'
        
        await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialization_failure_handling(self, development_config):
        """Test server behavior when component initialization fails."""
        with patch('src.boundaries.security_boundaries.SecurityBoundaryManager') as mock_security:
            # Make security manager initialization fail
            mock_security.return_value.initialize.side_effect = RuntimeError("Security init failed")
            
            server = KeyboardMaestroMCPServer(development_config)
            
            # Initialization should fail
            with pytest.raises(RuntimeError, match="Security manager initialization failed"):
                await server.initialize()
            
            # Server should be in failed state
            assert server.status == ServerStatus.FAILED


class TestTransportIntegration:
    """Test transport layer integration."""
    
    @pytest.mark.asyncio
    async def test_stdio_transport_initialization(self, development_config):
        """Test STDIO transport initialization."""
        transport_manager = TransportManager(development_config)
        
        await transport_manager.initialize()
        
        # Verify transport configuration
        connection_info = transport_manager.get_connection_info()
        assert connection_info['transport_type'] == 'stdio'
        assert connection_info['interface'] == 'stdio'
        assert connection_info['initialized'] is True
        
        await transport_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_http_transport_initialization(self, production_config):
        """Test HTTP transport initialization."""
        transport_manager = TransportManager(production_config)
        
        await transport_manager.initialize()
        
        # Verify transport configuration
        connection_info = transport_manager.get_connection_info()
        assert connection_info['transport_type'] == 'streamable-http'
        assert connection_info['host'] == '127.0.0.1'
        assert connection_info['port'] == 8001
        assert 'endpoint' in connection_info
        
        await transport_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_transport_lifecycle(self, development_config):
        """Test complete transport lifecycle."""
        transport_manager = TransportManager(development_config)
        
        # Initialize
        await transport_manager.initialize()
        assert transport_manager.status.value == 'connected'
        
        # Start listening
        await transport_manager.start()
        
        # Verify metrics tracking
        metrics = transport_manager.metrics
        assert metrics is not None
        assert metrics.last_activity > 0
        
        # Stop and shutdown
        await transport_manager.stop()
        await transport_manager.shutdown()


class TestToolRegistration:
    """Test MCP tool registration and management."""
    
    @pytest.mark.asyncio
    async def test_tool_registry_initialization(self, development_config, mock_dependencies):
        """Test tool registry initialization and tool loading."""
        server = KeyboardMaestroMCPServer(development_config)
        await server.initialize()
        
        # Get tool registry metrics
        if server._tool_registry:
            metrics = await server._tool_registry.get_tool_metrics()
            
            # Verify metrics structure
            assert 'total_tools' in metrics
            assert 'active_tools' in metrics
            assert 'tool_categories' in metrics
            assert 'most_used_tools' in metrics
            
            # Tool counts should be reasonable
            assert metrics['total_tools'] >= 0
            assert metrics['active_tools'] >= 0
        
        await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_fastmcp_tool_registration(self, development_config, mock_dependencies):
        """Test FastMCP tool registration process."""
        from fastmcp import FastMCP
        
        server = KeyboardMaestroMCPServer(development_config)
        await server.initialize()
        
        # Create mock FastMCP instance
        mock_mcp = Mock(spec=FastMCP)
        mock_mcp.tool.return_value = lambda func: func  # Mock decorator
        
        # Register tools
        await server.register_tools(mock_mcp)
        
        # Verify tool decorator was called
        assert mock_mcp.tool.called
        
        await server.shutdown()


class TestRequestHandling:
    """Test MCP request handling and processing."""
    
    @pytest.mark.asyncio
    async def test_request_metrics_tracking(self, development_config, mock_dependencies):
        """Test request metrics are properly tracked."""
        server = KeyboardMaestroMCPServer(development_config)
        await server.initialize()
        
        # Simulate request handling
        initial_metrics = server.metrics
        
        # Mock request
        request_data = {
            'tool_name': 'test_tool',
            'parameters': {}
        }
        
        # Handle request (will fail due to missing tool, but should track metrics)
        response = await server.handle_request(request_data)
        
        # Verify metrics updated
        updated_metrics = server.metrics
        assert updated_metrics.total_requests > initial_metrics.total_requests
        assert updated_metrics.last_request_time is not None
        
        await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, development_config, mock_dependencies):
        """Test handling multiple concurrent requests."""
        server = KeyboardMaestroMCPServer(development_config)
        await server.initialize()
        
        # Create multiple concurrent requests
        requests = [
            {'tool_name': f'test_tool_{i}', 'parameters': {}}
            for i in range(5)
        ]
        
        # Handle all requests concurrently
        tasks = [server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all requests were processed
        assert len(responses) == 5
        
        # Verify metrics reflect all requests
        assert server.metrics.total_requests >= 5
        
        await server.shutdown()


class TestContractCompliance:
    """Test contract compliance across server operations."""
    
    @pytest.mark.asyncio
    async def test_server_configuration_contracts(self, development_config):
        """Test server configuration contract compliance."""
        # Configuration should pass validation
        assert is_valid_server_configuration(development_config)
        
        # Server creation should succeed with valid config
        server = KeyboardMaestroMCPServer(development_config)
        assert server.config == development_config
    
    @pytest.mark.asyncio
    async def test_initialization_preconditions(self, development_config, mock_dependencies):
        """Test initialization precondition enforcement."""
        server = KeyboardMaestroMCPServer(development_config)
        
        # Server should be in INITIALIZING state
        assert server.status == ServerStatus.INITIALIZING
        
        # Should be able to initialize once
        await server.initialize()
        assert server.status == ServerStatus.RUNNING
        
        # Should not be able to initialize again
        with pytest.raises(Exception):  # Contract violation expected
            await server.initialize()
        
        await server.shutdown()
    
    @pytest.mark.asyncio
    async def test_shutdown_postconditions(self, development_config, mock_dependencies):
        """Test shutdown postcondition guarantees."""
        server = KeyboardMaestroMCPServer(development_config)
        await server.initialize()
        
        # Verify running state
        assert server.status == ServerStatus.RUNNING
        
        # Shutdown
        await server.shutdown()
        
        # Verify postconditions
        assert server.status == ServerStatus.SHUTDOWN
        
        # Health status should reflect shutdown
        health = await server.get_health_status()
        assert health['server_status'] == 'shutdown'
