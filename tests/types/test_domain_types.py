# tests/types/test_domain_types.py (Target: <250 lines)
"""
Comprehensive test suite for the domain type system.

This module provides extensive testing for all branded types, domain models,
and validation functions using both example-based and property-based testing.
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from hypothesis import given, strategies as st

from src.types import (
    # Identifier types
    MacroUUID, MacroName, VariableName, create_macro_uuid, create_macro_name,
    create_variable_name, MacroIdentifier, VariableIdentifier,
    
    # Value types
    create_execution_timeout, create_confidence_score, create_screen_coordinate,
    ScreenCoordinates, ScreenArea, ColorRGB,
    
    # Enumeration types
    MacroState, VariableScope, TriggerType, ExecutionStatus,
    
    # Domain types
    MacroMetadata, TriggerConfiguration, ActionConfiguration,
    MacroDefinition, create_macro_metadata, create_execution_context,
    OperationError, ErrorType,
    
    # Validation functions
    is_valid_macro_identifier, is_valid_variable_name_format
)


class TestBrandedIdentifierTypes:
    """Test branded identifier types and their validation."""
    
    def test_create_macro_uuid_valid(self):
        """Test valid macro UUID creation."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        macro_uuid = create_macro_uuid(uuid_str)
        assert isinstance(macro_uuid, UUID)
        assert str(macro_uuid) == uuid_str
    
    def test_create_macro_uuid_invalid(self):
        """Test invalid macro UUID creation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid macro UUID format"):
            create_macro_uuid("invalid-uuid")
    
    def test_create_macro_name_valid(self):
        """Test valid macro name creation."""
        name = "Test Macro_123"
        macro_name = create_macro_name(name)
        assert macro_name == name
        assert isinstance(macro_name, str)
    
    def test_create_macro_name_invalid_empty(self):
        """Test empty macro name raises ValueError."""
        with pytest.raises(ValueError, match="Macro name must be 1-255 characters"):
            create_macro_name("")
    
    def test_create_macro_name_invalid_too_long(self):
        """Test overly long macro name raises ValueError."""
        long_name = "a" * 256
        with pytest.raises(ValueError, match="Macro name must be 1-255 characters"):
            create_macro_name(long_name)
    
    def test_create_macro_name_invalid_characters(self):
        """Test macro name with invalid characters raises ValueError."""
        with pytest.raises(ValueError, match="Macro name contains invalid characters"):
            create_macro_name("Test@Macro$")
    
    def test_create_variable_name_valid(self):
        """Test valid variable name creation."""
        name = "test_variable_123"
        var_name = create_variable_name(name)
        assert var_name == name
    
    def test_create_variable_name_invalid_format(self):
        """Test invalid variable name format raises ValueError."""
        with pytest.raises(ValueError, match="Variable name must follow identifier conventions"):
            create_variable_name("123invalid")


class TestValueTypes:
    """Test value types and their validation."""
    
    def test_create_execution_timeout_valid(self):
        """Test valid execution timeout creation."""
        timeout = create_execution_timeout(30)
        assert timeout == 30
    
    def test_create_execution_timeout_invalid_range(self):
        """Test execution timeout outside valid range raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be between 1 and 300 seconds"):
            create_execution_timeout(0)
        
        with pytest.raises(ValueError, match="Timeout must be between 1 and 300 seconds"):
            create_execution_timeout(301)
    
    def test_create_confidence_score_valid(self):
        """Test valid confidence score creation."""
        score = create_confidence_score(0.85)
        assert score == 0.85
    
    def test_create_confidence_score_invalid_range(self):
        """Test confidence score outside valid range raises ValueError."""
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            create_confidence_score(-0.1)
        
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            create_confidence_score(1.1)
    
    def test_screen_coordinates_valid(self):
        """Test valid screen coordinates creation."""
        coords = ScreenCoordinates(
            create_screen_coordinate(100),
            create_screen_coordinate(200)
        )
        assert coords.x == 100
        assert coords.y == 200
    
    def test_screen_coordinates_offset(self):
        """Test screen coordinates offset calculation."""
        coords = ScreenCoordinates(
            create_screen_coordinate(100),
            create_screen_coordinate(200)
        )
        offset_coords = coords.offset(50, -50)
        assert offset_coords.x == 150
        assert offset_coords.y == 150
    
    def test_screen_area_valid(self):
        """Test valid screen area creation."""
        area = ScreenArea(
            ScreenCoordinates(create_screen_coordinate(0), create_screen_coordinate(0)),
            ScreenCoordinates(create_screen_coordinate(100), create_screen_coordinate(200))
        )
        assert area.width == 100
        assert area.height == 200
    
    def test_screen_area_invalid(self):
        """Test invalid screen area raises ValueError."""
        with pytest.raises(ValueError, match="Invalid screen area"):
            ScreenArea(
                ScreenCoordinates(create_screen_coordinate(100), create_screen_coordinate(200)),
                ScreenCoordinates(create_screen_coordinate(50), create_screen_coordinate(100))
            )
    
    def test_color_rgb_valid(self):
        """Test valid RGB color creation."""
        color = ColorRGB(255, 128, 0)
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 0
        assert color.to_hex() == "#FF8000"
    
    def test_color_rgb_from_hex(self):
        """Test RGB color creation from hex."""
        color = ColorRGB.from_hex("#FF8000")
        assert color.red == 255
        assert color.green == 128
        assert color.blue == 0


