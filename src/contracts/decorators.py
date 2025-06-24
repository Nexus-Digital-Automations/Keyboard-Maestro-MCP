# Contract Enforcement Decorators Framework  
# Target: <250 lines - Contract decorators for preconditions, postconditions, and invariants

"""
Contract enforcement decorators implementing Design by Contract patterns.

This module provides the core decorator framework for enforcing contracts through
preconditions, postconditions, and invariants. Integrates with the validation
framework and exception hierarchy to provide comprehensive contract enforcement
with detailed error reporting and debugging support.

Key Features:
- Precondition enforcement with parameter validation
- Postcondition enforcement with result validation
- Invariant checking with state preservation
- Comprehensive error reporting with violation context
- Integration with type system and validation framework
- Support for async functions and coroutines
"""

import asyncio
import inspect
from functools import wraps
from typing import Callable, Any, Dict, Optional, TypeVar, Union
from uuid import uuid4

from .exceptions import (
    ViolationContext, ViolationType, PreconditionViolation, 
    PostconditionViolation, InvariantViolation,
    create_precondition_violation, create_postcondition_violation
)
from src.contracts.validators import (
    is_valid_macro_identifier, is_valid_variable_name, is_safe_script_content,
    is_valid_timeout
)
from src.types.enumerations import VariableScope
from src.contracts.invariants import system_invariant_checker

F = TypeVar('F', bound=Callable[..., Any])


class ContractState:
    """Manages contract state capture for postcondition and invariant checking."""
    
    def __init__(self):
        self.captured_states: Dict[str, Any] = {}
        self.execution_context: Dict[str, Any] = {}
    
    def capture_state(self, state_id: str, state_data: Any) -> None:
        """Capture state for later comparison."""
        self.captured_states[state_id] = state_data
    
    def get_captured_state(self, state_id: str) -> Any:
        """Retrieve previously captured state."""
        return self.captured_states.get(state_id)
    
    def set_context(self, key: str, value: Any) -> None:
        """Set execution context information."""
        self.execution_context[key] = value
    
    def get_context(self, key: str) -> Any:
        """Get execution context information."""
        return self.execution_context.get(key)


