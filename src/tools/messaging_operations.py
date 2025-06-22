"""
Messaging operations tools for SMS and iMessage through Keyboard Maestro.

This module provides SMS and iMessage sending capabilities with service detection,
recipient validation, and intelligent service selection.
"""

from typing import Optional, List, Dict, Any
import logging
import asyncio
import time

from fastmcp import FastMCP
from src.core.communication_core import (
    CommunicationCore, CommunicationService, CommunicationResult,
    MessagingConfiguration
)
from src.contracts.decorators import requires, ensures
from src.core.km_interface import KMInterface

logger = logging.getLogger(__name__)


@requires(lambda recipient: len(recipient.strip()) > 0)
@requires(lambda message: len(message.strip()) > 0)
@ensures(lambda result: result["success"] or result["error"] is not None)
async def send_message(
    recipient: str,
    message: str,
    service: Optional[str] = None,
    fallback_to_sms: bool = True,
    delivery_confirmation: bool = False
) -> Dict[str, Any]:
    """
    Send SMS or iMessage through macOS Messages app.
    
    Args:
        recipient: Phone number or email address
        message: Message content
        service: Preferred service ("sms", "imessage", or "auto")
        fallback_to_sms: Whether to fall back to SMS if iMessage fails
        delivery_confirmation: Request delivery confirmation if supported
    
    Returns:
        Dict with success status, service used, and delivery information
    """
    start_time = time.time()
    
    try:
        # Get communication core instance
        from src.core.context_manager import get_communication_core
        comm_core = get_communication_core()
        
        # Validate recipient format
        from src.validators.input_validators import is_valid_phone_number, is_valid_email
        
        if not (is_valid_phone_number(recipient) or is_valid_email(recipient)):
            return {
                "success": False,
                "error": "Invalid recipient format",
                "error_code": "INVALID_RECIPIENT",
                "recipient": recipient
            }
        
        # Determine service to use
        if service == "auto" or service is None:
            detected_service = await comm_core.detect_message_service(recipient)
        elif service == "sms":
            detected_service = CommunicationService.SMS
        elif service == "imessage":
            detected_service = CommunicationService.IMESSAGE
        else:
            return {
                "success": False,
                "error": f"Unknown service: {service}",
                "error_code": "INVALID_SERVICE"
            }
        
        # Check service availability
        service_status = await comm_core.check_service_availability(detected_service)
        
        if not service_status.available:
            if fallback_to_sms and detected_service == CommunicationService.IMESSAGE:
                # Try SMS fallback
                sms_status = await comm_core.check_service_availability(CommunicationService.SMS)
                if sms_status.available:
                    detected_service = CommunicationService.SMS
                    service_status = sms_status
                else:
                    return {
                        "success": False,
                        "error": "No messaging services available",
                        "error_code": "NO_SERVICE_AVAILABLE",
                        "attempted_services": ["imessage", "sms"]
                    }
            else:
                return {
                    "success": False,
                    "error": f"{detected_service.value} service not available",
                    "error_code": "SERVICE_UNAVAILABLE",
                    "service": detected_service.value
                }
        
        # Format message for service
        formatted_message = await comm_core.format_message_content(message, detected_service)
        if len(formatted_message) != len(message):
            logger.warning(f"Message truncated for {detected_service.value}: {len(message)} -> {len(formatted_message)}")
        
        # Send message through Keyboard Maestro
        km_interface = get_km_interface()
        
        script = _build_message_applescript(recipient, formatted_message, detected_service)
        result = await km_interface.execute_applescript(script)
        
        processing_time = time.time() - start_time
        
        if result.get("success", False):
            return {
                "success": True,
                "recipient": recipient,
                "message": formatted_message,
                "service_used": detected_service.value,
                "message_truncated": len(formatted_message) != len(message),
                "original_length": len(message),
                "sent_length": len(formatted_message),
                "processing_time": processing_time,
                "delivery_status": "sent"
            }
        else:
            # Try fallback if configured and original attempt failed
            if (fallback_to_sms and 
                detected_service == CommunicationService.IMESSAGE and 
                not result.get("success", False)):
                
                sms_status = await comm_core.check_service_availability(CommunicationService.SMS)
                if sms_status.available:
                    sms_script = _build_message_applescript(recipient, formatted_message, CommunicationService.SMS)
                    sms_result = await km_interface.execute_applescript(sms_script)
                    
                    if sms_result.get("success", False):
                        return {
                            "success": True,
                            "recipient": recipient,
                            "message": formatted_message,
                            "service_used": "sms",
                            "service_fallback": True,
                            "original_service_attempted": "imessage",
                            "processing_time": time.time() - start_time,
                            "delivery_status": "sent"
                        }
            
            return {
                "success": False,
                "error": "Failed to send message",
                "error_code": "SEND_FAILED",
                "error_details": result.get("error", "Unknown error"),
                "service_attempted": detected_service.value
            }
    
    except Exception as e:
        logger.error(f"Message sending failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
            "processing_time": time.time() - start_time
        }


