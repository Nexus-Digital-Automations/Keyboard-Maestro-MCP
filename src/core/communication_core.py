"""
Core communication logic for email, messaging, and notification operations.

This module implements shared communication patterns, service detection, and utilities
for different communication channels with comprehensive error handling and validation.
"""

from typing import Optional, List, Dict, Any, Union, Protocol
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
import re
from abc import ABC, abstractmethod

from src.types.domain_types import EmailAddress, PhoneNumber, MessageContent
from src.types.values import FilePath, create_file_path
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_email, is_valid_phone_number
from src.core.km_interface import KMInterface
from src.core.km_error_handler import KMErrorHandler

logger = logging.getLogger(__name__)


class CommunicationService(Enum):
    """Available communication services."""
    EMAIL = "email"
    SMS = "sms"
    IMESSAGE = "imessage"
    NOTIFICATION = "notification"


class EmailAccount(Enum):
    """Email account selection options."""
    DEFAULT = "default"
    FIRST_AVAILABLE = "first"
    SPECIFIC = "specific"


@dataclass
class ServiceStatus:
    """Service availability status."""
    service: CommunicationService
    available: bool
    error_message: Optional[str] = None
    capabilities: Dict[str, bool] = None
    
    def __post_init__(self):
        """Initialize capabilities if not provided."""
        if self.capabilities is None:
            self.capabilities = {}


@dataclass
class EmailConfiguration:
    """Email sending configuration."""
    account: Union[EmailAccount, str]
    signature: Optional[str] = None
    format: str = "html"  # html or plain
    read_receipt: bool = False
    importance: str = "normal"  # low, normal, high
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.format not in ["html", "plain"]:
            raise ValueError("Email format must be 'html' or 'plain'")
        if self.importance not in ["low", "normal", "high"]:
            raise ValueError("Importance must be 'low', 'normal', or 'high'")


@dataclass
class MessagingConfiguration:
    """Messaging service configuration."""
    preferred_service: Optional[CommunicationService] = None
    fallback_to_sms: bool = True
    delivery_confirmation: bool = False
    
    def __post_init__(self):
        """Validate messaging configuration."""
        if (self.preferred_service and 
            self.preferred_service not in [CommunicationService.SMS, CommunicationService.IMESSAGE]):
            raise ValueError("Preferred service must be SMS or iMessage")


@dataclass
class NotificationConfiguration:
    """System notification configuration."""
    sound: Optional[str] = None
    duration: float = 5.0
    show_in_notification_center: bool = True
    banner_style: str = "alert"  # alert, banner, none
    
    def __post_init__(self):
        """Validate notification configuration."""
        if self.duration < 0:
            raise ValueError("Duration must be non-negative")
        if self.banner_style not in ["alert", "banner", "none"]:
            raise ValueError("Banner style must be 'alert', 'banner', or 'none'")


@dataclass
class CommunicationResult:
    """Base result for communication operations."""
    success: bool
    service_used: CommunicationService
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    delivery_status: Optional[str] = None
    processing_time: float = 0.0


class CommunicationServiceProtocol(Protocol):
    """Protocol for communication service implementations."""
    
    async def check_availability(self) -> ServiceStatus:
        """Check if the service is available."""
        ...
    
    async def send_message(self, content: Any, config: Any) -> CommunicationResult:
        """Send message through the service."""
        ...


