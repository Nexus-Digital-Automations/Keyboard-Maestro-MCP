# System Invariant Definitions and Checking Framework
# Target: <200 lines - System invariants for Keyboard Maestro MCP Server

"""
System invariant definitions and checking for the Keyboard Maestro MCP Server.

This module defines critical system invariants that must hold throughout the
server lifecycle and provides mechanisms for checking and enforcing these
invariants. Integrates with the contract framework to ensure system
consistency and detect corruption or security violations.

Key Features:
- Comprehensive system invariants for macro integrity, variable scope, permissions
- Resource limit invariants for performance and stability  
- Concurrent operation invariants for thread safety
- Invariant checking utilities with detailed violation reporting
- Integration with contract decorators for automatic checking
"""

from typing import Dict, Any, List, Set, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

# Import domain types and contract framework
from ..types.enumerations import VariableScope, MacroState
from src.contracts.exceptions import InvariantViolation, ViolationContext, ViolationType


class InvariantSeverity(Enum):
    """Severity levels for invariant violations."""
    CRITICAL = "critical"      # System must halt
    ERROR = "error"           # Operation must fail
    WARNING = "warning"       # Log but continue
    INFO = "info"            # Informational only


@dataclass(frozen=True)
class InvariantDefinition:
    """Immutable definition of a system invariant."""
    name: str
    description: str
    severity: InvariantSeverity
    check_function: Callable[[], bool]
    state_extractor: Optional[Callable[[], Dict[str, Any]]] = None
    recovery_suggestion: Optional[str] = None
    
    def check(self) -> bool:
        """Check if invariant currently holds."""
        try:
            return self.check_function()
        except Exception:
            # If check function fails, consider invariant violated
            return False
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current system state relevant to this invariant."""
        if self.state_extractor:
            try:
                return self.state_extractor()
            except Exception:
                return {"error": "State extraction failed"}
        return {}


class SystemInvariantChecker:
    """Manages and enforces system invariants."""
    
    def __init__(self):
        self.invariants: Dict[str, InvariantDefinition] = {}
        self.violation_handlers: Dict[InvariantSeverity, Callable] = {
            InvariantSeverity.CRITICAL: self._handle_critical_violation,
            InvariantSeverity.ERROR: self._handle_error_violation,
            InvariantSeverity.WARNING: self._handle_warning_violation,
            InvariantSeverity.INFO: self._handle_info_violation,
        }
        self._register_core_invariants()
    
    def register_invariant(self, invariant: InvariantDefinition) -> None:
        """Register a new system invariant."""
        self.invariants[invariant.name] = invariant
    
    def check_all_invariants(self) -> Dict[str, bool]:
        """Check all registered invariants."""
        results = {}
        for name, invariant in self.invariants.items():
            results[name] = invariant.check()
            
            # Handle violations
            if not results[name]:
                self._handle_violation(invariant)
        
        return results
    
    def check_invariant(self, name: str) -> bool:
        """Check specific invariant by name."""
        if name not in self.invariants:
            raise ValueError(f"Unknown invariant: {name}")
        
        invariant = self.invariants[name]
        result = invariant.check()
        
        if not result:
            self._handle_violation(invariant)
        
        return result
    
    def get_violations(self) -> List[str]:
        """Get list of currently violated invariants."""
        violations = []
        for name, invariant in self.invariants.items():
            if not invariant.check():
                violations.append(name)
        return violations
        
    def check_all(self) -> bool:
        """Check all invariants and return True if all pass."""
        return all(self.check_all_invariants().values())
    
    def _register_core_invariants(self) -> None:
        """Register core system invariants."""
        
        # Macro Integrity Invariant
        self.register_invariant(InvariantDefinition(
            name="macro_integrity",
            description="All macros maintain valid structure and relationships",
            severity=InvariantSeverity.ERROR,
            check_function=self._check_macro_integrity,
            state_extractor=self._get_macro_state,
            recovery_suggestion="Validate macro structures and repair corrupted entries"
        ))
        
        # Variable Scope Invariant
        self.register_invariant(InvariantDefinition(
            name="variable_scope",
            description="Local variables never persist beyond execution context",
            severity=InvariantSeverity.ERROR,
            check_function=self._check_variable_scope,
            state_extractor=self._get_variable_state,
            recovery_suggestion="Clean up orphaned local variables"
        ))
        
        # Permission Boundary Invariant
        self.register_invariant(InvariantDefinition(
            name="permission_boundary",
            description="Operations never exceed granted permissions",
            severity=InvariantSeverity.CRITICAL,
            check_function=self._check_permission_boundaries,
            state_extractor=self._get_permission_state,
            recovery_suggestion="Review and restore proper permission boundaries"
        ))
        
        # Resource Limit Invariant
        self.register_invariant(InvariantDefinition(
            name="resource_limits",
            description="System resources stay within defined limits",
            severity=InvariantSeverity.WARNING,
            check_function=self._check_resource_limits,
            state_extractor=self._get_resource_state,
            recovery_suggestion="Reduce concurrent operations or increase resource limits"
        ))
        
        # Concurrent Operation Invariant
        self.register_invariant(InvariantDefinition(
            name="concurrent_operations",
            description="Concurrent operations maintain thread safety",
            severity=InvariantSeverity.ERROR,
            check_function=self._check_concurrent_operations,
            state_extractor=self._get_operation_state,
            recovery_suggestion="Synchronize concurrent access to shared resources"
        ))
    
    def _handle_violation(self, invariant: InvariantDefinition) -> None:
        """Handle invariant violation based on severity."""
        handler = self.violation_handlers.get(invariant.severity)
        if handler:
            handler(invariant)
    
    def _handle_critical_violation(self, invariant: InvariantDefinition) -> None:
        """Handle critical invariant violations."""
        current_state = invariant.get_current_state()
        context = ViolationContext(
            function_name="system_invariant_check",
            module_name=__name__,
            violation_type=ViolationType.INVARIANT,
            parameters={},
            expected_condition=invariant.description,
            actual_values=current_state
        )
        
        # Critical violations should halt the system
        raise InvariantViolation(invariant.name, context, current_state)
    
    def _handle_error_violation(self, invariant: InvariantDefinition) -> None:
        """Handle error-level invariant violations."""
        # Log error and take corrective action
        print(f"ERROR: Invariant '{invariant.name}' violated: {invariant.description}")
        if invariant.recovery_suggestion:
            print(f"Recovery: {invariant.recovery_suggestion}")
    
    def _handle_warning_violation(self, invariant: InvariantDefinition) -> None:
        """Handle warning-level invariant violations."""
        print(f"WARNING: Invariant '{invariant.name}' violated: {invariant.description}")
    
    def _handle_info_violation(self, invariant: InvariantDefinition) -> None:
        """Handle info-level invariant violations."""
        print(f"INFO: Invariant '{invariant.name}' violated: {invariant.description}")
    
    # Invariant checking functions (simplified implementations)
    
    def _check_macro_integrity(self) -> bool:
        """Check macro integrity invariant."""
        # In real implementation, would query Keyboard Maestro for all macros
        # and validate their structure and relationships
        try:
            macros = self._get_all_macros()
            return all(self._validate_macro_structure(macro) for macro in macros)
        except Exception:
            return False
    
    def _check_variable_scope(self) -> bool:
        """Check variable scope invariant."""
        # In real implementation, would check for orphaned local variables
        try:
            local_vars = self._get_local_variables()
            active_contexts = self._get_active_execution_contexts()
            
            # All local variables should have active execution contexts
            return all(
                var.execution_context_id in active_contexts
                for var in local_vars
            )
        except Exception:
            return False
    
    def _check_permission_boundaries(self) -> bool:
        """Check permission boundary invariant."""
        # In real implementation, would verify current operations against permissions
        try:
            active_operations = self._get_active_operations()
            granted_permissions = self._get_granted_permissions()
            
            return all(
                op.required_permissions.issubset(granted_permissions)
                for op in active_operations
            )
        except Exception:
            return False
    
    def _check_resource_limits(self) -> bool:
        """Check resource limit invariant."""
        # In real implementation, would check actual resource usage
        try:
            current_usage = self._get_current_resource_usage()
            limits = self._get_resource_limits()
            
            return (
                current_usage.memory_mb <= limits.max_memory_mb and
                current_usage.concurrent_operations <= limits.max_concurrent_operations and
                current_usage.cpu_percent <= limits.max_cpu_percent
            )
        except Exception:
            return False
    
    def _check_concurrent_operations(self) -> bool:
        """Check concurrent operation invariant."""
        # In real implementation, would check for race conditions and deadlocks
        try:
            # Simplified check for demonstration
            return True
        except Exception:
            return False
    
    # State extraction functions (simplified implementations)
    
    def _get_macro_state(self) -> Dict[str, Any]:
        """Get current macro system state."""
        return {
            "total_macros": 0,  # Would query actual count
            "enabled_macros": 0,
            "corrupted_macros": [],
        }
    
    def _get_variable_state(self) -> Dict[str, Any]:
        """Get current variable system state."""
        return {
            "global_variables": 0,
            "local_variables": 0,
            "orphaned_locals": [],
        }
    
    def _get_permission_state(self) -> Dict[str, Any]:
        """Get current permission state."""
        return {
            "granted_permissions": set(),
            "required_permissions": set(),
            "permission_violations": [],
        }
    
    def _get_resource_state(self) -> Dict[str, Any]:
        """Get current resource usage state."""
        return {
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "concurrent_operations": 0,
        }
    
    def _get_operation_state(self) -> Dict[str, Any]:
        """Get current operation state."""
        return {
            "active_operations": 0,
            "queued_operations": 0,
            "failed_operations": 0,
        }
    
    # Helper functions (placeholder implementations)
    
    def _get_all_macros(self) -> List[Any]:
        """Get all macros from Keyboard Maestro."""
        return []  # Placeholder
    
    def _validate_macro_structure(self, macro: Any) -> bool:
        """Validate individual macro structure."""
        return True  # Placeholder
    
    def _get_local_variables(self) -> List[Any]:
        """Get all local variables."""
        return []  # Placeholder
    
    def _get_active_execution_contexts(self) -> Set[str]:
        """Get active execution context IDs."""
        return set()  # Placeholder
    
    def _get_active_operations(self) -> List[Any]:
        """Get currently active operations."""
        return []  # Placeholder
    
    def _get_granted_permissions(self) -> Set[str]:
        """Get currently granted permissions."""
        return set()  # Placeholder
    
    def _get_current_resource_usage(self) -> Any:
        """Get current resource usage."""
        class ResourceUsage:
            memory_mb = 0
            concurrent_operations = 0
            cpu_percent = 0
        return ResourceUsage()
    
    def _get_resource_limits(self) -> Any:
        """Get configured resource limits."""
        class ResourceLimits:
            max_memory_mb = 1000
            max_concurrent_operations = 100
            max_cpu_percent = 80
        return ResourceLimits()


# Global invariant checker instance
system_invariant_checker = SystemInvariantChecker()


# Convenience functions for common invariant checks

def check_macro_integrity() -> bool:
    """Check macro integrity invariant."""
    return system_invariant_checker.check_invariant("macro_integrity")


def check_variable_scope() -> bool:
    """Check variable scope invariant."""
    return system_invariant_checker.check_invariant("variable_scope")


def check_permission_boundaries() -> bool:
    """Check permission boundary invariant."""
    return system_invariant_checker.check_invariant("permission_boundary")


def check_all_system_invariants() -> bool:
    """Check all system invariants."""
    results = system_invariant_checker.check_all_invariants()
    return all(results.values())
