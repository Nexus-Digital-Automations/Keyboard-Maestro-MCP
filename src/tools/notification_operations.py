"""
Notification operations tools for macOS system notifications.

This module provides system notification capabilities with customizable sounds,
display options, and integration with macOS Notification Center.
"""

from typing import Optional, Dict, Any
import logging
import time

from fastmcp import FastMCP
from .core.communication_core import (
    CommunicationCore, CommunicationService, NotificationConfiguration
)
from src.contracts.decorators import requires, ensures
from src.core.km_interface import KMInterface

logger = logging.getLogger(__name__)


@requires(lambda title: len(title.strip()) > 0)
@requires(lambda message: len(message.strip()) > 0)
@ensures(lambda result: result["success"] or result["error"] is not None)
async def display_notification(
    title: str,
    message: str,
    subtitle: Optional[str] = None,
    sound: Optional[str] = None,
    duration: float = 5.0,
    style: str = "alert"
) -> Dict[str, Any]:
    """
    Display system notification through macOS Notification Center.
    
    Args:
        title: Notification title
        message: Main notification message
        subtitle: Optional subtitle text
        sound: Sound name or file path ("default", "none", or custom)
        duration: Display duration in seconds
        style: Notification style ("alert", "banner", "none")
    
    Returns:
        Dict with success status and notification details
    """
    start_time = time.time()
    
    try:
        # Get communication core instance
        from src.core.context_manager import get_communication_core
        comm_core = get_communication_core()
        
        # Check notification service availability
        notification_status = await comm_core.check_service_availability(CommunicationService.NOTIFICATION)
        
        if not notification_status.available:
            return {
                "success": False,
                "error": "Notification service not available",
                "error_code": "SERVICE_UNAVAILABLE",
                "error_details": notification_status.error_message
            }
        
        # Validate and sanitize inputs
        title = title.strip()[:256]  # Limit title length
        message = message.strip()[:512]  # Limit message length
        subtitle = subtitle.strip()[:256] if subtitle else None
        
        if duration < 0:
            duration = 5.0
        if duration > 60:
            duration = 60.0  # Max 60 seconds
        
        if style not in ["alert", "banner", "none"]:
            style = "alert"
        
        # Create notification configuration
        config = NotificationConfiguration(
            sound=sound,
            duration=duration,
            banner_style=style
        )
        
        # Send notification through Keyboard Maestro
        km_interface = get_km_interface()
        
        script = _build_notification_applescript(title, message, subtitle, config)
        result = await km_interface.execute_applescript(script)
        
        processing_time = time.time() - start_time
        
        if result.get("success", False):
            return {
                "success": True,
                "title": title,
                "message": message,
                "subtitle": subtitle,
                "sound": sound,
                "duration": duration,
                "style": style,
                "processing_time": processing_time,
                "notification_id": result.get("notification_id")
            }
        else:
            return {
                "success": False,
                "error": "Failed to display notification",
                "error_code": "DISPLAY_FAILED",
                "error_details": result.get("error", "Unknown error")
            }
    
    except Exception as e:
        logger.error(f"Notification display failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
            "processing_time": time.time() - start_time
        }


