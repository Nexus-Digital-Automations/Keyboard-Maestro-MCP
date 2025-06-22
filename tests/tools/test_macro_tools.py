"""
Comprehensive tests for macro MCP tools.

This module provides thorough testing for all macro-related MCP tools
with contract validation and error handling verification.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.tools.macro_execution import MacroExecutionTools
from src.tools.macro_management import MacroManagementTools
from src.tools.macro_groups import MacroGroupTools
from src.core.macro_operations import MacroOperations, MacroOperationStatus
from src.types.domain_types import ExecutionMethod


class TestMacroExecutionTools:
    """Test cases for macro execution tools."""
    
    @pytest.fixture
    def mock_macro_operations(self):
        """Create mock macro operations."""
        return Mock(spec=MacroOperations)
    
    @pytest.fixture
    def execution_tools(self, mock_macro_operations):
        """Create execution tools instance."""
        return MacroExecutionTools(mock_macro_operations)
    
    @pytest.mark.asyncio
    async def test_execute_macro_success(self, execution_tools, mock_macro_operations):
        """Test successful macro execution."""
        # Arrange
        mock_result = Mock()
        mock_result.status = MacroOperationStatus.SUCCESS
        mock_result.execution_time = 1.5
        mock_result.error_details = None
        mock_result.macro_uuid = "test-uuid"
        
        mock_macro_operations.execute_macro.return_value = mock_result
        
        # Act
        result = await execution_tools.execute_macro("test-macro")
        
        # Assert
        assert result["success"] is True
        assert result["status"] == "success"
        assert result["execution_time"] == 1.5
        assert result["error"] is None
        assert result["macro_uuid"] == "test-uuid"
        
        mock_macro_operations.execute_macro.assert_called_once_with(
            identifier="test-macro",
            trigger_value=None,
            method=ExecutionMethod.APPLESCRIPT,
            timeout=30
        )
    
    @pytest.mark.asyncio
    async def test_execute_macro_failure(self, execution_tools, mock_macro_operations):
        """Test macro execution failure."""
        # Arrange
        mock_result = Mock()
        mock_result.status = MacroOperationStatus.NOT_FOUND
        mock_result.execution_time = 0
        mock_result.error_details = "Macro not found"
        mock_result.macro_uuid = None
        
        mock_macro_operations.execute_macro.return_value = mock_result
        
        # Act
        result = await execution_tools.execute_macro("nonexistent-macro")
        
        # Assert
        assert result["success"] is False
        assert result["status"] == "not_found"
        assert result["error"] == "Macro not found"
    
    @pytest.mark.asyncio
    async def test_execute_macro_invalid_identifier(self, execution_tools):
        """Test execution with invalid identifier."""
        # Act
        result = await execution_tools.execute_macro("")
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Invalid macro identifier"
        assert result["error_code"] == "INVALID_IDENTIFIER"
    
    @pytest.mark.asyncio
    async def test_execute_macro_with_timeout(self, execution_tools, mock_macro_operations):
        """Test macro execution with custom timeout."""
        # Arrange
        mock_result = Mock()
        mock_result.status = MacroOperationStatus.SUCCESS
        mock_result.execution_time = 45.0
        mock_result.error_details = None
        mock_result.macro_uuid = "test-uuid"
        
        mock_macro_operations.execute_macro.return_value = mock_result
        
        # Act
        result = await execution_tools.execute_macro_with_timeout("test-macro", 60)
        
        # Assert
        assert result["success"] is True
        assert result["timeout_used"] == 60
        assert result["timed_out"] is False
        
        mock_macro_operations.execute_macro.assert_called_once_with(
            identifier="test-macro",
            trigger_value=None,
            method=ExecutionMethod.APPLESCRIPT,
            timeout=60
        )
    
    @pytest.mark.asyncio
    async def test_execute_macro_via_method(self, execution_tools, mock_macro_operations):
        """Test execution via specific method."""
        # Arrange
        mock_result = Mock()
        mock_result.status = MacroOperationStatus.SUCCESS
        mock_result.execution_time = 2.0
        mock_result.error_details = None
        mock_result.macro_uuid = "test-uuid"
        
        mock_macro_operations.execute_macro.return_value = mock_result
        
        # Act
        result = await execution_tools.execute_macro_via_method("test-macro", "url")
        
        # Assert
        assert result["success"] is True
        assert result["execution_method"] == "url"
        
        mock_macro_operations.execute_macro.assert_called_once_with(
            identifier="test-macro",
            trigger_value=None,
            method=ExecutionMethod.URL,
            timeout=30
        )
    
    @pytest.mark.asyncio
    async def test_test_macro_execution_ready(self, execution_tools, mock_macro_operations):
        """Test macro execution readiness check."""
        # Arrange
        mock_info = Mock()
        mock_info.name = "Test Macro"
        mock_info.uuid = "test-uuid"
        mock_info.enabled = True
        mock_info.group_uuid = "group-uuid"
        mock_info.trigger_count = 2
        mock_info.action_count = 5
        
        mock_macro_operations.get_macro_info.return_value = mock_info
        
        # Act
        result = await execution_tools.test_macro_execution("test-macro")
        
        # Assert
        assert result["ready"] is True
        assert result["macro_info"]["name"] == "Test Macro"
        assert result["macro_info"]["enabled"] is True
        assert len(result["execution_methods"]) == 4


class TestMacroManagementTools:
    """Test cases for macro management tools."""
    
    @pytest.fixture
    def mock_macro_operations(self):
        """Create mock macro operations."""
        return Mock(spec=MacroOperations)
    
    @pytest.fixture
    def management_tools(self, mock_macro_operations):
        """Create management tools instance."""
        return MacroManagementTools(mock_macro_operations)
    
    @pytest.mark.asyncio
    async def test_create_macro_success(self, management_tools, mock_macro_operations):
        """Test successful macro creation."""
        # Arrange
        mock_result = Mock()
        mock_result.status = MacroOperationStatus.SUCCESS
        mock_result.macro_uuid = "new-macro-uuid"
        mock_result.error_details = None
        
        mock_macro_operations.create_macro.return_value = mock_result
        
        # Act
        result = await management_tools.create_macro(
            name="New Test Macro",
            enabled=True,
            color="red"
        )
        
        # Assert
        assert result["success"] is True
        assert result["macro_uuid"] == "new-macro-uuid"
        assert result["macro_name"] == "New Test Macro"
        
        mock_macro_operations.create_macro.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_macro_info_found(self, management_tools, mock_macro_operations):
        """Test getting macro information."""
        # Arrange
        mock_info = Mock()
        mock_info.uuid = "test-uuid"
        mock_info.name = "Test Macro"
        mock_info.group_uuid = "group-uuid"
        mock_info.enabled = True
        mock_info.color = "blue"
        mock_info.notes = "Test notes"
        mock_info.creation_date = "2023-01-01"
        mock_info.modification_date = "2023-01-02"
        mock_info.last_used = "2023-01-03"
        mock_info.trigger_count = 1
        mock_info.action_count = 3
        
        mock_macro_operations.get_macro_info.return_value = mock_info
        
        # Act
        result = await management_tools.get_macro_info("test-macro")
        
        # Assert
        assert result["found"] is True
        assert result["macro"]["name"] == "Test Macro"
        assert result["macro"]["enabled"] is True
        assert result["macro"]["trigger_count"] == 1
    
    @pytest.mark.asyncio
    async def test_get_macro_info_not_found(self, management_tools, mock_macro_operations):
        """Test getting info for non-existent macro."""
        # Arrange
        mock_macro_operations.get_macro_info.return_value = None
        
        # Act
        result = await management_tools.get_macro_info("nonexistent")
        
        # Assert
        assert result["found"] is False
        assert result["error"] == "Macro not found"
        assert result["error_code"] == "MACRO_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_update_macro_success(self, management_tools, mock_macro_operations):
        """Test macro update."""
        # Arrange
        mock_result = Mock()
        mock_result.status = MacroOperationStatus.SUCCESS
        mock_result.error_details = None
        
        mock_macro_operations.modify_macro.return_value = mock_result
        
        # Act
        result = await management_tools.update_macro(
            "test-macro",
            name="Updated Name",
            enabled=False
        )
        
        # Assert
        assert result["success"] is True
        assert result["updated_fields"]["name"] == "Updated Name"
        assert result["updated_fields"]["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_delete_macro_without_confirmation(self, management_tools):
        """Test macro deletion without confirmation."""
        # Act
        result = await management_tools.delete_macro("test-macro")
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Confirmation required for deletion"
        assert result["error_code"] == "CONFIRMATION_REQUIRED"
    
    @pytest.mark.asyncio
    async def test_delete_macro_with_confirmation(self, management_tools, mock_macro_operations):
        """Test macro deletion with confirmation."""
        # Arrange
        mock_result = Mock()
        mock_result.status = MacroOperationStatus.SUCCESS
        mock_result.error_details = None
        
        mock_macro_operations.delete_macro.return_value = mock_result
        
        # Act
        result = await management_tools.delete_macro("test-macro", confirm=True)
        
        # Assert
        assert result["success"] is True
        assert result["deleted_identifier"] == "test-macro"
    
    @pytest.mark.asyncio
    async def test_list_macros(self, management_tools, mock_macro_operations):
        """Test listing macros."""
        # Arrange
        mock_macro1 = Mock()
        mock_macro1.uuid = "uuid1"
        mock_macro1.name = "Macro 1"
        mock_macro1.group_uuid = "group1"
        mock_macro1.enabled = True
        mock_macro1.color = None
        mock_macro1.trigger_count = 1
        mock_macro1.action_count = 2
        mock_macro1.last_used = None
        
        mock_macro2 = Mock()
        mock_macro2.uuid = "uuid2"
        mock_macro2.name = "Macro 2"
        mock_macro2.group_uuid = "group2"
        mock_macro2.enabled = False
        mock_macro2.color = "red"
        mock_macro2.trigger_count = 2
        mock_macro2.action_count = 3
        mock_macro2.last_used = "2023-01-01"
        
        mock_macro_operations.list_macros.return_value = [mock_macro1, mock_macro2]
        
        # Act
        result = await management_tools.list_macros()
        
        # Assert
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["macros"]) == 2
        assert result["macros"][0]["name"] == "Macro 1"
        assert result["macros"][1]["name"] == "Macro 2"


class TestMacroGroupTools:
    """Test cases for macro group tools."""
    
    @pytest.fixture
    def mock_macro_operations(self):
        """Create mock macro operations with KM interface."""
        mock_ops = Mock(spec=MacroOperations)
        mock_ops.km_interface = AsyncMock()
        return mock_ops
    
    @pytest.fixture
    def group_tools(self, mock_macro_operations):
        """Create group tools instance."""
        return MacroGroupTools(mock_macro_operations)
    
    @pytest.mark.asyncio
    async def test_create_macro_group_success(self, group_tools, mock_macro_operations):
        """Test successful group creation."""
        # Arrange
        mock_macro_operations.km_interface.create_macro_group.return_value = {
            "success": True,
            "group_uuid": "new-group-uuid"
        }
        
        # Act
        result = await group_tools.create_macro_group(
            name="Test Group",
            activation_method="always",
            enabled=True
        )
        
        # Assert
        assert result["success"] is True
        assert result["group_uuid"] == "new-group-uuid"
        assert result["group_name"] == "Test Group"
        assert result["activation_method"] == "always"
    
    @pytest.mark.asyncio
    async def test_create_macro_group_invalid_activation(self, group_tools):
        """Test group creation with invalid activation method."""
        # Act
        result = await group_tools.create_macro_group(
            name="Test Group",
            activation_method="invalid_method"
        )
        
        # Assert
        assert result["success"] is False
        assert result["error_code"] == "INVALID_ACTIVATION_METHOD"
        assert "invalid_method" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_macro_group(self, group_tools, mock_macro_operations):
        """Test group update."""
        # Arrange
        mock_macro_operations.km_interface.update_macro_group.return_value = {
            "success": True
        }
        
        # Act
        result = await group_tools.update_macro_group(
            "group-uuid",
            name="Updated Group",
            enabled=False
        )
        
        # Assert
        assert result["success"] is True
        assert result["group_uuid"] == "group-uuid"
        assert result["updated_fields"]["name"] == "Updated Group"
        assert result["updated_fields"]["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_delete_macro_group_without_confirmation(self, group_tools):
        """Test group deletion without confirmation."""
        # Act
        result = await group_tools.delete_macro_group("group-uuid")
        
        # Assert
        assert result["success"] is False
        assert result["error_code"] == "CONFIRMATION_REQUIRED"
    
    @pytest.mark.asyncio
    async def test_create_smart_group(self, group_tools, mock_macro_operations):
        """Test smart group creation."""
        # Arrange
        mock_macro_operations.km_interface.create_smart_group.return_value = {
            "success": True,
            "group_uuid": "smart-group-uuid"
        }
        
        # Act
        result = await group_tools.create_smart_group(
            name="Smart Group",
            search_criteria=["test", "automation"]
        )
        
        # Assert
        assert result["success"] is True
        assert result["group_uuid"] == "smart-group-uuid"
        assert result["type"] == "smart"
        assert result["search_criteria"] == ["test", "automation"]
    
    @pytest.mark.asyncio
    async def test_create_smart_group_no_criteria(self, group_tools):
        """Test smart group creation without criteria."""
        # Act
        result = await group_tools.create_smart_group(
            name="Smart Group",
            search_criteria=[]
        )
        
        # Assert
        assert result["success"] is False
        assert result["error_code"] == "MISSING_CRITERIA"


# Integration tests
class TestMacroToolsIntegration:
    """Integration tests for macro tools."""
    
    @pytest.mark.asyncio
    async def test_macro_lifecycle(self):
        """Test complete macro lifecycle."""
        # This would test creation -> execution -> modification -> deletion
        # Implementation would require actual KM interface or sophisticated mocking
        pass
    
    @pytest.mark.asyncio  
    async def test_error_propagation(self):
        """Test error handling across tool layers."""
        # This would test error propagation from KM interface through tools
        pass


if __name__ == "__main__":
    pytest.main([__file__])