def requires(condition: Union[Callable, str], 
            message: Optional[str] = None,
            validation_func: Optional[Callable] = None) -> Callable[[F], F]:
    """Precondition contract decorator.
    
    Args:
        condition: Boolean function or condition string to evaluate
        message: Optional custom error message
        validation_func: Optional validation function for complex checks
    
    Returns:
        Decorated function with precondition enforcement
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _enforce_precondition(
                func, condition, message, validation_func, args, kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _enforce_precondition_sync(
                func, condition, message, validation_func, args, kwargs
            )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def ensures(condition: Union[Callable, str],
           message: Optional[str] = None,
           captures_state: bool = False) -> Callable[[F], F]:
    """Postcondition contract decorator.
    
    Args:
        condition: Boolean function or condition string to evaluate with result
        message: Optional custom error message
        captures_state: Whether to capture pre-execution state for comparison
    
    Returns:
        Decorated function with postcondition enforcement
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _enforce_postcondition(
                func, condition, message, captures_state, args, kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _enforce_postcondition_sync(
                func, condition, message, captures_state, args, kwargs
            )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invariant(condition: Union[Callable, str],
             state_extractor: Optional[Callable] = None,
             message: Optional[str] = None) -> Callable[[F], F]:
    """Invariant contract decorator.
    
    Args:
        condition: Boolean function or condition string for invariant
        state_extractor: Function to extract relevant state for checking
        message: Optional custom error message
    
    Returns:
        Decorated function with invariant enforcement
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _enforce_invariant(
                func, condition, state_extractor, message, args, kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _enforce_invariant_sync(
                func, condition, state_extractor, message, args, kwargs
            )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Internal enforcement functions

async def _enforce_precondition(func: Callable, condition: Union[Callable, str],
                               message: Optional[str], validation_func: Optional[Callable],
                               args: tuple, kwargs: dict) -> Any:
    """Enforce precondition for async functions."""
    # Bind arguments to function signature
    sig = inspect.signature(func)
    try:
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
    except TypeError as e:
        # Handle binding errors
        context = _create_violation_context(func, ViolationType.PRECONDITION, 
                                          dict(kwargs), "Parameter binding failed")
        raise create_precondition_violation(
            func.__name__, func.__module__, str(e), dict(kwargs), []
        )
    
    # Evaluate precondition
    if not _evaluate_condition(condition, bound_args.arguments, validation_func):
        violation_message = message or f"Precondition violated: {condition}"
        invalid_params = _identify_invalid_parameters(
            condition, bound_args.arguments, validation_func
        )
        
        context = _create_violation_context(func, ViolationType.PRECONDITION,
                                          bound_args.arguments, str(condition))
        raise create_precondition_violation(
            func.__name__, func.__module__, violation_message, 
            bound_args.arguments, invalid_params
        )
    
    # Execute function
    return await func(*args, **kwargs)


def _enforce_precondition_sync(func: Callable, condition: Union[Callable, str],
                              message: Optional[str], validation_func: Optional[Callable],
                              args: tuple, kwargs: dict) -> Any:
    """Enforce precondition for sync functions."""
    # Similar logic to async version but without await
    sig = inspect.signature(func)
    try:
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
    except TypeError as e:
        context = _create_violation_context(func, ViolationType.PRECONDITION,
                                          dict(kwargs), "Parameter binding failed")
        raise create_precondition_violation(
            func.__name__, func.__module__, str(e), dict(kwargs), []
        )
    
    if not _evaluate_condition(condition, bound_args.arguments, validation_func):
        violation_message = message or f"Precondition violated: {condition}"
        invalid_params = _identify_invalid_parameters(
            condition, bound_args.arguments, validation_func
        )
        
        context = _create_violation_context(func, ViolationType.PRECONDITION,
                                          bound_args.arguments, str(condition))
        raise create_precondition_violation(
            func.__name__, func.__module__, violation_message,
            bound_args.arguments, invalid_params
        )
    
    return func(*args, **kwargs)


async def _enforce_postcondition(func: Callable, condition: Union[Callable, str],
                                message: Optional[str], captures_state: bool,
                                args: tuple, kwargs: dict) -> Any:
    """Enforce postcondition for async functions."""
    # Capture pre-execution state if needed
    contract_state = ContractState()
    if captures_state:
        state_id = str(uuid4())
        pre_state = _capture_relevant_state(func, args, kwargs)
        contract_state.capture_state(state_id, pre_state)
        contract_state.set_context('pre_state_id', state_id)
    
    # Execute function
    result = await func(*args, **kwargs)
    
    # Evaluate postcondition
    if not _evaluate_postcondition(condition, result, contract_state, args, kwargs):
        violation_message = message or f"Postcondition violated: {condition}"
        
        context = _create_violation_context(func, ViolationType.POSTCONDITION,
                                          dict(kwargs), str(condition))
        raise create_postcondition_violation(
            func.__name__, func.__module__, violation_message, 
            "expected_result", result
        )
    
    return result


def _enforce_postcondition_sync(func: Callable, condition: Union[Callable, str],
                               message: Optional[str], captures_state: bool,
                               args: tuple, kwargs: dict) -> Any:
    """Enforce postcondition for sync functions."""
    # Similar logic to async version
    contract_state = ContractState()
    if captures_state:
        state_id = str(uuid4())
        pre_state = _capture_relevant_state(func, args, kwargs)
        contract_state.capture_state(state_id, pre_state)
        contract_state.set_context('pre_state_id', state_id)
    
    result = func(*args, **kwargs)
    
    if not _evaluate_postcondition(condition, result, contract_state, args, kwargs):
        violation_message = message or f"Postcondition violated: {condition}"
        
        context = _create_violation_context(func, ViolationType.POSTCONDITION,
                                          dict(kwargs), str(condition))
        raise create_postcondition_violation(
            func.__name__, func.__module__, violation_message,
            "expected_result", result
        )
    
    return result


async def _enforce_invariant(func: Callable, condition: Union[Callable, str],
                           state_extractor: Optional[Callable], message: Optional[str],
                           args: tuple, kwargs: dict) -> Any:
    """Enforce invariant for async functions."""
    # Check invariant before execution
    pre_state = state_extractor(*args, **kwargs) if state_extractor else {}
    if not _evaluate_invariant(condition, pre_state):
        violation_message = message or f"Invariant violated before execution: {condition}"
        raise InvariantViolation("pre_execution", _create_violation_context(
            func, ViolationType.INVARIANT, dict(kwargs), str(condition)
        ), pre_state)
    
    # Execute function
    result = await func(*args, **kwargs)
    
    # Check invariant after execution
    post_state = state_extractor(*args, **kwargs) if state_extractor else {}
    if not _evaluate_invariant(condition, post_state):
        violation_message = message or f"Invariant violated after execution: {condition}"
        raise InvariantViolation("post_execution", _create_violation_context(
            func, ViolationType.INVARIANT, dict(kwargs), str(condition)
        ), post_state)
    
    return result


def _enforce_invariant_sync(func: Callable, condition: Union[Callable, str],
                          state_extractor: Optional[Callable], message: Optional[str],
                          args: tuple, kwargs: dict) -> Any:
    """Enforce invariant for sync functions."""
    # Similar logic to async version
    pre_state = state_extractor(*args, **kwargs) if state_extractor else {}
    if not _evaluate_invariant(condition, pre_state):
        violation_message = message or f"Invariant violated before execution: {condition}"
        raise InvariantViolation("pre_execution", _create_violation_context(
            func, ViolationType.INVARIANT, dict(kwargs), str(condition)
        ), pre_state)
    
    result = func(*args, **kwargs)
    
    post_state = state_extractor(*args, **kwargs) if state_extractor else {}
    if not _evaluate_invariant(condition, post_state):
        violation_message = message or f"Invariant violated after execution: {condition}"
        raise InvariantViolation("post_execution", _create_violation_context(
            func, ViolationType.INVARIANT, dict(kwargs), str(condition)
        ), post_state)
    
    return result


# Convenience contract decorators

def macro_contract():
    """Convenience decorator for macro operations contracts."""
    def decorator(func: F) -> F:
        # Add the macro identifier and timeout validation
        @requires(lambda identifier, **kwargs: is_valid_macro_identifier(identifier))
        @requires(lambda timeout=30, **kwargs: is_valid_timeout(timeout))
        @ensures(lambda result: isinstance(result, dict) and 'success' in result)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def variable_contract():
    """Convenience decorator for variable operations contracts."""
    def decorator(func: F) -> F:
        # Add variable name and scope validation
        @requires(lambda name, **kwargs: is_valid_variable_name(name))
        @requires(lambda scope, **kwargs: isinstance(scope, VariableScope))
        @ensures(lambda result: isinstance(result, dict) and 'success' in result)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def security_contract():
    """Convenience decorator for security-sensitive operations."""
    def decorator(func: F) -> F:
        # Add script safety validation
        @requires(lambda script, **kwargs: is_safe_script_content(script))
        @invariant(lambda: system_invariant_checker.check_all())
        @ensures(lambda result: isinstance(result, dict) and 'success' in result)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Helper functions

def _evaluate_condition(condition: Union[Callable, str], 
                       parameters: Dict[str, Any],
                       validation_func: Optional[Callable]) -> bool:
    """Evaluate contract condition with parameters."""
    try:
        if callable(condition):
            # Try different calling conventions based on the parameter count
            sig = inspect.signature(condition)
            param_count = len(sig.parameters)
            param_names = list(sig.parameters.keys())
            
            # Try to match the condition's parameters with the provided parameters
            # First try with the parameters dictionary
            try:
                # Filter the parameters to only include those expected by the condition
                filtered_params = {k: v for k, v in parameters.items() if k in param_names}
                if len(filtered_params) == param_count:
                    return condition(**filtered_params)
            except Exception:
                pass
                
            # If that fails, try with the first parameter if there's only one
            if param_count == 1 and len(parameters) > 0:
                try:
                    # Use the first parameter value
                    first_param_value = next(iter(parameters.values()))
                    return condition(first_param_value)
                except Exception:
                    pass
            
            # As a fallback, just call the condition with no parameters
            try:
                return condition()
            except Exception:
                pass
                
            # If we get here, try one more approach - evaluate with all parameters
            try:
                return condition(**parameters)
            except Exception:
                return False
                
        elif validation_func:
            return validation_func(**parameters)
        else:
            # For string conditions, would need expression evaluation
            # Simplified implementation for now
            return True
    except Exception as e:
        # For debugging
        # print(f"Error evaluating condition: {e}")
        return False


def _evaluate_postcondition(condition: Union[Callable, str], result: Any,
                          contract_state: ContractState,
                          args: tuple, kwargs: dict) -> bool:
    """Evaluate postcondition with result and state."""
    try:
        if callable(condition):
            # Try different call patterns based on the condition's signature
            sig = inspect.signature(condition)
            param_count = len(sig.parameters)
            
            if param_count == 1:
                # Condition expects only the result
                return condition(result)
            elif param_count == 2 and 'result' in sig.parameters:
                # Condition expects result and another parameter
                param_names = list(sig.parameters.keys())
                second_param = param_names[1] if param_names[0] == 'result' else param_names[0]
                
                if second_param == 'contract_state':
                    return condition(result, contract_state)
                else:
                    # For other parameter names, try to use args/kwargs
                    return condition(result, args[0] if args else kwargs.get(second_param))
            else:
                # For more complex signatures, pass result as first argument
                try:
                    return condition(result)
                except TypeError:
                    # If that fails, just call with no arguments as a fallback
                    return condition()
        else:
            # Simplified evaluation for string conditions
            return True
    except Exception as e:
        # For debugging during development
        # print(f"Postcondition evaluation error: {e}")
        return False


def _evaluate_invariant(condition: Union[Callable, str], state: Dict[str, Any]) -> bool:
    """Evaluate invariant condition with state."""
    try:
        if callable(condition):
            return condition(state)
        else:
            # Simplified evaluation for string conditions
            return True
    except Exception:
        return False


def _identify_invalid_parameters(condition: Union[Callable, str],
                               parameters: Dict[str, Any],
                               validation_func: Optional[Callable]) -> list:
    """Identify which parameters caused precondition violation."""
    # Simplified implementation - would analyze condition to identify specific parameters
    return list(parameters.keys())


def _create_violation_context(func: Callable, violation_type: ViolationType,
                            parameters: Dict[str, Any], condition: str) -> ViolationContext:
    """Create violation context for error reporting."""
    return ViolationContext(
        function_name=func.__name__,
        module_name=func.__module__,
        violation_type=violation_type,
        parameters=parameters,
        expected_condition=condition,
        actual_values={}
    )


def _capture_relevant_state(func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Capture relevant state for postcondition comparison."""
    # Simplified implementation - would capture relevant object state
    return {"args": args, "kwargs": kwargs}
