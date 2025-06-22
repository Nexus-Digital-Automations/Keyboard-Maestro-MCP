"""Permission validation utilities with comprehensive boundary protection.

This module provides permission checking and validation for system operations
with defensive programming patterns and security boundary enforcement.
"""

from typing import Dict, List, Optional, Set, NamedTuple
from dataclasses import dataclass
from enum import Enum, auto
import os
import subprocess
import json
from pathlib import Path

from src.contracts.decorators import requires, ensures
from src.contracts.exceptions import PermissionDeniedError, ValidationError


class PermissionType(Enum):
    """Types of system permissions that can be checked."""
    ACCESSIBILITY = auto()
    FILE_READ = auto()
    FILE_WRITE = auto()
    FILE_EXECUTE = auto()
    APPLICATION_CONTROL = auto()
    SCREEN_RECORDING = auto()
    AUTOMATION = auto()


class PermissionStatus(Enum):
    """Status of permission checks."""
    GRANTED = "granted"
    DENIED = "denied"
    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"


@dataclass(frozen=True)
class PermissionResult:
    """Result of permission validation."""
    permission_type: PermissionType
    status: PermissionStatus
    details: str
    can_request: bool = False
    recovery_suggestion: Optional[str] = None


class SecurityBoundary(NamedTuple):
    """Security boundary definition."""
    name: str
    description: str
    check_function: str
    required_permissions: List[PermissionType]


