# Type System Architecture: Keyboard Maestro MCP Server

## Type-Driven Development Framework

This document defines the comprehensive type system for the Keyboard Maestro MCP Server, implementing type-driven development principles with branded types, domain modeling, state machines, and functional programming patterns. The type system prevents common errors, enforces business rules, and provides clear contracts for all domain operations.

## Type System Principles

The Keyboard Maestro MCP Server implements a comprehensive type system based on type-driven development principles, providing compile-time safety, clear domain modeling, and robust error handling throughout the system.

### **1. Branded Types for Domain Safety**

- **Prevent Primitive Obsession**: Use distinct types for different domain concepts
- **Compile-Time Safety**: Catch domain violations during development  
- **Self-Documenting Code**: Types express business intent clearly
- **Refactoring Safety**: Type system guides safe code evolution

**Implementation Status**: ✅ **FULLY IMPLEMENTED**
- 10+ branded identifier types (MacroUUID, MacroName, VariableName, etc.)
- 8+ branded value types (ScreenCoordinate, ConfidenceScore, ExecutionTimeout, etc.)
- Comprehensive validation functions for all branded types
- Type-safe factory functions with error handling

### **2. State Machine Modeling**

- **Explicit State Management**: All entity states explicitly modeled
- **Valid Transitions**: Type system enforces legal state changes
- **Invariant Preservation**: States maintain required business invariants
- **Concurrent Safety**: State transitions safe in async contexts

**Implementation Status**: ✅ **FULLY IMPLEMENTED**
- MacroState enum with transition validation
- ExecutionStatus enum with terminal state detection
- ServerStatus and ComponentStatus for monitoring
- State transition methods on enum types

### **3. Functional Type Patterns**

- **Immutability by Default**: Data structures prefer immutable representations
- **Composition Over Inheritance**: Type building through composition
- **Validation Functions**: Explicit validation with error reporting
- **Type Safety**: Strong typing prevents common programming errors

**Implementation Status**: ✅ **FULLY IMPLEMENTED**
- All domain types use @dataclass(frozen=True)
- Composite identifier types for flexible lookups
- Comprehensive validation with detailed error messages
- Type-safe factory functions for all complex types

## Core Domain Type Hierarchy

### **1. Implemented Identifier Types**

#### **1.1 Branded Identifier Types** ✅ **IMPLEMENTED**

**Current Implementation** (`src/types/identifiers.py`):

```python
# Complete set of branded identifier types
MacroUUID = NewType('MacroUUID', UUID)
MacroName = NewType('MacroName', str)
GroupUUID = NewType('GroupUUID', UUID)
GroupName = NewType('GroupName', str)
VariableName = NewType('VariableName', str)
TriggerID = NewType('TriggerID', str)
ActionID = NewType('ActionID', str)
ApplicationBundleID = NewType('ApplicationBundleID', str)
ExecutionID = NewType('ExecutionID', str)
PluginID = NewType('PluginID', str)
```

**Type Safety Validation Examples**:

```python
# Macro UUID validation with comprehensive error handling
def create_macro_uuid(uuid_str: str) -> MacroUUID:
    """Create validated macro UUID with error handling."""
    try:
        return MacroUUID(UUID(uuid_str))
    except ValueError as e:
        raise ValueError(f"Invalid macro UUID format: {uuid_str}") from e

# Macro name validation following Keyboard Maestro conventions
def create_macro_name(name: str) -> MacroName:
    """Create validated macro name following Keyboard Maestro conventions."""
    if not name or len(name) > 255:
        raise ValueError("Macro name must be 1-255 characters")
    if not re.match(r'^[a-zA-Z0-9_\s\-\.]+

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type Conversion Utilities ✅ **IMPLEMENTED**

### **Type Conversion Functions**

The type system includes comprehensive conversion utilities for safe type transformations:

```python
# Current Implementation: Helper functions for type conversions
def is_valid_macro_identifier(identifier: Union[str, UUID]) -> bool:
    """Check if value can be used as macro identifier."""
    if isinstance(identifier, str):
        try:
            create_macro_name(identifier)
            return True
        except ValueError:
            return False
    elif isinstance(identifier, UUID):
        return True
    return False

