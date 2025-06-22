# src/types/domain_types.py (Target: <250 lines)
"""
Core domain types for the Keyboard Maestro MCP Server.

This module defines the primary domain types that model the core business
entities and their relationships using type-driven development principles.
"""

from typing import Optional, FrozenSet, Dict, Any, Union, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .identifiers import (
    MacroUUID, MacroName, GroupUUID, VariableName, 
    ExecutionID, MacroIdentifier, VariableIdentifier
)
from .values import (
    MacroExecutionTimeout, VariableValue, ScreenCoordinates,
    ConfidenceScore, FilePath
)
from .enumerations import (
    MacroState, VariableScope, TriggerType, ActionType,
    ExecutionStatus, ErrorType, ExecutionMethod,
    ConnectionStatus, PoolStatus, ResourceType, AlertLevel
)


# Core Domain Entity Types
@dataclass(frozen=True)
class MacroMetadata:
    """Immutable macro metadata with core properties."""
    uuid: MacroUUID
    name: MacroName
    group_id: Optional[GroupUUID]
    state: MacroState
    created_at: datetime
    modified_at: datetime
    notes: Optional[str] = None
    
    def is_executable(self) -> bool:
        """Check if macro can be executed."""
        return self.state.can_execute()
    
    def is_modifiable(self) -> bool:
        """Check if macro can be modified."""
        return self.state.can_modify()


@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Dict[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        if not self.parameters:
            raise ValueError("Trigger parameters cannot be empty")
        
        # Validate required parameters based on trigger type
        required_params = self._get_required_parameters()
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def _get_required_parameters(self) -> FrozenSet[str]:
        """Get required parameters for trigger type."""
        param_map = {
            TriggerType.HOTKEY: frozenset(['key', 'modifiers']),
            TriggerType.APPLICATION: frozenset(['application']),
            TriggerType.TIME: frozenset(['schedule']),
            TriggerType.FILE_FOLDER: frozenset(['path', 'event']),
            TriggerType.SYSTEM: frozenset(['event_type']),
            TriggerType.DEVICE: frozenset(['device_type']),
            TriggerType.NETWORK: frozenset(['endpoint']),
            TriggerType.CLIPBOARD: frozenset(['content_type'])
        }
        return param_map.get(self.trigger_type, frozenset())
    
    def _make_hashable(self, obj):
        """Convert potentially unhashable objects to hashable ones."""
        if isinstance(obj, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in obj.items()))
        elif isinstance(obj, list):
            return tuple(self._make_hashable(item) for item in obj)
        elif isinstance(obj, set):
            return frozenset(self._make_hashable(item) for item in obj)
        else:
            return obj
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((
            self.trigger_type, 
            self._make_hashable(self.parameters), 
            self.enabled
        ))


