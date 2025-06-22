"""Comprehensive test suite for system integration tools.

This module provides property-based and unit tests for all system integration
MCP tools with extensive error scenario coverage and defensive programming validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
from pathlib import Path
import tempfile
import os

from hypothesis import given, strategies as st, assume
from fastmcp import FastMCP, Context

from src.tools.file_operations import FileOperationTools
from src.tools.application_control import ApplicationControlTools
from src.tools.window_management import WindowManagementTools
from src.tools.interface_automation import InterfaceAutomationTools
from src.validators.system_validators import system_validator
from src.boundaries.permission_checker import permission_checker


class TestFileOperationTools:
    """Test suite for file operation MCP tools."""
    
    @pytest.fixture
    def mcp_server(self):
        """Create mock MCP server for testing."""
        return Mock(spec=FastMCP)
    
    @pytest.fixture
    def file_tools(self, mcp_server):
        """Create file operation tools instance."""
        return FileOperationTools(mcp_server)
    
    @pytest.fixture
    def mock_context(self):
        """Create mock MCP context."""
        context = AsyncMock(spec=Context)
        context.info = AsyncMock()
        context.error = AsyncMock()
        context.report_progress = AsyncMock()
        return context
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_copy_file_success(self, file_tools, mock_context, temp_dir):
        """Test successful file copy operation."""
        # Create source file
        source_file = temp_dir / "source.txt"
        source_file.write_text("test content")
        
        dest_file = temp_dir / "dest.txt"
        
        with patch('src.core.system_operations.system_manager') as mock_manager:
            mock_manager.copy_file.return_value = Mock(
                status=Mock(value="success"),
                message="File copied successfully",
                execution_time=0.1,
                data={"source": str(source_file), "destination": str(dest_file)}
            )
            
            result = await file_tools.copy_file(
                str(source_file), str(dest_file), ctx=mock_context
            )
            
            assert result["success"] is True
            assert "File copied successfully" in result["message"]
            mock_context.info.assert_called()
            mock_context.report_progress.assert_called()
    
    @pytest.mark.asyncio
    async def test_copy_file_validation_error(self, file_tools, mock_context):
        """Test file copy with validation errors."""
        result = await file_tools.copy_file("", "dest.txt", ctx=mock_context)
        
        assert result["success"] is False
        assert result["error_type"] == "validation_error"
        mock_context.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_file_safety_check(self, file_tools, mock_context):
        """Test file deletion safety checks."""
        # Try to delete a system file
        result = await file_tools.delete_file("/System/test", ctx=mock_context)
        
        assert result["success"] is False
        assert "safety_violation" in result["error_type"]
    
    @pytest.mark.asyncio
    async def test_create_directory_success(self, file_tools, mock_context, temp_dir):
        """Test successful directory creation."""
        new_dir = temp_dir / "new_directory"
        
        result = await file_tools.create_directory(str(new_dir), ctx=mock_context)
        
        assert result["success"] is True
        assert new_dir.exists()
    
    @pytest.mark.asyncio
    async def test_list_directory_with_limits(self, file_tools, mock_context, temp_dir):
        """Test directory listing with item limits."""
        # Create multiple files
        for i in range(15):
            (temp_dir / f"file{i}.txt").write_text(f"content {i}")
        
        result = await file_tools.list_directory(
            str(temp_dir), max_items=10, ctx=mock_context
        )
        
        assert result["success"] is True
        assert len(result["items"]) == 10
        assert result["truncated"] is True
    
    @given(
        source_path=st.text(min_size=1, max_size=100),
        dest_path=st.text(min_size=1, max_size=100)
    )
    @pytest.mark.asyncio
    async def test_copy_file_property_validation(self, file_tools, source_path, dest_path):
        """Property-based test for file copy validation."""
        assume(len(source_path.strip()) > 0 and len(dest_path.strip()) > 0)
        
        # Test that validation always occurs
        result = await file_tools.copy_file(source_path, dest_path)
        
        # Should either succeed or fail with proper error handling
        assert "success" in result
        assert isinstance(result["success"], bool)
        
        if not result["success"]:
            assert "error" in result
            assert "error_type" in result


class TestApplicationControlTools:
    """Test suite for application control MCP tools."""
    
    @pytest.fixture
    def mcp_server(self):
        return Mock(spec=FastMCP)
    
    @pytest.fixture
    def app_tools(self, mcp_server):
        return ApplicationControlTools(mcp_server)
    
    @pytest.fixture
    def mock_context(self):
        context = AsyncMock(spec=Context)
        context.info = AsyncMock()
        context.error = AsyncMock()
        context.report_progress = AsyncMock()
        return context
    
    @pytest.mark.asyncio
    async def test_launch_application_validation(self, app_tools, mock_context):
        """Test application launch validation."""
        # Test empty application identifier
        result = await app_tools.launch_application("", ctx=mock_context)
        
        assert result["success"] is False
        assert result["error_type"] == "validation_error"
    
    @pytest.mark.asyncio
    async def test_launch_application_permission_check(self, app_tools, mock_context):
        """Test permission checking for application launch."""
        with patch('src.boundaries.permission_checker.permission_checker') as mock_checker:
            mock_checker.check_permission.return_value = Mock(
                status=Mock(value="denied"),
                details="Permission denied",
                recovery_suggestion="Enable in System Preferences"
            )
            
            result = await app_tools.launch_application("com.apple.finder", ctx=mock_context)
            
            assert result["success"] is False
            assert result["error_type"] == "permission_denied"
    
    @pytest.mark.asyncio
    async def test_quit_application_not_running(self, app_tools, mock_context):
        """Test quitting application that's not running."""
        with patch.object(app_tools, '_verify_app_running', return_value=False):
            result = await app_tools.quit_application("com.apple.finder", ctx=mock_context)
            
            assert result["success"] is True
            assert result["was_running"] is False
    
    @pytest.mark.asyncio
    async def test_application_info_retrieval(self, app_tools, mock_context):
        """Test getting application information."""
        with patch.object(app_tools, '_verify_app_running', return_value=True):
            result = await app_tools.get_application_info("com.apple.finder", ctx=mock_context)
            
            assert result["success"] is True
            assert result["is_running"] is True
            assert "identifier_type" in result
    
    @given(app_id=st.text(min_size=1, max_size=50))
    @pytest.mark.asyncio
    async def test_app_validation_properties(self, app_tools, app_id):
        """Property-based test for application identifier validation."""
        assume(len(app_id.strip()) > 0)
        
        result = await app_tools.check_application_running(app_id)
        
        # Should always handle validation properly
        assert "success" in result
        if not result["success"]:
            assert "error_type" in result


