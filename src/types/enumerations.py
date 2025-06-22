# src/types/enumerations.py (Target: <250 lines)
"""
Enumeration types for Keyboard Maestro operations and state management.

This module defines comprehensive enumeration types that provide type safety
and clear domain modeling for all operational aspects of the MCP server.
"""

from enum import Enum, auto
from typing import Literal, Set


class MacroState(Enum):
    """Valid states for macro objects with state machine behavior."""
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


class MacroLifecycleState(Enum):
    """Detailed lifecycle states for property-based testing."""
    CREATED = "created"
    ENABLED = "enabled"
    DISABLED = "disabled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"
    
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in (MacroLifecycleState.COMPLETED, MacroLifecycleState.FAILED, MacroLifecycleState.DELETED)
    
    def can_transition_to(self, target: 'MacroLifecycleState') -> bool:
        """Check if transition to target state is valid."""
        valid_transitions = {
            MacroLifecycleState.CREATED: {MacroLifecycleState.ENABLED, MacroLifecycleState.DISABLED, MacroLifecycleState.DELETED},
            MacroLifecycleState.ENABLED: {MacroLifecycleState.DISABLED, MacroLifecycleState.EXECUTING, MacroLifecycleState.DELETED},
            MacroLifecycleState.DISABLED: {MacroLifecycleState.ENABLED, MacroLifecycleState.DELETED},
            MacroLifecycleState.EXECUTING: {MacroLifecycleState.COMPLETED, MacroLifecycleState.FAILED},
            MacroLifecycleState.COMPLETED: {MacroLifecycleState.ENABLED, MacroLifecycleState.DISABLED, MacroLifecycleState.DELETED},
            MacroLifecycleState.FAILED: {MacroLifecycleState.ENABLED, MacroLifecycleState.DISABLED, MacroLifecycleState.DELETED},
            MacroLifecycleState.DELETED: set()  # Terminal state
        }
        return target in valid_transitions.get(self, set())


class ExecutionMethod(Enum):
    """Supported macro execution methods."""
    APPLESCRIPT = "applescript"
    URL_SCHEME = "url_scheme"
    WEB_API = "web_api"
    REMOTE_TRIGGER = "remote_trigger"
    
    def requires_network(self) -> bool:
        """Check if execution method requires network access."""
        return self in (ExecutionMethod.WEB_API, ExecutionMethod.REMOTE_TRIGGER)
    
    def supports_parameters(self) -> bool:
        """Check if execution method supports parameter passing."""
        return self in (ExecutionMethod.APPLESCRIPT, ExecutionMethod.URL_SCHEME)


class VariableScope(Enum):
    """Variable scope classifications with persistence behavior."""
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
    
    def is_secure(self) -> bool:
        """Check if scope handles secure/sensitive data."""
        return self == VariableScope.PASSWORD


class TriggerType(Enum):
    """Types of macro triggers with capability information."""
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
    
    def requires_polling(self) -> bool:
        """Check if trigger requires periodic polling."""
        return self in (TriggerType.FILE_FOLDER, TriggerType.NETWORK)


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


class ApplicationOperation(Enum):
    """Application control operations with lifecycle information."""
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
    
    def is_destructive(self) -> bool:
        """Check if operation is potentially destructive."""
        return self in (ApplicationOperation.QUIT, ApplicationOperation.FORCE_QUIT)


class FileOperation(Enum):
    """File system operations with modification behavior."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_FOLDER = "create_folder"
    CREATE_FILE = "create_file"
    
    def modifies_source(self) -> bool:
        """Check if operation modifies the source file/folder."""
        return self in (FileOperation.MOVE, FileOperation.DELETE, FileOperation.RENAME)
    
    def requires_destination(self) -> bool:
        """Check if operation requires destination path."""
        return self in (FileOperation.COPY, FileOperation.MOVE, FileOperation.RENAME)
    
    def is_creation_operation(self) -> bool:
        """Check if operation creates new file system entities."""
        return self in (FileOperation.COPY, FileOperation.CREATE_FOLDER, FileOperation.CREATE_FILE)


class ClickType(Enum):
    """Mouse click types with behavior information."""
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MIDDLE_CLICK = "middle_click"
    
    def is_context_menu_trigger(self) -> bool:
        """Check if click type typically triggers context menu."""
        return self == ClickType.RIGHT_CLICK
    
    def is_multi_click(self) -> bool:
        """Check if click type involves multiple rapid clicks."""
        return self == ClickType.DOUBLE_CLICK


class ExecutionStatus(Enum):
    """Execution status for running operations."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    
    def is_terminal_state(self) -> bool:
        """Check if execution is in terminal state."""
        return self in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED,
                       ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT)
    
    def is_active_state(self) -> bool:
        """Check if execution is actively running."""
        return self in (ExecutionStatus.INITIALIZING, ExecutionStatus.RUNNING)
    
    def can_be_cancelled(self) -> bool:
        """Check if execution can be cancelled."""
        return self in (ExecutionStatus.PENDING, ExecutionStatus.INITIALIZING, 
                       ExecutionStatus.RUNNING, ExecutionStatus.PAUSED)


