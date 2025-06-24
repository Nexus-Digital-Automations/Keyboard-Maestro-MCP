"""
System Boundary Protection for Keyboard Maestro MCP Server.

This module implements system operation boundary validation including
resource limits, operation timeouts, concurrency controls, and
protection against resource exhaustion and system instability.

Target: <200 lines per ADDER+ modularity requirements
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import time
import threading
from collections import defaultdict, deque

# Import validation and contract types
try:
    from ..types.results import Result, OperationError, ErrorType
    from ..contracts.decorators import requires, ensures
except ImportError:
    # Fallback types for development
    @dataclass
    class OperationError:
        error_type: str
        message: str

class ResourceType(Enum):
    """Types of system resources to monitor and limit."""
    MEMORY = "memory"
    CPU = "cpu"
    DISK_IO = "disk_io"
    NETWORK = "network"
    CONCURRENT_OPERATIONS = "concurrent_operations"
    APPLESCRIPT_CONNECTIONS = "applescript_connections"

@dataclass(frozen=True)
class ResourceLimit:
    """Definition of a resource limit with threshold and enforcement."""
    resource_type: ResourceType
    max_value: float
    warning_threshold: float
    enforcement_action: str  # "warn", "throttle", "block"
    measurement_window: int  # seconds

@dataclass(frozen=True)
class SystemBoundaryResult:
    """Result of system boundary validation."""
    allowed: bool
    resource_usage: Dict[ResourceType, float]
    limit_violations: List[str]
    warnings: List[str]
    suggested_wait_time: Optional[float] = None
    denial_reason: Optional[str] = None

class ResourceMonitor:
    """Monitors system resource usage and enforces limits."""
    
    def __init__(self):
        self._usage_history = defaultdict(lambda: deque(maxlen=100))
        self._active_operations = set()
        self._lock = threading.Lock()
        
        # Default resource limits
        self.limits = {
            ResourceType.CONCURRENT_OPERATIONS: ResourceLimit(
                ResourceType.CONCURRENT_OPERATIONS, 
                max_value=50, 
                warning_threshold=40,
                enforcement_action="block",
                measurement_window=60
            ),
            ResourceType.APPLESCRIPT_CONNECTIONS: ResourceLimit(
                ResourceType.APPLESCRIPT_CONNECTIONS,
                max_value=10,
                warning_threshold=8,
                enforcement_action="throttle", 
                measurement_window=30
            ),
            ResourceType.MEMORY: ResourceLimit(
                ResourceType.MEMORY,
                max_value=100 * 1024 * 1024,  # 100MB in bytes
                warning_threshold=80 * 1024 * 1024,
                enforcement_action="warn",
                measurement_window=300
            )
        }
    
    def check_resource_availability(self, operation: str, 
                                  estimated_resources: Dict[ResourceType, float]) -> SystemBoundaryResult:
        """Check if operation can proceed within resource limits."""
        with self._lock:
            current_usage = self._get_current_usage()
            violations = []
            warnings = []
            
            for resource_type, estimated_usage in estimated_resources.items():
                if resource_type not in self.limits:
                    continue
                
                limit = self.limits[resource_type]
                current = current_usage.get(resource_type, 0)
                projected = current + estimated_usage
                
                if projected > limit.max_value:
                    if limit.enforcement_action == "block":
                        violations.append(
                            f"{resource_type.value} limit exceeded: {projected} > {limit.max_value}"
                        )
                    elif limit.enforcement_action == "throttle":
                        warnings.append(
                            f"{resource_type.value} approaching limit: {projected}/{limit.max_value}"
                        )
                
                elif projected > limit.warning_threshold:
                    warnings.append(
                        f"{resource_type.value} warning threshold reached: {projected}/{limit.warning_threshold}"
                    )
            
            allowed = len(violations) == 0
            suggested_wait = self._calculate_wait_time(violations) if violations else None
            
            return SystemBoundaryResult(
                allowed=allowed,
                resource_usage=current_usage,
                limit_violations=violations,
                warnings=warnings,
                suggested_wait_time=suggested_wait,
                denial_reason="Resource limits exceeded" if violations else None
            )
    
    def register_operation_start(self, operation_id: str, 
                               resource_usage: Dict[ResourceType, float]) -> None:
        """Register the start of an operation for resource tracking."""
        with self._lock:
            self._active_operations.add(operation_id)
            current_time = time.time()
            
            for resource_type, usage in resource_usage.items():
                self._usage_history[resource_type].append((current_time, usage, "start"))
    
    def register_operation_end(self, operation_id: str, 
                             resource_usage: Dict[ResourceType, float]) -> None:
        """Register the end of an operation for resource tracking."""
        with self._lock:
            if operation_id in self._active_operations:
                self._active_operations.remove(operation_id)
            
            current_time = time.time()
            for resource_type, usage in resource_usage.items():
                self._usage_history[resource_type].append((current_time, -usage, "end"))
    
    def _get_current_usage(self) -> Dict[ResourceType, float]:
        """Calculate current resource usage from history."""
        current_time = time.time()
        usage = {}
        
        for resource_type, limit in self.limits.items():
            total_usage = 0
            cutoff_time = current_time - limit.measurement_window
            
            # Sum up usage within measurement window
            for timestamp, amount, event_type in self._usage_history[resource_type]:
                if timestamp > cutoff_time:
                    total_usage += amount
            
            # Special handling for concurrent operations
            if resource_type == ResourceType.CONCURRENT_OPERATIONS:
                total_usage = len(self._active_operations)
            
            usage[resource_type] = max(0, total_usage)
        
        return usage
    
    def _calculate_wait_time(self, violations: List[str]) -> float:
        """Calculate suggested wait time based on violations."""
        # Simple backoff strategy
        base_wait = 1.0  # 1 second base
        return base_wait * len(violations)

class OperationTimeoutManager:
    """Manages operation timeouts to prevent hanging operations."""
    
    def __init__(self):
        self.default_timeouts = {
            "macro_execution": 30.0,
            "file_operation": 10.0,
            "applescript_execution": 15.0,
            "system_operation": 5.0,
            "network_operation": 30.0,
        }
        self.active_timeouts = {}
        self._lock = threading.Lock()
    
    def check_timeout_feasibility(self, operation_type: str, 
                                 requested_timeout: Optional[float]) -> SystemBoundaryResult:
        """Check if requested timeout is within acceptable bounds."""
        max_timeout = self.default_timeouts.get(operation_type, 30.0)
        effective_timeout = requested_timeout or max_timeout
        
        warnings = []
        violations = []
        
        if effective_timeout > max_timeout * 2:
            violations.append(f"Timeout too long: {effective_timeout}s > {max_timeout * 2}s")
        elif effective_timeout > max_timeout:
            warnings.append(f"Timeout longer than recommended: {effective_timeout}s > {max_timeout}s")
        
        if effective_timeout <= 0:
            violations.append("Timeout must be positive")
        
        return SystemBoundaryResult(
            allowed=len(violations) == 0,
            resource_usage={},
            limit_violations=violations,
            warnings=warnings,
            denial_reason="Invalid timeout specified" if violations else None
        )

class ConcurrencyController:
    """Controls concurrent operation execution to prevent resource conflicts."""
    
    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self.active_operations = {}
        self.operation_queue = deque()
        self._lock = threading.Lock()
    
    def can_start_operation(self, operation_id: str, operation_type: str, 
                           priority: int = 5) -> SystemBoundaryResult:
        """Check if operation can start immediately or needs to be queued."""
        with self._lock:
            current_count = len(self.active_operations)
            
            if current_count >= self.max_concurrent:
                return SystemBoundaryResult(
                    allowed=False,
                    resource_usage={ResourceType.CONCURRENT_OPERATIONS: current_count},
                    limit_violations=[f"Too many concurrent operations: {current_count}/{self.max_concurrent}"],
                    warnings=[],
                    suggested_wait_time=self._estimate_wait_time(),
                    denial_reason="Maximum concurrent operations exceeded"
                )
            
            # Check for operation type conflicts
            conflicting_ops = self._get_conflicting_operations(operation_type)
            if conflicting_ops:
                return SystemBoundaryResult(
                    allowed=False,
                    resource_usage={ResourceType.CONCURRENT_OPERATIONS: current_count},
                    limit_violations=[],
                    warnings=[f"Conflicting operations in progress: {conflicting_ops}"],
                    suggested_wait_time=5.0,
                    denial_reason="Conflicting operation in progress"
                )
            
            return SystemBoundaryResult(
                allowed=True,
                resource_usage={ResourceType.CONCURRENT_OPERATIONS: current_count + 1},
                limit_violations=[],
                warnings=[]
            )
    
    def start_operation(self, operation_id: str, operation_type: str) -> None:
        """Register operation start for concurrency tracking."""
        with self._lock:
            self.active_operations[operation_id] = {
                "type": operation_type,
                "start_time": time.time()
            }
    
    def end_operation(self, operation_id: str) -> None:
        """Register operation completion."""
        with self._lock:
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    def _get_conflicting_operations(self, operation_type: str) -> List[str]:
        """Get list of operations that conflict with the requested type."""
        conflicts = {
            "macro_creation": ["macro_deletion", "macro_modification"],
            "macro_deletion": ["macro_creation", "macro_modification"],
            "macro_modification": ["macro_creation", "macro_deletion"],
        }
        
        conflicting_types = conflicts.get(operation_type, [])
        return [
            op_id for op_id, info in self.active_operations.items()
            if info["type"] in conflicting_types
        ]
    
    def _estimate_wait_time(self) -> float:
        """Estimate how long to wait for an operation slot."""
        if not self.active_operations:
            return 0.0
        
        current_time = time.time()
        oldest_operation_time = min(
            info["start_time"] for info in self.active_operations.values()
        )
        
        # Estimate based on oldest operation age
        age = current_time - oldest_operation_time
        return max(1.0, min(10.0, age * 0.5))

class ComprehensiveSystemBoundary:
    """Comprehensive system boundary management."""
    
    def __init__(self):
        self.resource_monitor = ResourceMonitor()
        self.timeout_manager = OperationTimeoutManager()
        self.concurrency_controller = ConcurrencyController()
    
    def validate_system_operation(self, operation_id: str, operation_type: str, 
                                estimated_resources: Dict[ResourceType, float],
                                timeout: Optional[float] = None) -> SystemBoundaryResult:
        """Validate operation against all system boundaries."""
        
        # Check resource availability
        resource_result = self.resource_monitor.check_resource_availability(
            operation_type, estimated_resources
        )
        if not resource_result.allowed:
            return resource_result
        
        # Check timeout feasibility
        timeout_result = self.timeout_manager.check_timeout_feasibility(
            operation_type, timeout
        )
        if not timeout_result.allowed:
            return timeout_result
        
        # Check concurrency limits
        concurrency_result = self.concurrency_controller.can_start_operation(
            operation_id, operation_type
        )
        if not concurrency_result.allowed:
            return concurrency_result
        
        # Combine warnings from all checks
        all_warnings = (resource_result.warnings + 
                       timeout_result.warnings + 
                       concurrency_result.warnings)
        
        return SystemBoundaryResult(
            allowed=True,
            resource_usage=resource_result.resource_usage,
            limit_violations=[],
            warnings=all_warnings
        )

# Default system boundary instance
DEFAULT_SYSTEM_BOUNDARY = ComprehensiveSystemBoundary()

class SystemBoundaryManager:
    """Main system boundary management interface.
    
    This class provides the primary interface for system boundary validation,
    resource monitoring, and operation coordination across the MCP server.
    """
    
    def __init__(self):
        self.boundary = ComprehensiveSystemBoundary()
    
    def validate_operation(self, operation_id: str, operation_type: str, 
                          estimated_resources: Dict[ResourceType, float],
                          timeout: Optional[float] = None) -> SystemBoundaryResult:
        """Validate operation against all system boundaries."""
        return self.boundary.validate_system_operation(
            operation_id, operation_type, estimated_resources, timeout
        )
    
    def start_operation(self, operation_id: str, operation_type: str,
                       resource_usage: Dict[ResourceType, float]) -> None:
        """Register operation start for tracking."""
        self.boundary.resource_monitor.register_operation_start(operation_id, resource_usage)
        self.boundary.concurrency_controller.start_operation(operation_id, operation_type)
    
    def end_operation(self, operation_id: str, 
                     resource_usage: Dict[ResourceType, float]) -> None:
        """Register operation end for tracking."""
        self.boundary.resource_monitor.register_operation_end(operation_id, resource_usage)
        self.boundary.concurrency_controller.end_operation(operation_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and resource usage."""
        current_usage = self.boundary.resource_monitor._get_current_usage()
        active_ops = len(self.boundary.concurrency_controller.active_operations)
        
        return {
            "resource_usage": current_usage,
            "active_operations": active_ops,
            "max_concurrent": self.boundary.concurrency_controller.max_concurrent,
            "resource_limits": {
                rt.value: {
                    "max": limit.max_value,
                    "warning": limit.warning_threshold,
                    "enforcement": limit.enforcement_action
                }
                for rt, limit in self.boundary.resource_monitor.limits.items()
            }
        }

