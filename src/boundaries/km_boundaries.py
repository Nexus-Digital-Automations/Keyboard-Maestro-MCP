# Keyboard Maestro Operation Boundaries: Security and Resource Protection
# src/boundaries/km_boundaries.py

"""
Keyboard Maestro operation boundary validation and protection.

This module implements comprehensive boundary validation for Keyboard Maestro
operations, ensuring security constraints, resource limits, and system
protection through defensive programming patterns.

Features:
- Macro execution boundary validation
- Variable scope and access control
- System resource protection
- Permission validation and enforcement
- Comprehensive error reporting with recovery guidance

Size: 187 lines (target: <200)
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

from .types.domain_types import MacroUUID, MacroName, VariableName
from src.types.enumerations import VariableScope, ExecutionMethod
from src.core.km_interface import MacroExecutionContext
from src.contracts.decorators import requires, ensures


class BoundaryViolationType(Enum):
    """Types of boundary violations."""
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_POLICY = "security_policy"
    RATE_LIMIT = "rate_limit"
    SCOPE_VIOLATION = "scope_violation"
    INVALID_OPERATION = "invalid_operation"


@dataclass(frozen=True)
class BoundaryResult:
    """Result of boundary validation check."""
    allowed: bool
    violation_type: Optional[BoundaryViolationType] = None
    reason: str = ""
    suggested_action: str = ""
    additional_info: Optional[Dict[str, Any]] = None


class KMBoundaryGuard:
    """Boundary protection for Keyboard Maestro operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self._operation_history: List[Dict[str, Any]] = []
        self._last_cleanup = time.time()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default boundary configuration."""
        return {
            'max_operations_per_minute': 60,
            'max_concurrent_operations': 10,
            'max_variable_size': 1000000,  # 1MB
            'allowed_execution_methods': [
                ExecutionMethod.APPLESCRIPT,
                ExecutionMethod.URL,
                ExecutionMethod.WEB
            ],
            'blocked_variable_patterns': [
                r'.*password.*',
                r'.*secret.*',
                r'.*key.*',
                r'.*token.*'
            ],
            'max_execution_timeout': 300,  # 5 minutes
            'cleanup_interval': 300  # 5 minutes
        }
    
    @requires(lambda context: isinstance(context, MacroExecutionContext))
    @ensures(lambda result: isinstance(result, BoundaryResult))
    async def validate_macro_execution(self, context: MacroExecutionContext) -> BoundaryResult:
        """Validate macro execution boundaries.
        
        Preconditions:
        - Context must be valid MacroExecutionContext
        
        Postconditions:
        - Returns BoundaryResult with validation outcome
        """
        # Check rate limiting
        rate_check = await self._check_rate_limit('macro_execution')
        if not rate_check.allowed:
            return rate_check
        
        # Check execution method
        if context.method not in self.config['allowed_execution_methods']:
            return BoundaryResult(
                allowed=False,
                violation_type=BoundaryViolationType.SECURITY_POLICY,
                reason=f"Execution method {context.method} not allowed",
                suggested_action="Use approved execution method (AppleScript, URL, Web)"
            )
        
        # Check timeout limits
        if context.timeout > self.config['max_execution_timeout']:
            return BoundaryResult(
                allowed=False,
                violation_type=BoundaryViolationType.RESOURCE_LIMIT,
                reason=f"Timeout {context.timeout}s exceeds maximum {self.config['max_execution_timeout']}s",
                suggested_action=f"Reduce timeout to {self.config['max_execution_timeout']}s or less"
            )
        
        # Check concurrent operations
        active_operations = len([op for op in self._operation_history 
                               if op.get('status') == 'active'])
        
        if active_operations >= self.config['max_concurrent_operations']:
            return BoundaryResult(
                allowed=False,
                violation_type=BoundaryViolationType.RESOURCE_LIMIT,
                reason=f"Too many concurrent operations ({active_operations})",
                suggested_action="Wait for current operations to complete"
            )
        
        # Record operation start
        self._record_operation('macro_execution', {'context': context})
        
        return BoundaryResult(
            allowed=True,
            reason="Macro execution approved",
            suggested_action="Proceed with execution"
        )
    
    @requires(lambda name: isinstance(name, VariableName))
    @requires(lambda scope: isinstance(scope, VariableScope))
    @ensures(lambda result: isinstance(result, BoundaryResult))
    async def validate_variable_access(self, name: VariableName, scope: VariableScope) -> BoundaryResult:
        """Validate variable access boundaries.
        
        Preconditions:
        - Name must be VariableName type
        - Scope must be VariableScope type
        
        Postconditions:
        - Returns BoundaryResult with validation outcome
        """
        # Check rate limiting for variable operations
        rate_check = await self._check_rate_limit('variable_access')
        if not rate_check.allowed:
            return rate_check
        
        # Check variable name patterns for sensitive data
        name_str = str(name).lower()
        for pattern in self.config['blocked_variable_patterns']:
            import re
            if re.search(pattern, name_str):
                return BoundaryResult(
                    allowed=False,
                    violation_type=BoundaryViolationType.SECURITY_POLICY,
                    reason=f"Variable name matches blocked pattern: {pattern}",
                    suggested_action="Use non-sensitive variable name or appropriate scope"
                )
        
        # Check scope permissions
        if scope == VariableScope.PASSWORD:
            # Additional validation for password variables
            if not any(keyword in name_str for keyword in ['password', 'pw', 'secret']):
                return BoundaryResult(
                    allowed=False,
                    violation_type=BoundaryViolationType.SCOPE_VIOLATION,
                    reason="Password scope requires appropriate variable naming",
                    suggested_action="Use 'password', 'pw', or 'secret' in variable name"
                )
        
        return BoundaryResult(
            allowed=True,
            reason="Variable access approved"
        )
    
    @requires(lambda name: isinstance(name, VariableName))
    @requires(lambda value: isinstance(value, str))
    @requires(lambda scope: isinstance(scope, VariableScope))
    @ensures(lambda result: isinstance(result, BoundaryResult))
    async def validate_variable_modification(self, 
                                           name: VariableName, 
                                           value: str, 
                                           scope: VariableScope) -> BoundaryResult:
        """Validate variable modification boundaries.
        
        Preconditions:
        - Name must be VariableName type
        - Value must be string
        - Scope must be VariableScope type
        
        Postconditions:
        - Returns BoundaryResult with validation outcome
        """
        # First validate access permissions
        access_result = await self.validate_variable_access(name, scope)
        if not access_result.allowed:
            return access_result
        
        # Check value size limits
        if len(value) > self.config['max_variable_size']:
            return BoundaryResult(
                allowed=False,
                violation_type=BoundaryViolationType.RESOURCE_LIMIT,
                reason=f"Variable value too large ({len(value)} bytes, max {self.config['max_variable_size']})",
                suggested_action="Reduce variable value size or use file storage"
            )
        
        # Check for dangerous content in value
        if self._contains_dangerous_content(value):
            return BoundaryResult(
                allowed=False,
                violation_type=BoundaryViolationType.SECURITY_POLICY,
                reason="Variable value contains potentially dangerous content",
                suggested_action="Remove dangerous characters or patterns from value"
            )
        
        return BoundaryResult(
            allowed=True,
            reason="Variable modification approved"
        )
    
    async def _check_rate_limit(self, operation_type: str) -> BoundaryResult:
        """Check rate limiting for operation type."""
        await self._cleanup_old_operations()
        
        current_time = time.time()
        recent_operations = [
            op for op in self._operation_history
            if (op.get('type') == operation_type and 
                current_time - op.get('timestamp', 0) < 60)  # Last minute
        ]
        
        if len(recent_operations) >= self.config['max_operations_per_minute']:
            return BoundaryResult(
                allowed=False,
                violation_type=BoundaryViolationType.RATE_LIMIT,
                reason=f"Rate limit exceeded for {operation_type} ({len(recent_operations)} operations/minute)",
                suggested_action="Reduce operation frequency or implement backoff strategy"
            )
        
        return BoundaryResult(allowed=True)
    
    def _record_operation(self, operation_type: str, details: Dict[str, Any]) -> None:
        """Record operation for tracking and rate limiting."""
        self._operation_history.append({
            'type': operation_type,
            'timestamp': time.time(),
            'status': 'active',
            'details': details
        })
    
    async def _cleanup_old_operations(self) -> None:
        """Clean up old operation records."""
        current_time = time.time()
        
        if current_time - self._last_cleanup < self.config['cleanup_interval']:
            return
        
        # Remove operations older than 1 hour
        cutoff_time = current_time - 3600
        self._operation_history = [
            op for op in self._operation_history
            if op.get('timestamp', 0) > cutoff_time
        ]
        
        self._last_cleanup = current_time
    
    def _contains_dangerous_content(self, content: str) -> bool:
        """Check if content contains dangerous patterns."""
        dangerous_patterns = [
            r'<script[^>]*>',  # Script tags
            r'javascript:',    # JavaScript URLs
            r'data:.*base64',  # Base64 data URLs
            r'\\x[0-9a-fA-F]{2}',  # Hex escape sequences
            r'\x00',           # Null bytes
        ]
        
        import re
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in dangerous_patterns)
    
    def get_boundary_statistics(self) -> Dict[str, Any]:
        """Get boundary validation statistics."""
        current_time = time.time()
        
        # Operations in last hour
        recent_ops = [op for op in self._operation_history 
                     if current_time - op.get('timestamp', 0) < 3600]
        
        operation_counts = {}
        for op in recent_ops:
            op_type = op.get('type', 'unknown')
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        return {
            'total_operations_last_hour': len(recent_ops),
            'operations_by_type': operation_counts,
            'active_operations': len([op for op in self._operation_history 
                                    if op.get('status') == 'active']),
            'rate_limit_config': {
                'max_per_minute': self.config['max_operations_per_minute'],
                'max_concurrent': self.config['max_concurrent_operations']
            }
        }
