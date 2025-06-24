# Keyboard Maestro MCP Server Package
# src/__init__.py

"""
Main package for the Keyboard Maestro MCP Server.

This package provides comprehensive macOS automation capabilities through
the Model Context Protocol (MCP), enabling AI assistants to interact
with Keyboard Maestro for intelligent workflow automation.

Package Structure:
- boundaries/: Security and input validation boundaries
- contracts/: Design by Contract decorators and validators
- core/: Core server logic and component management
- interfaces/: External API interfaces and transport management
- pure/: Pure functional transformations and data operations
- tools/: MCP tool implementations for Keyboard Maestro operations
- types/: Domain types, branded types, and type system
- utils/: Utility functions and configuration management
- validators/: Input validation and sanitization functions

Features:
- 50+ MCP tools for comprehensive macOS automation
- Advanced security boundaries with multi-layer validation
- Type-driven development with branded domain types
- Contract-based programming with preconditions/postconditions
- Property-based testing infrastructure
- Performance monitoring and optimization
- Plugin management system with security isolation
"""

from typing import TYPE_CHECKING

# Version information
__version__ = "1.0.0"
__author__ = "Keyboard Maestro MCP Development Team"
__description__ = "Comprehensive macOS automation server for AI assistants"

# Package-level exports for external access
__all__ = [
    "__version__",
    "__author__", 
    "__description__",
]

# Conditional imports for type checking to avoid circular dependencies
if TYPE_CHECKING:
    from .core.mcp_server import KeyboardMaestroMCPServer
    from .utils.configuration import ServerConfiguration
    from .types.domain_types import ServerStatus, ComponentStatus