class CommunicationCore:
    """Core communication operations with service detection and management."""
    
    def __init__(self, km_interface: KMInterface, error_handler: KMErrorHandler):
        """Initialize communication core with required dependencies."""
        self.km_interface = km_interface
        self.error_handler = error_handler
        self._service_cache: Dict[CommunicationService, ServiceStatus] = {}
        self._cache_timeout = 300  # 5 minutes
        self._last_cache_update = 0
    
    @requires(lambda self, service: isinstance(service, CommunicationService))
    async def check_service_availability(self, service: CommunicationService) -> ServiceStatus:
        """Check if a communication service is available on the system."""
        try:
            logger.debug(f"Checking availability for service: {service.value}")
            
            if service == CommunicationService.EMAIL:
                return await self._check_email_availability()
            elif service == CommunicationService.SMS:
                return await self._check_sms_availability()
            elif service == CommunicationService.IMESSAGE:
                return await self._check_imessage_availability()
            elif service == CommunicationService.NOTIFICATION:
                return await self._check_notification_availability()
            else:
                return ServiceStatus(
                    service=service,
                    available=False,
                    error_message=f"Unknown service: {service.value}"
                )
                
        except Exception as e:
            logger.error(f"Error checking service availability for {service.value}: {e}")
            return ServiceStatus(
                service=service,
                available=False,
                error_message=str(e),
                capabilities={}
            )
    
    async def get_available_services(self) -> List[ServiceStatus]:
        """Get status of all available communication services."""
        try:
            services = [
                CommunicationService.EMAIL,
                CommunicationService.SMS,
                CommunicationService.IMESSAGE,
                CommunicationService.NOTIFICATION
            ]
            
            # Check all services concurrently
            tasks = [self.check_service_availability(service) for service in services]
            statuses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return valid statuses
            valid_statuses = []
            for status in statuses:
                if isinstance(status, ServiceStatus):
                    valid_statuses.append(status)
                else:
                    logger.warning(f"Service check failed with exception: {status}")
            
            return valid_statuses
            
        except Exception as e:
            logger.error(f"Error getting available services: {e}")
            return []
    
    @requires(lambda self, recipients: all(is_valid_email(email) for email in recipients))
    async def validate_email_recipients(self, recipients: List[str]) -> Dict[str, bool]:
        """Validate email recipient addresses."""
        validation_results = {}
        
        for recipient in recipients:
            try:
                # Basic email format validation
                is_valid = is_valid_email(recipient)
                validation_results[recipient] = is_valid
                
                if not is_valid:
                    logger.warning(f"Invalid email format: {recipient}")
                    
            except Exception as e:
                logger.error(f"Error validating email {recipient}: {e}")
                validation_results[recipient] = False
        
        return validation_results
    
    @requires(lambda self, phone_numbers: all(isinstance(num, str) for num in phone_numbers))
    async def validate_phone_numbers(self, phone_numbers: List[str]) -> Dict[str, bool]:
        """Validate phone number formats."""
        validation_results = {}
        
        for phone_number in phone_numbers:
            try:
                # Basic phone number validation
                is_valid = is_valid_phone_number(phone_number)
                validation_results[phone_number] = is_valid
                
                if not is_valid:
                    logger.warning(f"Invalid phone number format: {phone_number}")
                    
            except Exception as e:
                logger.error(f"Error validating phone number {phone_number}: {e}")
                validation_results[phone_number] = False
        
        return validation_results
    
    @requires(lambda self, file_paths: all(isinstance(path, str) for path in file_paths))
    async def validate_attachments(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """Validate attachment files for existence and safety."""
        validation_results = {}
        
        for file_path in file_paths:
            try:
                import os
                
                result = {
                    "exists": os.path.exists(file_path),
                    "readable": False,
                    "size": 0,
                    "type": "unknown",
                    "safe": True
                }
                
                if result["exists"]:
                    result["readable"] = os.access(file_path, os.R_OK)
                    result["size"] = os.path.getsize(file_path)
                    
                    # Get file type
                    _, ext = os.path.splitext(file_path)
                    result["type"] = ext.lower() if ext else "no_extension"
                    
                    # Basic safety check - avoid extremely large files
                    max_size = 25 * 1024 * 1024  # 25MB
                    if result["size"] > max_size:
                        result["safe"] = False
                        logger.warning(f"Attachment too large: {file_path} ({result['size']} bytes)")
                
                validation_results[file_path] = result
                
            except Exception as e:
                logger.error(f"Error validating attachment {file_path}: {e}")
                validation_results[file_path] = {
                    "exists": False,
                    "readable": False,
                    "size": 0,
                    "type": "error",
                    "safe": False,
                    "error": str(e)
                }
        
        return validation_results
    
    async def detect_message_service(self, recipient: str) -> CommunicationService:
        """Detect the best service (SMS vs iMessage) for a recipient."""
        try:
            # First check if iMessage is available
            imessage_status = await self.check_service_availability(CommunicationService.IMESSAGE)
            
            if not imessage_status.available:
                # Fall back to SMS if iMessage not available
                return CommunicationService.SMS
            
            # Check if recipient is iMessage-capable through Keyboard Maestro
            # This would involve checking the Messages app contact database
            # For now, we'll default to iMessage if available and recipient looks like a phone/email
            if is_valid_email(recipient) or is_valid_phone_number(recipient):
                return CommunicationService.IMESSAGE
            
            return CommunicationService.SMS
            
        except Exception as e:
            logger.error(f"Error detecting message service for {recipient}: {e}")
            return CommunicationService.SMS  # Safe fallback
    
    async def format_message_content(self, content: str, 
                                   service: CommunicationService) -> str:
        """Format message content for specific service constraints."""
        try:
            if service == CommunicationService.SMS:
                # SMS has length limitations
                max_length = 1600  # Conservative limit for concatenated SMS
                if len(content) > max_length:
                    return content[:max_length - 3] + "..."
            
            elif service == CommunicationService.IMESSAGE:
                # iMessage supports longer messages and rich content
                # No length restriction needed
                pass
            
            return content
            
        except Exception as e:
            logger.error(f"Error formatting message content: {e}")
            return content  # Return original content on error
    
    # Private helper methods
    
    async def _check_email_availability(self) -> ServiceStatus:
        """Check if email functionality is available."""
        try:
            # Use Keyboard Maestro to check Mail app availability
            script = '''
            tell application "System Events"
                set mailRunning to (name of processes) contains "Mail"
            end tell
            return mailRunning
            '''
            
            result = await self.km_interface.execute_applescript(script)
            is_available = result.get("result", "false").lower() == "true"
            
            capabilities = {
                "html_support": True,
                "attachments": True,
                "multiple_recipients": True,
                "cc_bcc": True
            }
            
            return ServiceStatus(
                service=CommunicationService.EMAIL,
                available=is_available,
                capabilities=capabilities,
                error_message=None if is_available else "Mail app not running"
            )
            
        except Exception as e:
            return ServiceStatus(
                service=CommunicationService.EMAIL,
                available=False,
                error_message=str(e),
                capabilities={}
            )
    
    async def _check_sms_availability(self) -> ServiceStatus:
        """Check if SMS functionality is available."""
        try:
            # Check if Messages app is available and SMS is configured
            script = '''
            tell application "System Events"
                set messagesRunning to (name of processes) contains "Messages"
            end tell
            return messagesRunning
            '''
            
            result = await self.km_interface.execute_applescript(script)
            is_available = result.get("result", "false").lower() == "true"
            
            capabilities = {
                "length_limit": 1600,
                "rich_content": False,
                "delivery_confirmation": False
            }
            
            return ServiceStatus(
                service=CommunicationService.SMS,
                available=is_available,
                capabilities=capabilities,
                error_message=None if is_available else "Messages app not available"
            )
            
        except Exception as e:
            return ServiceStatus(
                service=CommunicationService.SMS,
                available=False,
                error_message=str(e),
                capabilities={}
            )
    
    async def _check_imessage_availability(self) -> ServiceStatus:
        """Check if iMessage functionality is available."""
        try:
            # Similar to SMS but with enhanced capabilities
            script = '''
            tell application "System Events"
                set messagesRunning to (name of processes) contains "Messages"
            end tell
            return messagesRunning
            '''
            
            result = await self.km_interface.execute_applescript(script)
            is_available = result.get("result", "false").lower() == "true"
            
            capabilities = {
                "rich_content": True,
                "delivery_confirmation": True,
                "read_receipts": True,
                "group_messaging": True
            }
            
            return ServiceStatus(
                service=CommunicationService.IMESSAGE,
                available=is_available,
                capabilities=capabilities,
                error_message=None if is_available else "Messages app not available"
            )
            
        except Exception as e:
            return ServiceStatus(
                service=CommunicationService.IMESSAGE,
                available=False,
                error_message=str(e),
                capabilities={}
            )
    
    async def _check_notification_availability(self) -> ServiceStatus:
        """Check if system notification functionality is available."""
        try:
            # Notifications are generally always available on macOS
            capabilities = {
                "sound_support": True,
                "custom_icons": True,
                "actions": True,
                "banner_styles": True
            }
            
            return ServiceStatus(
                service=CommunicationService.NOTIFICATION,
                available=True,
                capabilities=capabilities
            )
            
        except Exception as e:
            return ServiceStatus(
                service=CommunicationService.NOTIFICATION,
                available=False,
                error_message=str(e),
                capabilities={}
            )


# Utility functions for validation
def is_valid_email_format(email: str) -> bool:
    """Validate email address format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_phone_format(phone: str) -> bool:
    """Validate phone number format."""
    # Remove common formatting characters
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Basic validation - must be between 10-15 digits, optionally starting with +
    pattern = r'^\+?[1-9]\d{9,14}$'
    return re.match(pattern, cleaned) is not None


def sanitize_message_content(content: str) -> str:
    """Sanitize message content for safety."""
    # Remove potentially dangerous characters/sequences
    # This is a basic implementation - enhance based on security requirements
    import html
    
    # HTML escape for safety
    sanitized = html.escape(content)
    
    # Remove control characters except common ones (tab, newline, carriage return)
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    return sanitized