def validate_system_boundary(operation_id: str, operation_type: str, 
                           estimated_resources: Dict[ResourceType, float],
                           timeout: Optional[float] = None) -> SystemBoundaryResult:
    """Convenience function for system boundary validation."""
    return DEFAULT_SYSTEM_BOUNDARY.validate_system_operation(
        operation_id, operation_type, estimated_resources, timeout
    )

def validate_system_permissions(operation_type: str, user_context: Optional[Dict] = None) -> bool:
    """Validate system permissions for operation type.
    
    Args:
        operation_type: Type of operation to validate
        user_context: Optional user context for permission checking
        
    Returns:
        bool: True if operation is permitted, False otherwise
    """
    # Basic permission validation
    # In a full implementation, this would check against user roles,
    # system policies, and operation-specific permissions
    
    restricted_operations = {
        "system_shutdown", "kernel_access", "raw_disk_access", 
        "network_configuration", "security_policy_modification"
    }
    
    if operation_type in restricted_operations:
        return False
    
    # Allow standard Keyboard Maestro operations
    allowed_operations = {
        "macro_execution", "macro_creation", "macro_modification", "macro_deletion",
        "variable_read", "variable_write", "file_operation", "applescript_execution",
        "clipboard_access", "window_management", "system_integration"
    }
    
    return operation_type in allowed_operations or operation_type.startswith("plugin_")

