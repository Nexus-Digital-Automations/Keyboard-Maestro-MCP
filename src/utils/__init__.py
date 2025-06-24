# Utilities Package  
# src/utils/__init__.py

"""
Utility functions and configuration management for the Keyboard Maestro MCP Server.

This package provides essential utility functions, configuration management,
and shared functionality used throughout the server components:

Configuration Management:
- Server configuration loading and validation
- Environment-based configuration selection
- Production vs development mode handling
- Transport and authentication configuration

Logging and Monitoring:
- Structured logging configuration
- Performance analytics and metrics
- Resource monitoring and optimization
- Debug and error tracking utilities

Data Processing:
- Macro serialization and deserialization
- AppleScript utility functions
- Coordinate and geometry utilities
- Resource optimization algorithms

Features:
- Type-safe configuration with validation
- Multi-environment support (dev/prod)
- Performance monitoring and analytics
- Resource optimization and memory management
- Structured logging with multiple outputs
- Defensive programming with input validation
"""

from typing import TYPE_CHECKING

# Package metadata
__all__ = [
    "ServerConfiguration",
    "load_configuration", 
    "setup_logging",
    "MacroSerializer",
    "PerformanceAnalytics",
    "ResourceOptimizer",
]

# Conditional imports for type checking
if TYPE_CHECKING:
    from .utils.configuration import ServerConfiguration, load_configuration
    from utils.logging_config import setup_logging
    from .macro_serialization import MacroSerializer
    from .performance_analytics import PerformanceAnalytics
    from .resource_optimizer import ResourceOptimizer