@requires(lambda title: len(title.strip()) > 0)
@requires(lambda message: len(message.strip()) > 0)
async def display_alert_dialog(
    title: str,
    message: str,
    buttons: Optional[List[str]] = None,
    default_button: Optional[str] = None,
    cancel_button: Optional[str] = None,
    icon: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display modal alert dialog with custom buttons.
    
    Args:
        title: Dialog title
        message: Dialog message
        buttons: List of button labels (default: ["OK"])
        default_button: Default button label
        cancel_button: Cancel button label
        icon: Icon type ("stop", "note", "caution", or file path)
    
    Returns:
        Dict with button clicked and dialog details
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        title = title.strip()[:256]
        message = message.strip()[:1024]
        
        if not buttons:
            buttons = ["OK"]
        
        # Limit to 3 buttons for macOS compatibility
        if len(buttons) > 3:
            buttons = buttons[:3]
        
        # Build and execute AppleScript
        km_interface = get_km_interface()
        script = _build_alert_dialog_applescript(title, message, buttons, default_button, cancel_button, icon)
        result = await km_interface.execute_applescript(script)
        
        processing_time = time.time() - start_time
        
        if result.get("success", False):
            return {
                "success": True,
                "title": title,
                "message": message,
                "buttons": buttons,
                "button_clicked": result.get("button_clicked"),
                "button_index": result.get("button_index", -1),
                "processing_time": processing_time
            }
        else:
            return {
                "success": False,
                "error": "Failed to display alert dialog",
                "error_code": "DIALOG_FAILED",
                "error_details": result.get("error", "Unknown error")
            }
    
    except Exception as e:
        logger.error(f"Alert dialog failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
            "processing_time": time.time() - start_time
        }


def _build_notification_applescript(
    title: str,
    message: str,
    subtitle: Optional[str],
    config: NotificationConfiguration
) -> str:
    """Build AppleScript for displaying system notification."""
    
    def escape_applescript_string(s: str) -> str:
        return s.replace('"', '\\"').replace('\\', '\\\\').replace('\n', '\\n')
    
    escaped_title = escape_applescript_string(title)
    escaped_message = escape_applescript_string(message)
    escaped_subtitle = escape_applescript_string(subtitle) if subtitle else ""
    
    # Build notification script
    script_parts = [
        'tell application "System Events"',
        f'    display notification "{escaped_message}"'
    ]
    
    # Add title
    script_parts.append(f'        with title "{escaped_title}"')
    
    # Add subtitle if provided
    if subtitle:
        script_parts.append(f'        subtitle "{escaped_subtitle}"')
    
    # Add sound if specified
    if config.sound and config.sound != "none":
        if config.sound == "default":
            script_parts.append('        sound name "default"')
        else:
            escaped_sound = escape_applescript_string(config.sound)
            script_parts.append(f'        sound name "{escaped_sound}"')
    
    script_parts.extend([
        '    return "success"',
        'end tell'
    ])
    
    return '\n'.join(script_parts)


def _build_alert_dialog_applescript(
    title: str,
    message: str,
    buttons: List[str],
    default_button: Optional[str],
    cancel_button: Optional[str],
    icon: Optional[str]
) -> str:
    """Build AppleScript for displaying alert dialog."""
    
    def escape_applescript_string(s: str) -> str:
        return s.replace('"', '\\"').replace('\\', '\\\\').replace('\n', '\\n')
    
    escaped_title = escape_applescript_string(title)
    escaped_message = escape_applescript_string(message)
    
    # Build button list
    button_list = "{" + ", ".join(f'"{escape_applescript_string(btn)}"' for btn in buttons) + "}"
    
    script_parts = [
        f'set dialogResult to display dialog "{escaped_message}"',
        f'    with title "{escaped_title}"',
        f'    buttons {button_list}'
    ]
    
    # Add default button if specified
    if default_button and default_button in buttons:
        escaped_default = escape_applescript_string(default_button)
        script_parts.append(f'    default button "{escaped_default}"')
    
    # Add cancel button if specified
    if cancel_button and cancel_button in buttons:
        escaped_cancel = escape_applescript_string(cancel_button)
        script_parts.append(f'    cancel button "{escaped_cancel}"')
    
    # Add icon if specified
    if icon:
        if icon in ["stop", "note", "caution"]:
            script_parts.append(f'    with icon {icon}')
        else:
            # Custom icon file path
            escaped_icon = escape_applescript_string(icon)
            script_parts.append(f'    with icon file "{escaped_icon}"')
    
    script_parts.extend([
        'set buttonClicked to button returned of dialogResult',
        'return buttonClicked'
    ])
    
    return '\n'.join(script_parts)


def register_notification_tools(mcp_server: FastMCP, communication_core: CommunicationCore) -> None:
    """Register notification operation tools with the FastMCP server."""
    
    @mcp_server.tool()
    async def km_display_notification(
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: Optional[str] = None,
        duration: float = 5.0,
        style: str = "alert"
    ) -> Dict[str, Any]:
        """
        Display system notification through macOS Notification Center.
        
        Supports customizable title, message, sound, and display duration.
        """
        return await display_notification(
            title=title,
            message=message,
            subtitle=subtitle,
            sound=sound,
            duration=duration,
            style=style
        )
    
    @mcp_server.tool()
    async def km_display_alert_dialog(
        title: str,
        message: str,
        buttons: Optional[List[str]] = None,
        default_button: Optional[str] = None,
        cancel_button: Optional[str] = None,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Display modal alert dialog with custom buttons.
        
        Returns which button was clicked by the user.
        """
        return await display_alert_dialog(
            title=title,
            message=message,
            buttons=buttons,
            default_button=default_button,
            cancel_button=cancel_button,
            icon=icon
        )
    
    @mcp_server.tool()
    async def km_check_notification_service(
    ) -> Dict[str, Any]:
        """
        Check notification service availability and capabilities.
        
        Returns service status and supported features.
        """
        try:
            status = await communication_core.check_service_availability(CommunicationService.NOTIFICATION)
            
            return {
                "available": status.available,
                "service": status.service.value,
                "capabilities": status.capabilities,
                "error_message": status.error_message
            }
        
        except Exception as e:
            logger.error(f"Error checking notification service: {e}")
            return {
                "available": False,
                "service": "notification",
                "error": str(e)
            }


# Legacy interface for backward compatibility
class NotificationOperationTools:
    """Notification operation tools class for backward compatibility."""
    
    def __init__(self, communication_core: CommunicationCore):
        """Initialize with communication core dependency."""
        self.communication_core = communication_core
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register notification tools with the MCP server."""
        register_notification_tools(mcp_server, self.communication_core)


# Convenience functions
def get_km_interface():
    """Get KM interface instance - would be properly injected in real implementation."""
    from src.core.context_manager import get_km_interface
    return get_km_interface()