def check_resource_limits(resource_usage: Dict[ResourceType, float]) -> SystemBoundaryResult:
    """Check if resource usage is within acceptable limits.
    
    Args:
        resource_usage: Dictionary of resource types and their usage levels
        
    Returns:
        SystemBoundaryResult: Result indicating if limits are respected
    """
    return DEFAULT_SYSTEM_BOUNDARY.resource_monitor.check_resource_availability(
        "resource_check", resource_usage
    )

def validate_file_operations(file_path: str, operation_type: str, user_context: Optional[Dict] = None) -> bool:
    """Validate file operation permissions and safety.
    
    Args:
        file_path: Path to file being operated on
        operation_type: Type of file operation (read, write, delete, etc.)
        user_context: Optional user context for permission checking
        
    Returns:
        bool: True if file operation is allowed, False otherwise
    """
    import os
    
    # Basic file operation validation
    # Check for dangerous paths
    dangerous_paths = {
        "/System", "/usr/bin", "/bin", "/sbin", "/etc",
        "/var/log", "/var/db", "/Library/Security"
    }
    
    # Normalize path
    normalized_path = os.path.normpath(file_path)
    
    # Check if path starts with any dangerous location
    for dangerous in dangerous_paths:
        if normalized_path.startswith(dangerous):
            return False
    
    # Check operation type permissions
    if operation_type in {"delete", "modify", "execute"}:
        # More restrictive for destructive operations
        if "/Applications/" in normalized_path or "/Library/" in normalized_path:
            return False
    
    # Allow operations in user directories and safe locations
    safe_prefixes = {
        os.path.expanduser("~/"),
        "/tmp/",
        "/var/tmp/",
        "/Users/"
    }
    
    return any(normalized_path.startswith(safe) for safe in safe_prefixes)