def _build_message_applescript(recipient: str, message: str, service: CommunicationService) -> str:
    """Build AppleScript for sending message through Messages app."""
    
    def escape_applescript_string(s: str) -> str:
        return s.replace('"', '\\"').replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')
    
    escaped_recipient = escape_applescript_string(recipient)
    escaped_message = escape_applescript_string(message)
    
    # Different approaches for SMS vs iMessage
    if service == CommunicationService.SMS:
        script = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = SMS
            set targetBuddy to buddy "{escaped_recipient}" of targetService
            send "{escaped_message}" to targetBuddy
            return "success"
        end tell
        '''
    else:  # iMessage
        script = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{escaped_recipient}" of targetService
            send "{escaped_message}" to targetBuddy
            return "success"
        end tell
        '''
    
    return script.strip()


def register_messaging_tools(mcp_server: FastMCP, communication_core: CommunicationCore) -> None:
    """Register messaging operation tools with the FastMCP server."""
    
    @mcp_server.tool()
    async def km_send_message(
        recipient: str,
        message: str,
        service: Optional[str] = None,
        fallback_to_sms: bool = True,
        delivery_confirmation: bool = False
    ) -> Dict[str, Any]:
        """
        Send SMS or iMessage through macOS Messages app.
        
        Automatically detects the best service for the recipient unless specified.
        Supports fallback from iMessage to SMS if configured.
        """
        return await send_message(
            recipient=recipient,
            message=message,
            service=service,
            fallback_to_sms=fallback_to_sms,
            delivery_confirmation=delivery_confirmation
        )
    
    @mcp_server.tool()
    async def km_check_messaging_services(
    ) -> Dict[str, Any]:
        """
        Check availability of SMS and iMessage services.
        
        Returns status and capabilities for both messaging services.
        """
        try:
            sms_status = await communication_core.check_service_availability(CommunicationService.SMS)
            imessage_status = await communication_core.check_service_availability(CommunicationService.IMESSAGE)
            
            return {
                "sms": {
                    "available": sms_status.available,
                    "capabilities": sms_status.capabilities,
                    "error_message": sms_status.error_message
                },
                "imessage": {
                    "available": imessage_status.available,
                    "capabilities": imessage_status.capabilities,
                    "error_message": imessage_status.error_message
                },
                "preferred_service": "imessage" if imessage_status.available else "sms" if sms_status.available else "none"
            }
        
        except Exception as e:
            logger.error(f"Error checking messaging services: {e}")
            return {
                "sms": {"available": False, "error": str(e)},
                "imessage": {"available": False, "error": str(e)},
                "preferred_service": "none"
            }
    
    @mcp_server.tool()
    async def km_detect_message_service(
        recipient: str
    ) -> Dict[str, Any]:
        """
        Detect the best messaging service for a specific recipient.
        
        Returns recommended service and reasoning for the recommendation.
        """
        try:
            detected_service = await communication_core.detect_message_service(recipient)
            
            # Validate recipient format
            from src.validators.input_validators import is_valid_phone_number, is_valid_email
            
            recipient_type = "unknown"
            if is_valid_phone_number(recipient):
                recipient_type = "phone_number"
            elif is_valid_email(recipient):
                recipient_type = "email"
            
            return {
                "recipient": recipient,
                "recipient_type": recipient_type,
                "recommended_service": detected_service.value,
                "reasoning": f"Best service for {recipient_type}: {detected_service.value}"
            }
        
        except Exception as e:
            logger.error(f"Error detecting message service: {e}")
            return {
                "recipient": recipient,
                "recipient_type": "unknown",
                "recommended_service": "sms",
                "error": str(e)
            }


# Legacy interface for backward compatibility
class MessagingOperationTools:
    """Messaging operation tools class for backward compatibility."""
    
    def __init__(self, communication_core: CommunicationCore):
        """Initialize with communication core dependency."""
        self.communication_core = communication_core
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register messaging tools with the MCP server."""
        register_messaging_tools(mcp_server, self.communication_core)


# Convenience functions
def get_km_interface():
    """Get KM interface instance - would be properly injected in real implementation."""
    from src.core.context_manager import get_km_interface
    return get_km_interface()