def is_valid_variable_name_format(name: str) -> bool:
    """Check if name follows variable naming conventions."""
    try:
        create_variable_name(name)
        return True
    except ValueError:
        return False

# Color conversion utilities
class ColorRGB:
    def to_hex(self) -> str:
        """Convert to hexadecimal representation."""
        return f"#{self.red:02X}{self.green:02X}{self.blue:02X}"
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'ColorRGB':
        """Create color from hex string."""
        # Implementation with validation

# Coordinate transformation utilities
class ScreenCoordinates:
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(max(0, self.x + dx)),
            create_screen_coordinate(max(0, self.y + dy))
        )
    
    def distance_to(self, other: 'ScreenCoordinates') -> float:
        """Calculate distance to another coordinate."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
```

## Type-Driven Development Patterns ✅ **IMPLEMENTED**

### **1. Factory Pattern with Type Safety**

**Pattern**: All complex types use factory functions for safe construction

```python
# Current Implementation Examples:
def create_macro_metadata(
    uuid: MacroUUID,
    name: MacroName,
    group_id: Optional[GroupUUID] = None,
    state: MacroState = MacroState.DISABLED,
    notes: Optional[str] = None
) -> MacroMetadata:
    """Factory function with type-safe defaults."""
    now = datetime.now()
    return MacroMetadata(
        uuid=uuid, name=name, group_id=group_id,
        state=state, created_at=now, modified_at=now, notes=notes
    )

def create_execution_context(
    execution_id: ExecutionID,
    macro_id: MacroUUID,
    method: ExecutionMethod,
    timeout: MacroExecutionTimeout,
    trigger_value: Optional[str] = None
) -> ExecutionContext:
    """Factory with validated defaults."""
    return ExecutionContext(
        execution_id=execution_id, macro_id=macro_id,
        method=method, trigger_value=trigger_value,
        timeout=timeout, start_time=datetime.now(),
        status=ExecutionStatus.PENDING
    )
```

### **2. Immutable Data Structures Pattern**

**Pattern**: All domain types use `@dataclass(frozen=True)` for immutability

```python
# Current Implementation: Immutable types with functional updates
@dataclass(frozen=True)
class MacroMetadata:
    """Immutable macro metadata."""
    uuid: MacroUUID
    name: MacroName
    state: MacroState
    # ...
    
    def with_state(self, new_state: MacroState) -> 'MacroMetadata':
        """Functional update pattern."""
        return dataclasses.replace(self, state=new_state, modified_at=datetime.now())
```

### **3. Validation-First Design Pattern**

**Pattern**: All type constructors validate inputs before creation

```python
# Current Implementation: Comprehensive validation
def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Validation-first constructor."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Range validation with descriptive errors."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)
```

### **4. State Machine Pattern**

**Pattern**: Enums with behavior methods for state management

```python
# Current Implementation: Behavioral enums
class MacroState(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Business logic encoded in type."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """State-dependent behavior."""
        return self != MacroState.EXECUTING

class ExecutionStatus(Enum):
    # State definitions...
    
    def is_terminal_state(self) -> bool:
        """Terminal state detection."""
        return self in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED,
                       ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT)
```

### **5. Composite Identifier Pattern**

**Pattern**: Support multiple lookup methods with type safety

```python
# Current Implementation: Flexible identification
@dataclass(frozen=True)
class MacroIdentifier:
    """Supports UUID or name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None
```

## Type System Testing ✅ **IMPLEMENTED**

### **1. Property-Based Type Safety Testing**

**Current Implementation** (`tests/types/test_type_safety.py`):

```python
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # Type checker (mypy) would catch this at compile time
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name must meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+, name):
        raise ValueError("Macro name contains invalid characters")
    return MacroName(name)

# Variable name validation with identifier conventions
def create_variable_name(name: str) -> VariableName:
    """Create validated variable name following Keyboard Maestro conventions."""
    if not name or len(name) > 255:
        raise ValueError("Variable name must be 1-255 characters")
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., name):
        raise ValueError("Variable name must follow identifier conventions")
    return VariableName(name)

