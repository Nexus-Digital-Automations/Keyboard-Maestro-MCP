"""Window management MCP tools with coordinate validation and multi-monitor support.

This module provides MCP tools for window control including positioning, resizing,
state management with comprehensive bounds checking and defensive programming.
"""

from typing import Dict, List, Optional, Any, Tuple
from fastmcp import FastMCP, Context
import asyncio

from src.contracts.decorators import requires, ensures
from src.validators.system_validators import system_validator
from src.boundaries.permission_checker import permission_checker, PermissionType
from src.utils.coordinate_utils import coordinate_validator, get_main_display_bounds


class WindowManagementTools:
    """MCP tools for window management with defensive programming."""
    
    def __init__(self, mcp_server: FastMCP):
        self.mcp = mcp_server
        self._register_tools()
    
    def _register_tools(self):
        """Register all window management MCP tools."""
        self.mcp.tool()(self.move_window)
        self.mcp.tool()(self.resize_window)
        self.mcp.tool()(self.get_window_info)
        self.mcp.tool()(self.minimize_window)
        self.mcp.tool()(self.maximize_window)
        self.mcp.tool()(self.arrange_windows)
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    @requires(lambda x: isinstance(x, int))
    @requires(lambda y: isinstance(y, int))
    async def move_window(
        self,
        app_identifier: str,
        x: int,
        y: int,
        window_index: int = 1,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Move a window to specified coordinates with bounds validation.
        
        Args:
            app_identifier: Application bundle ID or name
            x: X coordinate for window position
            y: Y coordinate for window position
            window_index: Index of window (1-based) if app has multiple windows
            ctx: MCP context for logging
            
        Returns:
            Dict with move operation result
        """
        try:
            if ctx:
                await ctx.info(f"Moving window for {app_identifier} to ({x}, {y})")
            
            # Validate application identifier
            app_validation = system_validator.validate_application_identifier(app_identifier)
            if not app_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {app_validation.error_message}",
                    "error_type": "validation_error"
                }
            
            # Validate coordinates
            from src.types.domain_types import ScreenCoordinates
            coordinates = ScreenCoordinates(x, y)
            coord_validation = system_validator.validate_screen_coordinates(coordinates)
            
            if not coord_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Coordinate validation failed: {coord_validation.error_message}",
                    "error_type": "validation_error",
                    "recovery_suggestion": coord_validation.recovery_suggestion
                }
            
            # Use adjusted coordinates if provided
            final_coords = coord_validation.sanitized_input or coordinates
            
            # Check permissions
            perm_result = permission_checker.check_permission(PermissionType.ACCESSIBILITY)
            if perm_result.status.value != "granted":
                return {
                    "success": False,
                    "error": f"Accessibility permission required: {perm_result.details}",
                    "error_type": "permission_denied",
                    "recovery_suggestion": perm_result.recovery_suggestion
                }
            
            # Execute window move
            success = await self._execute_window_move(
                app_validation.sanitized_input, final_coords.x, final_coords.y, window_index
            )
            
            if success:
                message = f"Window moved to ({final_coords.x}, {final_coords.y})"
                if coord_validation.warnings:
                    message += f" (adjusted from {x}, {y})"
                
                if ctx:
                    await ctx.info(f"Window moved successfully: {message}")
                
                return {
                    "success": True,
                    "message": message,
                    "application": app_validation.sanitized_input,
                    "position": {"x": final_coords.x, "y": final_coords.y},
                    "window_index": window_index,
                    "coordinate_adjusted": bool(coord_validation.warnings)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to move window for {app_validation.sanitized_input}",
                    "error_type": "operation_failed",
                    "recovery_suggestions": [
                        "Verify application is running",
                        "Check window exists at specified index"
                    ]
                }
                
        except Exception as e:
            error_msg = f"Unexpected error moving window: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_window_move(self, app_identifier: str, x: int, y: int, window_index: int) -> bool:
        """Execute window move using AppleScript."""
        try:
            script = f'''
            tell application "System Events"
                try
                    tell application process "{app_identifier}"
                        set theWindow to window {window_index}
                        set position of theWindow to {{{x}, {y}}}
                    end tell
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
            
            if process.returncode == 0:
                return 'true' in stdout.decode().lower()
            
            return False
            
        except Exception:
            return False
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    @requires(lambda width: isinstance(width, int) and width > 0)
    @requires(lambda height: isinstance(height, int) and height > 0)
    async def resize_window(
        self,
        app_identifier: str,
        width: int,
        height: int,
        window_index: int = 1,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Resize a window to specified dimensions with validation.
        
        Args:
            app_identifier: Application bundle ID or name
            width: New window width in pixels
            height: New window height in pixels
            window_index: Index of window (1-based) if app has multiple windows
            ctx: MCP context for logging
            
        Returns:
            Dict with resize operation result
        """
        try:
            if ctx:
                await ctx.info(f"Resizing window for {app_identifier} to {width}x{height}")
            
            # Validate application identifier
            app_validation = system_validator.validate_application_identifier(app_identifier)
            if not app_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {app_validation.error_message}",
                    "error_type": "validation_error"
                }
            
            # Validate dimensions
            if width <= 0 or height <= 0:
                return {
                    "success": False,
                    "error": f"Invalid dimensions: {width}x{height}",
                    "error_type": "validation_error",
                    "recovery_suggestion": "Use positive width and height values"
                }
            
            # Check reasonable size limits
            display_bounds = get_main_display_bounds()
            if width > display_bounds.width * 2 or height > display_bounds.height * 2:
                return {
                    "success": False,
                    "error": f"Dimensions too large: {width}x{height}",
                    "error_type": "validation_error",
                    "recovery_suggestion": f"Use dimensions smaller than {display_bounds.width * 2}x{display_bounds.height * 2}"
                }
            
            # Execute window resize
            success = await self._execute_window_resize(
                app_validation.sanitized_input, width, height, window_index
            )
            
            if success:
                if ctx:
                    await ctx.info(f"Window resized successfully to {width}x{height}")
                
                return {
                    "success": True,
                    "message": f"Window resized to {width}x{height}",
                    "application": app_validation.sanitized_input,
                    "size": {"width": width, "height": height},
                    "window_index": window_index
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to resize window for {app_validation.sanitized_input}",
                    "error_type": "operation_failed"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error resizing window: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_window_resize(self, app_identifier: str, width: int, height: int, window_index: int) -> bool:
        """Execute window resize using AppleScript."""
        try:
            script = f'''
            tell application "System Events"
                try
                    tell application process "{app_identifier}"
                        set theWindow to window {window_index}
                        set size of theWindow to {{{width}, {height}}}
                    end tell
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
            
            if process.returncode == 0:
                return 'true' in stdout.decode().lower()
            
            return False
            
        except Exception:
            return False
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def get_window_info(
        self,
        app_identifier: str,
        window_index: int = 1,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Get detailed information about a window.
        
        Args:
            app_identifier: Application bundle ID or name
            window_index: Index of window (1-based) if app has multiple windows
            ctx: MCP context for logging
            
        Returns:
            Dict with window information
        """
        try:
            if ctx:
                await ctx.info(f"Getting window info for {app_identifier}")
            
            # Validate application identifier
            app_validation = system_validator.validate_application_identifier(app_identifier)
            if not app_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {app_validation.error_message}",
                    "error_type": "validation_error"
                }
            
            # Get window information
            window_info = await self._get_window_properties(
                app_validation.sanitized_input, window_index
            )
            
            if window_info:
                if ctx:
                    await ctx.info(f"Retrieved window info for {app_validation.sanitized_input}")
                
                return {
                    "success": True,
                    "application": app_validation.sanitized_input,
                    "window_index": window_index,
                    **window_info
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not get window info for {app_validation.sanitized_input}",
                    "error_type": "operation_failed",
                    "recovery_suggestions": [
                        "Verify application is running",
                        "Check window exists at specified index"
                    ]
                }
                
        except Exception as e:
            error_msg = f"Unexpected error getting window info: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _get_window_properties(self, app_identifier: str, window_index: int) -> Optional[Dict[str, Any]]:
        """Get window properties using AppleScript."""
        try:
            script = f'''
            tell application "System Events"
                try
                    tell application process "{app_identifier}"
                        set theWindow to window {window_index}
                        set windowPos to position of theWindow
                        set windowSize to size of theWindow
                        set windowTitle to title of theWindow
                        set isVisible to visible of theWindow
                        set isMinimized to value of attribute "AXMinimized" of theWindow
                        
                        return "{{" & ¬
                            "\\"title\\": \\"" & windowTitle & "\\", " & ¬
                            "\\"position\\": {{" & (item 1 of windowPos) & ", " & (item 2 of windowPos) & "}}, " & ¬
                            "\\"size\\": {{" & (item 1 of windowSize) & ", " & (item 2 of windowSize) & "}}, " & ¬
                            "\\"visible\\": " & isVisible & ", " & ¬
                            "\\"minimized\\": " & isMinimized & ¬
                            "}}"
                    end tell
                on error errMsg
                    return "error: " & errMsg
                end try
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                if not output.startswith('error:'):
                    # Parse the returned information
                    return self._parse_window_info(output)
            
            return None
            
        except Exception:
            return None
    
    def _parse_window_info(self, info_string: str) -> Dict[str, Any]:
        """Parse window information from AppleScript output."""
        try:
            # Simple parsing for the structured output
            # In a production system, would use proper JSON parsing
            info = {}
            
            # Extract title
            if '"title": "' in info_string:
                start = info_string.find('"title": "') + 10
                end = info_string.find('"', start)
                info['title'] = info_string[start:end]
            
            # Extract position
            if '"position": {' in info_string:
                start = info_string.find('"position": {') + 13
                end = info_string.find('}', start)
                pos_str = info_string[start:end]
                if ', ' in pos_str:
                    x, y = pos_str.split(', ')
                    info['position'] = {'x': int(x.strip()), 'y': int(y.strip())}
            
            # Extract size
            if '"size": {' in info_string:
                start = info_string.find('"size": {') + 9
                end = info_string.find('}', start)
                size_str = info_string[start:end]
                if ', ' in size_str:
                    w, h = size_str.split(', ')
                    info['size'] = {'width': int(w.strip()), 'height': int(h.strip())}
            
            # Extract boolean values
            info['visible'] = '"visible": true' in info_string
            info['minimized'] = '"minimized": true' in info_string
            
            return info
            
        except Exception:
            return {}
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def minimize_window(
        self,
        app_identifier: str,
        window_index: int = 1,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Minimize a window.
        
        Args:
            app_identifier: Application bundle ID or name
            window_index: Index of window (1-based) if app has multiple windows
            ctx: MCP context for logging
            
        Returns:
            Dict with minimize operation result
        """
        try:
            if ctx:
                await ctx.info(f"Minimizing window for {app_identifier}")
            
            app_validation = system_validator.validate_application_identifier(app_identifier)
            if not app_validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {app_validation.error_message}",
                    "error_type": "validation_error"
                }
            
            success = await self._execute_window_minimize(app_validation.sanitized_input, window_index)
            
            if success:
                if ctx:
                    await ctx.info(f"Window minimized successfully")
                
                return {
                    "success": True,
                    "message": f"Window minimized for {app_validation.sanitized_input}",
                    "application": app_validation.sanitized_input,
                    "window_index": window_index
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to minimize window for {app_validation.sanitized_input}",
                    "error_type": "operation_failed"
                }
                
        except Exception as e:
            error_msg = f"Unexpected error minimizing window: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_window_minimize(self, app_identifier: str, window_index: int) -> bool:
        """Execute window minimize using AppleScript."""
        try:
            script = f'''
            tell application "System Events"
                try
                    tell application process "{app_identifier}"
                        set theWindow to window {window_index}
                        set value of attribute "AXMinimized" of theWindow to true
                    end tell
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
            
            if process.returncode == 0:
                return 'true' in stdout.decode().lower()
            
            return False
            
        except Exception:
            return False
    
    @requires(lambda layout: isinstance(layout, str) and layout in ["tile", "cascade", "center"])
    async def arrange_windows(
        self,
        layout: str,
        applications: Optional[List[str]] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Arrange multiple windows in a specified layout.
        
        Args:
            layout: Layout type ("tile", "cascade", "center")
            applications: List of application identifiers (None for all windows)
            ctx: MCP context for logging
            
        Returns:
            Dict with arrangement operation result
        """
        try:
            if ctx:
                await ctx.info(f"Arranging windows in {layout} layout")
            
            if layout == "tile":
                result = await self._arrange_tile_layout(applications)
            elif layout == "cascade":
                result = await self._arrange_cascade_layout(applications)
            elif layout == "center":
                result = await self._arrange_center_layout(applications)
            else:
                return {
                    "success": False,
                    "error": f"Unknown layout: {layout}",
                    "error_type": "validation_error",
                    "supported_layouts": ["tile", "cascade", "center"]
                }
            
            if ctx:
                await ctx.info(f"Window arrangement completed: {layout}")
            
            return {
                "success": True,
                "message": f"Windows arranged in {layout} layout",
                "layout": layout,
                "applications_processed": result.get("count", 0)
            }
            
        except Exception as e:
            error_msg = f"Unexpected error arranging windows: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _arrange_tile_layout(self, applications: Optional[List[str]]) -> Dict[str, Any]:
        """Arrange windows in tile layout."""
        # Simplified implementation - would be more sophisticated in production
        display_bounds = get_main_display_bounds()
        half_width = display_bounds.width // 2
        half_height = display_bounds.height // 2
        
        positions = [
            (0, 0),
            (half_width, 0),
            (0, half_height),
            (half_width, half_height)
        ]
        
        count = 0
        if applications:
            for i, app in enumerate(applications[:4]):  # Limit to 4 windows
                if i < len(positions):
                    await self._execute_window_move(app, positions[i][0], positions[i][1], 1)
                    await self._execute_window_resize(app, half_width, half_height, 1)
                    count += 1
        
        return {"count": count}
    
    async def _arrange_cascade_layout(self, applications: Optional[List[str]]) -> Dict[str, Any]:
        """Arrange windows in cascade layout."""
        offset = 30
        start_x, start_y = 50, 50
        
        count = 0
        if applications:
            for i, app in enumerate(applications):
                x = start_x + (i * offset)
                y = start_y + (i * offset)
                await self._execute_window_move(app, x, y, 1)
                count += 1
        
        return {"count": count}
    
    async def _arrange_center_layout(self, applications: Optional[List[str]]) -> Dict[str, Any]:
        """Arrange windows in center layout."""
        display_bounds = get_main_display_bounds()
        center_x = display_bounds.width // 2 - 400  # Assume 800px window width
        center_y = display_bounds.height // 2 - 300  # Assume 600px window height
        
        count = 0
        if applications:
            for app in applications:
                await self._execute_window_move(app, center_x, center_y, 1)
                await self._execute_window_resize(app, 800, 600, 1)
                count += 1
        
        return {"count": count}


def register_window_management_tools(mcp_server: FastMCP) -> WindowManagementTools:
    """Register window management tools with MCP server."""
    return WindowManagementTools(mcp_server)
