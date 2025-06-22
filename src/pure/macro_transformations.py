"""
Pure macro transformation functions for safe data manipulation.

This module provides pure functions for transforming macro data structures,
enabling safe manipulation without side effects.
"""

from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass, asdict
from copy import deepcopy
import json
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

from src.types.domain_types import (
    MacroIdentifier, MacroUUID, MacroName, GroupUUID,
    TriggerType, ActionType, MacroCreationData
)


@dataclass(frozen=True)
class MacroMetadata:
    """Immutable macro metadata structure."""
    uuid: str
    name: str
    group_uuid: str
    enabled: bool
    color: Optional[str] = None
    notes: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None


@dataclass(frozen=True)
class TriggerConfig:
    """Immutable trigger configuration."""
    trigger_type: str
    parameters: Dict[str, Any]
    enabled: bool = True


@dataclass(frozen=True)
class ActionConfig:
    """Immutable action configuration."""
    action_type: str
    parameters: Dict[str, Any]
    enabled: bool = True
    timeout: Optional[int] = None


def normalize_macro_identifier(identifier: MacroIdentifier) -> str:
    """
    Normalize macro identifier to consistent format.
    
    Pure function that converts various identifier formats to string.
    """
    if isinstance(identifier, uuid.UUID):
        return str(identifier).upper()
    elif isinstance(identifier, str):
        # Try to parse as UUID and normalize
        try:
            parsed_uuid = uuid.UUID(identifier)
            return str(parsed_uuid).upper()
        except ValueError:
            # Not a UUID, return as name (normalized)
            return identifier.strip()
    else:
        raise ValueError(f"Invalid macro identifier type: {type(identifier)}")


def create_macro_metadata(
    name: str, 
    group_uuid: Optional[str] = None,
    **kwargs
) -> MacroMetadata:
    """
    Create immutable macro metadata with validation.
    
    Pure function that generates metadata with consistent defaults.
    """
    if not name or not isinstance(name, str):
        raise ValueError("Macro name must be a non-empty string")
    
    current_time = datetime.now().isoformat()
    
    return MacroMetadata(
        uuid=str(uuid.uuid4()).upper(),
        name=name.strip(),
        group_uuid=group_uuid or "DEFAULT_GROUP",
        enabled=kwargs.get('enabled', True),
        color=kwargs.get('color'),
        notes=kwargs.get('notes'),
        creation_date=kwargs.get('creation_date', current_time),
        modification_date=kwargs.get('modification_date', current_time)
    )


def transform_trigger_data(trigger_data: Dict[str, Any]) -> TriggerConfig:
    """
    Transform raw trigger data to validated configuration.
    
    Pure function that normalizes trigger parameters.
    """
    if not isinstance(trigger_data, dict):
        raise ValueError("Trigger data must be a dictionary")
    
    trigger_type = trigger_data.get('type')
    if not trigger_type:
        raise ValueError("Trigger type is required")
    
    # Extract and normalize parameters
    parameters = deepcopy(trigger_data)
    parameters.pop('type', None)  # Remove type from parameters
    parameters.pop('enabled', None)  # Remove enabled from parameters
    
    return TriggerConfig(
        trigger_type=trigger_type,
        parameters=parameters,
        enabled=trigger_data.get('enabled', True)
    )


def transform_action_data(action_data: Dict[str, Any]) -> ActionConfig:
    """
    Transform raw action data to validated configuration.
    
    Pure function that normalizes action parameters.
    """
    if not isinstance(action_data, dict):
        raise ValueError("Action data must be a dictionary")
    
    action_type = action_data.get('type')
    if not action_type:
        raise ValueError("Action type is required")
    
    # Extract and normalize parameters
    parameters = deepcopy(action_data)
    parameters.pop('type', None)
    parameters.pop('enabled', None)
    parameters.pop('timeout', None)
    
    return ActionConfig(
        action_type=action_type,
        parameters=parameters,
        enabled=action_data.get('enabled', True),
        timeout=action_data.get('timeout')
    )