# Bundle ID validation with reverse domain notation
def create_application_bundle_id(bundle_id: str) -> ApplicationBundleID:
    """Create validated application bundle identifier."""
    if not bundle_id:
        raise ValueError("Bundle ID cannot be empty")
    if not re.match(r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., bundle_id):
        raise ValueError("Bundle ID must follow reverse domain notation")
    return ApplicationBundleID(bundle_id)
```

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., name)
    except ValueError:
        # If creation fails, name violates some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+, name):
        raise ValueError("Macro name contains invalid characters")
    return MacroName(name)

# Variable name validation with identifier conventions
def create_variable_name(name: str) -> VariableName:
    """Create validated variable name following Keyboard Maestro conventions."""
    if not name or len(name) > 255:
        raise ValueError("Variable name must be 1-255 characters")
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., name):
        raise ValueError("Variable name must follow identifier conventions")
    return VariableName(name)

# Bundle ID validation with reverse domain notation
def create_application_bundle_id(bundle_id: str) -> ApplicationBundleID:
    """Create validated application bundle identifier."""
    if not bundle_id:
        raise ValueError("Bundle ID cannot be empty")
    if not re.match(r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., bundle_id):
        raise ValueError("Bundle ID must follow reverse domain notation")
    return ApplicationBundleID(bundle_id)
```

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., name))

def test_state_machine_transitions():
    """Test state transition validation."""
    # Enum methods encode business logic
    assert MacroState.ENABLED.can_execute()
    assert not MacroState.DISABLED.can_execute()
    assert not MacroState.EXECUTING.can_modify()
```

## Implementation Summary

The Keyboard Maestro MCP Server implements a **complete type-driven development system** with:

✅ **10+ Branded Identifier Types**: MacroUUID, MacroName, VariableName, etc.  
✅ **8+ Branded Value Types**: ScreenCoordinate, ConfidenceScore, ExecutionTimeout, etc.  
✅ **15+ Enumeration Types**: MacroState, ExecutionStatus, TriggerType, etc.  
✅ **Immutable Domain Types**: All using `@dataclass(frozen=True)`  
✅ **Type-Safe Factory Functions**: Comprehensive validation for all types  
✅ **State Machine Patterns**: Enums with behavioral methods  
✅ **Composite Identifiers**: Flexible lookup with type safety  
✅ **Type Conversion Utilities**: Safe transformations and validation helpers  
✅ **Property-Based Testing**: Validation properties tested with Hypothesis  

This type system provides **compile-time safety**, **clear domain modeling**, and **robust error handling** throughout the entire Keyboard Maestro MCP Server implementation., name):
        raise ValueError("Macro name contains invalid characters")
    return MacroName(name)

# Variable name validation with identifier conventions
def create_variable_name(name: str) -> VariableName:
    """Create validated variable name following Keyboard Maestro conventions."""
    if not name or len(name) > 255:
        raise ValueError("Variable name must be 1-255 characters")
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., name):
        raise ValueError("Variable name must follow identifier conventions")
    return VariableName(name)

# Bundle ID validation with reverse domain notation
def create_application_bundle_id(bundle_id: str) -> ApplicationBundleID:
    """Create validated application bundle identifier."""
    if not bundle_id:
        raise ValueError("Bundle ID cannot be empty")
    if not re.match(r'^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system., bundle_id):
        raise ValueError("Bundle ID must follow reverse domain notation")
    return ApplicationBundleID(bundle_id)
```

#### **1.2 Composite Identifier Types**

```python
# Composite identifiers for complex lookups
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class MacroIdentifier:
    """Composite identifier supporting both UUID and name-based lookup."""
    value: Union[MacroUUID, MacroName]
    group_context: Optional[GroupUUID] = None
    
    def is_uuid(self) -> bool:
        return isinstance(self.value, UUID)
    
    def is_name(self) -> bool:
        return isinstance(self.value, str)
    
    def requires_group_context(self) -> bool:
        return self.is_name() and self.group_context is None

@dataclass(frozen=True)
class VariableIdentifier:
    """Variable identifier with scope context."""
    name: VariableName
    scope: 'VariableScope'
    instance_id: Optional[str] = None
    
    def is_global(self) -> bool:
        return self.scope == VariableScope.GLOBAL
    
    def is_local(self) -> bool:
        return self.scope == VariableScope.LOCAL
    
    def is_password(self) -> bool:
        return self.scope == VariableScope.PASSWORD
```

