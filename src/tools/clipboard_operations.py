"""Clipboard management MCP tools for Keyboard Maestro.

This module provides comprehensive MCP tools for Keyboard Maestro clipboard operations
including current clipboard access, history management, named clipboards, and multiple
format support with type safety and validation.

Key Features:
- Current clipboard content access with format detection
- Clipboard history management (default 200 items)
- Named clipboard operations for persistent storage
- Multiple format support (text, image, file)
- Type-safe clipboard operations with validation
"""

from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

from fastmcp import FastMCP
from src.types.results import Result, OperationError, ErrorType
from src.core.variable_operations import ClipboardEntry, ClipboardSnapshot
from src.validators.variable_validators import ClipboardValidator
from src.pure.data_transformations import ClipboardTransformations
from src.core.km_interface import KeyboardMaestroInterface
from src.contracts.decorators import requires, ensures
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def register_clipboard_tools(mcp: FastMCP, km_interface: KeyboardMaestroInterface) -> None:
    """Register all clipboard management MCP tools."""
    
    @mcp.tool()
    @ensures(lambda result: isinstance(result, dict))
    async def km_get_clipboard(
        format_type: str = 'text'
    ) -> Dict[str, Any]:
        """Get current clipboard content with format detection.
        
        Retrieves current clipboard content with automatic format detection
        and type validation. Supports text, image, and file formats.
        
        Args:
            format_type: Preferred format ('text', 'image', 'file', 'auto')
            
        Returns:
            Dict containing clipboard content and metadata
        """
        try:
            # Validate format type
            if format_type not in ['text', 'image', 'file', 'auto']:
                return {
                    'success': False,
                    'error': f'Unsupported format type: {format_type}',
                    'error_type': 'validation_error',
                    'suggestion': 'Use one of: text, image, file, auto'
                }
            
            # Get clipboard content through Keyboard Maestro interface
            clipboard_result = await km_interface.get_clipboard_content(format_type)
            
            if clipboard_result.is_failure:
                return {
                    'success': False,
                    'error': clipboard_result._error.message,
                    'error_type': clipboard_result._error.error_type.value,
                    'suggestion': clipboard_result._error.recovery_suggestion
                }
            
            clipboard_entry = clipboard_result.unwrap()
            
            if clipboard_entry is None:
                return {
                    'success': True,
                    'has_content': False,
                    'format_requested': format_type,
                    'message': 'No clipboard content available in requested format'
                }
            
            # Create content summary for response
            content_summary = ClipboardTransformations.create_content_summary(clipboard_entry)
            
            response = {
                'success': True,
                'has_content': True,
                'format_type': clipboard_entry.format_type,
                'format_requested': format_type,
                'content': clipboard_entry.content,
                'timestamp': clipboard_entry.timestamp.isoformat(),
                'summary': content_summary
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting clipboard content: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check format type and clipboard access permissions'
            }
    
    @mcp.tool()
    @requires(lambda content: isinstance(content, str))
    @requires(lambda format_type: format_type in ['text', 'image', 'file'])
    @ensures(lambda result: isinstance(result, dict))
    async def km_set_clipboard(
        content: str,
        format_type: str = 'text'
    ) -> Dict[str, Any]:
        """Set clipboard content with format specification.
        
        Sets clipboard content with validation and format handling.
        Supports text, image path, and file path formats.
        
        Args:
            content: Content to set on clipboard
            format_type: Content format ('text', 'image', 'file')
            
        Returns:
            Dict containing operation status and metadata
        """
        try:
            # Validate clipboard content
            validation_result = ClipboardValidator.validate_clipboard_content(content, format_type)
            if validation_result.is_failure:
                return {
                    'success': False,
                    'error': validation_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': validation_result._error.suggestion
                }
            
            # Set clipboard content through Keyboard Maestro interface
            set_result = await km_interface.set_clipboard_content(content, format_type)
            
            if set_result.is_failure:
                return {
                    'success': False,
                    'error': set_result._error.message,
                    'error_type': set_result._error.error_type.value,
                    'suggestion': set_result._error.recovery_suggestion
                }
            
            return {
                'success': True,
                'content_length': len(content),
                'format_type': format_type,
                'set_at': datetime.now().isoformat(),
                'message': 'Clipboard content set successfully'
            }
            
        except Exception as e:
            logger.error(f"Error setting clipboard content: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check content and format parameters'
            }
    
    @mcp.tool()
    @requires(lambda count: isinstance(count, int) and count > 0)
    @ensures(lambda result: isinstance(result, dict))
    async def km_get_clipboard_history(
        count: int = 10,
        format_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get clipboard history with filtering and limits.
        
        Retrieves recent clipboard entries with optional format filtering
        and count limits. Provides metadata and content summaries.
        
        Args:
            count: Number of history entries to retrieve (max 200)
            format_filter: Optional format filter ('text', 'image', 'file')
            
        Returns:
            Dict containing clipboard history and metadata
        """
        try:
            # Validate count parameter
            if count <= 0 or count > 200:
                return {
                    'success': False,
                    'error': 'Count must be between 1 and 200',
                    'error_type': 'validation_error',
                    'suggestion': 'Use count between 1 and 200'
                }
            
            # Validate format filter if provided
            if format_filter and format_filter not in ['text', 'image', 'file']:
                return {
                    'success': False,
                    'error': f'Invalid format filter: {format_filter}',
                    'error_type': 'validation_error',
                    'suggestion': 'Use one of: text, image, file'
                }
            
            # Get clipboard history through Keyboard Maestro interface
            history_result = await km_interface.get_clipboard_history(count)
            
            if history_result.is_failure:
                return {
                    'success': False,
                    'error': history_result._error.message,
                    'error_type': history_result._error.error_type.value,
                    'suggestion': history_result._error.recovery_suggestion
                }
            
            clipboard_snapshot = history_result.unwrap()
            
            # Apply format filtering if specified
            if format_filter:
                filtered_snapshot = ClipboardTransformations.filter_clipboard_by_format(
                    clipboard_snapshot, format_filter
                )
            else:
                filtered_snapshot = clipboard_snapshot
            
            # Get history entries
            history_entries = filtered_snapshot.get_history_entries(count)
            
            # Build response with entry summaries
            entries_data = []
            for entry in history_entries:
                entry_summary = ClipboardTransformations.create_content_summary(entry)
                entries_data.append({
                    'index': entry.index,
                    'format_type': entry.format_type,
                    'content': entry.content,
                    'timestamp': entry.timestamp.isoformat(),
                    'summary': entry_summary
                })
            
            return {
                'success': True,
                'entries': entries_data,
                'total_entries': len(entries_data),
                'requested_count': count,
                'format_filter': format_filter,
                'current_index': filtered_snapshot.current_index,
                'max_history_size': filtered_snapshot.max_history_size,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting clipboard history: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check count and format filter parameters'
            }
    
    @mcp.tool()
    @requires(lambda index: isinstance(index, int) and index >= 0)
    @ensures(lambda result: isinstance(result, dict))
    async def km_get_clipboard_history_item(
        index: int
    ) -> Dict[str, Any]:
        """Get specific clipboard history item by index.
        
        Retrieves specific clipboard entry from history by index position.
        Index 0 is the most recent entry.
        
        Args:
            index: History index (0 = most recent, max 199)
            
        Returns:
            Dict containing clipboard entry data and metadata
        """
        try:
            # Validate history index
            validation_result = ClipboardValidator.validate_history_index(index)
            if validation_result.is_failure:
                return {
                    'success': False,
                    'error': validation_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': validation_result._error.suggestion
                }
            
            # Get clipboard history item through Keyboard Maestro interface
            item_result = await km_interface.get_clipboard_history_item(index)
            
            if item_result.is_failure:
                return {
                    'success': False,
                    'error': item_result._error.message,
                    'error_type': item_result._error.error_type.value,
                    'suggestion': item_result._error.recovery_suggestion
                }
            
            clipboard_entry = item_result.unwrap()
            
            if clipboard_entry is None:
                return {
                    'success': True,
                    'exists': False,
                    'index': index,
                    'message': 'No clipboard entry at specified index'
                }
            
            # Create content summary
            content_summary = ClipboardTransformations.create_content_summary(clipboard_entry)
            
            return {
                'success': True,
                'exists': True,
                'index': index,
                'format_type': clipboard_entry.format_type,
                'content': clipboard_entry.content,
                'timestamp': clipboard_entry.timestamp.isoformat(),
                'summary': content_summary,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting clipboard history item {index}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check index parameter'
            }
    
    @mcp.tool()
    @requires(lambda clipboard_name: isinstance(clipboard_name, str) and len(clipboard_name) > 0)
    @requires(lambda content: isinstance(content, str))
    @ensures(lambda result: isinstance(result, dict))
    async def km_set_named_clipboard(
        clipboard_name: str,
        content: str,
        format_type: str = 'text'
    ) -> Dict[str, Any]:
        """Set content in named clipboard for persistent storage.
        
        Creates or updates named clipboard with content. Named clipboards
        persist across sessions and provide organized storage.
        
        Args:
            clipboard_name: Name for the clipboard
            content: Content to store
            format_type: Content format ('text', 'image', 'file')
            
        Returns:
            Dict containing operation status and metadata
        """
        try:
            # Validate clipboard name
            if not clipboard_name or not clipboard_name.strip():
                return {
                    'success': False,
                    'error': 'Clipboard name cannot be empty',
                    'error_type': 'validation_error',
                    'suggestion': 'Provide a non-empty clipboard name'
                }
            
            # Validate content and format
            validation_result = ClipboardValidator.validate_clipboard_content(content, format_type)
            if validation_result.is_failure:
                return {
                    'success': False,
                    'error': validation_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': validation_result._error.suggestion
                }
            
            # Set named clipboard through Keyboard Maestro interface
            set_result = await km_interface.set_named_clipboard(clipboard_name, content, format_type)
            
            if set_result.is_failure:
                return {
                    'success': False,
                    'error': set_result._error.message,
                    'error_type': set_result._error.error_type.value,
                    'suggestion': set_result._error.recovery_suggestion
                }
            
            return {
                'success': True,
                'clipboard_name': clipboard_name,
                'content_length': len(content),
                'format_type': format_type,
                'set_at': datetime.now().isoformat(),
                'message': 'Named clipboard set successfully'
            }
            
        except Exception as e:
            logger.error(f"Error setting named clipboard {clipboard_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check clipboard name and content parameters'
            }
    
    @mcp.tool()
    @requires(lambda clipboard_name: isinstance(clipboard_name, str) and len(clipboard_name) > 0)
    @ensures(lambda result: isinstance(result, dict))
    async def km_get_named_clipboard(
        clipboard_name: str
    ) -> Dict[str, Any]:
        """Get content from named clipboard.
        
        Retrieves content from named clipboard with metadata.
        Named clipboards provide persistent storage across sessions.
        
        Args:
            clipboard_name: Name of the clipboard to retrieve
            
        Returns:
            Dict containing clipboard content and metadata
        """
        try:
            # Validate clipboard name
            if not clipboard_name or not clipboard_name.strip():
                return {
                    'success': False,
                    'error': 'Clipboard name cannot be empty',
                    'error_type': 'validation_error',
                    'suggestion': 'Provide a non-empty clipboard name'
                }
            
            # Get named clipboard through Keyboard Maestro interface
            clipboard_result = await km_interface.get_named_clipboard(clipboard_name)
            
            if clipboard_result.is_failure:
                return {
                    'success': False,
                    'error': clipboard_result._error.message,
                    'error_type': clipboard_result._error.error_type.value,
                    'suggestion': clipboard_result._error.recovery_suggestion
                }
            
            clipboard_entry = clipboard_result.unwrap()
            
            if clipboard_entry is None:
                return {
                    'success': True,
                    'exists': False,
                    'clipboard_name': clipboard_name,
                    'message': 'Named clipboard does not exist'
                }
            
            # Create content summary
            content_summary = ClipboardTransformations.create_content_summary(clipboard_entry)
            
            return {
                'success': True,
                'exists': True,
                'clipboard_name': clipboard_name,
                'format_type': clipboard_entry.format_type,
                'content': clipboard_entry.content,
                'timestamp': clipboard_entry.timestamp.isoformat(),
                'summary': content_summary,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting named clipboard {clipboard_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check clipboard name parameter'
            }
    
    @mcp.tool()
    @ensures(lambda result: isinstance(result, dict))
    async def km_list_named_clipboards() -> Dict[str, Any]:
        """List all named clipboards with metadata.
        
        Retrieves list of all named clipboards with summary information.
        Provides clipboard names, sizes, and creation metadata.
        
        Returns:
            Dict containing named clipboard list and summary
        """
        try:
            # Get named clipboards through Keyboard Maestro interface
            clipboards_result = await km_interface.list_named_clipboards()
            
            if clipboards_result.is_failure:
                return {
                    'success': False,
                    'error': clipboards_result._error.message,
                    'error_type': clipboards_result._error.error_type.value,
                    'suggestion': clipboards_result._error.recovery_suggestion
                }
            
            named_clipboards = clipboards_result.unwrap()
            
            # Build clipboard summaries
            clipboard_list = []
            for clipboard_name, clipboard_entry in named_clipboards.items():
                content_summary = ClipboardTransformations.create_content_summary(clipboard_entry)
                clipboard_list.append({
                    'name': clipboard_name,
                    'format_type': clipboard_entry.format_type,
                    'content_length': len(clipboard_entry.content),
                    'timestamp': clipboard_entry.timestamp.isoformat(),
                    'summary': content_summary
                })
            
            # Sort by name for consistent ordering
            clipboard_list.sort(key=lambda x: x['name'])
            
            return {
                'success': True,
                'named_clipboards': clipboard_list,
                'total_count': len(clipboard_list),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error listing named clipboards: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check clipboard access permissions'
            }
    
    @mcp.tool()
    @requires(lambda clipboard_name: isinstance(clipboard_name, str) and len(clipboard_name) > 0)
    @ensures(lambda result: isinstance(result, dict))
    async def km_delete_named_clipboard(
        clipboard_name: str
    ) -> Dict[str, Any]:
        """Delete named clipboard.
        
        Removes named clipboard with confirmation. Provides safety check
        and deletion confirmation for persistent clipboard storage.
        
        Args:
            clipboard_name: Name of the clipboard to delete
            
        Returns:
            Dict containing deletion status and confirmation
        """
        try:
            # Validate clipboard name
            if not clipboard_name or not clipboard_name.strip():
                return {
                    'success': False,
                    'error': 'Clipboard name cannot be empty',
                    'error_type': 'validation_error',
                    'suggestion': 'Provide a non-empty clipboard name'
                }
            
            # Delete named clipboard through Keyboard Maestro interface
            delete_result = await km_interface.delete_named_clipboard(clipboard_name)
            
            if delete_result.is_failure:
                return {
                    'success': False,
                    'error': delete_result._error.message,
                    'error_type': delete_result._error.error_type.value,
                    'suggestion': delete_result._error.recovery_suggestion
                }
            
            existed = delete_result.unwrap()
            
            return {
                'success': True,
                'clipboard_name': clipboard_name,
                'existed': existed,
                'deleted_at': datetime.now().isoformat(),
                'message': 'Named clipboard deleted successfully' if existed else 'Named clipboard did not exist'
            }
            
        except Exception as e:
            logger.error(f"Error deleting named clipboard {clipboard_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check clipboard name parameter'
            }