def merge_macro_updates(
    original_metadata: MacroMetadata,
    updates: Dict[str, Any]
) -> MacroMetadata:
    """
    Merge updates into macro metadata immutably.
    
    Pure function that creates new metadata with updates applied.
    """
    # Convert to dict for manipulation
    metadata_dict = asdict(original_metadata)
    
    # Apply allowed updates
    allowed_fields = {'name', 'enabled', 'color', 'notes', 'group_uuid'}
    for field, value in updates.items():
        if field in allowed_fields and value is not None:
            metadata_dict[field] = value
    
    # Update modification date
    metadata_dict['modification_date'] = datetime.now().isoformat()
    
    return MacroMetadata(**metadata_dict)


def extract_macro_dependencies(
    triggers: List[TriggerConfig],
    actions: List[ActionConfig]
) -> Set[str]:
    """
    Extract macro dependencies from triggers and actions.
    
    Pure function that identifies referenced resources.
    """
    dependencies = set()
    
    # Extract from triggers
    for trigger in triggers:
        # File/folder triggers depend on paths
        if trigger.trigger_type in ['file_added', 'file_removed', 'file_modified']:
            path = trigger.parameters.get('path')
            if path:
                dependencies.add(f"path:{path}")
        
        # Application triggers depend on apps
        elif trigger.trigger_type in ['app_activate', 'app_deactivate', 'app_launch']:
            app = trigger.parameters.get('application')
            if app:
                dependencies.add(f"app:{app}")
    
    # Extract from actions
    for action in actions:
        # Variable actions depend on variables
        if action.action_type in ['set_variable', 'get_variable']:
            var_name = action.parameters.get('variable_name')
            if var_name:
                dependencies.add(f"variable:{var_name}")
        
        # File actions depend on paths
        elif action.action_type in ['copy_file', 'move_file', 'delete_file']:
            for path_key in ['source_path', 'dest_path', 'file_path']:
                path = action.parameters.get(path_key)
                if path:
                    dependencies.add(f"path:{path}")
        
        # Execute macro actions depend on other macros
        elif action.action_type == 'execute_macro':
            macro_id = action.parameters.get('macro_identifier')
            if macro_id:
                dependencies.add(f"macro:{macro_id}")
    
    return dependencies


def validate_macro_structure(
    metadata: MacroMetadata,
    triggers: List[TriggerConfig],
    actions: List[ActionConfig]
) -> Dict[str, Any]:
    """
    Validate complete macro structure for consistency.
    
    Pure function that returns validation results.
    """
    issues = []
    warnings = []
    
    # Check metadata
    if not metadata.name:
        issues.append("Macro name cannot be empty")
    
    if len(metadata.name) > 255:
        issues.append("Macro name exceeds 255 characters")
    
    # Check triggers
    if not triggers:
        warnings.append("Macro has no triggers - will not activate automatically")
    
    trigger_types = [t.trigger_type for t in triggers]
    if len(set(trigger_types)) != len(trigger_types):
        warnings.append("Macro has duplicate trigger types")
    
    # Check actions
    if not actions:
        issues.append("Macro must have at least one action")
    
    # Check for common problematic patterns
    action_types = [a.action_type for a in actions]
    if 'pause' in action_types and len(actions) == 1:
        warnings.append("Macro only contains pause action")
    
    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'trigger_count': len(triggers),
        'action_count': len(actions)
    }