@dataclass(frozen=True)
class ActionConfiguration:
    """Immutable action configuration."""
    action_type: ActionType
    parameters: Dict[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate action configuration."""
        if not self.parameters:
            raise ValueError("Action parameters cannot be empty")
    
    def _make_hashable(self, obj):
        """Convert potentially unhashable objects to hashable ones."""
        if isinstance(obj, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in obj.items()))
        elif isinstance(obj, list):
            return tuple(self._make_hashable(item) for item in obj)
        elif isinstance(obj, set):
            return frozenset(self._make_hashable(item) for item in obj)
        else:
            return obj
    
    def __hash__(self) -> int:
        """Make action configuration hashable for use in sets."""
        return hash((
            self.action_type,
            self._make_hashable(self.parameters),
            self.enabled
        ))


@dataclass(frozen=True)
class MacroDefinition:
    """Complete immutable macro definition."""
    metadata: MacroMetadata
    triggers: FrozenSet[TriggerConfiguration]
    actions: FrozenSet[ActionConfiguration]
    
    def __post_init__(self):
        """Validate macro definition."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    @property
    def trigger_count(self) -> int:
        """Get number of configured triggers."""
        return len(self.triggers)
    
    @property
    def action_count(self) -> int:
        """Get number of configured actions."""
        return len(self.actions)
    
    def has_trigger_type(self, trigger_type: TriggerType) -> bool:
        """Check if macro has trigger of specified type."""
        return any(trigger.trigger_type == trigger_type for trigger in self.triggers)
    
    def has_action_type(self, action_type: ActionType) -> bool:
        """Check if macro has action of specified type."""
        return any(action.action_type == action_type for action in self.actions)


@dataclass(frozen=True)
class VariableDefinition:
    """Immutable variable definition with metadata."""
    identifier: VariableIdentifier
    value: Optional[VariableValue]
    created_at: datetime
    modified_at: datetime
    
    @property
    def exists(self) -> bool:
        """Check if variable has a value."""
        return self.value is not None
    
    def is_password_variable(self) -> bool:
        """Check if variable is password type."""
        return self.identifier.is_password()


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context for operations."""
    execution_id: ExecutionID
    macro_id: MacroUUID
    method: ExecutionMethod
    trigger_value: Optional[str]
    timeout: MacroExecutionTimeout
    start_time: datetime
    status: ExecutionStatus
    
    def is_terminal(self) -> bool:
        """Check if execution is in terminal state."""
        return self.status.is_terminal_state()
    
    def is_active(self) -> bool:
        """Check if execution is actively running."""
        return self.status.is_active_state()
    
    def can_be_cancelled(self) -> bool:
        """Check if execution can be cancelled."""
        return self.status.can_be_cancelled()


@dataclass(frozen=True)
class OperationError:
    """Comprehensive error information."""
    error_type: ErrorType
    message: str
    details: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    error_code: Optional[str] = None
    
    def is_recoverable(self) -> bool:
        """Check if error is potentially recoverable."""
        return self.error_type.is_recoverable()
    
    def requires_user_action(self) -> bool:
        """Check if error requires user intervention."""
        return self.error_type.requires_user_action()


@dataclass(frozen=True)
class ContextInfo:
    """MCP context information for session tracking."""
    context_id: str
    session_id: str
    created_at: float
    last_activity: float = 0.0
    current_progress: int = 0
    total_progress: int = 0
    request_count: int = 0
    
    def __post_init__(self):
        """Initialize mutable fields if not set."""
        if self.last_activity == 0.0:
            object.__setattr__(self, 'last_activity', self.created_at)
    
    @property
    def age_seconds(self) -> float:
        """Get context age in seconds."""
        import time
        return time.time() - self.created_at
    
    @property
    def idle_seconds(self) -> float:
        """Get idle time in seconds."""
        import time
        return time.time() - self.last_activity


@dataclass(frozen=True)
class OCRTextExtraction:
    """Individual OCR text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenCoordinates  # Simplified for now
    language: str
    
    def __post_init__(self):
        """Validate extraction data."""
        if not self.text:
            raise ValueError("Extracted text cannot be empty")
        if not self.language:
            raise ValueError("Language must be specified")
    
    def is_high_confidence(self) -> bool:
        """Check if extraction has high confidence."""
        return self.confidence >= 0.8
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))


@dataclass(frozen=True)
class MacroCreationData:
    """Data structure for creating new macros."""
    name: str
    group_uuid: Optional[str] = None
    enabled: bool = True
    color: Optional[str] = None
    notes: Optional[str] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        """Validate creation data."""
        if not self.name or not self.name.strip():
            raise ValueError("Macro name cannot be empty")


@dataclass(frozen=True)
class MacroModificationData:
    """Data structure for modifying existing macros."""
    name: Optional[str] = None
    group_uuid: Optional[str] = None
    enabled: Optional[bool] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    
    def has_changes(self) -> bool:
        """Check if any modification data is provided."""
        return any([
            self.name is not None,
            self.group_uuid is not None,
            self.enabled is not None,
            self.color is not None,
            self.notes is not None,
            self.triggers is not None,
            self.actions is not None
        ])


