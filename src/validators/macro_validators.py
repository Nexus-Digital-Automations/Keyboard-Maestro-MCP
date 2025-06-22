"""
Macro-specific validation with comprehensive constraint checking.

This module provides specialized validation for macro operations,
enforcing Keyboard Maestro constraints and business rules.
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass
import re
import uuid
import logging

from src.types.domain_types import (
    MacroIdentifier, MacroName, GroupUUID, MacroCreationData,
    MacroModificationData, TriggerType, ActionType
)
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_macro_identifier
from src.core.km_interface import KMInterface

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operations."""
    is_valid: bool
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    field_errors: Optional[Dict[str, str]] = None


class MacroValidator:
    """Comprehensive macro validation with contract enforcement."""
    
    # Keyboard Maestro naming constraints
    MAX_MACRO_NAME_LENGTH = 255
    MAX_GROUP_NAME_LENGTH = 255
    RESERVED_NAMES = {"Untitled Macro", "New Macro", ""}
    
    # Action and trigger limits
    MAX_ACTIONS_PER_MACRO = 1000
    MAX_TRIGGERS_PER_MACRO = 10
    
    def __init__(self, km_interface: Optional[KMInterface] = None):
        """Initialize validator with optional KM interface for live validation."""
        self.km_interface = km_interface
    
    @requires(lambda self, data: data is not None)
    @ensures(lambda result: isinstance(result, ValidationResult))
    async def validate_creation_data(self, data: MacroCreationData) -> ValidationResult:
        """
        Validate macro creation data comprehensively.
        
        Checks name format, uniqueness, group existence, trigger/action validity.
        """
        try:
            # Basic structure validation
            basic_result = self._validate_basic_structure(data)
            if not basic_result.is_valid:
                return basic_result
            
            # Name validation
            name_result = self._validate_macro_name(data.name)
            if not name_result.is_valid:
                return name_result
            
            # Group validation
            if data.group_uuid:
                group_result = await self._validate_group_exists(data.group_uuid)
                if not group_result.is_valid:
                    return group_result
            
            # Name uniqueness validation
            if self.km_interface:
                uniqueness_result = await self._validate_name_uniqueness(
                    data.name, data.group_uuid
                )
                if not uniqueness_result.is_valid:
                    return uniqueness_result
            
            # Triggers validation
            if hasattr(data, 'triggers') and data.triggers:
                triggers_result = self._validate_triggers(data.triggers)
                if not triggers_result.is_valid:
                    return triggers_result
            
            # Actions validation
            if hasattr(data, 'actions') and data.actions:
                actions_result = self._validate_actions(data.actions)
                if not actions_result.is_valid:
                    return actions_result
            
            logger.debug(f"Validation passed for macro creation: {data.name}")
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation failed: {str(e)}",
                error_code="VALIDATION_ERROR"
            )
    
    @requires(lambda self, macro_id, data: is_valid_macro_identifier(macro_id) and data is not None)
    @ensures(lambda result: isinstance(result, ValidationResult))
    async def validate_modification_data(
        self, 
        macro_id: MacroIdentifier, 
        data: MacroModificationData
    ) -> ValidationResult:
        """
        Validate macro modification data.
        
        Ensures modifications maintain system constraints and uniqueness.
        """
        try:
            # Name modification validation
            if hasattr(data, 'name') and data.name is not None:
                name_result = self._validate_macro_name(data.name)
                if not name_result.is_valid:
                    return name_result
                
                # Check uniqueness if name is changing
                if self.km_interface:
                    current_info = await self.km_interface.get_macro_properties(macro_id)
                    if current_info and current_info.get('name') != data.name:
                        group_uuid = data.group_uuid or current_info.get('group_uuid')
                        uniqueness_result = await self._validate_name_uniqueness(
                            data.name, group_uuid, exclude_macro=macro_id
                        )
                        if not uniqueness_result.is_valid:
                            return uniqueness_result
            
            # Group change validation
            if hasattr(data, 'group_uuid') and data.group_uuid is not None:
                group_result = await self._validate_group_exists(data.group_uuid)
                if not group_result.is_valid:
                    return group_result
            
            # Color validation
            if hasattr(data, 'color') and data.color is not None:
                color_result = self._validate_color(data.color)
                if not color_result.is_valid:
                    return color_result
            
            logger.debug(f"Validation passed for macro modification: {macro_id}")
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Modification validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Modification validation failed: {str(e)}",
                error_code="MODIFICATION_VALIDATION_ERROR"
            )
    
    def _validate_basic_structure(self, data: MacroCreationData) -> ValidationResult:
        """Validate basic data structure requirements."""
        if not hasattr(data, 'name'):
            return ValidationResult(
                is_valid=False,
                error_message="Macro name is required",
                error_code="MISSING_NAME"
            )
        
        return ValidationResult(is_valid=True)
    
    def _validate_macro_name(self, name: MacroName) -> ValidationResult:
        """Validate macro name against Keyboard Maestro constraints."""
        if not name or not isinstance(name, str):
            return ValidationResult(
                is_valid=False,
                error_message="Macro name must be a non-empty string",
                error_code="INVALID_NAME_TYPE"
            )
        
        if len(name.strip()) == 0:
            return ValidationResult(
                is_valid=False,
                error_message="Macro name cannot be empty or whitespace only",
                error_code="EMPTY_NAME"
            )
        
        if len(name) > self.MAX_MACRO_NAME_LENGTH:
            return ValidationResult(
                is_valid=False,
                error_message=f"Macro name exceeds maximum length of {self.MAX_MACRO_NAME_LENGTH}",
                error_code="NAME_TOO_LONG"
            )
        
        if name.strip() in self.RESERVED_NAMES:
            return ValidationResult(
                is_valid=False,
                error_message=f"'{name}' is a reserved name",
                error_code="RESERVED_NAME"
            )
        
        # Check for invalid characters
        if '\n' in name or '\r' in name:
            return ValidationResult(
                is_valid=False,
                error_message="Macro name cannot contain line breaks",
                error_code="INVALID_CHARACTERS"
            )
        
        return ValidationResult(is_valid=True)
    
    async def _validate_group_exists(self, group_uuid: GroupUUID) -> ValidationResult:
        """Validate that the specified group exists."""
        if not self.km_interface:
            # Skip validation if no interface available
            return ValidationResult(is_valid=True)
        
        try:
            exists = await self.km_interface.group_exists(group_uuid)
            if not exists:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Macro group does not exist: {group_uuid}",
                    error_code="GROUP_NOT_FOUND"
                )
            
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Error checking group existence: {e}")
            return ValidationResult(
                is_valid=False,
                error_message="Could not verify group existence",
                error_code="GROUP_VALIDATION_ERROR"
            )
    
    async def _validate_name_uniqueness(
        self, 
        name: MacroName, 
        group_uuid: Optional[GroupUUID],
        exclude_macro: Optional[MacroIdentifier] = None
    ) -> ValidationResult:
        """Validate macro name uniqueness within group."""
        if not self.km_interface:
            return ValidationResult(is_valid=True)
        
        try:
            existing_macros = await self.km_interface.list_macros(group_uuid)
            
            for macro in existing_macros:
                if macro.get('name') == name:
                    # Exclude the current macro if modifying
                    if exclude_macro and (
                        macro.get('uuid') == exclude_macro or 
                        macro.get('name') == exclude_macro
                    ):
                        continue
                    
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Macro name '{name}' already exists in this group",
                        error_code="DUPLICATE_NAME"
                    )
            
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            logger.error(f"Error checking name uniqueness: {e}")
            return ValidationResult(
                is_valid=False,
                error_message="Could not verify name uniqueness",
                error_code="UNIQUENESS_VALIDATION_ERROR"
            )
    
    def _validate_triggers(self, triggers: List[Dict[str, Any]]) -> ValidationResult:
        """Validate trigger configurations."""
        if len(triggers) > self.MAX_TRIGGERS_PER_MACRO:
            return ValidationResult(
                is_valid=False,
                error_message=f"Too many triggers (max {self.MAX_TRIGGERS_PER_MACRO})",
                error_code="TOO_MANY_TRIGGERS"
            )
        
        for i, trigger in enumerate(triggers):
            if not isinstance(trigger, dict):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Trigger {i} must be a dictionary",
                    error_code="INVALID_TRIGGER_FORMAT"
                )
            
            if 'type' not in trigger:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Trigger {i} missing required 'type' field",
                    error_code="MISSING_TRIGGER_TYPE"
                )
        
        return ValidationResult(is_valid=True)
    
    def _validate_actions(self, actions: List[Dict[str, Any]]) -> ValidationResult:
        """Validate action configurations."""
        if len(actions) > self.MAX_ACTIONS_PER_MACRO:
            return ValidationResult(
                is_valid=False,
                error_message=f"Too many actions (max {self.MAX_ACTIONS_PER_MACRO})",
                error_code="TOO_MANY_ACTIONS"
            )
        
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Action {i} must be a dictionary",
                    error_code="INVALID_ACTION_FORMAT"
                )
            
            if 'type' not in action:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Action {i} missing required 'type' field",
                    error_code="MISSING_ACTION_TYPE"
                )
        
        return ValidationResult(is_valid=True)
    
    def _validate_color(self, color: str) -> ValidationResult:
        """Validate color specification."""
        # Keyboard Maestro supports named colors and hex values
        named_colors = {
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 
            'pink', 'brown', 'gray', 'black', 'white'
        }
        
        if color.lower() in named_colors:
            return ValidationResult(is_valid=True)
        
        # Check hex color format
        hex_pattern = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')
        if hex_pattern.match(color):
            return ValidationResult(is_valid=True)
        
        return ValidationResult(
            is_valid=False,
            error_message=f"Invalid color format: {color}",
            error_code="INVALID_COLOR"
        )