class TestWindowManagementTools:
    """Test suite for window management MCP tools."""
    
    @pytest.fixture
    def mcp_server(self):
        return Mock(spec=FastMCP)
    
    @pytest.fixture
    def window_tools(self, mcp_server):
        return WindowManagementTools(mcp_server)
    
    @pytest.fixture
    def mock_context(self):
        context = AsyncMock(spec=Context)
        context.info = AsyncMock()
        context.error = AsyncMock()
        return context
    
    @pytest.mark.asyncio
    async def test_move_window_coordinate_validation(self, window_tools, mock_context):
        """Test window move with coordinate validation."""
        with patch('src.utils.coordinate_utils.coordinate_validator') as mock_validator:
            mock_validator.validate_coordinates.return_value = Mock(
                is_valid=False,
                error_message="Coordinates out of bounds",
                recovery_suggestion="Use coordinates within screen bounds"
            )
            
            result = await window_tools.move_window("com.apple.finder", -1000, -1000, ctx=mock_context)
            
            assert result["success"] is False
            assert result["error_type"] == "validation_error"
    
    @pytest.mark.asyncio
    async def test_resize_window_dimension_validation(self, window_tools, mock_context):
        """Test window resize with invalid dimensions."""
        result = await window_tools.resize_window("com.apple.finder", -100, -100, ctx=mock_context)
        
        assert result["success"] is False
        assert result["error_type"] == "validation_error"
        assert "Invalid dimensions" in result["error"]
    
    @pytest.mark.asyncio
    async def test_window_info_parsing(self, window_tools):
        """Test window information parsing."""
        # Mock window info string
        info_string = '{"title": "Test Window", "position": {100, 200}, "size": {800, 600}, "visible": true, "minimized": false}'
        
        parsed_info = window_tools._parse_window_info(info_string)
        
        assert "title" in parsed_info
        assert "position" in parsed_info
        assert "size" in parsed_info
        assert isinstance(parsed_info["visible"], bool)
    
    @pytest.mark.asyncio
    async def test_arrange_windows_tile_layout(self, window_tools, mock_context):
        """Test window arrangement in tile layout."""
        apps = ["com.apple.finder", "com.apple.safari"]
        
        with patch.object(window_tools, '_execute_window_move', return_value=True):
            with patch.object(window_tools, '_execute_window_resize', return_value=True):
                result = await window_tools.arrange_windows("tile", apps, ctx=mock_context)
                
                assert result["success"] is True
                assert result["layout"] == "tile"
    
    @given(
        x=st.integers(min_value=-2000, max_value=5000),
        y=st.integers(min_value=-2000, max_value=5000),
        width=st.integers(min_value=1, max_value=3000),
        height=st.integers(min_value=1, max_value=3000)
    )
    @pytest.mark.asyncio
    async def test_window_operations_coordinate_properties(self, window_tools, x, y, width, height):
        """Property-based test for window coordinate handling."""
        # Test that coordinate validation always produces consistent results
        with patch('src.validators.system_validators.system_validator') as mock_validator:
            mock_validator.validate_application_identifier.return_value = Mock(
                is_valid=True,
                sanitized_input="test.app"
            )
            
            move_result = await window_tools.move_window("test.app", x, y)
            resize_result = await window_tools.resize_window("test.app", width, height)
            
            # Both operations should handle validation consistently
            assert "success" in move_result
            assert "success" in resize_result


