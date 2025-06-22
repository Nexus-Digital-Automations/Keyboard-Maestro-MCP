# Core MCP Server Implementation: Keyboard Maestro MCP Server
# src/core/mcp_server.py

"""
Core FastMCP server implementation with tool registration and lifecycle management.

This module implements the central KeyboardMaestroMCPServer class that orchestrates
all server functionality, tool registration, and component lifecycle management
with comprehensive error handling and monitoring.

Features:
- Tool registration and management with validation
- Server lifecycle management (initialization, shutdown)
- Component coordination and dependency injection
- Error handling and recovery mechanisms
- Performance monitoring and metrics collection

Size: 248 lines (target: <250)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

from fastmcp import FastMCP, Context

from src.utils.configuration import ServerConfiguration
from src.core.tool_registry import ToolRegistry
from src.core.context_manager import MCPContextManager
from src.core.km_interface import KeyboardMaestroInterface
from src.boundaries.security_boundaries import SecurityBoundaryManager
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_server_configuration
from src.types.domain_types import ServerStatus, ComponentStatus


@dataclass
class ServerMetrics:
    """Server performance and operational metrics."""
    startup_time: float
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_connections: int = 0
    last_request_time: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate request success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def uptime_seconds(self) -> float:
        """Calculate server uptime in seconds."""
        return time.time() - self.startup_time


class KeyboardMaestroMCPServer:
    """Core MCP server for Keyboard Maestro automation."""
    
    def __init__(self, config: ServerConfiguration):
        """Initialize server with configuration.
        
        Args:
            config: Validated server configuration
        """
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._status = ServerStatus.INITIALIZING
        self._metrics = ServerMetrics(startup_time=time.time())
        
        # Core components (initialized in initialize())
        self._tool_registry: Optional[ToolRegistry] = None
        self._context_manager: Optional[MCPContextManager] = None
        self._km_interface: Optional[KeyboardMaestroInterface] = None
        self._security_manager: Optional[SecurityBoundaryManager] = None
        
        # Component status tracking
        self._component_status: Dict[str, ComponentStatus] = {}
    
    @property
    def status(self) -> ServerStatus:
        """Current server status."""
        return self._status
    
    @property
    def metrics(self) -> ServerMetrics:
        """Current server metrics."""
        return self._metrics
    
    @property
    def config(self) -> ServerConfiguration:
        """Server configuration (read-only)."""
        return self._config
    
    @requires(lambda self: self._status == ServerStatus.INITIALIZING)
    @ensures(lambda self: self._status in [ServerStatus.RUNNING, ServerStatus.FAILED])
    async def initialize(self) -> None:
        """Initialize all server components.
        
        Preconditions:
        - Server must be in INITIALIZING status
        
        Postconditions:
        - Server status is RUNNING or FAILED
        - All components initialized successfully or error reported
        """
        try:
            self._logger.info("Initializing Keyboard Maestro MCP Server components...")
            
            # Initialize core components in dependency order
            await self._initialize_security_manager()
            await self._initialize_km_interface()
            await self._initialize_context_manager()
            await self._initialize_tool_registry()
            
            # Verify all components are healthy
            await self._verify_component_health()
            
            self._status = ServerStatus.RUNNING
            self._logger.info("Server initialization completed successfully")
            
        except Exception as e:
            self._status = ServerStatus.FAILED
            self._logger.error(f"Server initialization failed: {e}", exc_info=True)
            raise
    
    async def _initialize_security_manager(self) -> None:
        """Initialize security boundary manager."""
        try:
            self._security_manager = SecurityBoundaryManager(self._config)
            await self._security_manager.initialize()
            self._component_status['security_manager'] = ComponentStatus.HEALTHY
            self._logger.debug("Security manager initialized")
        except Exception as e:
            self._component_status['security_manager'] = ComponentStatus.FAILED
            raise RuntimeError(f"Security manager initialization failed: {e}")
    
    async def _initialize_km_interface(self) -> None:
        """Initialize Keyboard Maestro interface."""
        try:
            self._km_interface = KeyboardMaestroInterface(
                self._config,
                self._security_manager
            )
            await self._km_interface.initialize()
            self._component_status['km_interface'] = ComponentStatus.HEALTHY
            self._logger.debug("Keyboard Maestro interface initialized")
        except Exception as e:
            self._component_status['km_interface'] = ComponentStatus.FAILED
            raise RuntimeError(f"Keyboard Maestro interface initialization failed: {e}")
    
    async def _initialize_context_manager(self) -> None:
        """Initialize MCP context manager."""
        try:
            self._context_manager = MCPContextManager(
                self._config,
                self._km_interface
            )
            await self._context_manager.initialize()
            self._component_status['context_manager'] = ComponentStatus.HEALTHY
            self._logger.debug("MCP context manager initialized")
        except Exception as e:
            self._component_status['context_manager'] = ComponentStatus.FAILED
            raise RuntimeError(f"Context manager initialization failed: {e}")
    
    async def _initialize_tool_registry(self) -> None:
        """Initialize tool registry and load all tools."""
        try:
            self._tool_registry = ToolRegistry(
                self._config,
                self._km_interface,
                self._context_manager,
                self._security_manager
            )
            await self._tool_registry.initialize()
            self._component_status['tool_registry'] = ComponentStatus.HEALTHY
            self._logger.debug("Tool registry initialized")
        except Exception as e:
            self._component_status['tool_registry'] = ComponentStatus.FAILED
            raise RuntimeError(f"Tool registry initialization failed: {e}")
    
    async def _verify_component_health(self) -> None:
        """Verify all components are healthy and operational."""
        failed_components = [
            name for name, status in self._component_status.items()
            if status != ComponentStatus.HEALTHY
        ]
        
        if failed_components:
            raise RuntimeError(f"Component health check failed: {failed_components}")
        
        self._logger.info("All components healthy and operational")
    
    @requires(lambda self: self._status == ServerStatus.RUNNING)
    @requires(lambda mcp: mcp is not None)
    async def register_tools(self, mcp: FastMCP) -> None:
        """Register all MCP tools with FastMCP server.
        
        Preconditions:
        - Server must be running
        - FastMCP instance must be valid
        
        Args:
            mcp: FastMCP server instance to register tools with
        """
        try:
            self._logger.info("Registering MCP tools...")
            
            # Import and use the centralized tool registration
            from src.tools import register_all_tools
            
            # Register all tools with the FastMCP instance
            register_all_tools(mcp, self._km_interface)
            
            self._logger.info("Successfully registered all MCP tools")
            
        except Exception as e:
            self._logger.error(f"Tool registration failed: {e}", exc_info=True)
            raise
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request with metrics tracking.
        
        Args:
            request_data: MCP request data
            
        Returns:
            MCP response data
        """
        start_time = time.time()
        self._metrics.total_requests += 1
        self._metrics.last_request_time = start_time
        
        try:
            # Process request through appropriate tool
            if not self._tool_registry:
                raise RuntimeError("Server not properly initialized")
            
            response = await self._tool_registry.handle_request(request_data)
            
            self._metrics.successful_requests += 1
            return response
            
        except Exception as e:
            self._logger.error(f"Request handling failed: {e}", exc_info=True)
            self._metrics.failed_requests += 1
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        finally:
            execution_time = time.time() - start_time
            self._logger.debug(f"Request processed in {execution_time:.3f}s")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive server health status.
        
        Returns:
            Health status information including metrics and component status
        """
        return {
            'server_status': self._status.value,
            'uptime_seconds': self._metrics.uptime_seconds,
            'request_metrics': {
                'total_requests': self._metrics.total_requests,
                'successful_requests': self._metrics.successful_requests,
                'failed_requests': self._metrics.failed_requests,
                'success_rate': self._metrics.success_rate,
                'active_connections': self._metrics.active_connections
            },
            'component_status': {
                name: status.value for name, status in self._component_status.items()
            },
            'configuration': {
                'transport': self._config.transport,
                'max_concurrent_operations': self._config.max_concurrent_operations,
                'operation_timeout': self._config.operation_timeout,
                'development_mode': self._config.development_mode
            }
        }
    
    @requires(lambda self: self._status in [ServerStatus.RUNNING, ServerStatus.FAILED])
    async def shutdown(self) -> None:
        """Gracefully shutdown server and all components.
        
        Preconditions:
        - Server must be running or failed
        """
        try:
            self._logger.info("Initiating server shutdown...")
            self._status = ServerStatus.SHUTTING_DOWN
            
            # Shutdown components in reverse order
            if self._tool_registry:
                await self._tool_registry.shutdown()
                self._component_status['tool_registry'] = ComponentStatus.SHUTDOWN
            
            if self._context_manager:
                await self._context_manager.shutdown()
                self._component_status['context_manager'] = ComponentStatus.SHUTDOWN
            
            if self._km_interface:
                await self._km_interface.shutdown()
                self._component_status['km_interface'] = ComponentStatus.SHUTDOWN
            
            if self._security_manager:
                await self._security_manager.shutdown()
                self._component_status['security_manager'] = ComponentStatus.SHUTDOWN
            
            self._status = ServerStatus.SHUTDOWN
            self._logger.info("Server shutdown completed")
            
        except Exception as e:
            self._logger.error(f"Error during shutdown: {e}", exc_info=True)
            self._status = ServerStatus.FAILED
