# Core Components Package
# src/core/__init__.py

"""
Core server components and business logic for the Keyboard Maestro MCP Server.

This package contains the essential server components that handle:
- Server lifecycle management and initialization
- MCP tool registration and coordination
- Keyboard Maestro interface and communication
- Component orchestration and dependency injection
- Error handling and recovery mechanisms
- Performance monitoring and metrics collection

Key Components:
- mcp_server: Main server class and lifecycle management
- tool_registry: MCP tool registration and management
- km_interface: Keyboard Maestro communication interface
- context_manager: MCP context and session management
- performance_core: Performance monitoring and optimization
- applescript_pool: AppleScript execution pool management
- macro_operations: Core macro execution and management
- variable_operations: Variable and data management operations

Architecture:
- FastMCP integration with tool registration
- Async/await patterns for non-blocking operations
- Component-based architecture with clear boundaries
- Error recovery and defensive programming patterns
- Performance optimization with connection pooling
"""

from typing import TYPE_CHECKING

# Package metadata
__all__ = [
    "KeyboardMaestroMCPServer",
    "ToolRegistry", 
    "MCPContextManager",
    "KeyboardMaestroInterface",
    "MacroOperations",
    "VariableOperations",
]

# Conditional imports for type checking
if TYPE_CHECKING:
    from .core.mcp_server import KeyboardMaestroMCPServer
    from core.tool_registry import ToolRegistry
    from .context_manager import MCPContextManager
    from .km_interface import KeyboardMaestroInterface
    from .macro_operations import MacroOperations
    from .variable_operations import VariableOperations