### **2. Value Types**

#### **2.1 Primitive Value Types**

```python
# src/types/values.py (Target: <200 lines)
from typing import NewType, Literal
from decimal import Decimal

# Branded value types for domain-specific values
MacroExecutionTimeout = NewType('MacroExecutionTimeout', int)
VariableValue = NewType('VariableValue', str)
TriggerValue = NewType('TriggerValue', str)
ScreenCoordinate = NewType('ScreenCoordinate', int)
PixelColor = NewType('PixelColor', int)
ConfidenceScore = NewType('ConfidenceScore', float)

def create_execution_timeout(seconds: int) -> MacroExecutionTimeout:
    """Create validated execution timeout."""
    if not 1 <= seconds <= 300:
        raise ValueError("Timeout must be between 1 and 300 seconds")
    return MacroExecutionTimeout(seconds)

def create_confidence_score(score: float) -> ConfidenceScore:
    """Create validated confidence score."""
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")
    return ConfidenceScore(score)

def create_screen_coordinate(coord: int) -> ScreenCoordinate:
    """Create validated screen coordinate."""
    if coord < 0:
        raise ValueError("Screen coordinate must be non-negative")
    return ScreenCoordinate(coord)
```

#### **2.2 Structured Value Types**

```python
@dataclass(frozen=True)
class ScreenCoordinates:
    """Immutable screen coordinates with validation."""
    x: ScreenCoordinate
    y: ScreenCoordinate
    
    def __post_init__(self):
        """Validate coordinates within screen bounds."""
        bounds = get_screen_bounds()
        if self.x > bounds.width or self.y > bounds.height:
            raise ValueError(f"Coordinates ({self.x}, {self.y}) exceed screen bounds")
    
    def offset(self, dx: int, dy: int) -> 'ScreenCoordinates':
        """Create new coordinates with offset."""
        return ScreenCoordinates(
            create_screen_coordinate(self.x + dx),
            create_screen_coordinate(self.y + dy)
        )

@dataclass(frozen=True)
class ScreenArea:
    """Immutable screen area definition."""
    top_left: ScreenCoordinates
    bottom_right: ScreenCoordinates
    
    def __post_init__(self):
        """Validate area is well-formed."""
        if (self.bottom_right.x <= self.top_left.x or 
            self.bottom_right.y <= self.top_left.y):
            raise ValueError("Invalid screen area: bottom-right must be below and right of top-left")
    
    @property
    def width(self) -> int:
        return self.bottom_right.x - self.top_left.x
    
    @property
    def height(self) -> int:
        return self.bottom_right.y - self.top_left.y
    
    @property
    def center(self) -> ScreenCoordinates:
        return ScreenCoordinates(
            create_screen_coordinate(self.top_left.x + self.width // 2),
            create_screen_coordinate(self.top_left.y + self.height // 2)
        )
```

### **3. Enumeration Types**

#### **3.1 Core Operation Enums**

```python
# src/types/enumerations.py (Target: <250 lines)
from enum import Enum, auto
from typing import Literal

class MacroState(Enum):
    """Valid states for macro objects."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    DEBUGGING = "debugging"
    EXECUTING = "executing"
    
    def can_execute(self) -> bool:
        """Check if macro can be executed in current state."""
        return self in (MacroState.ENABLED, MacroState.DEBUGGING)
    
    def can_modify(self) -> bool:
        """Check if macro can be modified in current state."""
        return self != MacroState.EXECUTING

class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)

class VariableScope(Enum):
    """Variable scope classifications."""
    GLOBAL = "global"
    LOCAL = "local"
    INSTANCE = "instance"
    PASSWORD = "password"
    
    def is_persistent(self) -> bool:
        """Check if variables in this scope persist across sessions."""
        return self in (VariableScope.GLOBAL, VariableScope.PASSWORD)
    
    def requires_instance_id(self) -> bool:
        """Check if scope requires instance identifier."""
        return self == VariableScope.INSTANCE

class TriggerType(Enum):
    """Types of macro triggers."""
    HOTKEY = "hotkey"
    APPLICATION = "application"
    TIME = "time"
    SYSTEM = "system"
    FILE_FOLDER = "file_folder"
    DEVICE = "device"
    NETWORK = "network"
    CLIPBOARD = "clipboard"
    
    def supports_parameters(self) -> bool:
        """Check if trigger type supports parameter passing."""
        return self in (TriggerType.HOTKEY, TriggerType.APPLICATION, TriggerType.TIME)

class ActionType(Enum):
    """Categories of available actions."""
    APPLICATION_CONTROL = "application_control"
    FILE_OPERATIONS = "file_operations"
    TEXT_MANIPULATION = "text_manipulation"
    SYSTEM_CONTROL = "system_control"
    INTERFACE_AUTOMATION = "interface_automation"
    CLIPBOARD_OPERATIONS = "clipboard_operations"
    VARIABLE_MANAGEMENT = "variable_management"
    CONTROL_FLOW = "control_flow"
    COMMUNICATION = "communication"
    PLUGIN_ACTION = "plugin_action"
```

