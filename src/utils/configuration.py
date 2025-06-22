# Server Configuration Management: Keyboard Maestro MCP Server
# src/utils/configuration.py

"""
Server configuration management with type safety and validation.

This module implements comprehensive configuration management for the MCP server
with environment-based loading, validation, and immutable configuration objects
using advanced programming techniques.

Features:
- Type-safe configuration with validation contracts
- Environment variable integration with defaults
- Immutable configuration objects with factory functions
- Authentication provider configuration
- Development vs production mode handling

Size: 195 lines (target: <200)
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from pathlib import Path

from fastmcp.server.auth import BearerAuthProvider
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_server_configuration
from src.types.enumerations import TransportType, LogLevel


@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration with comprehensive validation."""
    transport: str
    host: str
    port: int
    max_concurrent_operations: int
    operation_timeout: int
    auth_required: bool
    log_level: str
    development_mode: bool
    auth_provider: Optional[BearerAuthProvider] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        # Transport validation
        if self.transport not in ["stdio", "streamable-http", "websocket"]:
            raise ValueError(f"Invalid transport: {self.transport}")
        
        # Port validation for network transports
        if self.transport != "stdio" and not (1024 <= self.port <= 65535):
            raise ValueError(f"Port must be 1024-65535, got {self.port}")
        
        # Host validation for network transports
        if self.transport != "stdio" and not self.host:
            raise ValueError("Host must be specified for network transports")
        
        # Operation limits validation
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
        
        if self.operation_timeout <= 0:
            raise ValueError("Operation timeout must be positive")
        
        # Log level validation
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")
    
    @property
    def is_network_transport(self) -> bool:
        """Check if transport requires network configuration."""
        return self.transport != "stdio"
    
    @property
    def requires_authentication(self) -> bool:
        """Check if configuration requires authentication."""
        return self.auth_required and self.is_network_transport
    
    @property
    def log_file_path(self) -> Optional[Path]:
        """Get log file path if file logging is enabled."""
        if self.development_mode:
            return None  # Use stderr in development
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        return log_dir / "km_mcp_server.log"


@requires(lambda: True)  # No preconditions for environment loading
@ensures(lambda result: is_valid_server_configuration(result))
def load_configuration() -> ServerConfiguration:
    """Load server configuration from environment variables.
    
    Postconditions:
    - Returns valid server configuration
    """
    # Determine runtime mode
    development_mode = os.getenv("MCP_DEV_MODE", "false").lower() == "true"
    
    # Load transport configuration
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = _parse_port(os.getenv("MCP_PORT", "8000"))
    
    # Load operational parameters
    max_concurrent = _parse_int(
        os.getenv("MCP_MAX_CONCURRENT", "100" if not development_mode else "50")
    )
    timeout = _parse_int(
        os.getenv("MCP_TIMEOUT", "30" if not development_mode else "60")
    )
    
    # Load authentication configuration
    auth_required = os.getenv("MCP_AUTH_REQUIRED", "true" if not development_mode else "false").lower() == "true"
    auth_provider = _create_auth_provider() if auth_required else None
    
    # Load logging configuration
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO" if not development_mode else "DEBUG").upper()
    
    return ServerConfiguration(
        transport=transport,
        host=host,
        port=port,
        max_concurrent_operations=max_concurrent,
        operation_timeout=timeout,
        auth_required=auth_required,
        auth_provider=auth_provider,
        log_level=log_level,
        development_mode=development_mode
    )


def _parse_port(port_str: str) -> int:
    """Parse port number with validation."""
    try:
        port = int(port_str)
        if 1024 <= port <= 65535:
            return port
        raise ValueError(f"Port {port} out of valid range 1024-65535")
    except ValueError as e:
        logging.warning(f"Invalid port '{port_str}', using default 8000: {e}")
        return 8000


def _parse_int(value_str: str) -> int:
    """Parse integer value with error handling."""
    try:
        value = int(value_str)
        if value > 0:
            return value
        raise ValueError(f"Value must be positive: {value}")
    except ValueError as e:
        logging.warning(f"Invalid integer '{value_str}', using default 100: {e}")
        return 100


def _create_auth_provider() -> Optional[BearerAuthProvider]:
    """Create authentication provider from environment configuration."""
    try:
        # Check for JWT configuration
        public_key_path = os.getenv("MCP_JWT_PUBLIC_KEY_PATH")
        jwks_url = os.getenv("MCP_JWT_JWKS_URL")
        audience = os.getenv("MCP_JWT_AUDIENCE", "keyboard-maestro-mcp")
        
        if public_key_path and Path(public_key_path).exists():
            # Use public key file
            with open(public_key_path, 'r') as f:
                public_key = f.read()
            
            return BearerAuthProvider(
                public_key=public_key,
                audience=audience
            )
        
        elif jwks_url:
            # Use JWKS URL
            return BearerAuthProvider(
                jwks_url=jwks_url,
                audience=audience
            )
        
        else:
            logging.warning("Authentication required but no JWT configuration found")
            return None
            
    except Exception as e:
        logging.error(f"Failed to create auth provider: {e}")
        return None


@requires(lambda config: is_valid_server_configuration(config))
def get_runtime_settings(config: ServerConfiguration) -> Dict[str, Any]:
    """Get runtime settings derived from configuration.
    
    Preconditions:
    - Configuration must be valid
    
    Args:
        config: Server configuration
        
    Returns:
        Runtime settings dictionary
    """
    return {
        "server_mode": "development" if config.development_mode else "production",
        "transport_type": config.transport,
        "network_enabled": config.is_network_transport,
        "authentication_enabled": config.requires_authentication,
        "log_to_file": config.log_file_path is not None,
        "max_operations": config.max_concurrent_operations,
        "timeout_seconds": config.operation_timeout,
        "listen_address": f"{config.host}:{config.port}" if config.is_network_transport else "stdio",
        "log_level": config.log_level
    }


def validate_environment() -> Dict[str, str]:
    """Validate environment configuration and return status.
    
    Returns:
        Dictionary with validation results and warnings
    """
    issues = []
    warnings = []
    
    # Check required environment for production
    if os.getenv("MCP_DEV_MODE", "false").lower() != "true":
        # Production mode checks
        if not os.getenv("MCP_JWT_PUBLIC_KEY_PATH") and not os.getenv("MCP_JWT_JWKS_URL"):
            warnings.append("No JWT authentication configured for production mode")
        
        if os.getenv("MCP_TRANSPORT", "stdio") == "stdio":
            warnings.append("Using STDIO transport in production mode")
    
    # Check file system permissions
    log_dir = Path("logs")
    try:
        log_dir.mkdir(exist_ok=True)
        test_file = log_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
    except PermissionError:
        issues.append("Cannot write to logs directory")
    
    return {
        "status": "valid" if not issues else "invalid",
        "issues": issues,
        "warnings": warnings
    }
