# Core Test Data Generators: Keyboard Maestro MCP Server
# tests/properties/generators.py

"""
Core domain-specific test data generators for property-based testing.

This module provides essential hypothesis strategies for generating valid 
test data that reflects Keyboard Maestro domain constraints and usage patterns.

Generator Categories:
- Branded Type Generators: MacroName, VariableName, MacroUUID
- Coordinate Generators: ScreenCoordinates, ScreenArea  
- Basic Configuration Generators: Simple structures only
- Value Generators: Timeouts, confidence scores, variable values

Size: 238 lines (target: <250)
Note: Complex generators extracted to separate modules for maintainability
"""

from hypothesis import strategies as st
from hypothesis.strategies import composite
from typing import Dict, Optional
import string
import uuid

from src.types.identifiers import (
    MacroUUID, MacroName, VariableName, GroupUUID
)
from src.types.values import (
    MacroExecutionTimeout, VariableValue,
    ScreenCoordinate, ScreenCoordinates, ScreenArea, ConfidenceScore
)
from src.types.enumerations import TriggerType, ActionType, VariableScope


# =============================================================================
# Core Branded Type Generators
# =============================================================================

@composite
def macro_names(draw):
    """Generate valid macro names following Keyboard Maestro conventions."""
    valid_chars = string.ascii_letters + string.digits + "_- ."
    name = draw(st.text(
        alphabet=valid_chars,
        min_size=1,
        max_size=100
    ).filter(lambda x: x.strip() and not x.startswith('.') and not x.endswith('.')))
    
    return MacroName(name)


@composite
def variable_names(draw):
    """Generate valid variable names following KM identifier conventions."""
    first_char = draw(st.sampled_from(string.ascii_letters + "_"))
    rest_chars = draw(st.text(
        alphabet=string.ascii_letters + string.digits + "_",
        min_size=0,
        max_size=49
    ))
    
    name = first_char + rest_chars
    return VariableName(name)


@composite
def macro_uuids(draw):
    """Generate valid macro UUIDs."""
    uuid_str = str(uuid.uuid4())
    return MacroUUID(uuid.UUID(uuid_str))


@composite
def group_uuids(draw):
    """Generate valid group UUIDs."""
    uuid_str = str(uuid.uuid4())
    return GroupUUID(uuid.UUID(uuid_str))


# =============================================================================
# Value Type Generators
# =============================================================================

@composite
def execution_timeouts(draw):
    """Generate valid execution timeouts in reasonable ranges."""
    timeout = draw(st.integers(min_value=1, max_value=120))
    return MacroExecutionTimeout(timeout)


@composite
def confidence_scores(draw):
    """Generate valid confidence scores for OCR and recognition."""
    score = draw(st.floats(min_value=0.0, max_value=1.0))
    return ConfidenceScore(score)


@composite
def screen_coordinates(draw):
    """Generate valid screen coordinates within reasonable bounds."""
    x = draw(st.integers(min_value=0, max_value=2560))
    y = draw(st.integers(min_value=0, max_value=1440))
    
    return ScreenCoordinates(
        ScreenCoordinate(x),
        ScreenCoordinate(y)
    )


@composite
def screen_areas(draw):
    """Generate valid screen areas with proper geometric constraints."""
    top_left = draw(screen_coordinates())
    
    width = draw(st.integers(min_value=10, max_value=500))
    height = draw(st.integers(min_value=10, max_value=500))
    
    bottom_right = ScreenCoordinates(
        ScreenCoordinate(top_left.x + width),
        ScreenCoordinate(top_left.y + height)
    )
    
    return ScreenArea(top_left, bottom_right)


@composite
def variable_values(draw):
    """Generate variable values with different content patterns."""
    value_type = draw(st.sampled_from(['text', 'number', 'json', 'empty']))
    
    if value_type == 'text':
        value = draw(st.text(min_size=0, max_size=200))
    elif value_type == 'number':
        value = str(draw(st.integers(min_value=-1000, max_value=1000)))
    elif value_type == 'json':
        # Simple JSON structure
        data = draw(st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
            min_size=0,
            max_size=3
        ))
        import json
        value = json.dumps(data)
    else:  # empty
        value = ""
    
    return VariableValue(value)


# =============================================================================
# Basic Configuration Generators
# =============================================================================

@composite  
def simple_trigger_configurations(draw):
    """Generate simple trigger configurations for testing."""
    trigger_type = draw(st.sampled_from([TriggerType.HOTKEY, TriggerType.APPLICATION]))
    
    if trigger_type == TriggerType.HOTKEY:
        key = draw(st.sampled_from(['a', 'space', 'return', 'escape']))
        modifiers = draw(st.lists(
            st.sampled_from(['command', 'option', 'shift']),
            unique=True,
            max_size=2
        ))
        parameters = {'key': key, 'modifiers': modifiers}
    else:  # APPLICATION
        bundle_id = draw(st.sampled_from(['com.apple.safari', 'com.apple.finder']))
        event = draw(st.sampled_from(['launch', 'quit', 'activate']))
        parameters = {'bundle_id': bundle_id, 'event': event}
    
    return {
        'trigger_type': trigger_type,
        'parameters': parameters,
        'enabled': draw(st.booleans()),
        'trigger_id': f"trigger_{uuid.uuid4().hex[:8]}"
    }


