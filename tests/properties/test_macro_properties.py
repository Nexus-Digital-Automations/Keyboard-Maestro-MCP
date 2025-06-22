"""
Property-based tests for macro operation invariants.

This module provides comprehensive property-based testing for macro operations,
verifying complex automation logic across the entire input space.
"""

import pytest
from hypothesis import given, strategies as st, assume, note, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle
from typing import Dict, Any, List
import uuid
from dataclasses import asdict

from src.pure.macro_transformations import (
    MacroMetadata, TriggerConfig, ActionConfig,
    normalize_macro_identifier, create_macro_metadata,
    transform_trigger_data, transform_action_data,
    merge_macro_updates, extract_macro_dependencies,
    validate_macro_structure, calculate_macro_complexity
)
from src.validators.macro_validators import MacroValidator, ValidationResult
from src.utils.macro_serialization import MacroSerializer
from src.types.domain_types import SerializationFormat


# Strategy generators for macro data
@st.composite
def macro_names(draw):
    """Generate valid macro names."""
    # Valid macro names: 1-255 chars, no newlines, not reserved
    name = draw(st.text(min_size=1, max_size=255).filter(
        lambda x: '\n' not in x and '\r' not in x and x.strip() not in {
            "Untitled Macro", "New Macro", ""
        }
    ))
    return name.strip()


@st.composite
def macro_uuids(draw):
    """Generate valid macro UUIDs."""
    return str(draw(st.uuids())).upper()


@st.composite
def macro_identifiers(draw):
    """Generate mixed macro identifiers (names or UUIDs)."""
    return draw(st.one_of(macro_names(), macro_uuids()))


@st.composite
def trigger_configs(draw):
    """Generate valid trigger configurations."""
    trigger_types = ["hotkey", "app_activate", "file_added", "time_based", "system_wake"]
    trigger_type = draw(st.sampled_from(trigger_types))
    
    # Generate appropriate parameters for each trigger type
    parameters = {}
    if trigger_type == "hotkey":
        parameters = {
            "key": draw(st.sampled_from(["a", "return", "space", "f1"])),
            "modifiers": draw(st.lists(
                st.sampled_from(["Command", "Option", "Shift", "Control"]),
                unique=True, max_size=4
            ))
        }
    elif trigger_type == "app_activate":
        parameters = {
            "application": draw(st.text(min_size=1, max_size=100))
        }
    elif trigger_type == "file_added":
        parameters = {
            "path": draw(st.text(min_size=1, max_size=200)),
            "recursive": draw(st.booleans())
        }
    
    return TriggerConfig(
        trigger_type=trigger_type,
        parameters=parameters,
        enabled=draw(st.booleans())
    )


@st.composite
def action_configs(draw):
    """Generate valid action configurations."""
    action_types = ["pause", "set_variable", "copy_file", "if_then", "execute_applescript"]
    action_type = draw(st.sampled_from(action_types))
    
    # Generate appropriate parameters for each action type
    parameters = {}
    if action_type == "pause":
        parameters = {
            "duration": draw(st.floats(min_value=0.1, max_value=60.0))
        }
    elif action_type == "set_variable":
        parameters = {
            "variable_name": draw(st.text(min_size=1, max_size=100)),
            "value": draw(st.text(max_size=1000))
        }
    elif action_type == "copy_file":
        parameters = {
            "source_path": draw(st.text(min_size=1, max_size=200)),
            "dest_path": draw(st.text(min_size=1, max_size=200))
        }
    
    return ActionConfig(
        action_type=action_type,
        parameters=parameters,
        enabled=draw(st.booleans()),
        timeout=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=300)))
    )


@st.composite
def macro_metadata(draw):
    """Generate valid macro metadata."""
    return create_macro_metadata(
        name=draw(macro_names()),
        group_uuid=draw(st.one_of(st.none(), macro_uuids())),
        enabled=draw(st.booleans()),
        color=draw(st.one_of(st.none(), st.sampled_from([
            "red", "green", "blue", "yellow", "orange", "#FF0000", "#00FF00"
        ]))),
        notes=draw(st.one_of(st.none(), st.text(max_size=1000)))
    )