class TestInterfaceAutomationTools:
    """Test suite for interface automation MCP tools."""
    
    @pytest.fixture
    def mcp_server(self):
        return Mock(spec=FastMCP)
    
    @pytest.fixture
    def interface_tools(self, mcp_server):
        return InterfaceAutomationTools(mcp_server)
    
    @pytest.fixture
    def mock_context(self):
        context = AsyncMock(spec=Context)
        context.info = AsyncMock()
        context.error = AsyncMock()
        context.report_progress = AsyncMock()
        return context
    
    @pytest.mark.asyncio
    async def test_click_coordinate_validation(self, interface_tools, mock_context):
        """Test click operation coordinate validation."""
        with patch('src.utils.coordinate_utils.normalize_coordinates') as mock_normalize:
            mock_normalize.return_value = (100, 200)
            
            with patch('src.core.system_operations.system_manager') as mock_manager:
                mock_manager.click_at_coordinates.return_value = Mock(
                    status=Mock(value="success"),
                    message="Click successful",
                    execution_time=0.1
                )
                
                result = await interface_tools.click_at_coordinates(50, 100, ctx=mock_context)
                
                # Should normalize coordinates and succeed
                assert result["success"] is True
                assert result["coordinates"]["x"] == 100
                assert result["coordinates"]["y"] == 200
    
    @pytest.mark.asyncio
    async def test_click_type_validation(self, interface_tools, mock_context):
        """Test click type validation."""
        result = await interface_tools.click_at_coordinates(100, 100, "invalid_click", ctx=mock_context)
        
        assert result["success"] is False
        assert result["error_type"] == "validation_error"
        assert "supported_types" in result
    
    @pytest.mark.asyncio
    async def test_text_input_validation(self, interface_tools, mock_context):
        """Test text input validation and sanitization."""
        # Test with text containing null bytes
        dangerous_text = "test\x00content"
        
        with patch('src.validators.system_validators.system_validator') as mock_validator:
            mock_validator.validate_input_text.return_value = Mock(
                is_valid=True,
                sanitized_input="testcontent",
                warnings=["Text contains null bytes"]
            )
            
            result = await interface_tools.type_text(dangerous_text, ctx=mock_context)
            
            # Should indicate text was sanitized
            if result["success"]:
                assert result.get("text_sanitized") is True
    
    @pytest.mark.asyncio
    async def test_key_combination_safety(self, interface_tools, mock_context):
        """Test dangerous key combination blocking."""
        # Test dangerous key combination
        result = await interface_tools.press_key("escape", ["command", "option"], ctx=mock_context)
        
        assert result["success"] is False
        assert result["error_type"] == "safety_violation"
    
    @pytest.mark.asyncio
    async def test_drag_operation_validation(self, interface_tools, mock_context):
        """Test drag operation validation."""
        with patch('src.utils.coordinate_utils.normalize_coordinates') as mock_normalize:
            mock_normalize.side_effect = [(100, 100), (200, 200)]
            
            with patch.object(interface_tools, '_execute_drag', return_value=True):
                result = await interface_tools.drag_from_to(50, 50, 150, 150, ctx=mock_context)
                
                assert result["success"] is True
                assert result["start_coordinates"]["x"] == 100
                assert result["end_coordinates"]["x"] == 200
    
    @pytest.mark.asyncio
    async def test_scroll_direction_validation(self, interface_tools, mock_context):
        """Test scroll direction validation."""
        result = await interface_tools.scroll_at_coordinates(100, 100, 5, "invalid_direction", ctx=mock_context)
        
        assert result["success"] is False
        assert result["error_type"] == "validation_error"
        assert "supported_directions" in result
    
    @given(
        x=st.integers(min_value=-1000, max_value=3000),
        y=st.integers(min_value=-1000, max_value=3000),
        click_type=st.sampled_from(["left", "right", "double", "middle"])
    )
    @pytest.mark.asyncio
    async def test_click_properties(self, interface_tools, x, y, click_type):
        """Property-based test for click operations."""
        with patch('src.utils.coordinate_utils.normalize_coordinates') as mock_normalize:
            mock_normalize.return_value = (max(0, min(x, 1920)), max(0, min(y, 1080)))
            
            with patch('src.boundaries.permission_checker.permission_checker') as mock_checker:
                mock_checker.check_permission.return_value = Mock(
                    status=Mock(value="granted")
                )
                
                with patch('src.core.system_operations.system_manager') as mock_manager:
                    mock_manager.click_at_coordinates.return_value = Mock(
                        status=Mock(value="success"),
                        message="Click successful",
                        execution_time=0.1
                    )
                    
                    result = await interface_tools.click_at_coordinates(x, y, click_type)
                    
                    # Should always handle coordinate normalization
                    assert "success" in result
                    if result["success"]:
                        assert "coordinates" in result
                        assert result["click_type"] == click_type


