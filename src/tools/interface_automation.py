"""Interface automation MCP tools with coordinate validation and input safety.

This module provides MCP tools for mouse and keyboard automation with comprehensive
validation, safety checks, and error recovery mechanisms.
"""

from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP, Context
import asyncio
import re

from .contracts.decorators import requires, ensures
from src.core.system_operations import system_manager, OperationStatus
from src.validators.system_validators import system_validator
from src.boundaries.permission_checker import permission_checker, PermissionType
from src.utils.coordinate_utils import coordinate_validator, normalize_coordinates
from src.types.domain_types import ScreenCoordinates, ScreenArea


class InterfaceAutomationTools:
    """MCP tools for interface automation with defensive programming."""
    
    def __init__(self, mcp_server: FastMCP):
        self.mcp = mcp_server
        self._click_types = {"left", "right", "double", "middle"}
        self._key_modifiers = {"command", "option", "shift", "control", "fn"}
        self._register_tools()
    
    def _register_tools(self):
        """Register all interface automation MCP tools."""
        self.mcp.tool()(self.click_at_coordinates)
        self.mcp.tool()(self.drag_from_to)
        self.mcp.tool()(self.type_text)
        self.mcp.tool()(self.press_key)
        self.mcp.tool()(self.scroll_at_coordinates)
        self.mcp.tool()(self.get_mouse_position)
    
    @requires(lambda x: isinstance(x, int))
    @requires(lambda y: isinstance(y, int))
    async def click_at_coordinates(
        self,
        x: int,
        y: int,
        click_type: str = "left",
        delay_before: float = 0.0,
        delay_after: float = 0.1,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Perform mouse click at specified coordinates with validation.
        
        Args:
            x: X coordinate for click
            y: Y coordinate for click
            click_type: Type of click ("left", "right", "double", "middle")
            delay_before: Delay before click in seconds
            delay_after: Delay after click in seconds
            ctx: MCP context for logging
            
        Returns:
            Dict with click operation result
        """
        try:
            if ctx:
                await ctx.info(f"Performing {click_type} click at ({x}, {y})")
            
            # Validate click type
            if click_type not in self._click_types:
                return {
                    "success": False,
                    "error": f"Invalid click type: {click_type}",
                    "error_type": "validation_error",
                    "supported_types": list(self._click_types)
                }
            
            # Validate delays
            if delay_before < 0 or delay_after < 0:
                return {
                    "success": False,
                    "error": "Delays must be non-negative",
                    "error_type": "validation_error"
                }
            
            if delay_before > 5.0 or delay_after > 5.0:
                return {
                    "success": False,
                    "error": "Delays must be 5 seconds or less",
                    "error_type": "validation_error"
                }
            
            # Validate and normalize coordinates
            normalized_x, normalized_y = normalize_coordinates(x, y)
            coordinates_adjusted = (normalized_x != x or normalized_y != y)
            
            # Check permissions
            perm_result = permission_checker.check_permission(PermissionType.ACCESSIBILITY)
            if perm_result.status.value != "granted":
                return {
                    "success": False,
                    "error": f"Accessibility permission required: {perm_result.details}",
                    "error_type": "permission_denied",
                    "recovery_suggestion": perm_result.recovery_suggestion
                }
            
            if ctx:
                await ctx.report_progress(25, 100, "Validation complete, preparing click")
            
            # Apply pre-click delay
            if delay_before > 0:
                await asyncio.sleep(delay_before)
            
            # Perform click operation
            result = await system_manager.click_at_coordinates(normalized_x, normalized_y, click_type)
            
            if ctx:
                await ctx.report_progress(75, 100, "Click executed")
            
            # Apply post-click delay
            if delay_after > 0:
                await asyncio.sleep(delay_after)
            
            if ctx:
                await ctx.report_progress(100, 100, "Click operation complete")
            
            if result.status == OperationStatus.SUCCESS:
                message = f"{click_type.title()} click at ({normalized_x}, {normalized_y})"
                if coordinates_adjusted:
                    message += f" (adjusted from {x}, {y})"
                
                if ctx:
                    await ctx.info(f"Click successful: {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "coordinates": {"x": normalized_x, "y": normalized_y},
                    "click_type": click_type,
                    "coordinates_adjusted": coordinates_adjusted,
                    "execution_time": result.execution_time
                }
            else:
                if ctx:
                    await ctx.error(f"Click failed: {result.message}")
                
                return {
                    "success": False,
                    "error": result.message,
                    "error_type": result.status.value,
                    "coordinates": {"x": normalized_x, "y": normalized_y},
                    "click_type": click_type,
                    "execution_time": result.execution_time
                }
                
        except Exception as e:
            error_msg = f"Unexpected error performing click: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda start_x: isinstance(start_x, int))
    @requires(lambda start_y: isinstance(start_y, int))
    @requires(lambda end_x: isinstance(end_x, int))
    @requires(lambda end_y: isinstance(end_y, int))
    async def drag_from_to(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 1.0,
        button: str = "left",
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Perform drag operation from start to end coordinates.
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Duration of drag in seconds
            button: Mouse button to use ("left", "right")
            ctx: MCP context for logging
            
        Returns:
            Dict with drag operation result
        """
        try:
            if ctx:
                await ctx.info(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
            # Validate button type
            if button not in ["left", "right"]:
                return {
                    "success": False,
                    "error": f"Invalid button: {button}",
                    "error_type": "validation_error",
                    "supported_buttons": ["left", "right"]
                }
            
            # Validate duration
            if duration <= 0 or duration > 10.0:
                return {
                    "success": False,
                    "error": "Duration must be between 0 and 10 seconds",
                    "error_type": "validation_error"
                }
            
            # Normalize coordinates
            norm_start_x, norm_start_y = normalize_coordinates(start_x, start_y)
            norm_end_x, norm_end_y = normalize_coordinates(end_x, end_y)
            
            start_adjusted = (norm_start_x != start_x or norm_start_y != start_y)
            end_adjusted = (norm_end_x != end_x or norm_end_y != end_y)
            
            # Check permissions
            perm_result = permission_checker.check_permission(PermissionType.ACCESSIBILITY)
            if perm_result.status.value != "granted":
                return {
                    "success": False,
                    "error": f"Accessibility permission required: {perm_result.details}",
                    "error_type": "permission_denied"
                }
            
            # Execute drag operation
            success = await self._execute_drag(
                norm_start_x, norm_start_y, norm_end_x, norm_end_y, duration, button
            )
            
            if success:
                message = f"Drag from ({norm_start_x}, {norm_start_y}) to ({norm_end_x}, {norm_end_y})"
                adjustments = []
                if start_adjusted:
                    adjustments.append(f"start adjusted from ({start_x}, {start_y})")
                if end_adjusted:
                    adjustments.append(f"end adjusted from ({end_x}, {end_y})")
                if adjustments:
                    message += f" ({', '.join(adjustments)})"
                
                if ctx:
                    await ctx.info(f"Drag successful: {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "start_coordinates": {"x": norm_start_x, "y": norm_start_y},
                    "end_coordinates": {"x": norm_end_x, "y": norm_end_y},
                    "duration": duration,
                    "button": button,
                    "coordinates_adjusted": start_adjusted or end_adjusted
                }
            else:
                return {
                    "success": False,
                    "error": "Drag operation failed",
                    "error_type": "operation_failed"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error performing drag: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                           duration: float, button: str) -> bool:
        """Execute drag operation using AppleScript."""
        try:
            # AppleScript for drag operation
            script = f'''
            tell application "System Events"
                try
                    set startPoint to {{{start_x}, {start_y}}}
                    set endPoint to {{{end_x}, {end_y}}}
                    
                    -- Move to start position
                    set the clipboard to ""
                    delay 0.1
                    
                    -- Perform drag
                    tell (first process whose frontmost is true)
                        -- Mouse down at start
                        -- This is a simplified drag - real implementation would use
                        -- more sophisticated mouse control
                        key down "mouse button 1" at startPoint
                        delay {duration}
                        key up "mouse button 1" at endPoint
                    end tell
                    
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            # Note: This is a simplified drag implementation
            # Real implementation would use more sophisticated mouse control
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=duration + 5.0)
            
            return process.returncode == 0 and 'true' in stdout.decode().lower()
            
        except Exception:
            return False
    
    @requires(lambda text: isinstance(text, str))
    async def type_text(
        self,
        text: str,
        typing_speed: float = 0.05,
        clear_before: bool = False,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Type text with validation and safety checks.
        
        Args:
            text: Text to type
            typing_speed: Delay between characters in seconds
            clear_before: Whether to clear existing text first (Cmd+A, Delete)
            ctx: MCP context for logging
            
        Returns:
            Dict with typing operation result
        """
        try:
            if ctx:
                await ctx.info(f"Typing text: {len(text)} characters")
            
            # Validate text input
            text_validation = system_validator.validate_input_text(text, max_length=5000)
            if not text_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Text validation failed: {text_validation.error_message}",
                    "error_type": "validation_error",
                    "recovery_suggestion": text_validation.recovery_suggestion
                }
            
            sanitized_text = text_validation.sanitized_input
            
            # Validate typing speed
            if typing_speed < 0 or typing_speed > 1.0:
                return {
                    "success": False,
                    "error": "Typing speed must be between 0 and 1.0 seconds",
                    "error_type": "validation_error"
                }
            
            # Check permissions
            perm_result = permission_checker.check_permission(PermissionType.ACCESSIBILITY)
            if perm_result.status.value != "granted":
                return {
                    "success": False,
                    "error": f"Accessibility permission required: {perm_result.details}",
                    "error_type": "permission_denied"
                }
            
            if ctx:
                await ctx.report_progress(25, 100, "Starting text input")
            
            # Clear existing text if requested
            if clear_before:
                await self._execute_key_combination(["command"], "a")
                await asyncio.sleep(0.1)
                await self._execute_key_combination([], "delete")
                await asyncio.sleep(0.1)
            
            # Type the text
            success = await self._execute_text_typing(sanitized_text, typing_speed)
            
            if ctx:
                await ctx.report_progress(100, 100, "Text input complete")
            
            if success:
                message = f"Typed {len(sanitized_text)} characters"
                if text_validation.warnings:
                    message += f" (text sanitized: {', '.join(text_validation.warnings)})"
                
                if ctx:
                    await ctx.info(f"Text typing successful: {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "character_count": len(sanitized_text),
                    "typing_speed": typing_speed,
                    "cleared_before": clear_before,
                    "text_sanitized": bool(text_validation.warnings)
                }
            else:
                return {
                    "success": False,
                    "error": "Text typing failed",
                    "error_type": "operation_failed"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error typing text: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_text_typing(self, text: str, typing_speed: float) -> bool:
        """Execute text typing using AppleScript."""
        try:
            # Escape text for AppleScript
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
            
            script = f'''
            tell application "System Events"
                try
                    keystroke "{escaped_text}"
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Calculate timeout based on text length and typing speed
            timeout = max(10.0, len(text) * typing_speed + 5.0)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            return process.returncode == 0 and 'true' in stdout.decode().lower()
            
        except Exception:
            return False
    
    @requires(lambda key: isinstance(key, str) and len(key) > 0)
    async def press_key(
        self,
        key: str,
        modifiers: Optional[List[str]] = None,
        repeat_count: int = 1,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Press key or key combination with validation.
        
        Args:
            key: Key to press (e.g., "return", "tab", "escape", "a")
            modifiers: List of modifier keys ("command", "option", "shift", "control")
            repeat_count: Number of times to repeat the key press
            ctx: MCP context for logging
            
        Returns:
            Dict with key press operation result
        """
        try:
            if ctx:
                await ctx.info(f"Pressing key: {key} with modifiers: {modifiers}")
            
            # Validate key
            if not key or len(key.strip()) == 0:
                return {
                    "success": False,
                    "error": "Key cannot be empty",
                    "error_type": "validation_error"
                }
            
            # Validate modifiers
            if modifiers:
                invalid_modifiers = set(modifiers) - self._key_modifiers
                if invalid_modifiers:
                    return {
                        "success": False,
                        "error": f"Invalid modifiers: {invalid_modifiers}",
                        "error_type": "validation_error",
                        "supported_modifiers": list(self._key_modifiers)
                    }
            
            # Validate repeat count
            if repeat_count < 1 or repeat_count > 100:
                return {
                    "success": False,
                    "error": "Repeat count must be between 1 and 100",
                    "error_type": "validation_error"
                }
            
            # Check for dangerous key combinations
            if self._is_dangerous_key_combo(key, modifiers or []):
                return {
                    "success": False,
                    "error": "Dangerous key combination blocked",
                    "error_type": "safety_violation",
                    "recovery_suggestion": "Use safer key combinations"
                }
            
            # Execute key presses
            success_count = 0
            for i in range(repeat_count):
                success = await self._execute_key_combination(modifiers or [], key)
                if success:
                    success_count += 1
                
                # Small delay between repeats
                if i < repeat_count - 1:
                    await asyncio.sleep(0.1)
            
            if success_count == repeat_count:
                modifier_text = f" with {', '.join(modifiers)}" if modifiers else ""
                repeat_text = f" (repeated {repeat_count}x)" if repeat_count > 1 else ""
                message = f"Key pressed: {key}{modifier_text}{repeat_text}"
                
                if ctx:
                    await ctx.info(f"Key press successful: {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "key": key,
                    "modifiers": modifiers or [],
                    "repeat_count": repeat_count,
                    "successful_presses": success_count
                }
            else:
                return {
                    "success": False,
                    "error": f"Key press partially failed: {success_count}/{repeat_count} successful",
                    "error_type": "partial_failure",
                    "successful_presses": success_count
                }
                
        except Exception as e:
            error_msg = f"Unexpected error pressing key: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    def _is_dangerous_key_combo(self, key: str, modifiers: List[str]) -> bool:
        """Check if key combination could be dangerous."""
        dangerous_combos = [
            # System shortcuts that could cause issues
            (["command", "option"], "escape"),  # Force quit
            (["command", "shift"], "q"),       # Quit all
            (["command", "option", "shift"], "escape"),  # Force quit dialog
        ]
        
        for danger_mods, danger_key in dangerous_combos:
            if (set(modifiers) == set(danger_mods) and 
                key.lower() == danger_key.lower()):
                return True
        
        return False
    
    async def _execute_key_combination(self, modifiers: List[str], key: str) -> bool:
        """Execute key combination using AppleScript."""
        try:
            # Build modifier string
            modifier_parts = []
            for modifier in modifiers:
                modifier_parts.append(f"{modifier} down")
            
            modifier_string = " using {" + ", ".join(modifier_parts) + "}" if modifier_parts else ""
            
            script = f'''
            tell application "System Events"
                try
                    key code (key code of "{key}"){modifier_string}
                    return true
                on error
                    try
                        keystroke "{key}"{modifier_string}
                        return true
                    on error
                        return false
                    end try
                end try
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            
            return process.returncode == 0 and 'true' in stdout.decode().lower()
            
        except Exception:
            return False
    
    @requires(lambda x: isinstance(x, int))
    @requires(lambda y: isinstance(y, int))
    async def scroll_at_coordinates(
        self,
        x: int,
        y: int,
        scroll_units: int,
        direction: str = "down",
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Perform scroll operation at specified coordinates.
        
        Args:
            x: X coordinate for scroll location
            y: Y coordinate for scroll location
            scroll_units: Number of scroll units (positive integer)
            direction: Scroll direction ("up", "down", "left", "right")
            ctx: MCP context for logging
            
        Returns:
            Dict with scroll operation result
        """
        try:
            if ctx:
                await ctx.info(f"Scrolling {direction} {scroll_units} units at ({x}, {y})")
            
            # Validate direction
            valid_directions = {"up", "down", "left", "right"}
            if direction not in valid_directions:
                return {
                    "success": False,
                    "error": f"Invalid direction: {direction}",
                    "error_type": "validation_error",
                    "supported_directions": list(valid_directions)
                }
            
            # Validate scroll units
            if scroll_units <= 0 or scroll_units > 50:
                return {
                    "success": False,
                    "error": "Scroll units must be between 1 and 50",
                    "error_type": "validation_error"
                }
            
            # Normalize coordinates
            norm_x, norm_y = normalize_coordinates(x, y)
            coordinates_adjusted = (norm_x != x or norm_y != y)
            
            # Execute scroll
            success = await self._execute_scroll(norm_x, norm_y, scroll_units, direction)
            
            if success:
                message = f"Scrolled {direction} {scroll_units} units at ({norm_x}, {norm_y})"
                if coordinates_adjusted:
                    message += f" (adjusted from {x}, {y})"
                
                if ctx:
                    await ctx.info(f"Scroll successful: {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "coordinates": {"x": norm_x, "y": norm_y},
                    "scroll_units": scroll_units,
                    "direction": direction,
                    "coordinates_adjusted": coordinates_adjusted
                }
            else:
                return {
                    "success": False,
                    "error": "Scroll operation failed",
                    "error_type": "operation_failed"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error scrolling: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_scroll(self, x: int, y: int, units: int, direction: str) -> bool:
        """Execute scroll operation using AppleScript."""
        try:
            # Map direction to scroll values
            if direction == "up":
                scroll_x, scroll_y = 0, units
            elif direction == "down":
                scroll_x, scroll_y = 0, -units
            elif direction == "left":
                scroll_x, scroll_y = units, 0
            else:  # right
                scroll_x, scroll_y = -units, 0
            
            script = f'''
            tell application "System Events"
                try
                    scroll at {{{x}, {y}}} by {{{scroll_x}, {scroll_y}}}
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            
            return process.returncode == 0 and 'true' in stdout.decode().lower()
            
        except Exception:
            return False
    
    async def get_mouse_position(
        self,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Get current mouse cursor position.
        
        Args:
            ctx: MCP context for logging
            
        Returns:
            Dict with current mouse position
        """
        try:
            if ctx:
                await ctx.info("Getting current mouse position")
            
            position = await self._get_current_mouse_position()
            
            if position:
                if ctx:
                    await ctx.info(f"Mouse position: {position}")
                
                return {
                    "success": True,
                    "position": position,
                    "x": position["x"],
                    "y": position["y"]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to get mouse position",
                    "error_type": "operation_failed"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error getting mouse position: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _get_current_mouse_position(self) -> Optional[Dict[str, int]]:
        """Get current mouse position using AppleScript."""
        try:
            script = '''
            tell application "System Events"
                try
                    set mousePos to (current mouse position)
                    return "{" & (item 1 of mousePos) & ", " & (item 2 of mousePos) & "}"
                on error
                    return "error"
                end try
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3.0)
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                if output != "error" and "{" in output:
                    # Parse position from output like "{123, 456}"
                    pos_str = output.strip('{}')
                    if ', ' in pos_str:
                        x_str, y_str = pos_str.split(', ')
                        return {"x": int(x_str.strip()), "y": int(y_str.strip())}
            
            return None
            
        except Exception:
            return None


def register_interface_automation_tools(mcp_server: FastMCP) -> InterfaceAutomationTools:
    """Register interface automation tools with MCP server."""
    return InterfaceAutomationTools(mcp_server)