def convert_to_km_xml(
    metadata: MacroMetadata,
    triggers: List[TriggerConfig],
    actions: List[ActionConfig]
) -> str:
    """
    Convert macro structure to Keyboard Maestro XML format.
    
    Pure function that generates XML representation.
    """
    # Create root macro element
    macro_elem = ET.Element('macro')
    macro_elem.set('name', metadata.name)
    macro_elem.set('uuid', metadata.uuid)
    macro_elem.set('enabled', str(metadata.enabled).lower())
    
    if metadata.color:
        macro_elem.set('color', metadata.color)
    
    # Add triggers
    if triggers:
        triggers_elem = ET.SubElement(macro_elem, 'triggers')
        for trigger in triggers:
            trigger_elem = ET.SubElement(triggers_elem, 'trigger')
            trigger_elem.set('type', trigger.trigger_type)
            trigger_elem.set('enabled', str(trigger.enabled).lower())
            
            # Add trigger parameters
            for key, value in trigger.parameters.items():
                param_elem = ET.SubElement(trigger_elem, key)
                param_elem.text = str(value)
    
    # Add actions
    if actions:
        actions_elem = ET.SubElement(macro_elem, 'actions')
        for action in actions:
            action_elem = ET.SubElement(actions_elem, 'action')
            action_elem.set('type', action.action_type)
            action_elem.set('enabled', str(action.enabled).lower())
            
            if action.timeout:
                action_elem.set('timeout', str(action.timeout))
            
            # Add action parameters
            for key, value in action.parameters.items():
                param_elem = ET.SubElement(action_elem, key)
                param_elem.text = str(value)
    
    return ET.tostring(macro_elem, encoding='unicode')


def parse_km_xml(xml_string: str) -> Dict[str, Any]:
    """
    Parse Keyboard Maestro XML to structured data.
    
    Pure function that extracts macro structure from XML.
    """
    try:
        root = ET.fromstring(xml_string)
        
        # Extract metadata
        metadata = {
            'name': root.get('name', ''),
            'uuid': root.get('uuid', ''),
            'enabled': root.get('enabled', 'true').lower() == 'true',
            'color': root.get('color')
        }
        
        # Extract triggers
        triggers = []
        triggers_elem = root.find('triggers')
        if triggers_elem is not None:
            for trigger_elem in triggers_elem.findall('trigger'):
                trigger_data = {
                    'type': trigger_elem.get('type'),
                    'enabled': trigger_elem.get('enabled', 'true').lower() == 'true'
                }
                
                # Extract parameters
                for param_elem in trigger_elem:
                    trigger_data[param_elem.tag] = param_elem.text or ''
                
                triggers.append(trigger_data)
        
        # Extract actions
        actions = []
        actions_elem = root.find('actions')
        if actions_elem is not None:
            for action_elem in actions_elem.findall('action'):
                action_data = {
                    'type': action_elem.get('type'),
                    'enabled': action_elem.get('enabled', 'true').lower() == 'true'
                }
                
                timeout = action_elem.get('timeout')
                if timeout:
                    action_data['timeout'] = int(timeout)
                
                # Extract parameters
                for param_elem in action_elem:
                    action_data[param_elem.tag] = param_elem.text or ''
                
                actions.append(action_data)
        
        return {
            'metadata': metadata,
            'triggers': triggers,
            'actions': actions
        }
        
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")


def calculate_macro_complexity(actions: List[ActionConfig]) -> Dict[str, int]:
    """
    Calculate macro complexity metrics.
    
    Pure function that analyzes macro structure.
    """
    complexity_weights = {
        'simple': 1,      # Basic actions like pause, beep
        'moderate': 2,    # Variable operations, file actions
        'complex': 3,     # Conditional logic, loops
        'advanced': 5     # AppleScript, shell scripts
    }
    
    action_complexity = {
        'pause': 'simple',
        'beep': 'simple',
        'set_variable': 'moderate',
        'copy_file': 'moderate',
        'if_then': 'complex',
        'for_each': 'complex',
        'execute_applescript': 'advanced',
        'execute_shell': 'advanced'
    }
    
    total_complexity = 0
    action_counts = {'simple': 0, 'moderate': 0, 'complex': 0, 'advanced': 0}
    
    for action in actions:
        complexity_level = action_complexity.get(action.action_type, 'moderate')
        weight = complexity_weights[complexity_level]
        
        total_complexity += weight
        action_counts[complexity_level] += 1
    
    return {
        'total_complexity': total_complexity,
        'total_actions': len(actions),
        'complexity_breakdown': action_counts,
        'average_complexity': total_complexity / len(actions) if actions else 0
    }