class TestSystemIntegrationSuite:
    """Integration tests for system tools working together."""
    
    @pytest.fixture
    def all_tools(self):
        """Create all system tool instances."""
        mcp_server = Mock(spec=FastMCP)
        return {
            "file": FileOperationTools(mcp_server),
            "app": ApplicationControlTools(mcp_server),
            "window": WindowManagementTools(mcp_server),
            "interface": InterfaceAutomationTools(mcp_server)
        }
    
    @pytest.mark.asyncio
    async def test_workflow_app_launch_and_window_control(self, all_tools):
        """Test workflow: launch app, then control its window."""
        app_tools = all_tools["app"]
        window_tools = all_tools["window"]
        
        # Mock successful app launch
        with patch.object(app_tools, '_execute_app_launch', return_value=True):
            with patch.object(app_tools, '_verify_app_running', return_value=True):
                launch_result = await app_tools.launch_application("com.apple.finder")
                
                assert launch_result["success"] is True
                
                # Then try to move its window
                with patch.object(window_tools, '_execute_window_move', return_value=True):
                    move_result = await window_tools.move_window("com.apple.finder", 100, 100)
                    
                    # Should succeed if app is running
                    if launch_result["success"]:
                        assert "success" in move_result
    
    @pytest.mark.asyncio
    async def test_permission_consistency_across_tools(self, all_tools):
        """Test that permission checking is consistent across tools."""
        with patch('src.boundaries.permission_checker.permission_checker') as mock_checker:
            mock_checker.check_permission.return_value = Mock(
                status=Mock(value="denied"),
                details="Permission denied",
                recovery_suggestion="Enable permissions"
            )
            
            # All tools requiring accessibility should fail consistently
            app_result = await all_tools["app"].launch_application("test.app")
            window_result = await all_tools["window"].move_window("test.app", 100, 100)
            click_result = await all_tools["interface"].click_at_coordinates(100, 100)
            
            for result in [app_result, window_result, click_result]:
                assert result["success"] is False
                assert result["error_type"] == "permission_denied"
    
    @pytest.mark.asyncio
    async def test_error_recovery_suggestions(self, all_tools):
        """Test that all tools provide helpful error recovery suggestions."""
        # Test various error scenarios
        scenarios = [
            (all_tools["file"].copy_file, ("", "dest")),
            (all_tools["app"].launch_application, ("",)),
            (all_tools["window"].move_window, ("", -1000, -1000)),
            (all_tools["interface"].click_at_coordinates, (0, 0, "invalid"))
        ]
        
        for tool_method, args in scenarios:
            result = await tool_method(*args)
            
            if not result["success"]:
                # Should have either recovery_suggestion or recovery_suggestions
                has_recovery = ("recovery_suggestion" in result or 
                              "recovery_suggestions" in result or
                              "recovery_actions" in result)
                assert has_recovery, f"No recovery guidance for {tool_method.__name__}"


