"""Core system operations with defensive programming and error recovery.

This module provides the core logic for system integration operations including
file operations, application control, and interface automation with comprehensive
error handling and recovery mechanisms.
"""

from typing import Dict, List, Optional, Union, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import asyncio
import subprocess
import os
import time

from src.contracts.decorators import requires, ensures
from src.contracts.exceptions import SystemOperationError, PermissionDeniedError
from src.types.domain_types import ScreenCoordinates, ScreenArea
from src.validators.system_validators import system_validator, ValidationResult
from src.boundaries.permission_checker import permission_checker
from src.utils.coordinate_utils import coordinate_validator


class OperationStatus(Enum):
    """Status of system operations."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"


class RecoveryAction(Enum):
    """Available recovery actions for failed operations."""
    RETRY = auto()
    ADJUST_PARAMETERS = auto()
    REQUEST_PERMISSION = auto()
    FALLBACK_METHOD = auto()
    ABORT = auto()


@dataclass(frozen=True)
class SystemOperationResult:
    """Result of system operation with recovery information."""
    status: OperationStatus
    message: str
    data: Optional[Any] = None
    execution_time: float = 0.0
    recovery_actions: List[RecoveryAction] = None
    error_details: Optional[str] = None
    
    def __post_init__(self):
        if self.recovery_actions is None:
            object.__setattr__(self, 'recovery_actions', [])


class RetryStrategy(NamedTuple):
    """Configuration for operation retry logic."""
    max_attempts: int
    delay_base: float
    delay_multiplier: float
    timeout: float


class SystemOperationManager:
    """Core system operations with defensive programming and error recovery."""
    
    def __init__(self):
        self._default_retry = RetryStrategy(3, 0.5, 2.0, 30.0)
        self._operation_timeouts = {
            'file_operation': 30.0,
            'app_launch': 10.0,
            'app_quit': 5.0,
            'interface_action': 2.0
        }
        self._active_operations: Dict[str, asyncio.Task] = {}
    
    @requires(lambda source_path: isinstance(source_path, str) and len(source_path) > 0)
    @requires(lambda dest_path: isinstance(dest_path, str) and len(dest_path) > 0)
    @ensures(lambda result: isinstance(result, SystemOperationResult))
    async def copy_file(self, source_path: str, dest_path: str, 
                       overwrite: bool = False) -> SystemOperationResult:
        """Copy file with comprehensive validation and error recovery."""
        start_time = time.time()
        
        try:
            # Validate source path
            source_validation = system_validator.validate_file_path(source_path, "read")
            if not source_validation.is_valid:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Source validation failed: {source_validation.error_message}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.ADJUST_PARAMETERS],
                    error_details=source_validation.recovery_suggestion
                )
            
            # Validate destination path
            dest_validation = system_validator.validate_file_path(dest_path, "write")
            if not dest_validation.is_valid:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Destination validation failed: {dest_validation.error_message}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.ADJUST_PARAMETERS, RecoveryAction.REQUEST_PERMISSION],
                    error_details=dest_validation.recovery_suggestion
                )
            
            # Use validated paths
            source = Path(source_validation.sanitized_input)
            dest = Path(dest_validation.sanitized_input)
            
            # Check if source exists
            if not source.exists():
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Source file does not exist: {source}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.ADJUST_PARAMETERS]
                )
            
            # Check if destination exists and handle overwrite
            if dest.exists() and not overwrite:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Destination exists and overwrite=False: {dest}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.ADJUST_PARAMETERS]
                )
            
            # Create destination directory if needed
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform copy operation with retry logic
            result = await self._retry_operation(
                self._execute_file_copy, 
                self._default_retry,
                source, dest
            )
            
            execution_time = time.time() - start_time
            
            if result:
                return SystemOperationResult(
                    OperationStatus.SUCCESS,
                    f"File copied successfully: {source} -> {dest}",
                    data={'source': str(source), 'destination': str(dest)},
                    execution_time=execution_time
                )
            else:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    "File copy operation failed",
                    execution_time=execution_time,
                    recovery_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK_METHOD]
                )
                
        except Exception as e:
            return SystemOperationResult(
                OperationStatus.FAILED,
                f"File copy error: {str(e)}",
                execution_time=time.time() - start_time,
                recovery_actions=[RecoveryAction.RETRY],
                error_details=f"Exception: {type(e).__name__}: {str(e)}"
            )
    
    async def _execute_file_copy(self, source: Path, dest: Path) -> bool:
        """Execute file copy with timeout protection."""
        try:
            # Use subprocess for reliable file copying
            process = await asyncio.create_subprocess_exec(
                'cp', str(source), str(dest),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self._operation_timeouts['file_operation']
            )
            
            return process.returncode == 0
            
        except asyncio.TimeoutError:
            return False
        except Exception:
            return False
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier) > 0)
    @ensures(lambda result: isinstance(result, SystemOperationResult))
    async def launch_application(self, app_identifier: str, 
                               wait_for_launch: bool = True) -> SystemOperationResult:
        """Launch application with validation and error recovery."""
        start_time = time.time()
        
        try:
            # Validate application identifier
            app_validation = system_validator.validate_application_identifier(app_identifier)
            if not app_validation.is_valid:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Application validation failed: {app_validation.error_message}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.ADJUST_PARAMETERS],
                    error_details=app_validation.recovery_suggestion
                )
            
            # Check automation permissions
            perm_result = permission_checker.check_permission(
                permission_checker.PermissionType.AUTOMATION
            )
            if perm_result.status.value != "granted":
                return SystemOperationResult(
                    OperationStatus.PERMISSION_DENIED,
                    f"Automation permission required: {perm_result.details}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.REQUEST_PERMISSION],
                    error_details=perm_result.recovery_suggestion
                )
            
            # Use validated identifier
            validated_app = app_validation.sanitized_input
            
            # Launch application with retry logic
            result = await self._retry_operation(
                self._execute_app_launch,
                self._default_retry,
                validated_app, wait_for_launch
            )
            
            execution_time = time.time() - start_time
            
            if result:
                return SystemOperationResult(
                    OperationStatus.SUCCESS,
                    f"Application launched successfully: {validated_app}",
                    data={'application': validated_app, 'wait_for_launch': wait_for_launch},
                    execution_time=execution_time
                )
            else:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Failed to launch application: {validated_app}",
                    execution_time=execution_time,
                    recovery_actions=[RecoveryAction.RETRY, RecoveryAction.ADJUST_PARAMETERS]
                )
                
        except Exception as e:
            return SystemOperationResult(
                OperationStatus.FAILED,
                f"Application launch error: {str(e)}",
                execution_time=time.time() - start_time,
                recovery_actions=[RecoveryAction.RETRY],
                error_details=f"Exception: {type(e).__name__}: {str(e)}"
            )
    
    async def _execute_app_launch(self, app_identifier: str, wait_for_launch: bool) -> bool:
        """Execute application launch with AppleScript."""
        try:
            if '.' in app_identifier and not app_identifier.endswith('.app'):
                # Bundle ID format
                script = f'''
                tell application id "{app_identifier}"
                    launch
                end tell
                '''
            else:
                # Application name format
                app_name = app_identifier.replace('.app', '')
                script = f'''
                tell application "{app_name}"
                    launch
                end tell
                '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._operation_timeouts['app_launch']
            )
            
            success = process.returncode == 0
            
            # If wait_for_launch is True, verify app is running
            if success and wait_for_launch:
                await asyncio.sleep(0.5)  # Brief delay for app to start
                success = await self._verify_app_running(app_identifier)
            
            return success
            
        except asyncio.TimeoutError:
            return False
        except Exception:
            return False
    
    async def _verify_app_running(self, app_identifier: str) -> bool:
        """Verify application is running."""
        try:
            script = f'''
            tell application "System Events"
                return exists application process "{app_identifier}"
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=5.0
            )
            
            return process.returncode == 0 and 'true' in stdout.decode().lower()
            
        except Exception:
            return False
    
    @requires(lambda x: isinstance(x, int))
    @requires(lambda y: isinstance(y, int))
    @ensures(lambda result: isinstance(result, SystemOperationResult))
    async def click_at_coordinates(self, x: int, y: int, 
                                 click_type: str = "left") -> SystemOperationResult:
        """Perform mouse click with coordinate validation and error recovery."""
        start_time = time.time()
        
        try:
            coordinates = ScreenCoordinates(x, y)
            
            # Validate coordinates
            coord_validation = system_validator.validate_screen_coordinates(coordinates)
            if not coord_validation.is_valid and coord_validation.result_type != ValidationResult.WARNING:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Coordinate validation failed: {coord_validation.error_message}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.ADJUST_PARAMETERS],
                    error_details=coord_validation.recovery_suggestion
                )
            
            # Use sanitized coordinates (adjusted if necessary)
            final_coords = coord_validation.sanitized_input
            
            # Check accessibility permissions
            perm_result = permission_checker.check_permission(
                permission_checker.PermissionType.ACCESSIBILITY
            )
            if perm_result.status.value != "granted":
                return SystemOperationResult(
                    OperationStatus.PERMISSION_DENIED,
                    f"Accessibility permission required: {perm_result.details}",
                    execution_time=time.time() - start_time,
                    recovery_actions=[RecoveryAction.REQUEST_PERMISSION],
                    error_details=perm_result.recovery_suggestion
                )
            
            # Perform click with retry logic
            result = await self._retry_operation(
                self._execute_mouse_click,
                self._default_retry,
                final_coords, click_type
            )
            
            execution_time = time.time() - start_time
            
            if result:
                message = f"Mouse {click_type} click at ({final_coords.x}, {final_coords.y})"
                if coord_validation.warnings:
                    message += f" (adjusted from {x}, {y})"
                
                return SystemOperationResult(
                    OperationStatus.SUCCESS,
                    message,
                    data={'coordinates': final_coords, 'click_type': click_type},
                    execution_time=execution_time
                )
            else:
                return SystemOperationResult(
                    OperationStatus.FAILED,
                    f"Mouse click failed at ({final_coords.x}, {final_coords.y})",
                    execution_time=execution_time,
                    recovery_actions=[RecoveryAction.RETRY, RecoveryAction.ADJUST_PARAMETERS]
                )
                
        except Exception as e:
            return SystemOperationResult(
                OperationStatus.FAILED,
                f"Mouse click error: {str(e)}",
                execution_time=time.time() - start_time,
                recovery_actions=[RecoveryAction.RETRY],
                error_details=f"Exception: {type(e).__name__}: {str(e)}"
            )
    
    async def _execute_mouse_click(self, coordinates: ScreenCoordinates, click_type: str) -> bool:
        """Execute mouse click using AppleScript."""
        try:
            # Map click types to AppleScript commands
            click_commands = {
                'left': 'click',
                'right': 'right click',
                'double': 'double click'
            }
            
            if click_type not in click_commands:
                return False
            
            script = f'''
            tell application "System Events"
                {click_commands[click_type]} at {{{coordinates.x}, {coordinates.y}}}
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._operation_timeouts['interface_action']
            )
            
            return process.returncode == 0
            
        except asyncio.TimeoutError:
            return False
        except Exception:
            return False
    
    async def _retry_operation(self, operation_func, retry_strategy: RetryStrategy, *args) -> Any:
        """Generic retry mechanism for operations."""
        last_exception = None
        
        for attempt in range(retry_strategy.max_attempts):
            try:
                result = await asyncio.wait_for(
                    operation_func(*args),
                    timeout=retry_strategy.timeout
                )
                
                if result:  # Operation succeeded
                    return result
                    
            except Exception as e:
                last_exception = e
            
            # Don't delay after the last attempt
            if attempt < retry_strategy.max_attempts - 1:
                delay = retry_strategy.delay_base * (retry_strategy.delay_multiplier ** attempt)
                await asyncio.sleep(delay)
        
        return False
    
    def get_operation_status(self, operation_id: str) -> Optional[str]:
        """Get status of active operation."""
        if operation_id in self._active_operations:
            task = self._active_operations[operation_id]
            if task.done():
                return "completed"
            else:
                return "running"
        return None
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel active operation."""
        if operation_id in self._active_operations:
            task = self._active_operations[operation_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                return True
        return False


# Global system operation manager instance
system_manager = SystemOperationManager()


async def safe_file_copy(source: str, dest: str, overwrite: bool = False) -> bool:
    """Simple wrapper for file copy operations."""
    try:
        result = await system_manager.copy_file(source, dest, overwrite)
        return result.status == OperationStatus.SUCCESS
    except Exception:
        return False


async def safe_app_launch(app_id: str, wait: bool = True) -> bool:
    """Simple wrapper for application launch."""
    try:
        result = await system_manager.launch_application(app_id, wait)
        return result.status == OperationStatus.SUCCESS
    except Exception:
        return False


async def safe_mouse_click(x: int, y: int, click_type: str = "left") -> bool:
    """Simple wrapper for mouse click operations."""
    try:
        result = await system_manager.click_at_coordinates(x, y, click_type)
        return result.status == OperationStatus.SUCCESS
    except Exception:
        return False
