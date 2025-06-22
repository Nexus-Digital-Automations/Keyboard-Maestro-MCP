"""Application control MCP tools with defensive programming and error recovery.

This module provides MCP tools for application lifecycle management including launch,
quit, activation, and menu control with comprehensive validation and error handling.
"""

from typing import Dict, List, Optional, Any
from fastmcp import FastMCP, Context
import asyncio

from src.contracts.decorators import requires, ensures
from src.core.system_operations import system_manager, OperationStatus
from src.validators.system_validators import system_validator
from src.boundaries.permission_checker import permission_checker, PermissionType


class ApplicationControlTools:
    """MCP tools for application control with defensive programming."""
    
    def __init__(self, mcp_server: FastMCP):
        self.mcp = mcp_server
        self._register_tools()
    
    def _register_tools(self):
        """Register all application control MCP tools."""
        self.mcp.tool()(self.launch_application)
        self.mcp.tool()(self.quit_application)
        self.mcp.tool()(self.activate_application)
        self.mcp.tool()(self.force_quit_application)
        self.mcp.tool()(self.check_application_running)
        self.mcp.tool()(self.get_application_info)
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def launch_application(
        self,
        app_identifier: str,
        wait_for_launch: bool = True,
        timeout: int = 30,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Launch an application with comprehensive validation and monitoring.
        
        Args:
            app_identifier: Application bundle ID or name
            wait_for_launch: Whether to wait for app to fully launch
            timeout: Maximum time to wait for launch
            ctx: MCP context for logging and progress
            
        Returns:
            Dict with launch result and application info
        """
        try:
            if ctx:
                await ctx.info(f"Launching application: {app_identifier}")
            
            # Validate application identifier
            validation = system_validator.validate_application_identifier(app_identifier)
            if not validation.is_valid:
                error_msg = f"Application validation failed: {validation.error_message}"
                if ctx:
                    await ctx.error(error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "validation_error",
                    "recovery_suggestion": validation.recovery_suggestion
                }
            
            # Check permissions
            perm_result = permission_checker.check_permission(PermissionType.AUTOMATION)
            if perm_result.status.value != "granted":
                error_msg = f"Automation permission required: {perm_result.details}"
                if ctx:
                    await ctx.error(error_msg)
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "permission_denied",
                    "recovery_suggestion": perm_result.recovery_suggestion
                }
            
            if ctx:
                await ctx.report_progress(25, 100, "Validation complete, launching application")
            
            # Perform launch operation
            result = await system_manager.launch_application(
                validation.sanitized_input, wait_for_launch
            )
            
            if ctx:
                await ctx.report_progress(75, 100, "Launch command executed")
            
            if result.status == OperationStatus.SUCCESS:
                # Verify application is running if requested
                if wait_for_launch:
                    is_running = await self._verify_app_running(validation.sanitized_input)
                    if ctx:
                        await ctx.report_progress(100, 100, "Launch verification complete")
                    
                    return {
                        "success": True,
                        "message": result.message,
                        "application": validation.sanitized_input,
                        "is_running": is_running,
                        "execution_time": result.execution_time,
                        "waited_for_launch": wait_for_launch
                    }
                else:
                    if ctx:
                        await ctx.report_progress(100, 100, "Launch command completed")
                    
                    return {
                        "success": True,
                        "message": result.message,
                        "application": validation.sanitized_input,
                        "execution_time": result.execution_time,
                        "waited_for_launch": False
                    }
            else:
                if ctx:
                    await ctx.error(f"Application launch failed: {result.message}")
                
                return {
                    "success": False,
                    "error": result.message,
                    "error_type": result.status.value,
                    "application": validation.sanitized_input,
                    "execution_time": result.execution_time,
                    "recovery_actions": [action.name for action in result.recovery_actions]
                }
                
        except Exception as e:
            error_msg = f"Unexpected error launching application: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def quit_application(
        self,
        app_identifier: str,
        force: bool = False,
        timeout: int = 10,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Quit an application gracefully or forcefully.
        
        Args:
            app_identifier: Application bundle ID or name
            force: Whether to force quit if normal quit fails
            timeout: Maximum time to wait for quit
            ctx: MCP context for logging
            
        Returns:
            Dict with quit result and status
        """
        try:
            if ctx:
                await ctx.info(f"Quitting application: {app_identifier} (force={force})")
            
            # Validate application identifier
            validation = system_validator.validate_application_identifier(app_identifier)
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {validation.error_message}",
                    "error_type": "validation_error"
                }
            
            validated_app = validation.sanitized_input
            
            # Check if app is running first
            is_running = await self._verify_app_running(validated_app)
            if not is_running:
                if ctx:
                    await ctx.info("Application is not running")
                
                return {
                    "success": True,
                    "message": "Application is not running (no action needed)",
                    "application": validated_app,
                    "was_running": False
                }
            
            # Try normal quit first
            if ctx:
                await ctx.report_progress(25, 100, "Attempting normal quit")
            
            quit_result = await self._execute_quit(validated_app, force=False)
            
            if quit_result:
                # Wait briefly and verify quit
                await asyncio.sleep(1.0)
                still_running = await self._verify_app_running(validated_app)
                
                if not still_running:
                    if ctx:
                        await ctx.info("Application quit successfully")
                        await ctx.report_progress(100, 100, "Quit completed")
                    
                    return {
                        "success": True,
                        "message": f"Application quit successfully: {validated_app}",
                        "application": validated_app,
                        "method": "normal",
                        "was_running": True
                    }
            
            # If normal quit failed and force is requested
            if force:
                if ctx:
                    await ctx.report_progress(75, 100, "Normal quit failed, attempting force quit")
                
                force_result = await self._execute_quit(validated_app, force=True)
                
                if force_result:
                    await asyncio.sleep(0.5)
                    still_running = await self._verify_app_running(validated_app)
                    
                    if ctx:
                        await ctx.report_progress(100, 100, "Force quit completed")
                    
                    return {
                        "success": True,
                        "message": f"Application force quit: {validated_app}",
                        "application": validated_app,
                        "method": "force",
                        "was_running": True,
                        "still_running": still_running
                    }
            
            return {
                "success": False,
                "error": f"Failed to quit application: {validated_app}",
                "error_type": "quit_failed",
                "application": validated_app,
                "tried_force": force,
                "recovery_suggestions": [
                    "Try force quit if not already attempted",
                    "Check application for unsaved work"
                ]
            }
            
        except Exception as e:
            error_msg = f"Unexpected error quitting application: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_quit(self, app_identifier: str, force: bool = False) -> bool:
        """Execute application quit using AppleScript."""
        try:
            if force:
                # Force quit using System Events
                script = f'''
                tell application "System Events"
                    try
                        set appProcess to application process "{app_identifier}"
                        set visible of appProcess to false
                        tell appProcess to quit
                    on error
                        -- App may not be running
                    end try
                end tell
                '''
            else:
                # Normal quit
                if '.' in app_identifier and not app_identifier.endswith('.app'):
                    # Bundle ID format
                    script = f'''
                    tell application id "{app_identifier}"
                        try
                            quit
                        on error
                            -- App may not respond to quit
                        end try
                    end tell
                    '''
                else:
                    # Application name format
                    app_name = app_identifier.replace('.app', '')
                    script = f'''
                    tell application "{app_name}"
                        try
                            quit
                        on error
                            -- App may not respond to quit
                        end try
                    end tell
                    '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            return process.returncode == 0
            
        except Exception:
            return False
    
    async def _verify_app_running(self, app_identifier: str) -> bool:
        """Verify if application is currently running."""
        try:
            # Use System Events to check if process exists
            script = f'''
            tell application "System Events"
                try
                    return exists application process "{app_identifier}"
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
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3.0)
            
            if process.returncode == 0:
                return 'true' in stdout.decode().lower()
            
            return False
            
        except Exception:
            return False
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def activate_application(
        self,
        app_identifier: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Activate (bring to front) an application.
        
        Args:
            app_identifier: Application bundle ID or name
            ctx: MCP context for logging
            
        Returns:
            Dict with activation result
        """
        try:
            if ctx:
                await ctx.info(f"Activating application: {app_identifier}")
            
            validation = system_validator.validate_application_identifier(app_identifier)
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {validation.error_message}",
                    "error_type": "validation_error"
                }
            
            validated_app = validation.sanitized_input
            
            # Check if app is running
            is_running = await self._verify_app_running(validated_app)
            if not is_running:
                return {
                    "success": False,
                    "error": "Application is not running",
                    "error_type": "not_running",
                    "application": validated_app,
                    "recovery_suggestions": ["Launch application first"]
                }
            
            # Activate application
            success = await self._execute_activate(validated_app)
            
            if success:
                if ctx:
                    await ctx.info(f"Application activated: {validated_app}")
                
                return {
                    "success": True,
                    "message": f"Application activated: {validated_app}",
                    "application": validated_app
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to activate application: {validated_app}",
                    "error_type": "activation_failed",
                    "application": validated_app
                }
                
        except Exception as e:
            error_msg = f"Unexpected error activating application: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    async def _execute_activate(self, app_identifier: str) -> bool:
        """Execute application activation using AppleScript."""
        try:
            if '.' in app_identifier and not app_identifier.endswith('.app'):
                # Bundle ID format
                script = f'''
                tell application id "{app_identifier}"
                    activate
                end tell
                '''
            else:
                # Application name format
                app_name = app_identifier.replace('.app', '')
                script = f'''
                tell application "{app_name}"
                    activate
                end tell
                '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            return process.returncode == 0
            
        except Exception:
            return False
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def force_quit_application(
        self,
        app_identifier: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Force quit an application immediately.
        
        Args:
            app_identifier: Application bundle ID or name
            ctx: MCP context for logging
            
        Returns:
            Dict with force quit result
        """
        try:
            if ctx:
                await ctx.info(f"Force quitting application: {app_identifier}")
            
            return await self.quit_application(app_identifier, force=True, ctx=ctx)
            
        except Exception as e:
            error_msg = f"Unexpected error force quitting application: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def check_application_running(
        self,
        app_identifier: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Check if an application is currently running.
        
        Args:
            app_identifier: Application bundle ID or name
            ctx: MCP context for logging
            
        Returns:
            Dict with running status and details
        """
        try:
            validation = system_validator.validate_application_identifier(app_identifier)
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {validation.error_message}",
                    "error_type": "validation_error"
                }
            
            validated_app = validation.sanitized_input
            is_running = await self._verify_app_running(validated_app)
            
            if ctx:
                await ctx.info(f"Application running check: {validated_app} -> {is_running}")
            
            return {
                "success": True,
                "application": validated_app,
                "is_running": is_running,
                "status": "running" if is_running else "not_running"
            }
            
        except Exception as e:
            error_msg = f"Error checking application status: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }
    
    @requires(lambda app_identifier: isinstance(app_identifier, str) and len(app_identifier.strip()) > 0)
    async def get_application_info(
        self,
        app_identifier: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Get detailed information about an application.
        
        Args:
            app_identifier: Application bundle ID or name
            ctx: MCP context for logging
            
        Returns:
            Dict with application information
        """
        try:
            validation = system_validator.validate_application_identifier(app_identifier)
            if not validation.is_valid:
                return {
                    "success": False,
                    "error": f"Application validation failed: {validation.error_message}",
                    "error_type": "validation_error"
                }
            
            validated_app = validation.sanitized_input
            is_running = await self._verify_app_running(validated_app)
            
            app_info = {
                "success": True,
                "application": validated_app,
                "is_running": is_running,
                "identifier_type": "bundle_id" if '.' in validated_app else "name"
            }
            
            # Try to get additional info for running apps
            if is_running:
                try:
                    # Get process info using System Events
                    script = f'''
                    tell application "System Events"
                        try
                            set appProcess to application process "{validated_app}"
                            return {{visible of appProcess, frontmost of appProcess}}
                        on error
                            return {{false, false}}
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
                        if 'true' in output:
                            app_info["visible"] = 'true' in output.split(',')[0]
                            app_info["frontmost"] = 'true' in output.split(',')[1] if ',' in output else False
                        
                except Exception:
                    # Add basic info even if detailed query fails
                    app_info["visible"] = None
                    app_info["frontmost"] = None
            
            if ctx:
                await ctx.info(f"Retrieved info for application: {validated_app}")
            
            return app_info
            
        except Exception as e:
            error_msg = f"Error getting application info: {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected_error"
            }


def register_application_control_tools(mcp_server: FastMCP) -> ApplicationControlTools:
    """Register application control tools with MCP server."""
    return ApplicationControlTools(mcp_server)