class ErrorType(Enum):
    """Classification of error types for systematic handling."""
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    TIMEOUT_ERROR = "timeout_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    APPLESCRIPT_ERROR = "applescript_error"
    CONFIGURATION_ERROR = "configuration_error"
    
    def is_recoverable(self) -> bool:
        """Check if error type is potentially recoverable."""
        return self in (ErrorType.TIMEOUT_ERROR, ErrorType.NETWORK_ERROR,
                       ErrorType.APPLESCRIPT_ERROR)
    
    def requires_user_action(self) -> bool:
        """Check if error requires user intervention."""
        return self in (ErrorType.PERMISSION_ERROR, ErrorType.CONFIGURATION_ERROR)


class LogLevel(Enum):
    """Logging levels with severity ordering."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    
    def get_numeric_level(self) -> int:
        """Get numeric level for comparison."""
        levels = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50
        }
        return levels[self]


class TransportType(Enum):
    """Supported transport protocols."""
    STDIO = "stdio"
    HTTP = "streamable-http"
    WEBSOCKET = "websocket"
    
    def supports_authentication(self) -> bool:
        """Check if transport supports authentication."""
        return self in (TransportType.HTTP, TransportType.WEBSOCKET)
    
    def is_local_transport(self) -> bool:
        """Check if transport is for local communication."""
        return self == TransportType.STDIO


class ServerStatus(Enum):
    """Server operational status with lifecycle states."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    FAILED = "failed"
    
    def is_operational(self) -> bool:
        """Check if server is operational."""
        return self == ServerStatus.RUNNING
    
    def can_accept_requests(self) -> bool:
        """Check if server can accept new requests."""
        return self == ServerStatus.RUNNING


class ComponentStatus(Enum):
    """Component health status for monitoring."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    SHUTDOWN = "shutdown"
    
    def is_functional(self) -> bool:
        """Check if component is functional."""
        return self in (ComponentStatus.HEALTHY, ComponentStatus.DEGRADED)


class ToolStatus(Enum):
    """MCP tool availability status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    ERROR = "error"
    
    def can_execute(self) -> bool:
        """Check if tool can be executed."""
        return self == ToolStatus.ACTIVE


class ToolCategory(Enum):
    """Categories for organizing MCP tools."""
    MACRO_MANAGEMENT = "macro_management"
    VARIABLE_MANAGEMENT = "variable_management"
    FILE_OPERATIONS = "file_operations"
    APPLICATION_CONTROL = "application_control"
    WINDOW_MANAGEMENT = "window_management"
    INTERFACE_AUTOMATION = "interface_automation"
    OCR_IMAGE = "ocr_image"
    COMMUNICATION = "communication"
    SYSTEM_INTEGRATION = "system_integration"
    
    def is_core_category(self) -> bool:
        """Check if category is core functionality."""
        return self in (ToolCategory.MACRO_MANAGEMENT, ToolCategory.VARIABLE_MANAGEMENT)


class ConnectionStatus(Enum):
    """AppleScript connection status for pool management."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    CLOSED = "closed"
    
    def is_usable(self) -> bool:
        """Check if connection can be used."""
        return self == ConnectionStatus.AVAILABLE


class PoolStatus(Enum):
    """AppleScript connection pool status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    FAILED = "failed"
    
    def is_operational(self) -> bool:
        """Check if pool is operational."""
        return self == PoolStatus.ACTIVE
    
    def can_accept_requests(self) -> bool:
        """Check if pool can accept new requests."""
        return self == PoolStatus.ACTIVE


class ResourceType(Enum):
    """System resource types for performance monitoring."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    
    def get_unit(self) -> str:
        """Get appropriate unit for resource type."""
        units = {
            ResourceType.CPU: "percent",
            ResourceType.MEMORY: "percent",
            ResourceType.DISK: "percent",
            ResourceType.NETWORK: "bytes"
        }
        return units.get(self, "unknown")


class AlertLevel(Enum):
    """Performance alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    
    def requires_immediate_action(self) -> bool:
        """Check if alert level requires immediate action."""
        return self == AlertLevel.CRITICAL


class SessionStatus(Enum):
    """MCP session status for lifecycle management."""
    ACTIVE = "active"
    IDLE = "idle"
    ENDED = "ended"
    EXPIRED = "expired"
    
    def is_active(self) -> bool:
        """Check if session is active."""
        return self in (SessionStatus.ACTIVE, SessionStatus.IDLE)


# Constants for validation and constraints
VALID_VARIABLE_SCOPES = frozenset(scope for scope in VariableScope)
VALID_LIFECYCLE_STATES = frozenset(state for state in MacroLifecycleState)
SUPPORTED_EXECUTION_METHODS = frozenset(method for method in ExecutionMethod)
TERMINAL_EXECUTION_STATES = frozenset(
    status for status in ExecutionStatus if status.is_terminal_state()
)
RECOVERABLE_ERROR_TYPES = frozenset(
    error_type for error_type in ErrorType if error_type.is_recoverable()
)
