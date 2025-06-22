# src/types/values.py (Target: <200 lines)
"""
Value types and structured values for the Keyboard Maestro MCP Server.

This module implements immutable value types with validation and safety
constraints for all value-based domain concepts.
"""

from typing import NewType, Optional, Any, Dict, FrozenSet
from dataclasses import dataclass
from decimal import Decimal
import os


# Branded Value Types for Domain-Specific Values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)
ProcessID = NewType('ProcessID', int)
FilePath = NewType('FilePath', str)


# Value Creation Functions with Validation
def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        MacroExecutionTimeout: Validated timeout
        
    Raises:
        ValueError: If timeout is not in valid range
    """
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)


def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score.
    
    Args:
        score: Confidence score value
        
    Returns:
        ConfidenceScore: Validated score
        
    Raises:
        ValueError: If score is not between 0.0 and 1.0
    """
    import math
    if not isinstance(score, (int, float)) or math.isnan(score) or not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)


def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate.
    
    Args:
        coord: Coordinate value
        
    Returns:
        ScreenCoordinate: Validated coordinate
        
    Raises:
        ValueError: If coordinate is negative
    """
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)


def create_file_path(path: str) -> FilePath:
    """Create validated file path.
    
    Args:
        path: File system path
        
    Returns:
        FilePath: Validated path
        
    Raises:
        ValueError: If path is invalid
    """
    if not path or len(path) > 1024:
        raise ValueError("File path must be 1-1024 characters")
    
    # Basic path validation - avoid path traversal
    if ".." in path or path.startswith("/"):
        if not os.path.isabs(path):
            raise ValueError("Relative paths with '..' are not allowed")
    
    return FilePath(path)


# Structured Value Types
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates are reasonable."""
        # Basic validation - coordinates should be positive
        if self.x < 0 or self.y < 0:
            raise ValueError("Screen coordinates must be non-negative")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset.
        
        Args:
            dx: X offset
            dy: Y offset
            
        Returns:
            ScreenCoordinates: New coordinates with offset applied
        """
        return ScreenCoordinates(
            create_screen_coordinate(max(0, self.x + dx)),
            create_screen_coordinate(max(0, self.y + dy))
        )
    
    def distance_to(self, other: 'ScreenCoordinates') -> float:
        """Calculate distance to another coordinate.
        
        Args:
            other: Target coordinates
            
        Returns:
            float: Distance between coordinates
        """
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        """Calculate area width."""
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        """Calculate area height."""
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        """Calculate center coordinates."""
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
    
    def contains_point(self, point: ScreenCoordinates) -> bool:
        """Check if area contains given point.
        
        Args:
            point: Point to check
            
        Returns:
            bool: True if point is within area
        """
        return (self.top_left.x <= point.x <= self.bottom_right.x and
                self.top_left.y <= point.y <= self.bottom_right.y)


@dataclass(frozen=True)
class ColorRGB:
    """Immutable RGB color representation."""
    red: int
    green: int
    blue: int
    
    def __post_init__(self):
        """Validate color component ranges."""
        for component, name in [(self.red, 'red'), (self.green, 'green'), (self.blue, 'blue')]:
            if not 0 <= component <= 255:
                raise ValueError(f"{name} component must be 0-255")
    
    def to_hex(self) -> str:
        """Convert to hexadecimal representation.
        
        Returns:
            str: Hex color string (e.g., '#FF0000')
        """
        return f"#{self.red:02X}{self.green:02X}{self.blue:02X}"
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'ColorRGB':
        """Create color from hex string.
        
        Args:
            hex_color: Hex color string (e.g., '#FF0000' or 'FF0000')
            
        Returns:
            ColorRGB: Color object
            
        Raises:
            ValueError: If hex format is invalid
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError("Hex color must be 6 characters")
        
        try:
            red = int(hex_color[0:2], 16)
            green = int(hex_color[2:4], 16)
            blue = int(hex_color[4:6], 16)
            return cls(red, green, blue)
        except ValueError as e:
            raise ValueError(f"Invalid hex color format: {hex_color}") from e


@dataclass(frozen=True)
class NetworkEndpoint:
    """Immutable network endpoint definition."""
    host: str
    port: int
    protocol: str = "http"
    
    def __post_init__(self):
        """Validate endpoint parameters."""
        if not self.host:
            raise ValueError("Host cannot be empty")
        
        if not 1 <= self.port <= 65535:
            raise ValueError("Port must be in range 1-65535")
        
        if self.protocol not in ("http", "https", "ws", "wss"):
            raise ValueError("Protocol must be http, https, ws, or wss")
    
    @property
    def url(self) -> str:
        """Generate URL from endpoint.
        
        Returns:
            str: Complete URL
        """
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def is_secure(self) -> bool:
        """Check if endpoint uses secure protocol.
        
        Returns:
            bool: True if using HTTPS or WSS
        """
        return self.protocol in ("https", "wss")