class TestMacroIdentifierProperties:
    """Property-based tests for macro identifier handling."""
    
    @given(identifier=macro_identifiers())
    def test_identifier_normalization_idempotent(self, identifier):
        """Test that identifier normalization is idempotent."""
        normalized_once = normalize_macro_identifier(identifier)
        normalized_twice = normalize_macro_identifier(normalized_once)
        
        assert normalized_once == normalized_twice
    
    @given(uuid_val=st.uuids())
    def test_uuid_identifier_normalization(self, uuid_val):
        """Test UUID identifier normalization produces consistent format."""
        normalized = normalize_macro_identifier(uuid_val)
        
        # Should be uppercase string representation
        assert isinstance(normalized, str)
        assert normalized == str(uuid_val).upper()
        assert len(normalized) == 36  # Standard UUID length
    
    @given(name=macro_names())
    def test_name_identifier_normalization(self, name):
        """Test name identifier normalization preserves valid names."""
        normalized = normalize_macro_identifier(name)
        
        # Should strip whitespace but preserve content
        assert normalized == name.strip()
        assert len(normalized) > 0


class TestMacroMetadataProperties:
    """Property-based tests for macro metadata operations."""
    
    @given(metadata=macro_metadata())
    def test_metadata_immutability(self, metadata):
        """Test that macro metadata is truly immutable."""
        original_dict = asdict(metadata)
        
        # Attempting to modify should fail
        with pytest.raises(AttributeError):
            metadata.name = "Modified Name"
        
        # Verify no changes occurred
        assert asdict(metadata) == original_dict
    
    @given(
        metadata=macro_metadata(),
        updates=st.dictionaries(
            st.sampled_from(["name", "enabled", "color", "notes"]),
            st.one_of(
                macro_names(),
                st.booleans(),
                st.sampled_from(["red", "blue", "#FF0000"]),
                st.text(max_size=100)
            )
        )
    )
    def test_metadata_merge_preserves_structure(self, metadata, updates):
        """Test that merging updates preserves metadata structure."""
        merged = merge_macro_updates(metadata, updates)
        
        # Should still be MacroMetadata instance
        assert isinstance(merged, MacroMetadata)
        
        # Should have all required fields
        assert hasattr(merged, 'uuid')
        assert hasattr(merged, 'name')
        assert hasattr(merged, 'group_uuid')
        assert hasattr(merged, 'enabled')
        
        # UUID should never change
        assert merged.uuid == metadata.uuid
        
        # Applied updates should be reflected
        for key, value in updates.items():
            if hasattr(merged, key):
                assert getattr(merged, key) == value


class TestTriggerActionProperties:
    """Property-based tests for trigger and action configurations."""
    
    @given(trigger_data=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=1
    ))
    def test_trigger_transformation_requires_type(self, trigger_data):
        """Test that trigger transformation requires 'type' field."""
        if 'type' not in trigger_data:
            with pytest.raises(ValueError, match="Trigger type is required"):
                transform_trigger_data(trigger_data)
        else:
            # Should succeed if type is present
            result = transform_trigger_data(trigger_data)
            assert isinstance(result, TriggerConfig)
            assert result.trigger_type == trigger_data['type']
    
    @given(action_data=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=1
    ))
    def test_action_transformation_requires_type(self, action_data):
        """Test that action transformation requires 'type' field."""
        if 'type' not in action_data:
            with pytest.raises(ValueError, match="Action type is required"):
                transform_action_data(action_data)
        else:
            # Should succeed if type is present
            result = transform_action_data(action_data)
            assert isinstance(result, ActionConfig)
            assert result.action_type == action_data['type']
    
    @given(
        triggers=st.lists(trigger_configs(), max_size=20),
        actions=st.lists(action_configs(), max_size=50)
    )
    def test_dependency_extraction_consistency(self, triggers, actions):
        """Test that dependency extraction is consistent and deterministic."""
        deps1 = extract_macro_dependencies(triggers, actions)
        deps2 = extract_macro_dependencies(triggers, actions)
        
        # Should produce identical results
        assert deps1 == deps2
        
        # Should be a set
        assert isinstance(deps1, set)
        
        # All dependencies should be strings with proper format
        for dep in deps1:
            assert isinstance(dep, str)
            assert ':' in dep  # Should have type:value format


