"""
Security Boundary Protection for Keyboard Maestro MCP Server.

This module implements comprehensive security boundary validation including
permission checking, access control, authentication verification, and
protection against unauthorized operations and security threats.

Target: <250 lines per ADDER+ modularity requirements
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Protocol
from enum import Enum
import os
import subprocess
import time
from pathlib import Path

# Import validation and contract types
try:
    from .input_validators import ValidationResult
    from ..types.domain_types import MacroUUID, VariableName
    from ..types.enumerations import VariableScope
    from ..types.results import Result, OperationError, ErrorType
    from ..contracts.decorators import requires, ensures
except ImportError:
    # Fallback types for development
    @dataclass
    class ValidationResult:
        is_valid: bool
        errors: List[Any] = None

class SecurityLevel(Enum):
    """Security enforcement levels for different operation types."""
    PUBLIC = "public"         # No restrictions
    AUTHENTICATED = "authenticated"  # Requires valid authentication
    AUTHORIZED = "authorized"        # Requires specific permissions
    PRIVILEGED = "privileged"        # Requires elevated privileges
    RESTRICTED = "restricted"        # Highly restricted operations

class PermissionType(Enum):
    """Types of macOS permissions required for operations."""
    ACCESSIBILITY = "accessibility"
    FULL_DISK_ACCESS = "full_disk_access"
    CAMERA = "camera"
    MICROPHONE = "microphone"
    SCREEN_RECORDING = "screen_recording"
    NOTIFICATIONS = "notifications"
    AUTOMATION = "automation"
    CONTACTS = "contacts"
    CALENDARS = "calendars"
    REMINDERS = "reminders"

@dataclass(frozen=True)
class SecurityContext:
    """Immutable security context for operation validation."""
    user_id: Optional[str]
    session_id: Optional[str]
    source_ip: Optional[str]
    permissions: Set[PermissionType]
    security_level: SecurityLevel
    timestamp: float
    
    def has_permission(self, permission: PermissionType) -> bool:
        """Check if context has specific permission."""
        return permission in self.permissions
    
    def is_expired(self, max_age_seconds: int = 3600) -> bool:
        """Check if security context has expired."""
        return time.time() - self.timestamp > max_age_seconds

@dataclass(frozen=True)
class SecurityBoundaryResult:
    """Result of security boundary validation."""
    allowed: bool
    required_permissions: Set[PermissionType]
    missing_permissions: Set[PermissionType]
    security_warnings: List[str]
    denial_reason: Optional[str] = None

class SecurityBoundaryChecker(ABC):
    """Abstract base for security boundary validation."""
    
    @abstractmethod
    def check_boundary(self, operation: str, context: SecurityContext, 
                      parameters: Dict[str, Any]) -> SecurityBoundaryResult:
        """Check if operation is allowed within security boundaries."""
        ...
    
    @abstractmethod
    def get_required_permissions(self, operation: str) -> Set[PermissionType]:
        """Get permissions required for specific operation."""
        ...

class MacOSPermissionChecker:
    """Checks macOS system permissions for automation operations."""
    
    def __init__(self):
        self._permission_cache = {}
        self._cache_expiry = {}
        self._cache_duration = 300  # 5 minutes
    
    def check_accessibility_permission(self) -> bool:
        """Check if accessibility permissions are granted."""
        if self._is_cached("accessibility"):
            return self._permission_cache["accessibility"]
        
        try:
            # Use osascript to check accessibility permissions
            result = subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to return name of first process'
            ], capture_output=True, timeout=5)
            
            has_permission = result.returncode == 0
            self._cache_permission("accessibility", has_permission)
            return has_permission
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Assume no permission if check fails
            self._cache_permission("accessibility", False)
            return False
    
    def check_full_disk_access(self) -> bool:
        """Check if full disk access is granted."""
        if self._is_cached("full_disk_access"):
            return self._permission_cache["full_disk_access"]
        
        try:
            # Try to access a protected location
            protected_path = Path.home() / "Library" / "Safari" / "Bookmarks.plist"
            has_permission = protected_path.exists() and os.access(str(protected_path), os.R_OK)
            self._cache_permission("full_disk_access", has_permission)
            return has_permission
            
        except (OSError, PermissionError):
            self._cache_permission("full_disk_access", False)
            return False
    
    def check_screen_recording_permission(self) -> bool:
        """Check if screen recording permission is granted."""
        if self._is_cached("screen_recording"):
            return self._permission_cache["screen_recording"]
        
        # Screen recording permission check is complex in recent macOS
        # For now, assume it needs to be manually verified
        # TODO: Implement more sophisticated check
        self._cache_permission("screen_recording", False)
        return False
    
    def _is_cached(self, permission: str) -> bool:
        """Check if permission result is cached and valid."""
        if permission not in self._permission_cache:
            return False
        
        expiry_time = self._cache_expiry.get(permission, 0)
        return time.time() < expiry_time
    
    def _cache_permission(self, permission: str, result: bool) -> None:
        """Cache permission check result."""
        self._permission_cache[permission] = result
        self._cache_expiry[permission] = time.time() + self._cache_duration

class MacroOperationBoundary(SecurityBoundaryChecker):
    """Security boundary checker for macro operations."""
    
    def __init__(self):
        self.permission_checker = MacOSPermissionChecker()
        self.operation_permissions = {
            "execute_macro": {PermissionType.ACCESSIBILITY},
            "create_macro": {PermissionType.ACCESSIBILITY},
            "modify_macro": {PermissionType.ACCESSIBILITY},
            "delete_macro": {PermissionType.ACCESSIBILITY},
            "export_macro": {PermissionType.FULL_DISK_ACCESS},
            "import_macro": {PermissionType.FULL_DISK_ACCESS},
        }
    
    def check_boundary(self, operation: str, context: SecurityContext, 
                      parameters: Dict[str, Any]) -> SecurityBoundaryResult:
        """Check macro operation security boundaries."""
        required_permissions = self.get_required_permissions(operation)
        missing_permissions = required_permissions - context.permissions
        warnings = []
        
        # Check basic authentication
        if context.security_level == SecurityLevel.PUBLIC and required_permissions:
            return SecurityBoundaryResult(
                allowed=False,
                required_permissions=required_permissions,
                missing_permissions=missing_permissions,
                security_warnings=warnings,
                denial_reason="Authentication required for macro operations"
            )
        
        # Check macOS permissions
        if PermissionType.ACCESSIBILITY in required_permissions:
            if not self.permission_checker.check_accessibility_permission():
                missing_permissions.add(PermissionType.ACCESSIBILITY)
                warnings.append("Accessibility permission required but not granted")
        
        # Check for dangerous macro operations
        if operation in ("delete_macro", "modify_macro"):
            macro_id = parameters.get("macro_id")
            if self._is_system_macro(macro_id):
                return SecurityBoundaryResult(
                    allowed=False,
                    required_permissions=required_permissions,
                    missing_permissions=missing_permissions,
                    security_warnings=warnings,
                    denial_reason="Cannot modify system-protected macros"
                )
        
        # Check session validity
        if context.is_expired():
            return SecurityBoundaryResult(
                allowed=False,
                required_permissions=required_permissions,
                missing_permissions=missing_permissions,
                security_warnings=warnings,
                denial_reason="Security context has expired"
            )
        
        allowed = len(missing_permissions) == 0
        return SecurityBoundaryResult(
            allowed=allowed,
            required_permissions=required_permissions,
            missing_permissions=missing_permissions,
            security_warnings=warnings,
            denial_reason=None if allowed else "Insufficient permissions"
        )
    
    def get_required_permissions(self, operation: str) -> Set[PermissionType]:
        """Get permissions required for macro operation."""
        return self.operation_permissions.get(operation, set())
    
    def _is_system_macro(self, macro_id: Any) -> bool:
        """Check if macro is system-protected (placeholder implementation)."""
        # TODO: Implement actual system macro detection
        return False

class FileOperationBoundary(SecurityBoundaryChecker):
    """Security boundary checker for file operations."""
    
    PROTECTED_DIRECTORIES = {
        "/System",
        "/usr",
        "/bin",
        "/sbin",
        "/private",
        str(Path.home() / "Library" / "Keychains"),
        str(Path.home() / "Library" / "Application Support" / "com.apple.sharedfilelist"),
    }
    
    def check_boundary(self, operation: str, context: SecurityContext, 
                      parameters: Dict[str, Any]) -> SecurityBoundaryResult:
        """Check file operation security boundaries."""
        required_permissions = self.get_required_permissions(operation)
        missing_permissions = required_permissions - context.permissions
        warnings = []
        
        file_path = parameters.get("file_path", "")
        
        # Check for access to protected directories
        if any(file_path.startswith(protected) for protected in self.PROTECTED_DIRECTORIES):
            return SecurityBoundaryResult(
                allowed=False,
                required_permissions=required_permissions,
                missing_permissions=missing_permissions,
                security_warnings=warnings,
                denial_reason=f"Access to protected directory denied: {file_path}"
            )
        
        # Check for directory traversal attempts
        if ".." in file_path or file_path.startswith("/"):
            warnings.append("Potential directory traversal attempt detected")
        
        # Check write operations
        if operation in ("write_file", "delete_file", "move_file"):
            if not self._has_write_permission(file_path):
                missing_permissions.add(PermissionType.FULL_DISK_ACCESS)
        
        allowed = len(missing_permissions) == 0
        return SecurityBoundaryResult(
            allowed=allowed,
            required_permissions=required_permissions,
            missing_permissions=missing_permissions,
            security_warnings=warnings,
            denial_reason=None if allowed else "Insufficient file system permissions"
        )
    
    def get_required_permissions(self, operation: str) -> Set[PermissionType]:
        """Get permissions required for file operation."""
        if operation in ("write_file", "delete_file", "move_file", "create_directory"):
            return {PermissionType.FULL_DISK_ACCESS}
        return set()
    
    def _has_write_permission(self, file_path: str) -> bool:
        """Check if we have write permission to file or directory."""
        try:
            path = Path(file_path)
            parent = path.parent if path.exists() else path
            return os.access(str(parent), os.W_OK)
        except (OSError, PermissionError):
            return False

class ComprehensiveSecurityBoundary:
    """Comprehensive security boundary management for all operations."""
    
    def __init__(self):
        self.macro_boundary = MacroOperationBoundary()
        self.file_boundary = FileOperationBoundary()
        self.rate_limits = {}  # Simple rate limiting
        self.max_requests_per_minute = 60
    
    def validate_operation(self, operation_type: str, operation: str, 
                         context: SecurityContext, parameters: Dict[str, Any]) -> SecurityBoundaryResult:
        """Validate operation against all applicable security boundaries."""
        
        # Check rate limits first
        if not self._check_rate_limit(context.user_id or "anonymous"):
            return SecurityBoundaryResult(
                allowed=False,
                required_permissions=set(),
                missing_permissions=set(),
                security_warnings=["Rate limit exceeded"],
                denial_reason="Too many requests"
            )
        
        # Route to appropriate boundary checker
        if operation_type == "macro":
            return self.macro_boundary.check_boundary(operation, context, parameters)
        elif operation_type == "file":
            return self.file_boundary.check_boundary(operation, context, parameters)
        else:
            # Default to requiring authentication
            return SecurityBoundaryResult(
                allowed=context.security_level != SecurityLevel.PUBLIC,
                required_permissions=set(),
                missing_permissions=set(),
                security_warnings=[],
                denial_reason=None if context.security_level != SecurityLevel.PUBLIC else "Authentication required"
            )
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Simple rate limiting implementation."""
        current_time = time.time()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Remove old entries
        cutoff_time = current_time - 60  # 1 minute window
        self.rate_limits[user_id] = [
            timestamp for timestamp in self.rate_limits[user_id]
            if timestamp > cutoff_time
        ]
        
        # Check if under limit
        if len(self.rate_limits[user_id]) >= self.max_requests_per_minute:
            return False
        
        # Add current request
        self.rate_limits[user_id].append(current_time)
        return True

# Alias for compatibility with tool registry
SecurityBoundaryManager = ComprehensiveSecurityBoundary

# Default security boundary instance
DEFAULT_SECURITY_BOUNDARY = ComprehensiveSecurityBoundary()

def validate_security_boundary(operation_type: str, operation: str, 
                             context: SecurityContext, parameters: Dict[str, Any]) -> SecurityBoundaryResult:
    """Convenience function for security boundary validation."""
    return DEFAULT_SECURITY_BOUNDARY.validate_operation(operation_type, operation, context, parameters)
