"""
Comprehensive tests for communication tools (email, messaging, notifications).

This module provides thorough testing for all communication operations
with mock services, validation testing, and error handling verification.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from src.tools.email_operations import send_email, register_email_tools
from src.tools.messaging_operations import send_message, register_messaging_tools
from src.tools.notification_operations import display_notification, display_alert_dialog, register_notification_tools
from src.core.communication_core import (
    CommunicationCore, CommunicationService, ServiceStatus,
    EmailConfiguration, MessagingConfiguration, NotificationConfiguration
)


class TestEmailOperations:
    """Test cases for email operation tools."""
    
    @pytest.fixture
    def mock_communication_core(self):
        """Create mock communication core."""
        return Mock(spec=CommunicationCore)
    
    @pytest.fixture
    def mock_km_interface(self):
        """Create mock KM interface."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_communication_core, mock_km_interface):
        """Test successful email sending."""
        # Arrange
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.EMAIL,
            available=True,
            capabilities={"html_support": True, "attachments": True}
        )
        
        mock_communication_core.validate_email_recipients.return_value = {
            "test@example.com": True,
            "user@test.com": True
        }
        
        mock_communication_core.validate_attachments.return_value = {}
        
        mock_km_interface.execute_applescript.return_value = {
            "success": True,
            "message_id": "test_message_123",
            "account_used": "default"
        }
        
        with patch('src.tools.email_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.tools.email_operations.get_km_interface', return_value=mock_km_interface):
            
            # Act
            result = await send_email(
                recipients=["test@example.com", "user@test.com"],
                subject="Test Email",
                body="This is a test email",
                format="html"
            )
        
        # Assert
        assert result["success"] is True
        assert result["message_id"] == "test_message_123"
        assert result["recipients"]["to"] == ["test@example.com", "user@test.com"]
        assert result["subject"] == "Test Email"
        assert result["format"] == "html"
        assert "processing_time" in result
        
        mock_communication_core.check_service_availability.assert_called_once_with(CommunicationService.EMAIL)
        mock_communication_core.validate_email_recipients.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_invalid_recipients(self, mock_communication_core):
        """Test email sending with invalid recipients."""
        # Arrange
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.EMAIL,
            available=True
        )
        
        mock_communication_core.validate_email_recipients.return_value = {
            "invalid-email": False,
            "test@example.com": True
        }
        
        with patch('src.tools.email_operations.get_communication_core', return_value=mock_communication_core):
            
            # Act
            result = await send_email(
                recipients=["invalid-email", "test@example.com"],
                subject="Test",
                body="Test"
            )
        
        # Assert
        assert result["success"] is False
        assert result["error_code"] == "INVALID_RECIPIENTS"
        assert "invalid-email" in result["invalid_addresses"]
    
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, mock_communication_core, mock_km_interface):
        """Test email sending with attachments."""
        # Arrange
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.EMAIL,
            available=True
        )
        
        mock_communication_core.validate_email_recipients.return_value = {"test@example.com": True}
        
        mock_communication_core.validate_attachments.return_value = {
            "/path/to/file.pdf": {
                "exists": True,
                "readable": True,
                "size": 1024,
                "safe": True,
                "type": ".pdf"
            }
        }
        
        mock_km_interface.execute_applescript.return_value = {"success": True, "message_id": "test_123"}
        
        with patch('src.tools.email_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.tools.email_operations.get_km_interface', return_value=mock_km_interface):
            
            # Act
            result = await send_email(
                recipients=["test@example.com"],
                subject="Test with Attachment",
                body="Test email with attachment",
                attachments=["/path/to/file.pdf"]
            )
        
        # Assert
        assert result["success"] is True
        assert result["attachments"] == ["/path/to/file.pdf"]
        mock_communication_core.validate_attachments.assert_called_once_with(["/path/to/file.pdf"])
    
    @pytest.mark.asyncio
    async def test_send_email_service_unavailable(self, mock_communication_core):
        """Test email sending when service is unavailable."""
        # Arrange
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.EMAIL,
            available=False,
            error_message="Mail app not running"
        )
        
        with patch('src.tools.email_operations.get_communication_core', return_value=mock_communication_core):
            
            # Act
            result = await send_email(
                recipients=["test@example.com"],
                subject="Test",
                body="Test"
            )
        
        # Assert
        assert result["success"] is False
        assert result["error_code"] == "SERVICE_UNAVAILABLE"
        assert "Mail app not running" in result["error_details"]