#### **3.2 System Integration Enums**

```python
class ApplicationOperation(Enum):
    """Application control operations."""
    LAUNCH = "launch"
    QUIT = "quit"
    ACTIVATE = "activate"
    FORCE_QUIT = "force_quit"
    HIDE = "hide"
    SHOW = "show"
    
    def is_lifecycle_operation(self) -> bool:
        """Check if operation affects application lifecycle."""
        return self in (ApplicationOperation.LAUNCH, ApplicationOperation.QUIT, 
                       ApplicationOperation.FORCE_QUIT)

class FileOperation(Enum):
    """File system operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)

class ClickType(Enum):
    """Mouse click types."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
```

### **4. State Machine Types**

#### **4.1 Macro Lifecycle State Machine**

```python
# src/types/state_machines.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Set, Dict, Optional
from enum import Enum

class MacroLifecycleState(Enum):
    """Complete macro lifecycle states."""
    CREATED = "created"
    CONFIGURED = "configured"
    ENABLED = "enabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"
    DELETED = "deleted"

@dataclass(frozen=True)
class MacroStateTransition:
    """Represents a valid state transition."""
    from_state: MacroLifecycleState
    to_state: MacroLifecycleState
    trigger: str
    conditions: Set[str]
    
    def is_valid_transition(self, current_state: MacroLifecycleState) -> bool:
        """Check if transition is valid from current state."""
        return current_state == self.from_state

class MacroStateMachine:
    """State machine for macro lifecycle management."""
    
    def __init__(self):
        self._transitions: Dict[MacroLifecycleState, Set[MacroStateTransition]] = {
            MacroLifecycleState.CREATED: {
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.CONFIGURED,
                    "configure",
                    {"has_triggers", "has_actions"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CREATED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            MacroLifecycleState.CONFIGURED: {
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.ENABLED,
                    "enable",
                    {"is_valid_configuration"}
                ),
                MacroStateTransition(
                    MacroLifecycleState.CONFIGURED,
                    MacroLifecycleState.DELETED,
                    "delete",
                    set()
                )
            },
            # ... additional transitions
        }
    
    def get_valid_transitions(self, 
                            current_state: MacroLifecycleState) -> Set[MacroStateTransition]:
        """Get all valid transitions from current state."""
        return self._transitions.get(current_state, set())
    
    def can_transition(self, 
                      current_state: MacroLifecycleState,
                      target_state: MacroLifecycleState) -> bool:
        """Check if transition from current to target state is valid."""
        valid_transitions = self.get_valid_transitions(current_state)
        return any(
            transition.to_state == target_state
            for transition in valid_transitions
        )
```

#### **4.2 Execution State Machine**

```python
class ExecutionState(Enum):
    """Execution state for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context."""
    execution_id: str
    macro_id: MacroUUID
    trigger_value: Optional[TriggerValue]
    start_time: float
    timeout: MacroExecutionTimeout
    current_state: ExecutionState
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self.current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.TIMEOUT
        )
    
    def can_pause(self) -> bool:
        """Check if execution can be paused."""
        return self.current_state == ExecutionState.RUNNING
    
    def can_resume(self) -> bool:
        """Check if execution can be resumed."""
        return self.current_state == ExecutionState.PAUSED
```

