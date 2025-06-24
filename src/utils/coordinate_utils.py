"""Screen coordinate utilities with bounds validation and defensive programming.

This module provides coordinate validation and transformation utilities for screen-based
operations with comprehensive bounds checking and error recovery.
"""

from typing import NamedTuple, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import json

from .contracts.decorators import requires, ensures
from src.contracts.exceptions import ValidationError
from src.types.domain_types import ScreenCoordinates, ScreenArea


class DisplayInfo(NamedTuple):
    """Display information with bounds and properties."""
    width: int
    height: int
    origin_x: int
    origin_y: int
    scale_factor: float
    is_main: bool


class CoordinateValidationResult(NamedTuple):
    """Result of coordinate validation with error details."""
    is_valid: bool
    error_message: Optional[str]
    adjusted_coordinates: Optional[ScreenCoordinates]


@dataclass(frozen=True)
class ScreenBounds:
    """Screen bounds with validation methods."""
    width: int
    height: int
    origin_x: int = 0
    origin_y: int = 0
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within bounds."""
        return (self.origin_x <= x <= self.origin_x + self.width and
                self.origin_y <= y <= self.origin_y + self.height)
    
    def contains_area(self, area: ScreenArea) -> bool:
        """Check if entire area is within bounds."""
        return (self.contains_point(area.x, area.y) and
                self.contains_point(area.x + area.width, area.y + area.height))


class CoordinateValidator:
    """Validates and adjusts screen coordinates with defensive programming."""
    
    def __init__(self):
        self._display_cache: Optional[List[DisplayInfo]] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = 5.0  # Cache displays for 5 seconds
    
    def get_display_info(self, force_refresh: bool = False) -> List[DisplayInfo]:
        """Get current display information with caching."""
        import time
        
        current_time = time.time()
        if (not force_refresh and 
            self._display_cache is not None and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._display_cache
        
        try:
            displays = self._query_displays()
            self._display_cache = displays
            self._cache_timestamp = current_time
            return displays
        except Exception as e:
            # Fallback to safe defaults if display query fails
            if self._display_cache:
                return self._display_cache
            return [DisplayInfo(1920, 1080, 0, 0, 1.0, True)]
    
    def _query_displays(self) -> List[DisplayInfo]:
        """Query system for current display configuration."""
        try:
            # Use system_profiler for display information
            result = subprocess.run([
                'system_profiler', 'SPDisplaysDataType', '-json'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                raise RuntimeError("Failed to query displays")
            
            data = json.loads(result.stdout)
            displays = []
            
            for item in data.get('SPDisplaysDataType', []):
                displays_list = item.get('spdisplays_ndrvs', [])
                for display in displays_list:
                    resolution = display.get('_spdisplays_resolution', '1920 x 1080')
                    width, height = self._parse_resolution(resolution)
                    
                    displays.append(DisplayInfo(
                        width=width,
                        height=height,
                        origin_x=0,  # Simplified - would need additional queries for multi-monitor
                        origin_y=0,
                        scale_factor=1.0,  # Simplified
                        is_main=len(displays) == 0
                    ))
            
            return displays if displays else [DisplayInfo(1920, 1080, 0, 0, 1.0, True)]
            
        except Exception:
            # Fallback to reasonable defaults
            return [DisplayInfo(1920, 1080, 0, 0, 1.0, True)]
    
    def _parse_resolution(self, resolution_str: str) -> Tuple[int, int]:
        """Parse resolution string safely."""
        try:
            parts = resolution_str.split(' x ')
            if len(parts) >= 2:
                width = int(parts[0].strip())
                height = int(parts[1].strip())
                return width, height
        except (ValueError, IndexError):
            pass
        return 1920, 1080  # Safe default
    
    @requires(lambda coordinates: coordinates is not None)
    @ensures(lambda result: result.is_valid or result.error_message is not None)
    def validate_coordinates(self, coordinates: ScreenCoordinates) -> CoordinateValidationResult:
        """Validate coordinates against current display configuration."""
        try:
            displays = self.get_display_info()
            
            # Check if coordinates are within any display
            for display in displays:
                bounds = ScreenBounds(display.width, display.height, display.origin_x, display.origin_y)
                if bounds.contains_point(coordinates.x, coordinates.y):
                    return CoordinateValidationResult(True, None, coordinates)
            
            # Try to adjust coordinates to nearest valid position
            main_display = next((d for d in displays if d.is_main), displays[0])
            adjusted = self._adjust_to_bounds(coordinates, main_display)
            
            return CoordinateValidationResult(
                False,
                f"Coordinates ({coordinates.x}, {coordinates.y}) outside display bounds",
                adjusted
            )
            
        except Exception as e:
            return CoordinateValidationResult(
                False,
                f"Validation failed: {str(e)}",
                None
            )
    
    def _adjust_to_bounds(self, coordinates: ScreenCoordinates, display: DisplayInfo) -> ScreenCoordinates:
        """Adjust coordinates to fit within display bounds."""
        adjusted_x = max(display.origin_x, min(coordinates.x, display.origin_x + display.width - 1))
        adjusted_y = max(display.origin_y, min(coordinates.y, display.origin_y + display.height - 1))
        
        return ScreenCoordinates(adjusted_x, adjusted_y)
    
    @requires(lambda area: area is not None)
    @ensures(lambda result: result.is_valid or result.error_message is not None)
    def validate_screen_area(self, area: ScreenArea) -> CoordinateValidationResult:
        """Validate screen area bounds."""
        try:
            # Validate area dimensions
            if area.width <= 0 or area.height <= 0:
                return CoordinateValidationResult(
                    False,
                    f"Invalid area dimensions: {area.width}x{area.height}",
                    None
                )
            
            displays = self.get_display_info()
            
            # Check if area fits within any display
            for display in displays:
                bounds = ScreenBounds(display.width, display.height, display.origin_x, display.origin_y)
                if bounds.contains_area(area):
                    return CoordinateValidationResult(True, None, None)
            
            return CoordinateValidationResult(
                False,
                f"Area {area.x},{area.y} {area.width}x{area.height} exceeds display bounds",
                None
            )
            
        except Exception as e:
            return CoordinateValidationResult(
                False,
                f"Area validation failed: {str(e)}",
                None
            )
    
    def get_safe_click_area(self, target_x: int, target_y: int, 
                           margin: int = 10) -> Optional[ScreenArea]:
        """Get safe clickable area around target coordinates."""
        try:
            coordinates = ScreenCoordinates(target_x, target_y)
            validation = self.validate_coordinates(coordinates)
            
            if not validation.is_valid:
                return None
            
            # Create area with margin around target
            area = ScreenArea(
                x=max(0, target_x - margin),
                y=max(0, target_y - margin),
                width=margin * 2,
                height=margin * 2
            )
            
            area_validation = self.validate_screen_area(area)
            return area if area_validation.is_valid else None
            
        except Exception:
            return None


# Global validator instance for use across modules
coordinate_validator = CoordinateValidator()


def validate_screen_coordinates(x: int, y: int) -> bool:
    """Simple coordinate validation function."""
    coordinates = ScreenCoordinates(x, y)
    result = coordinate_validator.validate_coordinates(coordinates)
    return result.is_valid


def get_main_display_bounds() -> ScreenBounds:
    """Get main display bounds with error handling."""
    try:
        displays = coordinate_validator.get_display_info()
        main_display = next((d for d in displays if d.is_main), displays[0])
        return ScreenBounds(main_display.width, main_display.height)
    except Exception:
        return ScreenBounds(1920, 1080)  # Safe default


def normalize_coordinates(x: int, y: int) -> Tuple[int, int]:
    """Normalize coordinates to valid screen bounds."""
    try:
        coordinates = ScreenCoordinates(x, y)
        validation = coordinate_validator.validate_coordinates(coordinates)
        
        if validation.is_valid:
            return x, y
        elif validation.adjusted_coordinates:
            return validation.adjusted_coordinates.x, validation.adjusted_coordinates.y
        else:
            # Fallback to screen center
            bounds = get_main_display_bounds()
            return bounds.width // 2, bounds.height // 2
    except Exception:
        return 960, 540  # Safe center default