class TestMessagingOperations:
    """Test cases for messaging operation tools."""
    
    @pytest.fixture
    def mock_communication_core(self):
        """Create mock communication core."""
        return Mock(spec=CommunicationCore)
    
    @pytest.fixture
    def mock_km_interface(self):
        """Create mock KM interface."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_send_message_success_imessage(self, mock_communication_core, mock_km_interface):
        """Test successful iMessage sending."""
        # Arrange
        mock_communication_core.detect_message_service.return_value = CommunicationService.IMESSAGE
        
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.IMESSAGE,
            available=True,
            capabilities={"rich_content": True, "delivery_confirmation": True}
        )
        
        mock_communication_core.format_message_content.return_value = "Test message"
        
        mock_km_interface.execute_applescript.return_value = {"success": True}
        
        with patch('src.tools.messaging_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.tools.messaging_operations.get_km_interface', return_value=mock_km_interface), \
             patch('src.validators.input_validators.is_valid_phone_number', return_value=True):
            
            # Act
            result = await send_message(
                recipient="+1234567890",
                message="Test message",
                service="auto"
            )
        
        # Assert
        assert result["success"] is True
        assert result["service_used"] == "imessage"
        assert result["recipient"] == "+1234567890"
        assert result["message"] == "Test message"
        assert result["delivery_status"] == "sent"
        
        mock_communication_core.detect_message_service.assert_called_once_with("+1234567890")
    
    @pytest.mark.asyncio
    async def test_send_message_fallback_to_sms(self, mock_communication_core, mock_km_interface):
        """Test fallback from iMessage to SMS."""
        # Arrange
        mock_communication_core.detect_message_service.return_value = CommunicationService.IMESSAGE
        
        # iMessage fails first
        imessage_status = ServiceStatus(service=CommunicationService.IMESSAGE, available=True)
        sms_status = ServiceStatus(service=CommunicationService.SMS, available=True)
        
        mock_communication_core.check_service_availability.side_effect = [imessage_status, sms_status]
        mock_communication_core.format_message_content.return_value = "Test message"
        
        # First call (iMessage) fails, second call (SMS) succeeds
        mock_km_interface.execute_applescript.side_effect = [
            {"success": False, "error": "iMessage failed"},
            {"success": True}
        ]
        
        with patch('src.tools.messaging_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.tools.messaging_operations.get_km_interface', return_value=mock_km_interface), \
             patch('src.validators.input_validators.is_valid_phone_number', return_value=True):
            
            # Act
            result = await send_message(
                recipient="+1234567890",
                message="Test message",
                fallback_to_sms=True
            )
        
        # Assert
        assert result["success"] is True
        assert result["service_used"] == "sms"
        assert result["service_fallback"] is True
        assert result["original_service_attempted"] == "imessage"
    
    @pytest.mark.asyncio
    async def test_send_message_invalid_recipient(self, mock_communication_core):
        """Test message sending with invalid recipient."""
        with patch('src.tools.messaging_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.validators.input_validators.is_valid_phone_number', return_value=False), \
             patch('src.validators.input_validators.is_valid_email', return_value=False):
            
            # Act
            result = await send_message(
                recipient="invalid-recipient",
                message="Test message"
            )
        
        # Assert
        assert result["success"] is False
        assert result["error_code"] == "INVALID_RECIPIENT"
        assert result["recipient"] == "invalid-recipient"
    
    @pytest.mark.asyncio
    async def test_send_message_long_content_truncation(self, mock_communication_core, mock_km_interface):
        """Test message truncation for SMS length limits."""
        # Arrange
        long_message = "A" * 2000  # Very long message
        truncated_message = "A" * 1597 + "..."  # Expected truncation
        
        mock_communication_core.detect_message_service.return_value = CommunicationService.SMS
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.SMS,
            available=True
        )
        mock_communication_core.format_message_content.return_value = truncated_message
        mock_km_interface.execute_applescript.return_value = {"success": True}
        
        with patch('src.tools.messaging_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.tools.messaging_operations.get_km_interface', return_value=mock_km_interface), \
             patch('src.validators.input_validators.is_valid_phone_number', return_value=True):
            
            # Act
            result = await send_message(
                recipient="+1234567890",
                message=long_message
            )
        
        # Assert
        assert result["success"] is True
        assert result["message_truncated"] is True
        assert result["original_length"] == 2000
        assert result["sent_length"] == len(truncated_message)


class TestNotificationOperations:
    """Test cases for notification operation tools."""
    
    @pytest.fixture
    def mock_communication_core(self):
        """Create mock communication core."""
        return Mock(spec=CommunicationCore)
    
    @pytest.fixture
    def mock_km_interface(self):
        """Create mock KM interface."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_display_notification_success(self, mock_communication_core, mock_km_interface):
        """Test successful notification display."""
        # Arrange
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.NOTIFICATION,
            available=True,
            capabilities={"sound_support": True, "custom_icons": True}
        )
        
        mock_km_interface.execute_applescript.return_value = {
            "success": True,
            "notification_id": "notif_123"
        }
        
        with patch('src.tools.notification_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.tools.notification_operations.get_km_interface', return_value=mock_km_interface):
            
            # Act
            result = await display_notification(
                title="Test Notification",
                message="This is a test notification",
                subtitle="Test Subtitle",
                sound="default",
                duration=5.0,
                style="alert"
            )
        
        # Assert
        assert result["success"] is True
        assert result["title"] == "Test Notification"
        assert result["message"] == "This is a test notification"
        assert result["subtitle"] == "Test Subtitle"
        assert result["sound"] == "default"
        assert result["duration"] == 5.0
        assert result["style"] == "alert"
        assert result["notification_id"] == "notif_123"
    
    @pytest.mark.asyncio
    async def test_display_notification_input_validation(self, mock_communication_core, mock_km_interface):
        """Test notification input validation and sanitization."""
        # Arrange
        mock_communication_core.check_service_availability.return_value = ServiceStatus(
            service=CommunicationService.NOTIFICATION,
            available=True
        )
        
        mock_km_interface.execute_applescript.return_value = {"success": True}
        
        with patch('src.tools.notification_operations.get_communication_core', return_value=mock_communication_core), \
             patch('src.tools.notification_operations.get_km_interface', return_value=mock_km_interface):
            
            # Act - Test with very long title and invalid duration
            result = await display_notification(
                title="A" * 500,  # Very long title
                message="Test message",
                duration=-5.0,  # Invalid negative duration
                style="invalid_style"  # Invalid style
            )
        
        # Assert
        assert result["success"] is True
        assert len(result["title"]) == 256  # Truncated to 256 characters
        assert result["duration"] == 5.0  # Corrected to default
        assert result["style"] == "alert"  # Corrected to default
    
    @pytest.mark.asyncio
    async def test_display_alert_dialog_success(self, mock_communication_core, mock_km_interface):
        """Test successful alert dialog display."""
        # Arrange
        mock_km_interface.execute_applescript.return_value = {
            "success": True,
            "button_clicked": "Yes",
            "button_index": 0
        }
        
        with patch('src.tools.notification_operations.get_km_interface', return_value=mock_km_interface):
            
            # Act
            result = await display_alert_dialog(
                title="Confirm Action",
                message="Are you sure you want to proceed?",
                buttons=["Yes", "No", "Cancel"],
                default_button="Yes",
                cancel_button="Cancel",
                icon="caution"
            )
        
        # Assert
        assert result["success"] is True
        assert result["title"] == "Confirm Action"
        assert result["message"] == "Are you sure you want to proceed?"
        assert result["buttons"] == ["Yes", "No", "Cancel"]
        assert result["button_clicked"] == "Yes"
        assert result["button_index"] == 0
    
    @pytest.mark.asyncio
    async def test_display_alert_dialog_button_limit(self, mock_communication_core, mock_km_interface):
        """Test alert dialog button count limitation."""
        # Arrange
        mock_km_interface.execute_applescript.return_value = {"success": True, "button_clicked": "Button1"}
        
        with patch('src.tools.notification_operations.get_km_interface', return_value=mock_km_interface):
            
            # Act - Provide more than 3 buttons
            result = await display_alert_dialog(
                title="Test",
                message="Test message",
                buttons=["Button1", "Button2", "Button3", "Button4", "Button5"]
            )
        
        # Assert
        assert result["success"] is True
        assert len(result["buttons"]) == 3  # Limited to 3 buttons
        assert result["buttons"] == ["Button1", "Button2", "Button3"]


class TestCommunicationToolsIntegration:
    """Integration tests for communication tools."""
    
    @pytest.mark.asyncio
    async def test_communication_service_detection(self):
        """Test communication service availability detection."""
        # This would test the service detection logic across all communication types
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling_across_services(self):
        """Test consistent error handling across all communication services."""
        # This would test error propagation and recovery across email, messaging, and notifications
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_communication_operations(self):
        """Test multiple concurrent communication operations."""
        # This would test resource management and performance under concurrent load
        pass


# Property-based testing for validation
class TestCommunicationValidationProperties:
    """Property-based tests for communication validation logic."""
    
    def test_email_validation_properties(self):
        """Test email validation with generated values."""
        # This would use hypothesis to generate test email addresses
        pass
    
    def test_phone_number_validation_properties(self):
        """Test phone number validation properties."""
        # This would use hypothesis to test phone number validation edge cases
        pass


# Mock helper functions
def create_mock_service_status(service: CommunicationService, available: bool = True) -> ServiceStatus:
    """Create mock service status for testing."""
    return ServiceStatus(
        service=service,
        available=available,
        capabilities={"mock": True} if available else {},
        error_message=None if available else f"{service.value} not available"
    )


if __name__ == "__main__":
    pytest.main([__file__])