### **5. Configuration Types**

#### **5.1 Immutable Configuration Objects**

```python
# src/types/configuration.py (Target: <250 lines)
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional

@dataclass(frozen=True)
class ServerConfiguration:
    """Immutable server configuration."""
    host: str
    port: int
    transport: str
    max_concurrent_operations: int
    operation_timeout: MacroExecutionTimeout
    auth_required: bool
    log_level: str
    
    def __post_init__(self):
        """Validate configuration values."""
        if not 1024 <= self.port <= 65535:
            raise ValueError("Port must be in range 1024-65535")
        if self.max_concurrent_operations <= 0:
            raise ValueError("Max concurrent operations must be positive")
    
    def with_port(self, new_port: int) -> 'ServerConfiguration':
        """Create new configuration with different port."""
        return dataclasses.replace(self, port=new_port)

@dataclass(frozen=True)
class MacroConfiguration:
    """Immutable macro configuration."""
    name: MacroName
    group_id: Optional[GroupUUID]
    enabled: bool
    color: Optional[str]
    notes: Optional[str]
    triggers: FrozenSet['TriggerConfiguration']
    actions: FrozenSet['ActionConfiguration']
    
    def __post_init__(self):
        """Validate macro configuration."""
        if not self.triggers and not self.actions:
            raise ValueError("Macro must have at least one trigger or action")
    
    def add_trigger(self, trigger: 'TriggerConfiguration') -> 'MacroConfiguration':
        """Create new configuration with additional trigger."""
        new_triggers = self.triggers | {trigger}
        return dataclasses.replace(self, triggers=new_triggers)

@dataclass(frozen=True)
class TriggerConfiguration:
    """Immutable trigger configuration."""
    trigger_type: TriggerType
    parameters: Mapping[str, Any]
    enabled: bool = True
    
    def __post_init__(self):
        """Validate trigger configuration."""
        required_params = get_required_parameters(self.trigger_type)
        missing_params = required_params - set(self.parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
    
    def __hash__(self) -> int:
        """Make trigger configuration hashable for use in sets."""
        return hash((self.trigger_type, tuple(sorted(self.parameters.items())), self.enabled))
```

### **6. Result Types**

#### **6.1 Operation Result Types**

```python
# src/types/results.py (Target: <250 lines)
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Union
from enum import Enum

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Functional result type for explicit error handling."""
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    def __post_init__(self):
        """Ensure exactly one of value or error is set."""
        if (self._value is None) == (self._error is None):
            raise ValueError("Result must have exactly one of value or error")
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """Create successful result."""
        return cls(_value=value)
    
    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        """Create failed result."""
        return cls(_error=error)
    
    @property
    def is_success(self) -> bool:
        """Check if result represents success."""
        return self._value is not None
    
    @property
    def is_failure(self) -> bool:
        """Check if result represents failure."""
        return self._error is not None
    
    def unwrap(self) -> T:
        """Get value or raise exception if error."""
        if self._value is not None:
            return self._value
        raise ValueError(f"Cannot unwrap failed result: {self._error}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform successful value using function."""
        if self.is_success:
            return Result.success(func(self._value))
        return Result.failure(self._error)

class ErrorType(Enum):
    """Classification of error types."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"

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
        return self.error_type in (
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR
        )

# Specific result types for domain operations
MacroOperationResult = Result[MacroConfiguration, OperationError]
VariableOperationResult = Result[VariableValue, OperationError]
ExecutionResult = Result[ExecutionContext, OperationError]
ValidationResult = Result[bool, OperationError]
```

#### **6.2 Specialized Result Types**

