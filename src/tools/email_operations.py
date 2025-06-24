"""
Email operations tools for Keyboard Maestro MCP server.

This module provides comprehensive email sending capabilities with recipient validation,
attachment handling, and integration with macOS Mail application.
"""

from typing import Optional, List, Dict, Any, Union
import logging
import asyncio
import time

from fastmcp import FastMCP
from .core.communication_core import (
    CommunicationCore, CommunicationService, CommunicationResult,
    EmailConfiguration, EmailAccount
)
from src.contracts.decorators import requires, ensures
from src.validators.input_validators import validate_email_addresses
from src.core.km_interface import KMInterface

logger = logging.getLogger(__name__)


@requires(lambda recipients: len(recipients) > 0)
@requires(lambda subject: len(subject.strip()) > 0)
@ensures(lambda result: result["success"] or result["error"] is not None)
async def send_email(
    recipients: List[str],
    subject: str,
    body: str,
    cc_recipients: Optional[List[str]] = None,
    bcc_recipients: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    account: str = "default",
    format: str = "html",
    importance: str = "normal"
) -> Dict[str, Any]:
    """
    Send email through macOS Mail with comprehensive validation.
    
    Args:
        recipients: List of email addresses for To field
        subject: Email subject line
        body: Email content (HTML or plain text)
        cc_recipients: Optional CC recipients
        bcc_recipients: Optional BCC recipients
        attachments: Optional file paths for attachments
        account: Email account to use ("default", "first", or specific account)
        format: Email format ("html" or "plain")
        importance: Message importance ("low", "normal", "high")
    
    Returns:
        Dict with success status, message details, and any errors
    """
    start_time = time.time()
    
    try:
        # Get communication core instance (would be injected in real implementation)
        from src.core.context_manager import get_communication_core
        comm_core = get_communication_core()
        
        # Validate email service availability
        email_status = await comm_core.check_service_availability(CommunicationService.EMAIL)
        if not email_status.available:
            return {
                "success": False,
                "error": "Email service not available",
                "error_code": "SERVICE_UNAVAILABLE",
                "error_details": email_status.error_message
            }
        
        # Validate all email recipients
        all_recipients = recipients.copy()
        if cc_recipients:
            all_recipients.extend(cc_recipients)
        if bcc_recipients:
            all_recipients.extend(bcc_recipients)
        
        validation_results = await comm_core.validate_email_recipients(all_recipients)
        invalid_emails = [email for email, valid in validation_results.items() if not valid]
        
        if invalid_emails:
            return {
                "success": False,
                "error": "Invalid email addresses",
                "error_code": "INVALID_RECIPIENTS",
                "invalid_addresses": invalid_emails
            }
        
        # Validate attachments if provided
        attachment_validation = {}
        if attachments:
            attachment_validation = await comm_core.validate_attachments(attachments)
            invalid_attachments = [
                path for path, info in attachment_validation.items()
                if not info.get("exists") or not info.get("safe")
            ]
            
            if invalid_attachments:
                return {
                    "success": False,
                    "error": "Invalid attachments",
                    "error_code": "INVALID_ATTACHMENTS",
                    "invalid_attachments": invalid_attachments,
                    "attachment_details": attachment_validation
                }
        
        # Create email configuration
        config = EmailConfiguration(
            account=EmailAccount.DEFAULT if account == "default" else account,
            format=format,
            importance=importance
        )
        
        # Send email through Keyboard Maestro interface
        km_interface = get_km_interface()  # Would be injected
        
        # Build AppleScript for sending email
        script = _build_email_applescript(
            recipients, subject, body, cc_recipients, bcc_recipients,
            attachments, config
        )
        
        result = await km_interface.execute_applescript(script)
        
        if result.get("success", False):
            processing_time = time.time() - start_time
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "recipients": {
                    "to": recipients,
                    "cc": cc_recipients or [],
                    "bcc": bcc_recipients or []
                },
                "subject": subject,
                "format": format,
                "attachments": attachments or [],
                "processing_time": processing_time,
                "account_used": result.get("account_used", account)
            }
        else:
            return {
                "success": False,
                "error": "Failed to send email",
                "error_code": "SEND_FAILED",
                "error_details": result.get("error", "Unknown error")
            }
    
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "INTERNAL_ERROR",
            "processing_time": time.time() - start_time
        }


