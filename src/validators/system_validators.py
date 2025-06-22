"""System operation validation with defensive programming patterns.

This module provides comprehensive validation for system operations including
file operations, application control, and interface automation with error recovery.
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
import os

from src.contracts.decorators import requires, ensures
from src.contracts.exceptions import ValidationError
from src.types.domain_types import ScreenCoordinates, ScreenArea
from src.boundaries.permission_checker import permission_checker, PermissionType
from src.utils.coordinate_utils import coordinate_validator


class ValidationResult(Enum):
    """Result of validation operations."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass(frozen=True)
class SystemValidationResult:
    """Result of system operation validation."""
    is_valid: bool
    result_type: ValidationResult
    error_message: Optional[str] = None
    warnings: List[str] = None
    sanitized_input: Optional[Any] = None
    recovery_suggestion: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])


class SystemOperationValidator:
    """Comprehensive system operation validation with defensive programming."""
    
    def __init__(self):
        self._app_bundle_pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]+$')
        self._safe_filename_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        self._dangerous_paths = {
            '/System', '/usr/bin', '/usr/sbin', '/bin', '/sbin',
            '/private/etc', '/Library/System'
        }
        self._max_path_length = 1024
        self._max_filename_length = 255
    
    @requires(lambda path: isinstance(path, (str, Path)))
    @ensures(lambda result: isinstance(result, SystemValidationResult))
    def validate_file_path(self, path: Union[str, Path], 
                          operation: str = "read") -> SystemValidationResult:
        """Validate file path with comprehensive security checks."""
        try:
            # Convert to Path object
            if isinstance(path, str):
                if len(path) > self._max_path_length:
                    return SystemValidationResult(
                        False, ValidationResult.INVALID,
                        f"Path too long: {len(path)} > {self._max_path_length}",
                        recovery_suggestion="Use shorter path"
                    )
                path_obj = Path(path).expanduser()
            else:
                path_obj = path.expanduser()
            
            # Resolve path safely
            try:
                resolved_path = path_obj.resolve()
            except (OSError, RuntimeError) as e:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Path resolution failed: {str(e)}",
                    recovery_suggestion="Check path format and existence"
                )
            
            warnings = []
            
            # Check for dangerous paths
            if self._is_dangerous_path(resolved_path):
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Access to system path denied: {resolved_path}",
                    recovery_suggestion="Use user-accessible paths only"
                )
            
            # Check path traversal attempts
            if '..' in str(path_obj):
                warnings.append("Path contains parent directory references")
            
            # Check filename length
            if len(resolved_path.name) > self._max_filename_length:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Filename too long: {len(resolved_path.name)}",
                    recovery_suggestion="Use shorter filename"
                )
            
            # Check permissions based on operation
            if operation in ("read", "execute"):
                perm_result = permission_checker.check_permission(
                    PermissionType.FILE_READ, str(resolved_path)
                )
            elif operation == "write":
                perm_result = permission_checker.check_permission(
                    PermissionType.FILE_WRITE, str(resolved_path)
                )
            else:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Unknown operation: {operation}",
                    recovery_suggestion="Use 'read', 'write', or 'execute'"
                )
            
            if perm_result.status.value != "granted":
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Permission denied: {perm_result.details}",
                    recovery_suggestion=perm_result.recovery_suggestion
                )
            
            # Path validation successful
            return SystemValidationResult(
                True, ValidationResult.VALID,
                sanitized_input=str(resolved_path),
                warnings=warnings
            )
            
        except Exception as e:
            return SystemValidationResult(
                False, ValidationResult.INVALID,
                f"Path validation failed: {str(e)}",
                recovery_suggestion="Check path format and permissions"
            )
    
    def _is_dangerous_path(self, path: Path) -> bool:
        """Check if path is in dangerous system locations."""
        try:
            path_str = str(path)
            return any(path_str.startswith(dangerous) for dangerous in self._dangerous_paths)
        except Exception:
            return True  # Err on side of caution
    
    @requires(lambda app_id: isinstance(app_id, str) and len(app_id) > 0)
    @ensures(lambda result: isinstance(result, SystemValidationResult))
    def validate_application_identifier(self, app_id: str) -> SystemValidationResult:
        """Validate application identifier (bundle ID or name)."""
        try:
            warnings = []
            sanitized_id = app_id.strip()
            
            if not sanitized_id:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    "Empty application identifier",
                    recovery_suggestion="Provide valid bundle ID or application name"
                )
            
            # Check if it looks like a bundle ID
            if self._app_bundle_pattern.match(sanitized_id):
                # Bundle ID format (e.g., com.apple.finder)
                if len(sanitized_id) > 200:
                    return SystemValidationResult(
                        False, ValidationResult.INVALID,
                        "Bundle ID too long",
                        recovery_suggestion="Use shorter bundle identifier"
                    )
                
                return SystemValidationResult(
                    True, ValidationResult.VALID,
                    sanitized_input=sanitized_id,
                    warnings=warnings
                )
            
            # Application name format
            if len(sanitized_id) > 100:
                warnings.append("Application name is unusually long")
            
            # Check for dangerous characters in app name
            dangerous_chars = ['/', '\\', '..', '\x00']
            if any(char in sanitized_id for char in dangerous_chars):
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    "Application name contains dangerous characters",
                    recovery_suggestion="Use alphanumeric characters and spaces only"
                )
            
            return SystemValidationResult(
                True, ValidationResult.VALID,
                sanitized_input=sanitized_id,
                warnings=warnings
            )
            
        except Exception as e:
            return SystemValidationResult(
                False, ValidationResult.INVALID,
                f"Application ID validation failed: {str(e)}",
                recovery_suggestion="Check application identifier format"
            )
    
    @requires(lambda coordinates: coordinates is not None)
    @ensures(lambda result: isinstance(result, SystemValidationResult))
    def validate_screen_coordinates(self, coordinates: ScreenCoordinates) -> SystemValidationResult:
        """Validate screen coordinates with bounds checking."""
        try:
            # Use coordinate validator for bounds checking
            coord_result = coordinate_validator.validate_coordinates(coordinates)
            
            if coord_result.is_valid:
                return SystemValidationResult(
                    True, ValidationResult.VALID,
                    sanitized_input=coordinates
                )
            else:
                warnings = []
                if coord_result.adjusted_coordinates:
                    warnings.append("Coordinates adjusted to fit screen bounds")
                    return SystemValidationResult(
                        True, ValidationResult.WARNING,
                        error_message=coord_result.error_message,
                        warnings=warnings,
                        sanitized_input=coord_result.adjusted_coordinates,
                        recovery_suggestion="Use adjusted coordinates or verify screen setup"
                    )
                else:
                    return SystemValidationResult(
                        False, ValidationResult.INVALID,
                        coord_result.error_message,
                        recovery_suggestion="Check coordinates are within screen bounds"
                    )
                    
        except Exception as e:
            return SystemValidationResult(
                False, ValidationResult.INVALID,
                f"Coordinate validation failed: {str(e)}",
                recovery_suggestion="Verify coordinate format and screen configuration"
            )
    
    @requires(lambda command: isinstance(command, str) and len(command) > 0)
    @ensures(lambda result: isinstance(result, SystemValidationResult))
    def validate_system_command(self, command: str) -> SystemValidationResult:
        """Validate system command for security."""
        try:
            sanitized_command = command.strip()
            
            if not sanitized_command:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    "Empty command",
                    recovery_suggestion="Provide valid command"
                )
            
            if len(sanitized_command) > 2048:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    "Command too long",
                    recovery_suggestion="Use shorter command"
                )
            
            # Check command safety
            if not permission_checker.is_command_safe(sanitized_command):
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    "Command contains restricted operations",
                    recovery_suggestion="Use safe command alternatives"
                )
            
            warnings = []
            
            # Check for shell injection patterns
            dangerous_patterns = [
                r';|\||\&\&|\|\|',  # Command chaining
                r'\$\(',  # Command substitution
                r'`',     # Backticks
                r'>\s*/dev/',  # Device redirection
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, sanitized_command):
                    warnings.append("Command contains shell metacharacters")
                    break
            
            return SystemValidationResult(
                True, ValidationResult.VALID,
                sanitized_input=sanitized_command,
                warnings=warnings
            )
            
        except Exception as e:
            return SystemValidationResult(
                False, ValidationResult.INVALID,
                f"Command validation failed: {str(e)}",
                recovery_suggestion="Check command syntax and safety"
            )
    
    @requires(lambda text: isinstance(text, str))
    @ensures(lambda result: isinstance(result, SystemValidationResult))
    def validate_input_text(self, text: str, max_length: int = 10000) -> SystemValidationResult:
        """Validate input text with length and content checks."""
        try:
            if len(text) > max_length:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Text too long: {len(text)} > {max_length}",
                    recovery_suggestion="Reduce text length"
                )
            
            warnings = []
            
            # Check for potentially dangerous content
            if '\x00' in text:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    "Text contains null bytes",
                    recovery_suggestion="Remove null characters"
                )
            
            # Check for excessive control characters
            control_char_count = sum(1 for c in text if ord(c) < 32 and c not in '\t\n\r')
            if control_char_count > 10:
                warnings.append("Text contains many control characters")
            
            # Basic sanitization - remove dangerous characters but preserve functionality
            sanitized_text = text.replace('\x00', '').replace('\x08', '')
            
            return SystemValidationResult(
                True, ValidationResult.VALID,
                sanitized_input=sanitized_text,
                warnings=warnings
            )
            
        except Exception as e:
            return SystemValidationResult(
                False, ValidationResult.INVALID,
                f"Text validation failed: {str(e)}",
                recovery_suggestion="Check text format and encoding"
            )
    
    @requires(lambda area: area is not None)
    @ensures(lambda result: isinstance(result, SystemValidationResult))
    def validate_screen_area(self, area: ScreenArea) -> SystemValidationResult:
        """Validate screen area bounds and dimensions."""
        try:
            # Validate dimensions
            if area.width <= 0 or area.height <= 0:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Invalid area dimensions: {area.width}x{area.height}",
                    recovery_suggestion="Use positive width and height values"
                )
            
            # Check maximum reasonable area size
            max_area = 7680 * 4320  # 8K resolution
            if area.width * area.height > max_area:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    f"Area too large: {area.width * area.height} pixels",
                    recovery_suggestion="Reduce area size"
                )
            
            # Use coordinate validator for bounds checking
            coord_result = coordinate_validator.validate_screen_area(area)
            
            if coord_result.is_valid:
                return SystemValidationResult(
                    True, ValidationResult.VALID,
                    sanitized_input=area
                )
            else:
                return SystemValidationResult(
                    False, ValidationResult.INVALID,
                    coord_result.error_message,
                    recovery_suggestion="Adjust area to fit within screen bounds"
                )
                
        except Exception as e:
            return SystemValidationResult(
                False, ValidationResult.INVALID,
                f"Area validation failed: {str(e)}",
                recovery_suggestion="Check area parameters and screen configuration"
            )


# Global validator instance
system_validator = SystemOperationValidator()


def validate_file_operation(path: str, operation: str = "read") -> bool:
    """Simple file operation validation."""
    try:
        result = system_validator.validate_file_path(path, operation)
        return result.is_valid
    except Exception:
        return False


def validate_application_operation(app_id: str) -> bool:
    """Simple application operation validation."""
    try:
        result = system_validator.validate_application_identifier(app_id)
        return result.is_valid
    except Exception:
        return False


def validate_coordinate_operation(x: int, y: int) -> bool:
    """Simple coordinate operation validation."""
    try:
        coordinates = ScreenCoordinates(x, y)
        result = system_validator.validate_screen_coordinates(coordinates)
        return result.is_valid or result.result_type == ValidationResult.WARNING
    except Exception:
        return False