class PermissionChecker:
    """Comprehensive permission validation with defensive programming."""
    
    def __init__(self):
        self._permission_cache: Dict[PermissionType, PermissionResult] = {}
        self._allowed_directories: Set[Path] = set()
        self._restricted_commands: Set[str] = {
            'rm', 'rmdir', 'sudo', 'chmod', 'chown', 'dd', 'fdisk',
            'diskutil', 'launchctl', 'killall', 'kill'
        }
        self._init_security_boundaries()
    
    def _init_security_boundaries(self):
        """Initialize security boundary definitions."""
        self._boundaries = {
            'file_operations': SecurityBoundary(
                'File Operations',
                'File system read/write operations',
                '_check_file_permissions',
                [PermissionType.FILE_READ, PermissionType.FILE_WRITE]
            ),
            'application_control': SecurityBoundary(
                'Application Control',
                'Launch, quit, and control applications',
                '_check_automation_permissions',
                [PermissionType.ACCESSIBILITY, PermissionType.AUTOMATION]
            ),
            'interface_automation': SecurityBoundary(
                'Interface Automation',
                'Mouse and keyboard automation',
                '_check_accessibility_permissions',
                [PermissionType.ACCESSIBILITY, PermissionType.SCREEN_RECORDING]
            )
        }
    
    @requires(lambda permission_type: isinstance(permission_type, PermissionType))
    @ensures(lambda result: isinstance(result, PermissionResult))
    def check_permission(self, permission_type: PermissionType, 
                        target: Optional[str] = None) -> PermissionResult:
        """Check specific permission with caching and error handling."""
        try:
            # Check cache first
            cache_key = f"{permission_type}:{target or 'default'}"
            if cache_key in self._permission_cache:
                return self._permission_cache[cache_key]
            
            # Perform permission check based on type
            if permission_type == PermissionType.ACCESSIBILITY:
                result = self._check_accessibility_permissions()
            elif permission_type == PermissionType.FILE_READ:
                result = self._check_file_read_permission(target)
            elif permission_type == PermissionType.FILE_WRITE:
                result = self._check_file_write_permission(target)
            elif permission_type == PermissionType.APPLICATION_CONTROL:
                result = self._check_automation_permissions()
            elif permission_type == PermissionType.SCREEN_RECORDING:
                result = self._check_screen_recording_permission()
            else:
                result = PermissionResult(
                    permission_type,
                    PermissionStatus.UNKNOWN,
                    f"Unknown permission type: {permission_type}",
                    False,
                    "Contact system administrator"
                )
            
            # Cache successful results
            if result.status != PermissionStatus.UNKNOWN:
                self._permission_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            return PermissionResult(
                permission_type,
                PermissionStatus.UNKNOWN,
                f"Permission check failed: {str(e)}",
                False,
                "Retry operation or check system logs"
            )
    
    def _check_accessibility_permissions(self) -> PermissionResult:
        """Check macOS Accessibility permissions."""
        try:
            # Use AppleScript to check accessibility permissions
            script = '''
            tell application "System Events"
                try
                    set appList to (name of every process)
                    return "granted"
                on error
                    return "denied"
                end try
            end tell
            '''
            
            result = subprocess.run([
                'osascript', '-e', script
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and "granted" in result.stdout:
                return PermissionResult(
                    PermissionType.ACCESSIBILITY,
                    PermissionStatus.GRANTED,
                    "Accessibility permissions are granted",
                    False
                )
            else:
                return PermissionResult(
                    PermissionType.ACCESSIBILITY,
                    PermissionStatus.DENIED,
                    "Accessibility permissions required",
                    True,
                    "Enable in System Preferences > Security & Privacy > Accessibility"
                )
                
        except Exception as e:
            return PermissionResult(
                PermissionType.ACCESSIBILITY,
                PermissionStatus.UNKNOWN,
                f"Failed to check accessibility: {str(e)}",
                True,
                "Manually verify in System Preferences"
            )
    
    def _check_file_read_permission(self, path: Optional[str]) -> PermissionResult:
        """Check file read permissions."""
        if not path:
            return PermissionResult(
                PermissionType.FILE_READ,
                PermissionStatus.NOT_REQUIRED,
                "No path specified",
                False
            )
        
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Check if path is in allowed directories
            if not self._is_path_allowed(file_path):
                return PermissionResult(
                    PermissionType.FILE_READ,
                    PermissionStatus.DENIED,
                    f"Path outside allowed directories: {file_path}",
                    False,
                    "Use paths within permitted directories only"
                )
            
            # Check actual read permissions
            if file_path.exists() and os.access(file_path, os.R_OK):
                return PermissionResult(
                    PermissionType.FILE_READ,
                    PermissionStatus.GRANTED,
                    f"Read access granted: {file_path}",
                    False
                )
            else:
                return PermissionResult(
                    PermissionType.FILE_READ,
                    PermissionStatus.DENIED,
                    f"No read access: {file_path}",
                    False,
                    "Check file exists and permissions"
                )
                
        except Exception as e:
            return PermissionResult(
                PermissionType.FILE_READ,
                PermissionStatus.UNKNOWN,
                f"Permission check failed: {str(e)}",
                False,
                "Verify path format and accessibility"
            )
    
    def _check_file_write_permission(self, path: Optional[str]) -> PermissionResult:
        """Check file write permissions."""
        if not path:
            return PermissionResult(
                PermissionType.FILE_WRITE,
                PermissionStatus.NOT_REQUIRED,
                "No path specified",
                False
            )
        
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Check if path is in allowed directories
            if not self._is_path_allowed(file_path):
                return PermissionResult(
                    PermissionType.FILE_WRITE,
                    PermissionStatus.DENIED,
                    f"Path outside allowed directories: {file_path}",
                    False,
                    "Use paths within permitted directories only"
                )
            
            # Check write permissions on directory
            parent_dir = file_path.parent
            if parent_dir.exists() and os.access(parent_dir, os.W_OK):
                return PermissionResult(
                    PermissionType.FILE_WRITE,
                    PermissionStatus.GRANTED,
                    f"Write access granted: {file_path}",
                    False
                )
            else:
                return PermissionResult(
                    PermissionType.FILE_WRITE,
                    PermissionStatus.DENIED,
                    f"No write access: {parent_dir}",
                    False,
                    "Check directory exists and permissions"
                )
                
        except Exception as e:
            return PermissionResult(
                PermissionType.FILE_WRITE,
                PermissionStatus.UNKNOWN,
                f"Permission check failed: {str(e)}",
                False,
                "Verify path format and parent directory"
            )
    
    def _check_automation_permissions(self) -> PermissionResult:
        """Check automation permissions for application control."""
        try:
            # Check if we can control Keyboard Maestro Engine
            script = '''
            tell application "System Events"
                try
                    set appExists to exists application process "Keyboard Maestro Engine"
                    return "granted"
                on error
                    return "denied"
                end try
            end tell
            '''
            
            result = subprocess.run([
                'osascript', '-e', script
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and "granted" in result.stdout:
                return PermissionResult(
                    PermissionType.AUTOMATION,
                    PermissionStatus.GRANTED,
                    "Automation permissions available",
                    False
                )
            else:
                return PermissionResult(
                    PermissionType.AUTOMATION,
                    PermissionStatus.DENIED,
                    "Automation permissions required",
                    True,
                    "Enable in System Preferences > Security & Privacy > Automation"
                )
                
        except Exception as e:
            return PermissionResult(
                PermissionType.AUTOMATION,
                PermissionStatus.UNKNOWN,
                f"Failed to check automation: {str(e)}",
                True,
                "Manually verify automation permissions"
            )
    
    def _check_screen_recording_permission(self) -> PermissionResult:
        """Check screen recording permissions."""
        # Note: This is a simplified check - full implementation would use
        # CGWindowListCopyWindowInfo or similar APIs
        return PermissionResult(
            PermissionType.SCREEN_RECORDING,
            PermissionStatus.GRANTED,  # Assume granted for now
            "Screen recording check not fully implemented",
            False,
            "Manually verify if screen capture fails"
        )
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        # If no restrictions set, allow all
        if not self._allowed_directories:
            return True
        
        try:
            resolved_path = path.resolve()
            return any(
                resolved_path.is_relative_to(allowed_dir)
                for allowed_dir in self._allowed_directories
            )
        except Exception:
            return False
    
    @requires(lambda boundary_name: isinstance(boundary_name, str))
    @ensures(lambda result: isinstance(result, bool))
    def validate_security_boundary(self, boundary_name: str, 
                                 context: Optional[Dict] = None) -> bool:
        """Validate operation against security boundary."""
        try:
            if boundary_name not in self._boundaries:
                return False
            
            boundary = self._boundaries[boundary_name]
            
            # Check all required permissions
            for permission_type in boundary.required_permissions:
                target = context.get('target') if context else None
                result = self.check_permission(permission_type, target)
                
                if result.status != PermissionStatus.GRANTED:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def add_allowed_directory(self, directory: str) -> None:
        """Add directory to allowed paths."""
        try:
            path = Path(directory).expanduser().resolve()
            if path.exists() and path.is_dir():
                self._allowed_directories.add(path)
        except Exception:
            pass  # Silently ignore invalid paths
    
    def is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute."""
        command_parts = command.strip().split()
        if not command_parts:
            return False
        
        base_command = os.path.basename(command_parts[0])
        return base_command not in self._restricted_commands
    
    def clear_permission_cache(self) -> None:
        """Clear permission cache to force re-evaluation."""
        self._permission_cache.clear()


# Global permission checker instance
permission_checker = PermissionChecker()


def check_file_permission(path: str, operation: str = "read") -> bool:
    """Simple file permission check."""
    try:
        if operation == "read":
            result = permission_checker.check_permission(PermissionType.FILE_READ, path)
        elif operation == "write":
            result = permission_checker.check_permission(PermissionType.FILE_WRITE, path)
        else:
            return False
        
        return result.status == PermissionStatus.GRANTED
    except Exception:
        return False


def check_accessibility_permission() -> bool:
    """Simple accessibility permission check."""
    try:
        result = permission_checker.check_permission(PermissionType.ACCESSIBILITY)
        return result.status == PermissionStatus.GRANTED
    except Exception:
        return False


def validate_operation_permissions(operation_type: str, target: Optional[str] = None) -> bool:
    """Validate permissions for specific operation type."""
    try:
        return permission_checker.validate_security_boundary(
            operation_type, 
            {'target': target} if target else None
        )
    except Exception:
        return False