```python
@dataclass(frozen=True)
class MacroExecutionResult:
    """Detailed macro execution result."""
    success: bool
    execution_id: str
    macro_id: MacroUUID
    start_time: float
    end_time: Optional[float]
    execution_time: float
    error_details: Optional[OperationError]
    output: Optional[str]
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.success and self.error_details is not None:
            raise ValueError("Successful result cannot have error details")
        if not self.success and self.error_details is None:
            raise ValueError("Failed result must have error details")

@dataclass(frozen=True)
class OCRResult:
    """OCR operation result with confidence scores."""
    success: bool
    extracted_text: FrozenSet['TextExtraction']
    processing_time: float
    area_processed: ScreenArea
    error_details: Optional[OperationError] = None
    
    @property
    def high_confidence_text(self) -> FrozenSet['TextExtraction']:
        """Get text extractions with high confidence."""
        return frozenset(
            extraction for extraction in self.extracted_text
            if extraction.confidence >= 0.8
        )

@dataclass(frozen=True)
class TextExtraction:
    """Individual text extraction with metadata."""
    text: str
    confidence: ConfidenceScore
    bounding_box: ScreenArea
    language: str
    
    def __hash__(self) -> int:
        """Make text extraction hashable."""
        return hash((self.text, self.confidence, self.language))
```

### **7. Option Types**

#### **7.1 Optional Value Handling**

```python
# src/types/optional.py (Target: <200 lines)
from typing import Optional, TypeVar, Callable, Union
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Option(Generic[T]):
    """Explicit optional type for safer null handling."""
    _value: Optional[T]
    
    @classmethod
    def some(cls, value: T) -> 'Option[T]':
        """Create option with value."""
        if value is None:
            raise ValueError("Cannot create Some with None value")
        return cls(value)
    
    @classmethod
    def none(cls) -> 'Option[T]':
        """Create empty option."""
        return cls(None)
    
    @property
    def is_some(self) -> bool:
        """Check if option has value."""
        return self._value is not None
    
    @property
    def is_none(self) -> bool:
        """Check if option is empty."""
        return self._value is None
    
    def unwrap(self) -> T:
        """Get value or raise exception."""
        if self._value is not None:
            return self._value
        raise ValueError("Cannot unwrap None option")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or return default."""
        return self._value if self._value is not None else default
    
    def map(self, func: Callable[[T], U]) -> 'Option[U]':
        """Transform value if present."""
        if self.is_some:
            return Option.some(func(self._value))
        return Option.none()
    
    def flat_map(self, func: Callable[[T], 'Option[U]']) -> 'Option[U]':
        """Flat map operation for option chaining."""
        if self.is_some:
            return func(self._value)
        return Option.none()

# Convenience type aliases
OptionalMacro = Option[MacroConfiguration]
OptionalVariable = Option[VariableValue]
OptionalGroup = Option[GroupConfiguration]
```

### **8. Validation Types**

#### **8.1 Type Validators**

```python
# src/types/validators.py (Target: <250 lines)
from typing import Protocol, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

class TypeValidator(Protocol[T]):
    """Protocol for type validation."""
    
    def validate(self, value: Any) -> Result[T, ValidationError]:
        """Validate value and return typed result."""
        ...
    
    def is_valid(self, value: Any) -> bool:
        """Check if value is valid without creating result."""
        ...

@dataclass(frozen=True)
class ValidationError:
    """Type validation error information."""
    field_name: str
    expected_type: str
    actual_value: Any
    validation_rule: str
    message: str

class MacroNameValidator:
    """Validator for macro names."""
    
    def validate(self, value: Any) -> Result[MacroName, ValidationError]:
        """Validate macro name format and constraints."""
        if not isinstance(value, str):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="type_check",
                message="Macro name must be string"
            ))
        
        if not 1 <= len(value) <= 255:
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="length_check",
                message="Macro name must be 1-255 characters"
            ))
        
        if not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', value):
            return Result.failure(ValidationError(
                field_name="macro_name",
                expected_type="str",
                actual_value=value,
                validation_rule="character_check",
                message="Macro name contains invalid characters"
            ))
        
        return Result.success(MacroName(value))
    
    def is_valid(self, value: Any) -> bool:
        """Quick validation check."""
        return self.validate(value).is_success

class CompositeValidator(Generic[T]):
    """Compose multiple validators with configurable logic."""
    
    def __init__(self, validators: List[TypeValidator[T]], 
                 logic: Literal["AND", "OR"] = "AND"):
        self.validators = validators
        self.logic = logic
    
    def validate(self, value: Any) -> Result[T, List[ValidationError]]:
        """Validate using composite logic."""
        results = [validator.validate(value) for validator in self.validators]
        
        if self.logic == "AND":
            errors = [result._error for result in results if result.is_failure]
            if errors:
                return Result.failure(errors)
            return results[0]  # All successful, return first result
        
        else:  # OR logic
            successful_results = [result for result in results if result.is_success]
            if successful_results:
                return successful_results[0]
            
            all_errors = [result._error for result in results if result.is_failure]
            return Result.failure(all_errors)
```

