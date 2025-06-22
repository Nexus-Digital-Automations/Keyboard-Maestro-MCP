# Property Testing Module: Keyboard Maestro MCP Server
# tests/properties/__init__.py

"""
Property-based testing framework for the Keyboard Maestro MCP Server.

This module provides comprehensive property-based testing infrastructure
using hypothesis to verify complex automation logic through generated
test scenarios and systematic invariant validation.

Public API:
- PropertyTestRunner: Execute and coordinate property tests
- KeyboardMaestroPropertyTester: Base testing framework
- Standard test generators for all domain types
- Metamorphic and invariant test suites

Module Structure:
- framework.py: Core testing infrastructure and state machines
- generators.py: Domain-specific test data generators  
- invariants.py: System invariant property tests
- metamorphic.py: Operation relationship and equivalence tests
- conftest.py: Pytest configuration and fixtures

Size: 47 lines (target: <50)
"""

from .framework import (
    PropertyTestConfig,
    PropertyTestRunner, 
    KeyboardMaestroPropertyTester,
    MacroOperationStateMachine,
    VariableOperationStateMachine,
    TestMacroLifecycle,
    TestVariableOperations
)

from .generators import (
    macro_names,
    variable_names,
    macro_uuids,
    screen_coordinates,
    screen_areas,
    macro_configurations,
    execution_contexts,
    variable_collections,
    generators
)

__all__ = [
    # Core framework classes
    'PropertyTestConfig',
    'PropertyTestRunner',
    'KeyboardMaestroPropertyTester',
    
    # State machine testing
    'MacroOperationStateMachine', 
    'VariableOperationStateMachine',
    'TestMacroLifecycle',
    'TestVariableOperations',
    
    # Generators
    'macro_names',
    'variable_names', 
    'macro_uuids',
    'screen_coordinates',
    'screen_areas',
    'macro_configurations',
    'execution_contexts',
    'variable_collections',
    'generators'
]