class TestMacroValidationProperties:
    """Property-based tests for macro validation logic."""
    
    @given(name=st.text())
    def test_name_validation_properties(self, name):
        """Test properties of macro name validation."""
        validator = MacroValidator()
        result = validator._validate_macro_name(name)
        
        # Empty or whitespace-only names should be invalid
        if not name or not name.strip():
            assert not result.is_valid
            assert result.error_code in ["INVALID_NAME_TYPE", "EMPTY_NAME"]
        
        # Names exceeding length limit should be invalid
        elif len(name) > 255:
            assert not result.is_valid
            assert result.error_code == "NAME_TOO_LONG"
        
        # Names with line breaks should be invalid
        elif '\n' in name or '\r' in name:
            assert not result.is_valid
            assert result.error_code == "INVALID_CHARACTERS"
        
        # Reserved names should be invalid
        elif name.strip() in {"Untitled Macro", "New Macro", ""}:
            assert not result.is_valid
            assert result.error_code == "RESERVED_NAME"
        
        # Otherwise should be valid
        else:
            assert result.is_valid
    
    @given(
        metadata=macro_metadata(),
        triggers=st.lists(trigger_configs(), max_size=10),
        actions=st.lists(action_configs(), min_size=1, max_size=20)
    )
    def test_structure_validation_completeness(self, metadata, triggers, actions):
        """Test that structure validation covers all important cases."""
        validation = validate_macro_structure(metadata, triggers, actions)
        
        # Should always have required fields
        assert 'is_valid' in validation
        assert 'issues' in validation
        assert 'warnings' in validation
        assert 'trigger_count' in validation
        assert 'action_count' in validation
        
        # Counts should match input
        assert validation['trigger_count'] == len(triggers)
        assert validation['action_count'] == len(actions)
        
        # If there are issues, should be invalid
        if validation['issues']:
            assert not validation['is_valid']
        
        # If no actions, should have issues
        if len(actions) == 0:
            assert not validation['is_valid']
            assert any("action" in issue.lower() for issue in validation['issues'])


class TestSerializationProperties:
    """Property-based tests for macro serialization."""
    
    @given(
        metadata=macro_metadata(),
        triggers=st.lists(trigger_configs(), max_size=5),
        actions=st.lists(action_configs(), max_size=10)
    )
    def test_serialization_round_trip_json(self, metadata, triggers, actions):
        """Test JSON serialization round-trip preserves data."""
        serializer = MacroSerializer()
        
        # Create macro data
        macro_data = {
            'metadata': asdict(metadata),
            'triggers': [asdict(t) for t in triggers],
            'actions': [asdict(a) for a in actions]
        }
        
        # Serialize and deserialize
        serialized = serializer.serialize_macro(macro_data, SerializationFormat.JSON)
        deserialized = serializer.deserialize_macro(serialized, SerializationFormat.JSON)
        
        # Should preserve essential structure
        assert 'metadata' in deserialized
        assert 'triggers' in deserialized
        assert 'actions' in deserialized
        
        # Metadata should be preserved
        assert deserialized['metadata']['name'] == metadata.name
        assert deserialized['metadata']['uuid'] == metadata.uuid
        assert deserialized['metadata']['enabled'] == metadata.enabled
    
    @given(
        macros=st.lists(
            st.builds(dict,
                metadata=macro_metadata().map(asdict),
                triggers=st.lists(trigger_configs().map(asdict), max_size=3),
                actions=st.lists(action_configs().map(asdict), max_size=5)
            ),
            min_size=1, max_size=5
        )
    )
    def test_collection_serialization_preserves_count(self, macros):
        """Test that collection serialization preserves macro count."""
        serializer = MacroSerializer()
        
        # Serialize collection
        serialized = serializer.serialize_macro_collection(macros, SerializationFormat.JSON)
        deserialized = serializer.deserialize_macro_collection(serialized, SerializationFormat.JSON)
        
        # Should preserve count
        assert len(deserialized) == len(macros)
        
        # Each macro should have required structure
        for macro in deserialized:
            assert 'metadata' in macro
            assert 'triggers' in macro
            assert 'actions' in macro