## Type System Integration

### **1. FastMCP Integration Types**

```python
# src/types/mcp_types.py (Target: <200 lines)
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class MCPToolRequest:
    """Type-safe MCP tool request."""
    tool_name: str
    parameters: Dict[str, Any]
    request_id: str
    
    def get_parameter(self, name: str, parameter_type: type) -> Option[Any]:
        """Get typed parameter with validation."""
        if name not in self.parameters:
            return Option.none()
        
        value = self.parameters[name]
        if not isinstance(value, parameter_type):
            return Option.none()
        
        return Option.some(value)

@dataclass(frozen=True)
class MCPToolResponse:
    """Type-safe MCP tool response."""
    success: bool
    content: List[Any]
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, content: List[Any]) -> 'MCPToolResponse':
        """Create successful response."""
        return cls(success=True, content=content)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'MCPToolResponse':
        """Create error response."""
        return cls(success=False, content=[], error_message=error_message)
```

### **2. AppleScript Integration Types**

```python
# src/types/applescript_types.py (Target: <200 lines)
from typing import Union, Literal

ScriptLanguage = Literal["applescript", "javascript", "shell", "python", "php"]

@dataclass(frozen=True)
class AppleScriptCommand:
    """Type-safe AppleScript command."""
    script: str
    language: ScriptLanguage
    timeout: MacroExecutionTimeout
    
    def __post_init__(self):
        """Validate script command."""
        if not self.script.strip():
            raise ValueError("Script cannot be empty")
        if self.language not in ["applescript", "javascript", "shell", "python", "php"]:
            raise ValueError(f"Unsupported script language: {self.language}")

@dataclass(frozen=True)
class AppleScriptResult:
    """AppleScript execution result."""
    success: bool
    output: Optional[str]
    error_message: Optional[str]
    execution_time: float
    
    def is_error_result(self) -> bool:
        """Check if result indicates error."""
        return not self.success or self.error_message is not None
```

## Type System Testing

### **1. Type Safety Testing**

```python
# tests/types/test_type_safety.py (Target: <200 lines)
import pytest
from hypothesis import given, strategies as st
from src.types.domain_types import *

def test_branded_types_prevent_confusion():
    """Test that branded types prevent accidental mixing."""
    macro_uuid = create_macro_uuid("550e8400-e29b-41d4-a716-446655440000")
    group_uuid = create_group_uuid("550e8400-e29b-41d4-a716-446655440001")
    
    # This should be caught by type checker (mypy)
    # macro_operation(group_uuid)  # Type error
    
    assert isinstance(macro_uuid, UUID)
    assert isinstance(group_uuid, UUID)
    assert macro_uuid != group_uuid

@given(name=st.text())
def test_macro_name_validation_properties(name):
    """Property-based testing for macro name validation."""
    try:
        macro_name = create_macro_name(name)
        # If creation succeeds, name should meet all criteria
        assert 1 <= len(name) <= 255
        assert re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name)
    except ValueError:
        # If creation fails, name should violate some criteria
        assert (len(name) == 0 or len(name) > 255 or 
                not re.match(r'^[a-zA-Z0-9_\s\-\.]+$', name))

def test_state_machine_transitions():
    """Test state machine transition validation."""
    machine = MacroStateMachine()
    
    # Valid transitions
    assert machine.can_transition(
        MacroLifecycleState.CREATED,
        MacroLifecycleState.CONFIGURED
    )
    
    # Invalid transitions
    assert not machine.can_transition(
        MacroLifecycleState.EXECUTING,
        MacroLifecycleState.DELETED
    )
```

This comprehensive type system provides the foundation for type-driven development of the Keyboard Maestro MCP Server, ensuring compile-time safety, clear domain modeling, and robust error handling throughout the system.