def _build_email_applescript(
    recipients: List[str],
    subject: str,
    body: str,
    cc_recipients: Optional[List[str]],
    bcc_recipients: Optional[List[str]],
    attachments: Optional[List[str]],
    config: EmailConfiguration
) -> str:
    """Build AppleScript for sending email through Mail app."""
    
    # Escape strings for AppleScript
    def escape_applescript_string(s: str) -> str:
        return s.replace('"', '\\"').replace('\\', '\\\\')
    
    escaped_subject = escape_applescript_string(subject)
    escaped_body = escape_applescript_string(body)
    
    # Build recipient lists
    to_list = ', '.join(f'"{escape_applescript_string(email)}"' for email in recipients)
    cc_list = ', '.join(f'"{escape_applescript_string(email)}"' for email in cc_recipients) if cc_recipients else ""
    bcc_list = ', '.join(f'"{escape_applescript_string(email)}"' for email in bcc_recipients) if bcc_recipients else ""
    
    # Build AppleScript
    script_parts = [
        'tell application "Mail"',
        '    set newMessage to make new outgoing message with properties {',
        f'        subject: "{escaped_subject}",',
        f'        content: "{escaped_body}",',
        f'        visible: false'
    ]
    
    if config.importance != "normal":
        priority_map = {"low": "low", "high": "high"}
        script_parts.append(f'        priority: {priority_map[config.importance]},')
    
    script_parts.extend([
        '    }',
        f'    tell newMessage to make new to recipient at end of to recipients with properties {{address: {to_list}}}'
    ])
    
    if cc_list:
        script_parts.append(f'    tell newMessage to make new cc recipient at end of cc recipients with properties {{address: {cc_list}}}')
    
    if bcc_list:
        script_parts.append(f'    tell newMessage to make new bcc recipient at end of bcc recipients with properties {{address: {bcc_list}}}')
    
    # Add attachments
    if attachments:
        for attachment in attachments:
            escaped_path = escape_applescript_string(attachment)
            script_parts.append(f'    tell newMessage to make new attachment with properties {{file name: POSIX file "{escaped_path}"}}')
    
    script_parts.extend([
        '    send newMessage',
        '    return "success"',
        'end tell'
    ])
    
    return '\n'.join(script_parts)


def register_email_tools(mcp_server: FastMCP, communication_core: CommunicationCore) -> None:
    """Register email operation tools with the FastMCP server."""
    
    @mcp_server.tool()
    async def km_send_email(
        recipients: List[str],
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        account: str = "default",
        format: str = "html",
        importance: str = "normal"
    ) -> Dict[str, Any]:
        """
        Send email through macOS Mail application.
        
        Supports multiple recipients, CC/BCC, attachments, and different formats.
        Validates all recipients and attachments before sending.
        """
        return await send_email(
            recipients=recipients,
            subject=subject,
            body=body,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            attachments=attachments,
            account=account,
            format=format,
            importance=importance
        )
    
    @mcp_server.tool()
    async def km_check_email_service(
    ) -> Dict[str, Any]:
        """
        Check if email service is available and get capabilities.
        
        Returns service status, available features, and account information.
        """
        try:
            status = await communication_core.check_service_availability(CommunicationService.EMAIL)
            
            return {
                "available": status.available,
                "service": status.service.value,
                "capabilities": status.capabilities,
                "error_message": status.error_message
            }
        
        except Exception as e:
            logger.error(f"Error checking email service: {e}")
            return {
                "available": False,
                "service": "email",
                "error": str(e)
            }
    
    @mcp_server.tool()
    async def km_validate_email_addresses(
        email_addresses: List[str]
    ) -> Dict[str, Any]:
        """
        Validate email address formats and availability.
        
        Returns validation results for each provided email address.
        """
        try:
            validation_results = await communication_core.validate_email_recipients(email_addresses)
            
            valid_count = sum(1 for valid in validation_results.values() if valid)
            invalid_addresses = [email for email, valid in validation_results.items() if not valid]
            
            return {
                "total_addresses": len(email_addresses),
                "valid_count": valid_count,
                "invalid_count": len(invalid_addresses),
                "validation_results": validation_results,
                "invalid_addresses": invalid_addresses
            }
        
        except Exception as e:
            logger.error(f"Error validating email addresses: {e}")
            return {
                "total_addresses": len(email_addresses),
                "valid_count": 0,
                "invalid_count": len(email_addresses),
                "error": str(e)
            }


# Legacy interface for backward compatibility
class EmailOperationTools:
    """Email operation tools class for backward compatibility."""
    
    def __init__(self, communication_core: CommunicationCore):
        """Initialize with communication core dependency."""
        self.communication_core = communication_core
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register email tools with the MCP server."""
        register_email_tools(mcp_server, self.communication_core)


# Convenience functions
def get_km_interface():
    """Get KM interface instance - would be properly injected in real implementation."""
    # This is a placeholder - in real implementation this would be dependency injection
    from src.core.context_manager import get_km_interface
    return get_km_interface()
