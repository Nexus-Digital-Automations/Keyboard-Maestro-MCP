# Contract Violation Exceptions Framework
# Target: <150 lines - Exception classes and error handling for contract violations

"""
Contract violation exception hierarchy for Design by Contract implementation.

This module provides comprehensive exception classes for different types of 
contract violations including preconditions, postconditions, and invariants.
All exceptions include detailed context for debugging and recovery.

Key Features:
- Hierarchical exception types with common base class
- Detailed error context including function names and violation details
- Recovery guidance for different violation types
- Integration with contract decorators and validation framework
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """Classification of contract violation types."""
    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    INVARIANT = "invariant"
    TYPE_SAFETY = "type_safety"
    SECURITY_BOUNDARY = "security_boundary"


@dataclass(frozen=True)
class ViolationContext:
    """Immutable context information for contract violations."""
    function_name: str
    module_name: str
    violation_type: ViolationType
    parameters: Dict[str, Any]
    expected_condition: str
    actual_values: Dict[str, Any]
    
    def get_debug_info(self) -> str:
        """Generate detailed debug information for violation."""
        return (
            f"Function: {self.module_name}.{self.function_name}\n"
            f"Violation: {self.violation_type.value}\n"
            f"Expected: {self.expected_condition}\n"
            f"Parameters: {self.parameters}\n"
            f"Actual Values: {self.actual_values}"
        )


class ContractViolation(Exception):
    """Base class for all contract violations with comprehensive context."""
    
    def __init__(self, 
                 message: str, 
                 context: ViolationContext,
                 recovery_suggestion: Optional[str] = None):
        """Initialize contract violation with context and recovery guidance.
        
        Args:
            message: Human-readable violation description
            context: Detailed violation context information
            recovery_suggestion: Optional guidance for resolving violation
        """
        self.message = message
        self.context = context
        self.recovery_suggestion = recovery_suggestion
        
        # Format comprehensive error message
        full_message = f"{context.violation_type.value.title()} violation: {message}"
        if recovery_suggestion:
            full_message += f"\nRecovery: {recovery_suggestion}"
        
        super().__init__(full_message)
    
    def get_violation_type(self) -> ViolationType:
        """Get the specific type of contract violation."""
        return self.context.violation_type
    
    def is_recoverable(self) -> bool:
        """Check if violation is potentially recoverable."""
        return self.recovery_suggestion is not None
    
    def get_function_signature(self) -> str:
        """Get formatted function signature for debugging."""
        return f"{self.context.module_name}.{self.context.function_name}"


class PreconditionViolation(ContractViolation):
    """Raised when function preconditions are not satisfied."""
    
    def __init__(self, 
                 condition: str, 
                 context: ViolationContext,
                 invalid_parameters: List[str]):
        """Initialize precondition violation with parameter details.
        
        Args:
            condition: The violated precondition expression
            context: Violation context information
            invalid_parameters: List of parameter names that caused violation
        """
        self.condition = condition
        self.invalid_parameters = invalid_parameters
        
        message = f"Precondition '{condition}' violated"
        if invalid_parameters:
            message += f" - Invalid parameters: {', '.join(invalid_parameters)}"
        
        recovery = f"Validate parameters: {', '.join(invalid_parameters)} before calling function"
        
        super().__init__(message, context, recovery)


class PostconditionViolation(ContractViolation):
    """Raised when function postconditions are not satisfied."""
    
    def __init__(self, 
                 condition: str, 
                 context: ViolationContext,
                 expected_result: Any,
                 actual_result: Any):
        """Initialize postcondition violation with result details.
        
        Args:
            condition: The violated postcondition expression
            context: Violation context information
            expected_result: Expected function result
            actual_result: Actual function result
        """
        self.condition = condition
        self.expected_result = expected_result
        self.actual_result = actual_result
        
        message = (f"Postcondition '{condition}' violated - "
                  f"Expected: {expected_result}, Got: {actual_result}")
        
        recovery = "Review function implementation to ensure correct result generation"
        
        super().__init__(message, context, recovery)


class InvariantViolation(ContractViolation):
    """Raised when system or object invariants are broken."""
    
    def __init__(self, 
                 invariant_name: str, 
                 context: ViolationContext,
                 current_state: Dict[str, Any]):
        """Initialize invariant violation with state information.
        
        Args:
            invariant_name: Name of the violated invariant
            context: Violation context information
            current_state: Current system state that violates invariant
        """
        self.invariant_name = invariant_name
        self.current_state = current_state
        
        message = f"Invariant '{invariant_name}' violated in current system state"
        
        recovery = f"Restore system state to satisfy invariant '{invariant_name}'"
        
        super().__init__(message, context, recovery)


class TypeSafetyViolation(ContractViolation):
    """Raised when type safety contracts are violated."""
    
    def __init__(self, 
                 parameter_name: str, 
                 expected_type: type, 
                 actual_type: type,
                 context: ViolationContext):
        """Initialize type safety violation with type information.
        
        Args:
            parameter_name: Name of parameter with incorrect type
            expected_type: Expected parameter type
            actual_type: Actual parameter type
            context: Violation context information
        """
        self.parameter_name = parameter_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        
        message = (f"Type safety violation for parameter '{parameter_name}' - "
                  f"Expected: {expected_type.__name__}, Got: {actual_type.__name__}")
        
        recovery = f"Ensure parameter '{parameter_name}' is of type {expected_type.__name__}"
        
        super().__init__(message, context, recovery)


class SecurityBoundaryViolation(ContractViolation):
    """Raised when security boundary contracts are violated."""
    
    def __init__(self, 
                 boundary_name: str, 
                 attempted_operation: str,
                 context: ViolationContext):
        """Initialize security boundary violation.
        
        Args:
            boundary_name: Name of violated security boundary
            attempted_operation: Operation that violated boundary
            context: Violation context information
        """
        self.boundary_name = boundary_name
        self.attempted_operation = attempted_operation
        
        message = (f"Security boundary '{boundary_name}' violated by "
                  f"operation: {attempted_operation}")
        
        recovery = f"Ensure operation '{attempted_operation}' respects security boundary"
        
        super().__init__(message, context, recovery)


# Exception factory functions for consistent violation creation

def create_precondition_violation(function_name: str, 
                                 module_name: str,
                                 condition: str, 
                                 parameters: Dict[str, Any],
                                 invalid_parameters: List[str]) -> PreconditionViolation:
    """Factory function for creating precondition violations."""
    context = ViolationContext(
        function_name=function_name,
        module_name=module_name,
        violation_type=ViolationType.PRECONDITION,
        parameters=parameters,
        expected_condition=condition,
        actual_values={}
    )
    return PreconditionViolation(condition, context, invalid_parameters)


def create_postcondition_violation(function_name: str,
                                  module_name: str, 
                                  condition: str,
                                  expected_result: Any,
                                  actual_result: Any) -> PostconditionViolation:
    """Factory function for creating postcondition violations."""
    context = ViolationContext(
        function_name=function_name,
        module_name=module_name,
        violation_type=ViolationType.POSTCONDITION,
        parameters={},
        expected_condition=condition,
        actual_values={"result": actual_result}
    )
    return PostconditionViolation(condition, context, expected_result, actual_result)


def create_invariant_violation(function_name: str,
                              module_name: str,
                              invariant_name: str,
                              current_state: Dict[str, Any]) -> InvariantViolation:
    """Factory function for creating invariant violations."""
    context = ViolationContext(
        function_name=function_name,
        module_name=module_name,
        violation_type=ViolationType.INVARIANT,
        parameters={},
        expected_condition=f"Invariant {invariant_name} must hold",
        actual_values=current_state
    )
    return InvariantViolation(invariant_name, context, current_state)