class TestDomainTypes:
    """Test core domain types and their behavior."""
    
    def test_macro_metadata_creation(self):
        """Test macro metadata creation."""
        uuid = create_macro_uuid(str(uuid4()))
        name = create_macro_name("Test Macro")
        metadata = create_macro_metadata(uuid, name)
        
        assert metadata.uuid == uuid
        assert metadata.name == name
        assert metadata.state == MacroState.DISABLED
        assert isinstance(metadata.created_at, datetime)
    
    def test_trigger_configuration_valid(self):
        """Test valid trigger configuration."""
        config = TriggerConfiguration(
            trigger_type=TriggerType.HOTKEY,
            parameters={'key': 'F1', 'modifiers': ['cmd']},
            enabled=True
        )
        assert config.trigger_type == TriggerType.HOTKEY
        assert config.enabled
    
    def test_trigger_configuration_missing_params(self):
        """Test trigger configuration with missing required parameters."""
        with pytest.raises(ValueError, match="Missing required parameters"):
            TriggerConfiguration(
                trigger_type=TriggerType.HOTKEY,
                parameters={'key': 'F1'},  # Missing modifiers
                enabled=True
            )
    
    def test_macro_definition_valid(self):
        """Test valid macro definition creation."""
        uuid = create_macro_uuid(str(uuid4()))
        name = create_macro_name("Test Macro")
        metadata = create_macro_metadata(uuid, name)
        
        trigger = TriggerConfiguration(
            trigger_type=TriggerType.HOTKEY,
            parameters={'key': 'F1', 'modifiers': ['cmd']}
        )
        
        action = ActionConfiguration(
            action_type=TriggerType.APPLICATION,  # Simplified for test
            parameters={'action': 'launch', 'app': 'Calculator'}
        )
        
        macro_def = MacroDefinition(
            metadata=metadata,
            triggers=frozenset([trigger]),
            actions=frozenset([action])
        )
        
        assert macro_def.trigger_count == 1
        assert macro_def.action_count == 1
        assert macro_def.has_trigger_type(TriggerType.HOTKEY)
    
    def test_operation_error_creation(self):
        """Test operation error creation."""
        error = OperationError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Invalid input",
            details="Parameter 'name' is required",
            recovery_suggestion="Provide a valid name parameter"
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert not error.is_recoverable()
        assert not error.requires_user_action()


class TestValidationFunctions:
    """Test validation functions for type safety."""
    
    def test_is_valid_macro_identifier_string(self):
        """Test macro identifier validation with string."""
        assert is_valid_macro_identifier("Valid Macro Name")
        assert not is_valid_macro_identifier("")
        assert not is_valid_macro_identifier("Invalid@Name")
    
    def test_is_valid_macro_identifier_uuid(self):
        """Test macro identifier validation with UUID."""
        valid_uuid = uuid4()
        assert is_valid_macro_identifier(valid_uuid)
    
    def test_is_valid_variable_name_format(self):
        """Test variable name format validation."""
        assert is_valid_variable_name_format("valid_variable")
        assert is_valid_variable_name_format("_private_var")
        assert not is_valid_variable_name_format("123invalid")
        assert not is_valid_variable_name_format("var-with-dashes")


# Property-based tests for comprehensive validation
@given(st.text(min_size=1, max_size=255, alphabet=st.sampled_from(
    list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.- ')))
)
def test_macro_name_creation_properties(name):
    """Property-based test for macro name creation."""
    import re
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert all(c.isalnum() or c in '_.- ' for c in name)
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name) is not None
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (
            len(name) == 0 or 
            len(name) > 255 or 
            not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
        )


@given(st.integers())
def test_execution_timeout_properties(timeout):
    """Property-based test for execution timeout validation."""
    try:
        result = create_execution_timeout(timeout)
        # If creation succeeds, timeout should be in valid range
        assert 1 <= timeout <= 300
        assert result == timeout
    except ValueError:
        # If creation fails, timeout should be outside valid range
        assert timeout < 1 or timeout > 300


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_confidence_score_properties(score):
    """Property-based test for confidence score validation."""
    import math
    # Skip NaN and infinity values
    if math.isnan(score) or math.isinf(score):
        return
        
    try:
        result = create_confidence_score(score)
        # If creation succeeds, score should be in valid range
        assert 0.0 <= score <= 1.0
        assert result == score
    except ValueError:
        # If creation fails, score should be outside valid range
        assert score < 0.0 or score > 1.0
