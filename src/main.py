# FastMCP Server Entry Point: Keyboard Maestro MCP Server
# src/main.py

"""
FastMCP server entry point with configuration and startup logic.

This module provides the main entry point for the Keyboard Maestro MCP Server,
implementing FastMCP initialization, transport configuration, and graceful
startup/shutdown procedures with comprehensive error handling.

Features:
- Multi-transport support (STDIO/HTTP) with environment-based selection
- Graceful shutdown handling with cleanup procedures
- Configuration loading and validation
- Comprehensive logging setup
- Development vs production mode selection

Size: 186 lines (target: <200)
"""

import asyncio
import signal
import sys
import os
import logging
from typing import Optional
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.auth import BearerAuthProvider

from src.core.mcp_server import KeyboardMaestroMCPServer
from src.utils.configuration import ServerConfiguration, load_configuration
from src.utils.logging_config import setup_logging
from src.contracts.validators import is_valid_server_configuration
from src.contracts.decorators import requires, ensures


# Global server instance for signal handling
_server_instance: Optional[KeyboardMaestroMCPServer] = None


@requires(lambda config: is_valid_server_configuration(config))
@ensures(lambda result: result is not None)
def create_mcp_server(config: ServerConfiguration) -> FastMCP:
    """Create and configure FastMCP server instance.
    
    Preconditions:
    - Configuration must be valid and complete
    
    Postconditions:
    - Returns configured FastMCP server instance
    """
    # Create FastMCP instance with basic configuration
    mcp = FastMCP(
        name="keyboard-maestro-mcp-server",
        version="1.0.0",
        instructions="Comprehensive Keyboard Maestro automation server providing "
                    "50+ MCP tools for intelligent macOS workflow automation."
    )
    
    # Configure authentication if required
    if config.auth_required and config.auth_provider:
        mcp = FastMCP(
            name="keyboard-maestro-mcp-server",
            version="1.0.0",
            auth=config.auth_provider
        )
    
    return mcp


@requires(lambda transport: transport in ["stdio", "streamable-http"])
def setup_signal_handlers(transport: str) -> None:
    """Setup graceful shutdown signal handlers.
    
    Preconditions:
    - Transport type must be supported
    """
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        if _server_instance:
            # Trigger cleanup in server instance
            asyncio.create_task(_server_instance.shutdown())
        
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Additional signals for Unix systems
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)


def determine_transport_config() -> tuple[str, Optional[str], Optional[int]]:
    """Determine transport configuration from environment.
    
    Returns:
        Tuple of (transport_type, host, port)
    """
    # Check environment variables for transport configuration
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port_str = os.getenv("MCP_PORT", "8000")
    
    try:
        port = int(port_str) if port_str else 8000
    except ValueError:
        port = 8000
    
    # Validate transport type
    if transport not in ["stdio", "streamable-http", "sse"]:
        transport = "stdio"
    
    return transport, host if transport != "stdio" else None, port if transport != "stdio" else None


def setup_development_mode() -> ServerConfiguration:
    """Setup server configuration for development mode."""
    return ServerConfiguration(
        transport="stdio",
        host="127.0.0.1",
        port=8000,
        max_concurrent_operations=50,
        operation_timeout=60,
        auth_required=False,
        log_level="DEBUG",
        development_mode=True
    )


def setup_production_mode() -> ServerConfiguration:
    """Setup server configuration for production mode."""
    transport, host, port = determine_transport_config()
    
    return ServerConfiguration(
        transport=transport,
        host=host or "127.0.0.1",
        port=port or 8000,
        max_concurrent_operations=100,
        operation_timeout=30,
        auth_required=True,
        log_level="INFO",
        development_mode=False
    )


async def initialize_server(config: ServerConfiguration) -> KeyboardMaestroMCPServer:
    """Initialize the Keyboard Maestro MCP Server with configuration.
    
    Returns:
        Configured and initialized server instance
    """
    # Create core server instance
    server = KeyboardMaestroMCPServer(config)
    
    # Initialize server components
    await server.initialize()
    
    return server


def main() -> None:
    """Main entry point for the Keyboard Maestro MCP Server."""
    global _server_instance
    
    try:
        # Determine runtime mode
        development_mode = os.getenv("MCP_DEV_MODE", "false").lower() == "true"
        
        # Load configuration
        if development_mode:
            config = setup_development_mode()
        else:
            config = setup_production_mode()
        
        # Setup logging
        setup_logging(config.log_level, development_mode)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting Keyboard Maestro MCP Server in {config.transport} mode")
        logger.info(f"Development mode: {development_mode}")
        
        # Setup signal handlers
        setup_signal_handlers(config.transport)
        
        # Create FastMCP server
        mcp = create_mcp_server(config)
        
        # Initialize and run server
        async def run_server():
            global _server_instance
            
            # Initialize server components
            _server_instance = await initialize_server(config)
            
            # Register all MCP tools with FastMCP
            await _server_instance.register_tools(mcp)
            
            logger.info("Server initialization complete")
            
            # Run server with appropriate transport
            if config.transport == "stdio":
                logger.info("Starting STDIO transport")
                mcp.run(transport="stdio")
            else:
                logger.info(f"Starting HTTP transport on {config.host}:{config.port}")
                mcp.run(
                    transport="streamable-http",
                    host=config.host,
                    port=config.port
                )
        
        # Run the server
        asyncio.run(run_server())
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Keyboard Maestro MCP Server shutdown complete")


if __name__ == "__main__":
    main()