@pytest.mark.asyncio
async def test_system_validator_integration():
    """Test system validator integration across all tools."""
    # Test that system validator properly handles various input types
    test_cases = [
        ("file_path", "/valid/path/file.txt", True),
        ("file_path", "", False),
        ("file_path", "/System/dangerous", False),
        ("app_identifier", "com.apple.finder", True),
        ("app_identifier", "", False),
        ("input_text", "normal text", True),
        ("input_text", "text\x00with\x00nulls", True),  # Should sanitize
    ]
    
    for validation_type, test_input, should_be_valid in test_cases:
        if validation_type == "file_path":
            result = system_validator.validate_file_path(test_input)
        elif validation_type == "app_identifier":
            result = system_validator.validate_application_identifier(test_input)
        elif validation_type == "input_text":
            result = system_validator.validate_input_text(test_input)
        
        if should_be_valid:
            assert result.is_valid or result.result_type.value == "warning"
        else:
            assert not result.is_valid


@pytest.mark.asyncio 
async def test_permission_checker_integration():
    """Test permission checker integration."""
    from src.boundaries.permission_checker import PermissionType
    
    # Test permission checking for different types
    permission_types = [
        PermissionType.ACCESSIBILITY,
        PermissionType.FILE_READ,
        PermissionType.FILE_WRITE,
        PermissionType.AUTOMATION
    ]
    
    for perm_type in permission_types:
        result = permission_checker.check_permission(perm_type)
        
        # Should always return a valid result
        assert hasattr(result, 'status')
        assert hasattr(result, 'details')
        
        # Status should be one of the known values
        assert result.status.value in ["granted", "denied", "unknown", "not_required"]


def test_coordinate_validation_properties():
    """Property-based test for coordinate validation."""
    from src.utils.coordinate_utils import validate_screen_coordinates, normalize_coordinates
    
    @given(x=st.integers(), y=st.integers())
    def test_coordinate_normalization_properties(x, y):
        """Test that coordinate normalization always produces valid results."""
        norm_x, norm_y = normalize_coordinates(x, y)
        
        # Normalized coordinates should always be valid
        assert validate_screen_coordinates(norm_x, norm_y)
        
        # Normalized coordinates should be within reasonable bounds
        assert 0 <= norm_x <= 10000  # Reasonable upper bound
        assert 0 <= norm_y <= 10000
    
    test_coordinate_normalization_properties()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