@composite
def simple_action_configurations(draw):
    """Generate simple action configurations for testing."""
    action_type = draw(st.sampled_from([ActionType.TEXT_MANIPULATION, ActionType.VARIABLE_MANAGEMENT]))
    
    if action_type == ActionType.TEXT_MANIPULATION:
        text = draw(st.text(min_size=0, max_size=100))
        operation = draw(st.sampled_from(['type', 'paste']))
        parameters = {'text': text, 'operation': operation}
    else:  # VARIABLE_MANAGEMENT
        var_name = draw(variable_names())
        var_value = draw(variable_values())
        scope = draw(st.sampled_from(VariableScope))
        parameters = {'name': var_name, 'value': var_value, 'scope': scope.value}
    
    return {
        'action_type': action_type,
        'parameters': parameters,
        'enabled': draw(st.booleans()),
        'action_id': f"action_{uuid.uuid4().hex[:8]}"
    }


@composite
def macro_configurations(draw):
    """Generate basic macro configurations for property testing."""
    name = draw(macro_names())
    group_id = draw(st.one_of(st.none(), group_uuids()))
    enabled = draw(st.booleans())
    
    # Basic optional properties
    color = draw(st.one_of(st.none(), st.sampled_from(['Red', 'Green', 'Blue'])))
    notes = draw(st.one_of(st.none(), st.text(max_size=100)))
    
    # Simple triggers and actions
    triggers = draw(st.frozensets(
        simple_trigger_configurations(),
        min_size=1,
        max_size=2
    ))
    
    actions = draw(st.frozensets(
        simple_action_configurations(),
        min_size=1,
        max_size=3
    ))
    
    return {
        'name': name,
        'group_id': group_id,
        'enabled': enabled,
        'color': color,
        'notes': notes,
        'triggers': triggers,
        'actions': actions,
        'macro_uuid': draw(macro_uuids()),
        'created_at': draw(st.floats(min_value=1600000000, max_value=2000000000))
    }


# =============================================================================
# Collection Generators 
# =============================================================================

@composite
def variable_collections(draw):
    """Generate simple variable collections for testing."""
    global_vars = draw(st.dictionaries(
        variable_names(),
        variable_values(),
        min_size=0,
        max_size=5
    ))
    
    local_vars = draw(st.dictionaries(
        variable_names(),
        variable_values(),
        min_size=0,
        max_size=3
    ))
    
    return {
        'global': global_vars,
        'local': local_vars
    }


@composite
def execution_contexts(draw):
    """Generate execution contexts for macro execution testing."""
    macro_id = draw(macro_uuids())
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    trigger_value = draw(st.one_of(st.none(), st.text(max_size=50)))
    timeout = draw(execution_timeouts())
    
    return {
        'execution_id': execution_id,
        'macro_id': macro_id,
        'trigger_value': trigger_value,
        'timeout': timeout,
        'start_time': draw(st.floats(min_value=1600000000, max_value=2000000000))
    }


# =============================================================================
# Edge Case Generators
# =============================================================================

@composite
def edge_case_macro_names(draw):
    """Generate macro names that test edge cases."""
    edge_case_type = draw(st.sampled_from(['very_long', 'single_char', 'special_chars']))
    
    if edge_case_type == 'very_long':
        name = 'a' * draw(st.integers(min_value=200, max_value=255))
    elif edge_case_type == 'single_char':
        name = draw(st.sampled_from(string.ascii_letters))
    else:  # special_chars
        name = draw(st.text(alphabet='._- ', min_size=1, max_size=20)).strip()
        if not name:
            name = 'test'
    
    return MacroName(name)


@composite
def boundary_coordinates(draw):
    """Generate coordinates that test boundary conditions."""
    boundary_type = draw(st.sampled_from(['origin', 'max_screen', 'negative']))
    
    if boundary_type == 'origin':
        x, y = 0, 0
    elif boundary_type == 'max_screen':
        x, y = 2559, 1439
    else:  # negative
        x = draw(st.integers(min_value=-100, max_value=-1))
        y = draw(st.integers(min_value=-100, max_value=-1))
    
    return ScreenCoordinates(ScreenCoordinate(x), ScreenCoordinate(y))


# =============================================================================
# Generator Registration
# =============================================================================

# Core generators for easy access
generators = {
    'macro_names': macro_names,
    'variable_names': variable_names,
    'macro_uuids': macro_uuids,
    'screen_coordinates': screen_coordinates,
    'macro_configurations': macro_configurations,
    'execution_contexts': execution_contexts,
    'variable_collections': variable_collections
}