class TestComplexityCalculationProperties:
    """Property-based tests for macro complexity calculations."""
    
    @given(actions=st.lists(action_configs(), min_size=1, max_size=50))
    def test_complexity_calculation_properties(self, actions):
        """Test properties of complexity calculation."""
        complexity = calculate_macro_complexity(actions)
        
        # Should have all required fields
        assert 'total_complexity' in complexity
        assert 'total_actions' in complexity
        assert 'complexity_breakdown' in complexity
        assert 'average_complexity' in complexity
        
        # Total actions should match input
        assert complexity['total_actions'] == len(actions)
        
        # Total complexity should be positive
        assert complexity['total_complexity'] > 0
        
        # Average should be reasonable
        assert complexity['average_complexity'] > 0
        assert complexity['average_complexity'] <= 5  # Max weight per action
        
        # Breakdown should sum to total actions
        breakdown = complexity['complexity_breakdown']
        total_breakdown = sum(breakdown.values())
        assert total_breakdown == len(actions)


# Stateful testing for macro operations
class MacroOperationStateMachine(RuleBasedStateMachine):
    """Stateful testing for macro operation sequences."""
    
    # Use Bundle to track macro IDs that can be used in rules
    created_macros = Bundle('macros')
    
    def __init__(self):
        super().__init__()
        self.macros = {}  # Track created macros
        self.groups = {}  # Track created groups
        self.next_macro_id = 1
    
    @rule(target=created_macros, name=macro_names())
    def create_macro(self, name):
        """Test macro creation."""
        # Skip if name already exists
        existing_names = {m['name'] for m in self.macros.values()}
        assume(name not in existing_names)
        
        macro_id = f"macro_{self.next_macro_id}"
        self.next_macro_id += 1
        
        # Create macro metadata
        metadata = create_macro_metadata(name)
        self.macros[macro_id] = {
            'metadata': metadata,
            'name': name,
            'enabled': True
        }
        
        note(f"Created macro: {name} -> {macro_id}")
        return macro_id  # Return ID to add to bundle
    
    @rule(macro_id=created_macros)
    def modify_macro(self, macro_id):
        """Test macro modification."""
        # Skip if macro was deleted
        if macro_id not in self.macros:
            return
        
        # Modify enabled state
        current = self.macros[macro_id]
        current['enabled'] = not current['enabled']
        
        note(f"Modified macro: {macro_id} enabled={current['enabled']}")
    
    @rule(macro_id=created_macros)
    def delete_macro(self, macro_id):
        """Test macro deletion."""
        # Skip if already deleted
        if macro_id not in self.macros:
            return
        
        del self.macros[macro_id]
        note(f"Deleted macro: {macro_id}")
    
    @invariant()
    def macro_names_unique(self):
        """Invariant: All macro names should be unique."""
        names = [macro['name'] for macro in self.macros.values()]
        assert len(names) == len(set(names)), "Duplicate macro names found"
    
    @invariant()
    def macro_metadata_valid(self):
        """Invariant: All macro metadata should be valid."""
        for macro_id, macro in self.macros.items():
            assert 'metadata' in macro
            assert 'name' in macro
            assert macro['name'] == macro['metadata'].name


# Configure Hypothesis settings for thorough testing
TestMacroStateMachine = MacroOperationStateMachine.TestCase
TestMacroStateMachine.settings = settings(
    max_examples=50,
    stateful_step_count=20,
    suppress_health_check=[],
    deadline=5000  # 5 second deadline
)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
