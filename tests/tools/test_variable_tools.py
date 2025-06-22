"""Tests for variable management MCP tools.

This module provides comprehensive tests for variable, dictionary, and clipboard
MCP tools using property-based testing and contract verification.

Key Features:
- Property-based testing for variable operations
- Contract compliance verification
- Mock Keyboard Maestro interface testing
- Type safety validation testing
- Immutability pattern verification
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from typing import Dict, Any, Optional

from src.tools.variable_management import register_variable_tools
from src.tools.dictionary_management import register_dictionary_tools
from src.tools.clipboard_operations import register_clipboard_tools
from src.types.domain_types import VariableName, VariableValue
from src.types.enumerations import VariableScope
from src.types.results import Result, OperationError, ErrorType
from src.core.variable_operations import VariableEntry, VariableMetadata, VariableSnapshot
from src.core.variable_operations import DictionaryEntry, ClipboardEntry, ClipboardSnapshot
from fastmcp import FastMCP


@pytest.fixture
def mock_km_interface():
    """Mock Keyboard Maestro interface for testing."""
    interface = Mock()
    
    # Variable operations
    interface.get_variable = AsyncMock()
    interface.set_variable = AsyncMock()
    interface.delete_variable = AsyncMock()
    interface.variable_exists = AsyncMock()
    interface.get_all_variables_snapshot = AsyncMock()
    interface.get_variables_by_scope = AsyncMock()
    
    # Dictionary operations
    interface.create_dictionary = AsyncMock()
    interface.get_dictionary_value = AsyncMock()
    interface.set_dictionary_value = AsyncMock()
    interface.get_dictionary_keys = AsyncMock()
    interface.import_dictionary_json = AsyncMock()
    interface.export_dictionary_json = AsyncMock()
    interface.delete_dictionary_key = AsyncMock()
    
    # Clipboard operations
    interface.get_clipboard_content = AsyncMock()
    interface.set_clipboard_content = AsyncMock()
    interface.get_clipboard_history = AsyncMock()
    interface.get_clipboard_history_item = AsyncMock()
    interface.set_named_clipboard = AsyncMock()
    interface.get_named_clipboard = AsyncMock()
    interface.list_named_clipboards = AsyncMock()
    interface.delete_named_clipboard = AsyncMock()
    
    return interface


@pytest.fixture
def mcp_server(mock_km_interface):
    """FastMCP server with registered tools for testing."""
    mcp = FastMCP("test-server")
    register_variable_tools(mcp, mock_km_interface)
    register_dictionary_tools(mcp, mock_km_interface)
    register_clipboard_tools(mcp, mock_km_interface)
    return mcp


@pytest.fixture
def sample_variable_entry():
    """Sample variable entry for testing."""
    metadata = VariableMetadata(
        name=VariableName("test_variable"),
        scope=VariableScope.GLOBAL,
        instance_id=None,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        is_password=False
    )
    return VariableEntry(metadata=metadata, value=VariableValue("test_value"))


@pytest.fixture
def sample_dictionary_entry():
    """Sample dictionary entry for testing."""
    return DictionaryEntry(
        name="test_dict",
        data={"key1": "value1", "key2": 42, "key3": True},
        created_at=datetime.now(),
        modified_at=datetime.now()
    )


@pytest.fixture
def sample_clipboard_entry():
    """Sample clipboard entry for testing."""
    return ClipboardEntry(
        content="test clipboard content",
        format_type="text",
        timestamp=datetime.now(),
        index=0
    )


class TestVariableManagementTools:
    """Test cases for variable management MCP tools."""
    
    @pytest.mark.asyncio
    async def test_km_get_variable_success(self, mcp_server, mock_km_interface, sample_variable_entry):
        """Test successful variable retrieval."""
        # Setup mock
        mock_km_interface.get_variable.return_value = Result.success(sample_variable_entry)
        
        # Call tool
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "test_variable",
            "scope": "global"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['exists'] is True
        assert result['name'] == "test_variable"
        assert result['scope'] == "global"
        assert result['value'] == "test_value"
        assert result['is_password'] is False
        
        # Verify interface call
        mock_km_interface.get_variable.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_km_get_variable_not_found(self, mcp_server, mock_km_interface):
        """Test variable retrieval when variable doesn't exist."""
        # Setup mock
        mock_km_interface.get_variable.return_value = Result.success(None)
        
        # Call tool
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "nonexistent_variable",
            "scope": "global"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['exists'] is False
        assert result['value'] is None
    
    @pytest.mark.asyncio
    async def test_km_get_variable_invalid_name(self, mcp_server, mock_km_interface):
        """Test variable retrieval with invalid name."""
        # Call tool with invalid name
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "",
            "scope": "global"
        })
        
        # Verify validation error
        assert result['success'] is False
        assert result['error_type'] == 'validation_error'
        assert 'empty' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_km_set_variable_success(self, mcp_server, mock_km_interface):
        """Test successful variable setting."""
        # Setup mock
        mock_km_interface.set_variable.return_value = Result.success(True)
        
        # Call tool
        result = await mcp_server.call_tool("km_set_variable", {
            "name": "test_variable",
            "value": "test_value",
            "scope": "global"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['name'] == "test_variable"
        assert result['value'] == "test_value"
        assert result['scope'] == "global"
        
        # Verify interface call
        mock_km_interface.set_variable.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_km_set_variable_password_detection(self, mcp_server, mock_km_interface):
        """Test automatic password variable detection."""
        # Setup mock
        mock_km_interface.set_variable.return_value = Result.success(True)
        
        # Call tool with password-like name
        result = await mcp_server.call_tool("km_set_variable", {
            "name": "user_password",
            "value": "secret123",
            "scope": "global"
        })
        
        # Verify password detection
        assert result['success'] is True
        assert result['is_password'] is True
        assert result['value'] == "<password_set>"
    
    @pytest.mark.asyncio
    async def test_km_delete_variable_success(self, mcp_server, mock_km_interface, sample_variable_entry):
        """Test successful variable deletion."""
        # Setup mocks
        mock_km_interface.get_variable.return_value = Result.success(sample_variable_entry)
        mock_km_interface.delete_variable.return_value = Result.success(True)
        
        # Call tool
        result = await mcp_server.call_tool("km_delete_variable", {
            "name": "test_variable",
            "scope": "global"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['existed'] is True
        assert result['name'] == "test_variable"
    
    @pytest.mark.asyncio
    async def test_km_list_variables_success(self, mcp_server, mock_km_interface, sample_variable_entry):
        """Test successful variable listing."""
        # Setup mock
        snapshot = VariableSnapshot(
            variables=frozenset([sample_variable_entry]),
            snapshot_time=datetime.now()
        )
        mock_km_interface.get_variables_by_scope.return_value = Result.success(snapshot)
        
        # Call tool
        result = await mcp_server.call_tool("km_list_variables", {
            "scope": "global",
            "limit": 10
        })
        
        # Verify result
        assert result['success'] is True
        assert len(result['variables']) == 1
        assert result['variables'][0]['name'] == "test_variable"
        assert result['total_found'] == 1
    
    @pytest.mark.asyncio
    async def test_km_variable_exists_success(self, mcp_server, mock_km_interface):
        """Test variable existence check."""
        # Setup mock
        mock_km_interface.variable_exists.return_value = Result.success(True)
        
        # Call tool
        result = await mcp_server.call_tool("km_variable_exists", {
            "name": "test_variable",
            "scope": "global"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['exists'] is True
        assert result['name'] == "test_variable"


class TestDictionaryManagementTools:
    """Test cases for dictionary management MCP tools."""
    
    @pytest.mark.asyncio
    async def test_km_create_dictionary_success(self, mcp_server, mock_km_interface, sample_dictionary_entry):
        """Test successful dictionary creation."""
        # Setup mock
        mock_km_interface.create_dictionary.return_value = Result.success(sample_dictionary_entry)
        
        # Call tool
        result = await mcp_server.call_tool("km_create_dictionary", {
            "dictionary_name": "test_dict",
            "initial_data": {"key1": "value1"}
        })
        
        # Verify result
        assert result['success'] is True
        assert result['dictionary_name'] == "test_dict"
        assert result['key_count'] == 3
        assert 'key1' in result['keys']
    
    @pytest.mark.asyncio
    async def test_km_get_dictionary_value_success(self, mcp_server, mock_km_interface):
        """Test successful dictionary value retrieval."""
        # Setup mock
        mock_km_interface.get_dictionary_value.return_value = Result.success("value1")
        
        # Call tool
        result = await mcp_server.call_tool("km_get_dictionary_value", {
            "dictionary_name": "test_dict",
            "key": "key1"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['exists'] is True
        assert result['value'] == "value1"
        assert result['key'] == "key1"
    
    @pytest.mark.asyncio
    async def test_km_set_dictionary_value_success(self, mcp_server, mock_km_interface):
        """Test successful dictionary value setting."""
        # Setup mock
        mock_km_interface.set_dictionary_value.return_value = Result.success(True)
        
        # Call tool
        result = await mcp_server.call_tool("km_set_dictionary_value", {
            "dictionary_name": "test_dict",
            "key": "new_key",
            "value": "new_value"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['key'] == "new_key"
        assert result['value'] == "new_value"
    
    @pytest.mark.asyncio
    async def test_km_import_dictionary_json_success(self, mcp_server, mock_km_interface, sample_dictionary_entry):
        """Test successful JSON import."""
        # Setup mock
        mock_km_interface.import_dictionary_json.return_value = Result.success(sample_dictionary_entry)
        
        # Call tool
        json_data = '{"key1": "value1", "key2": 42}'
        result = await mcp_server.call_tool("km_import_dictionary_json", {
            "dictionary_name": "test_dict",
            "json_data": json_data,
            "merge_mode": "replace"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['dictionary_name'] == "test_dict"
        assert result['merge_mode'] == "replace"
        assert len(result['imported_keys']) == 2
    
    @pytest.mark.asyncio
    async def test_km_export_dictionary_json_success(self, mcp_server, mock_km_interface, sample_dictionary_entry):
        """Test successful JSON export."""
        # Setup mock
        mock_km_interface.export_dictionary_json.return_value = Result.success(sample_dictionary_entry)
        
        # Call tool
        result = await mcp_server.call_tool("km_export_dictionary_json", {
            "dictionary_name": "test_dict",
            "pretty_format": True
        })
        
        # Verify result
        assert result['success'] is True
        assert result['dictionary_name'] == "test_dict"
        assert result['key_count'] == 3
        assert 'json_data' in result
        assert isinstance(result['json_data'], str)


class TestClipboardOperationTools:
    """Test cases for clipboard operation MCP tools."""
    
    @pytest.mark.asyncio
    async def test_km_get_clipboard_success(self, mcp_server, mock_km_interface, sample_clipboard_entry):
        """Test successful clipboard content retrieval."""
        # Setup mock
        mock_km_interface.get_clipboard_content.return_value = Result.success(sample_clipboard_entry)
        
        # Call tool
        result = await mcp_server.call_tool("km_get_clipboard", {
            "format_type": "text"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['has_content'] is True
        assert result['content'] == "test clipboard content"
        assert result['format_type'] == "text"
    
    @pytest.mark.asyncio
    async def test_km_set_clipboard_success(self, mcp_server, mock_km_interface):
        """Test successful clipboard content setting."""
        # Setup mock
        mock_km_interface.set_clipboard_content.return_value = Result.success(True)
        
        # Call tool
        result = await mcp_server.call_tool("km_set_clipboard", {
            "content": "new clipboard content",
            "format_type": "text"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['content_length'] == len("new clipboard content")
        assert result['format_type'] == "text"
    
    @pytest.mark.asyncio
    async def test_km_get_clipboard_history_success(self, mcp_server, mock_km_interface, sample_clipboard_entry):
        """Test successful clipboard history retrieval."""
        # Setup mock
        snapshot = ClipboardSnapshot(
            entries=(sample_clipboard_entry,),
            current_index=0,
            max_history_size=200
        )
        mock_km_interface.get_clipboard_history.return_value = Result.success(snapshot)
        
        # Call tool
        result = await mcp_server.call_tool("km_get_clipboard_history", {
            "count": 5
        })
        
        # Verify result
        assert result['success'] is True
        assert len(result['entries']) == 1
        assert result['entries'][0]['content'] == "test clipboard content"
        assert result['requested_count'] == 5
    
    @pytest.mark.asyncio
    async def test_km_set_named_clipboard_success(self, mcp_server, mock_km_interface):
        """Test successful named clipboard setting."""
        # Setup mock
        mock_km_interface.set_named_clipboard.return_value = Result.success(True)
        
        # Call tool
        result = await mcp_server.call_tool("km_set_named_clipboard", {
            "clipboard_name": "test_clipboard",
            "content": "named clipboard content",
            "format_type": "text"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['clipboard_name'] == "test_clipboard"
        assert result['format_type'] == "text"
    
    @pytest.mark.asyncio
    async def test_km_get_named_clipboard_success(self, mcp_server, mock_km_interface, sample_clipboard_entry):
        """Test successful named clipboard retrieval."""
        # Setup mock
        mock_km_interface.get_named_clipboard.return_value = Result.success(sample_clipboard_entry)
        
        # Call tool
        result = await mcp_server.call_tool("km_get_named_clipboard", {
            "clipboard_name": "test_clipboard"
        })
        
        # Verify result
        assert result['success'] is True
        assert result['exists'] is True
        assert result['content'] == "test clipboard content"
        assert result['clipboard_name'] == "test_clipboard"


class TestValidationAndErrorHandling:
    """Test cases for validation and error handling."""
    
    @pytest.mark.asyncio
    async def test_variable_name_validation(self, mcp_server, mock_km_interface):
        """Test variable name validation."""
        # Test empty name
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "",
            "scope": "global"
        })
        assert result['success'] is False
        assert result['error_type'] == 'validation_error'
        
        # Test invalid characters
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "invalid-name-with-hyphens",
            "scope": "global"
        })
        assert result['success'] is False
        assert result['error_type'] == 'validation_error'
    
    @pytest.mark.asyncio
    async def test_scope_validation(self, mcp_server, mock_km_interface):
        """Test variable scope validation."""
        # Test invalid scope
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "test_var",
            "scope": "invalid_scope"
        })
        assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_instance_variable_validation(self, mcp_server, mock_km_interface):
        """Test instance variable validation requires instance_id."""
        # Instance variables should require instance_id
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "test_var",
            "scope": "instance"
            # Missing instance_id
        })
        assert result['success'] is False
        assert result['error_type'] == 'validation_error'
    
    @pytest.mark.asyncio
    async def test_json_validation(self, mcp_server, mock_km_interface):
        """Test JSON validation for dictionary import."""
        # Test invalid JSON
        result = await mcp_server.call_tool("km_import_dictionary_json", {
            "dictionary_name": "test_dict",
            "json_data": "invalid json {"
        })
        assert result['success'] is False
        assert result['error_type'] == 'validation_error'
    
    @pytest.mark.asyncio
    async def test_clipboard_format_validation(self, mcp_server, mock_km_interface):
        """Test clipboard format validation."""
        # Test invalid format
        result = await mcp_server.call_tool("km_get_clipboard", {
            "format_type": "invalid_format"
        })
        assert result['success'] is False
        assert result['error_type'] == 'validation_error'


class TestContractCompliance:
    """Test cases for contract compliance."""
    
    @pytest.mark.asyncio
    async def test_function_contracts(self, mcp_server, mock_km_interface):
        """Test that functions satisfy their contracts."""
        # All tools should return dictionaries
        tools_to_test = [
            ("km_get_variable", {"name": "test", "scope": "global"}),
            ("km_set_variable", {"name": "test", "value": "value", "scope": "global"}),
            ("km_variable_exists", {"name": "test", "scope": "global"})
        ]
        
        # Setup mocks for successful operations
        mock_km_interface.get_variable.return_value = Result.success(None)
        mock_km_interface.set_variable.return_value = Result.success(True)
        mock_km_interface.variable_exists.return_value = Result.success(True)
        
        for tool_name, params in tools_to_test:
            result = await mcp_server.call_tool(tool_name, params)
            assert isinstance(result, dict), f"{tool_name} must return dict"
            assert 'success' in result, f"{tool_name} must include success field"
    
    @pytest.mark.asyncio
    async def test_immutability_preservation(self, sample_variable_entry):
        """Test that data transformations preserve immutability."""
        # Original entry should not be modified
        original_value = sample_variable_entry.value
        original_modified_time = sample_variable_entry.metadata.modified_at
        
        # Create new entry with different value
        new_entry = sample_variable_entry.with_value(VariableValue("new_value"))
        
        # Verify original is unchanged
        assert sample_variable_entry.value == original_value
        assert sample_variable_entry.metadata.modified_at == original_modified_time
        
        # Verify new entry has changes
        assert new_entry.value == "new_value"
        assert new_entry.metadata.modified_at > original_modified_time


@pytest.mark.integration
class TestToolIntegration:
    """Integration tests for tool interactions."""
    
    @pytest.mark.asyncio
    async def test_variable_lifecycle(self, mcp_server, mock_km_interface):
        """Test complete variable lifecycle operations."""
        # Setup mocks for lifecycle
        mock_km_interface.variable_exists.return_value = Result.success(False)
        mock_km_interface.set_variable.return_value = Result.success(True)
        mock_km_interface.get_variable.return_value = Result.success(None)  # Will be updated
        mock_km_interface.delete_variable.return_value = Result.success(True)
        
        # 1. Check variable doesn't exist
        result = await mcp_server.call_tool("km_variable_exists", {
            "name": "lifecycle_test",
            "scope": "global"
        })
        assert result['exists'] is False
        
        # 2. Create variable
        result = await mcp_server.call_tool("km_set_variable", {
            "name": "lifecycle_test",
            "value": "test_value",
            "scope": "global"
        })
        assert result['success'] is True
        
        # 3. Update mock for retrieval
        metadata = VariableMetadata(
            name=VariableName("lifecycle_test"),
            scope=VariableScope.GLOBAL,
            instance_id=None,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            is_password=False
        )
        entry = VariableEntry(metadata=metadata, value=VariableValue("test_value"))
        mock_km_interface.get_variable.return_value = Result.success(entry)
        
        # 4. Retrieve variable
        result = await mcp_server.call_tool("km_get_variable", {
            "name": "lifecycle_test",
            "scope": "global"
        })
        assert result['success'] is True
        assert result['value'] == "test_value"
        
        # 5. Delete variable
        result = await mcp_server.call_tool("km_delete_variable", {
            "name": "lifecycle_test",
            "scope": "global"
        })
        assert result['success'] is True
        assert result['existed'] is True