@dataclass(frozen=True)
class PerformanceThreshold:
    """Performance monitoring thresholds configuration."""
    resource_type: ResourceType
    warning_threshold: float
    critical_threshold: float
    alert_level: AlertLevel = AlertLevel.WARNING
    
    def __post_init__(self):
        """Validate threshold configuration."""
        if self.critical_threshold <= self.warning_threshold:
            raise ValueError("Critical threshold must be greater than warning threshold")
        if self.warning_threshold < 0 or self.critical_threshold > 100:
            raise ValueError("Thresholds must be between 0 and 100")
    
    def is_exceeded(self, current_value: float) -> bool:
        """Check if current value exceeds thresholds."""
        return current_value >= self.warning_threshold
    
    def is_critical(self, current_value: float) -> bool:
        """Check if current value exceeds critical threshold."""
        return current_value >= self.critical_threshold


@dataclass(frozen=True)
class MacroExecutionContext:
    """Context for macro execution with validation."""
    identifier: Union[MacroUUID, MacroName]
    trigger_value: Optional[str] = None
    method: ExecutionMethod = ExecutionMethod.APPLESCRIPT
    timeout: int = 30
    context_variables: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        """Validate execution context parameters."""
        if self.timeout <= 0 or self.timeout > 300:
            raise ValueError("Timeout must be between 1 and 300 seconds")
        if isinstance(self.identifier, str) and len(self.identifier.strip()) == 0:
            raise ValueError("Macro identifier cannot be empty")


# Factory Functions for Safe Construction
def create_macro_metadata(
    uuid: MacroUUID,
    name: MacroName,
    group_id: Optional[GroupUUID] = None,
    state: MacroState = MacroState.DISABLED,
    notes: Optional[str] = None
) -> MacroMetadata:
    """Create macro metadata with safe defaults.
    
    Args:
        uuid: Macro UUID
        name: Macro name
        group_id: Optional group UUID
        state: Initial state
        notes: Optional notes
        
    Returns:
        MacroMetadata: Validated metadata object
    """
    now = datetime.now()
    return MacroMetadata(
        uuid=uuid,
        name=name,
        group_id=group_id,
        state=state,
        created_at=now,
        modified_at=now,
        notes=notes
    )


def create_execution_context(
    execution_id: ExecutionID,
    macro_id: MacroUUID,
    method: ExecutionMethod,
    timeout: MacroExecutionTimeout,
    trigger_value: Optional[str] = None
) -> ExecutionContext:
    """Create execution context with safe defaults.
    
    Args:
        execution_id: Unique execution identifier
        macro_id: Target macro UUID
        method: Execution method
        timeout: Execution timeout
        trigger_value: Optional trigger value
        
    Returns:
        ExecutionContext: Validated execution context
    """
    return ExecutionContext(
        execution_id=execution_id,
        macro_id=macro_id,
        method=method,
        trigger_value=trigger_value,
        timeout=timeout,
        start_time=datetime.now(),
        status=ExecutionStatus.PENDING
    )


# Additional Enums needed by other modules
class SessionStatus(Enum):
    """Status of MCP session."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"


class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = "json"
    XML = "xml"
    PLIST = "plist"
    KMMACROS = "kmmacros"
    KMLIBRARY = "kmlibrary"


class ToolStatus(Enum):
    """Status of a tool in the MCP server."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class ServiceStatus:
    """Status of a communication service."""
    available: bool
    service_name: str
    last_check: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class MacroExecutionResult:
    """Result of macro execution operation."""
    success: bool
    execution_id: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate execution result."""
        if self.success and self.error_message:
            raise ValueError("Successful result cannot have error message")
        if not self.success and not self.error_message:
            raise ValueError("Failed result must have error message")
