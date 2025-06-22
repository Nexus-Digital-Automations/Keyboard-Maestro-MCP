# src/types/results.py
"""
Result types for operation outcomes.

This module defines Result type for functional error handling following 
Either/Result monad patterns for safe composition of operations.
"""

from typing import TypeVar, Generic, Union, Optional, Callable, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .domain_types import OperationError  # Re-export from domain_types
from .enumerations import ErrorType  # Re-export from enumerations

# Generic type variables
T = TypeVar('T')  # Success value type
E = TypeVar('E')  # Error value type
U = TypeVar('U')  # Transformed value type


class Result(Generic[T, E], ABC):
    """
    Abstract base class for Result type representing success or failure.
    
    Implements monadic operations for safe error handling and composition.
    """
    
    @abstractmethod
    def is_success(self) -> bool:
        """Check if result is successful."""
        pass
    
    @abstractmethod
    def is_failure(self) -> bool:
        """Check if result is failure."""
        pass
    
    @abstractmethod
    def get_value(self) -> Optional[T]:
        """Get the success value if present."""
        pass
    
    @abstractmethod
    def get_error(self) -> Optional[E]:
        """Get the error if present."""
        pass
    
    @abstractmethod
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform success value with function."""
        pass
    
    @abstractmethod
    def flat_map(self, func: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        """Chain operations that return Results."""
        pass
    
    @abstractmethod
    def map_error(self, func: Callable[[E], E]) -> 'Result[T, E]':
        """Transform error with function."""
        pass
    
    @abstractmethod
    def or_else(self, default: T) -> T:
        """Get value or return default."""
        pass
    
    @abstractmethod
    def or_else_get(self, supplier: Callable[[], T]) -> T:
        """Get value or compute default."""
        pass


@dataclass(frozen=True)
class Success(Result[T, E]):
    """Successful result containing a value."""
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_failure(self) -> bool:
        return False
    
    def get_value(self) -> Optional[T]:
        return self.value
    
    def get_error(self) -> Optional[E]:
        return None
    
    def map(self, func: Callable[[T], U]) -> Result[U, E]:
        """Apply function to success value."""
        try:
            return Success(func(self.value))
        except Exception as e:
            return Failure(OperationError(
                error_type=ErrorType.SYSTEM_ERROR,
                message=f"Error in map operation: {str(e)}",
                details=str(e)
            ))
    
    def flat_map(self, func: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Chain Result-returning operations."""
        try:
            return func(self.value)
        except Exception as e:
            return Failure(OperationError(
                error_type=ErrorType.SYSTEM_ERROR,
                message=f"Error in flat_map operation: {str(e)}",
                details=str(e)
            ))
    
    def map_error(self, func: Callable[[E], E]) -> Result[T, E]:
        """No-op for success."""
        return self
    
    def or_else(self, default: T) -> T:
        """Return the success value."""
        return self.value
    
    def or_else_get(self, supplier: Callable[[], T]) -> T:
        """Return the success value."""
        return self.value


@dataclass(frozen=True)
class Failure(Result[T, E]):
    """Failed result containing an error."""
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_failure(self) -> bool:
        return True
    
    def get_value(self) -> Optional[T]:
        return None
    
    def get_error(self) -> Optional[E]:
        return self.error
    
    def map(self, func: Callable[[T], U]) -> Result[U, E]:
        """Propagate failure."""
        return Failure(self.error)
    
    def flat_map(self, func: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Propagate failure."""
        return Failure(self.error)
    
    def map_error(self, func: Callable[[E], E]) -> Result[T, E]:
        """Transform the error."""
        try:
            return Failure(func(self.error))
        except Exception as e:
            # If error transformation fails, keep original error
            return self
    
    def or_else(self, default: T) -> T:
        """Return the default value."""
        return default
    
    def or_else_get(self, supplier: Callable[[], T]) -> T:
        """Compute and return default value."""
        return supplier()


# Factory functions for creating Results
def success(value: T) -> Result[T, OperationError]:
    """Create a successful result."""
    return Success(value)


def failure(error: OperationError) -> Result[T, OperationError]:
    """Create a failed result."""
    return Failure(error)


def from_optional(value: Optional[T], error_msg: str = "Value not found") -> Result[T, OperationError]:
    """Convert optional value to Result."""
    if value is not None:
        return Success(value)
    else:
        return Failure(OperationError(
            error_type=ErrorType.NOT_FOUND_ERROR,
            message=error_msg
        ))


def from_exception(func: Callable[[], T]) -> Result[T, OperationError]:
    """Execute function and wrap result/exception in Result."""
    try:
        return Success(func())
    except Exception as e:
        return Failure(OperationError(
            error_type=ErrorType.SYSTEM_ERROR,
            message=str(e),
            details=repr(e)
        ))


# Re-exports for convenience
__all__ = [
    'Result', 'Success', 'Failure',
    'success', 'failure', 'from_optional', 'from_exception',
    'OperationError', 'ErrorType'
]
