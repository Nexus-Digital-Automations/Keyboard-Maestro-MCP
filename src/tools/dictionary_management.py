"""Dictionary management MCP tools for Keyboard Maestro.

This module provides comprehensive MCP tools for Keyboard Maestro dictionary operations
including CRUD operations, JSON import/export, and bulk data management with type safety.

Key Features:
- Complete dictionary CRUD operations with validation
- JSON import/export for bulk operations
- Key-value management with type safety
- Dictionary structure validation and schema extraction
- Immutable transformation patterns
"""

from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

from fastmcp import FastMCP
from src.types.results import Result, OperationError, ErrorType
from src.core.variable_operations import DictionaryEntry, VariableOperations
from src.validators.variable_validators import DictionaryValidator
from src.pure.data_transformations import DictionaryTransformations, FormatTransformations
from src.core.km_interface import KeyboardMaestroInterface
from src.contracts.decorators import requires, ensures
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def register_dictionary_tools(mcp: FastMCP, km_interface: KeyboardMaestroInterface) -> None:
    """Register all dictionary management MCP tools."""
    
    @mcp.tool()
    @requires(lambda dictionary_name: isinstance(dictionary_name, str) and len(dictionary_name) > 0)
    @ensures(lambda result: isinstance(result, dict))
    async def km_create_dictionary(
        dictionary_name: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new Keyboard Maestro dictionary with optional initial data.
        
        Creates a new dictionary with validation and type safety. Supports
        initial data population with JSON structure validation.
        
        Args:
            dictionary_name: Name for the new dictionary
            initial_data: Optional initial key-value data
            
        Returns:
            Dict containing creation status and dictionary metadata
        """
        try:
            # Validate dictionary name
            name_result = DictionaryValidator.validate_dictionary_name(dictionary_name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            validated_name = name_result.unwrap()
            
            # Validate initial data if provided
            if initial_data is not None:
                data_result = DictionaryValidator.validate_dictionary_data(initial_data)
                if data_result.is_failure:
                    return {
                        'success': False,
                        'error': data_result._error.message,
                        'error_type': 'validation_error',
                        'suggestion': data_result._error.suggestion
                    }
                validated_data = data_result.unwrap()
            else:
                validated_data = {}
            
            # Create dictionary through Keyboard Maestro interface
            create_result = await km_interface.create_dictionary(validated_name, validated_data)
            
            if create_result.is_failure:
                return {
                    'success': False,
                    'error': create_result._error.message,
                    'error_type': create_result._error.error_type.value,
                    'suggestion': create_result._error.recovery_suggestion
                }
            
            dictionary_entry = create_result.unwrap()
            
            return {
                'success': True,
                'dictionary_name': dictionary_entry.name,
                'created_at': dictionary_entry.created_at.isoformat(),
                'key_count': len(dictionary_entry.data),
                'keys': list(dictionary_entry.data.keys()),
                'size_bytes': len(json.dumps(dictionary_entry.data))
            }
            
        except Exception as e:
            logger.error(f"Error creating dictionary {dictionary_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check dictionary name and initial data parameters'
            }
    
    @mcp.tool()
    @requires(lambda dictionary_name: isinstance(dictionary_name, str) and len(dictionary_name) > 0)
    @requires(lambda key: isinstance(key, str))
    @ensures(lambda result: isinstance(result, dict))
    async def km_get_dictionary_value(
        dictionary_name: str,
        key: str
    ) -> Dict[str, Any]:
        """Get value from Keyboard Maestro dictionary by key.
        
        Retrieves specific key value from dictionary with type preservation
        and error handling for non-existent keys or dictionaries.
        
        Args:
            dictionary_name: Name of the dictionary
            key: Key to retrieve
            
        Returns:
            Dict containing key value and metadata
        """
        try:
            # Validate dictionary name
            name_result = DictionaryValidator.validate_dictionary_name(dictionary_name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            validated_name = name_result.unwrap()
            
            # Get dictionary value through Keyboard Maestro interface
            value_result = await km_interface.get_dictionary_value(validated_name, key)
            
            if value_result.is_failure:
                return {
                    'success': False,
                    'error': value_result._error.message,
                    'error_type': value_result._error.error_type.value,
                    'suggestion': value_result._error.recovery_suggestion
                }
            
            value = value_result.unwrap()
            
            response = {
                'success': True,
                'dictionary_name': dictionary_name,
                'key': key,
                'exists': value is not None
            }
            
            if value is not None:
                response.update({
                    'value': value,
                    'value_type': type(value).__name__,
                    'retrieved_at': datetime.now().isoformat()
                })
            else:
                response['value'] = None
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting dictionary value {dictionary_name}[{key}]: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check dictionary name and key parameters'
            }
    
    @mcp.tool()
    @requires(lambda dictionary_name: isinstance(dictionary_name, str) and len(dictionary_name) > 0)
    @requires(lambda key: isinstance(key, str))
    @ensures(lambda result: isinstance(result, dict))
    async def km_set_dictionary_value(
        dictionary_name: str,
        key: str,
        value: Any
    ) -> Dict[str, Any]:
        """Set value in Keyboard Maestro dictionary with validation.
        
        Sets key-value pair in dictionary with JSON validation and type checking.
        Creates dictionary if it doesn't exist.
        
        Args:
            dictionary_name: Name of the dictionary
            key: Key to set
            value: Value to set (must be JSON-serializable)
            
        Returns:
            Dict containing operation status and metadata
        """
        try:
            # Validate dictionary name
            name_result = DictionaryValidator.validate_dictionary_name(dictionary_name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            validated_name = name_result.unwrap()
            
            # Validate value is JSON-serializable
            try:
                json.dumps(value)
            except (TypeError, ValueError) as e:
                return {
                    'success': False,
                    'error': f'Value is not JSON-serializable: {str(e)}',
                    'error_type': 'validation_error',
                    'suggestion': 'Ensure value contains only JSON-compatible types'
                }
            
            # Set dictionary value through Keyboard Maestro interface
            set_result = await km_interface.set_dictionary_value(validated_name, key, value)
            
            if set_result.is_failure:
                return {
                    'success': False,
                    'error': set_result._error.message,
                    'error_type': set_result._error.error_type.value,
                    'suggestion': set_result._error.recovery_suggestion
                }
            
            return {
                'success': True,
                'dictionary_name': dictionary_name,
                'key': key,
                'value': value,
                'value_type': type(value).__name__,
                'set_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error setting dictionary value {dictionary_name}[{key}]: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check dictionary name, key, and value parameters'
            }
    
    @mcp.tool()
    @requires(lambda dictionary_name: isinstance(dictionary_name, str) and len(dictionary_name) > 0)
    @ensures(lambda result: isinstance(result, dict))
    async def km_list_dictionary_keys(
        dictionary_name: str
    ) -> Dict[str, Any]:
        """List all keys in Keyboard Maestro dictionary.
        
        Retrieves all keys from dictionary with metadata and statistics.
        Provides key count and type information.
        
        Args:
            dictionary_name: Name of the dictionary
            
        Returns:
            Dict containing key list and dictionary metadata
        """
        try:
            # Validate dictionary name
            name_result = DictionaryValidator.validate_dictionary_name(dictionary_name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            validated_name = name_result.unwrap()
            
            # Get dictionary keys through Keyboard Maestro interface
            keys_result = await km_interface.get_dictionary_keys(validated_name)
            
            if keys_result.is_failure:
                return {
                    'success': False,
                    'error': keys_result._error.message,
                    'error_type': keys_result._error.error_type.value,
                    'suggestion': keys_result._error.recovery_suggestion
                }
            
            keys = keys_result.unwrap()
            
            return {
                'success': True,
                'dictionary_name': dictionary_name,
                'keys': keys,
                'key_count': len(keys),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error listing dictionary keys {dictionary_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check dictionary name parameter'
            }
    
    @mcp.tool()
    @requires(lambda dictionary_name: isinstance(dictionary_name, str) and len(dictionary_name) > 0)
    @requires(lambda json_data: isinstance(json_data, str))
    @ensures(lambda result: isinstance(result, dict))
    async def km_import_dictionary_json(
        dictionary_name: str,
        json_data: str,
        merge_mode: str = 'replace'
    ) -> Dict[str, Any]:
        """Import JSON data into Keyboard Maestro dictionary.
        
        Imports JSON data with validation and merge options. Supports
        replacing existing data or merging with current dictionary content.
        
        Args:
            dictionary_name: Name of the dictionary
            json_data: JSON string containing dictionary data
            merge_mode: Import mode ('replace' or 'merge')
            
        Returns:
            Dict containing import status and statistics
        """
        try:
            # Validate dictionary name
            name_result = DictionaryValidator.validate_dictionary_name(dictionary_name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            validated_name = name_result.unwrap()
            
            # Validate JSON data
            json_result = DictionaryValidator.validate_json_import(json_data)
            if json_result.is_failure:
                return {
                    'success': False,
                    'error': json_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': json_result._error.suggestion
                }
            
            import_data = json_result.unwrap()
            
            # Validate merge mode
            if merge_mode not in ['replace', 'merge']:
                return {
                    'success': False,
                    'error': 'Invalid merge mode',
                    'error_type': 'validation_error',
                    'suggestion': 'Use "replace" or "merge" for merge_mode'
                }
            
            # Import through Keyboard Maestro interface
            import_result = await km_interface.import_dictionary_json(
                validated_name, import_data, merge_mode == 'merge'
            )
            
            if import_result.is_failure:
                return {
                    'success': False,
                    'error': import_result._error.message,
                    'error_type': import_result._error.error_type.value,
                    'suggestion': import_result._error.recovery_suggestion
                }
            
            final_dictionary = import_result.unwrap()
            
            return {
                'success': True,
                'dictionary_name': dictionary_name,
                'merge_mode': merge_mode,
                'imported_keys': list(import_data.keys()),
                'total_keys': len(final_dictionary.data),
                'imported_at': datetime.now().isoformat(),
                'size_bytes': len(json.dumps(final_dictionary.data))
            }
            
        except Exception as e:
            logger.error(f"Error importing dictionary JSON {dictionary_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check dictionary name and JSON data parameters'
            }
    
    @mcp.tool()
    @requires(lambda dictionary_name: isinstance(dictionary_name, str) and len(dictionary_name) > 0)
    @ensures(lambda result: isinstance(result, dict))
    async def km_export_dictionary_json(
        dictionary_name: str,
        pretty_format: bool = True
    ) -> Dict[str, Any]:
        """Export Keyboard Maestro dictionary as JSON.
        
        Exports dictionary data as JSON string with formatting options.
        Includes metadata and statistics about the exported data.
        
        Args:
            dictionary_name: Name of the dictionary
            pretty_format: Whether to format JSON with indentation
            
        Returns:
            Dict containing JSON data and export metadata
        """
        try:
            # Validate dictionary name
            name_result = DictionaryValidator.validate_dictionary_name(dictionary_name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            validated_name = name_result.unwrap()
            
            # Export through Keyboard Maestro interface
            export_result = await km_interface.export_dictionary_json(validated_name)
            
            if export_result.is_failure:
                return {
                    'success': False,
                    'error': export_result._error.message,
                    'error_type': export_result._error.error_type.value,
                    'suggestion': export_result._error.recovery_suggestion
                }
            
            dictionary_entry = export_result.unwrap()
            
            # Format JSON
            if pretty_format:
                json_data = json.dumps(dictionary_entry.data, indent=2, sort_keys=True)
            else:
                json_data = json.dumps(dictionary_entry.data, separators=(',', ':'))
            
            # Extract schema
            schema = DictionaryTransformations.extract_schema(dictionary_entry)
            
            return {
                'success': True,
                'dictionary_name': dictionary_name,
                'json_data': json_data,
                'key_count': len(dictionary_entry.data),
                'keys': list(dictionary_entry.data.keys()),
                'schema': schema,
                'exported_at': datetime.now().isoformat(),
                'size_bytes': len(json_data),
                'created_at': dictionary_entry.created_at.isoformat(),
                'modified_at': dictionary_entry.modified_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting dictionary JSON {dictionary_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check dictionary name parameter'
            }
    
    @mcp.tool()
    @requires(lambda dictionary_name: isinstance(dictionary_name, str) and len(dictionary_name) > 0)
    @requires(lambda key: isinstance(key, str))
    @ensures(lambda result: isinstance(result, dict))
    async def km_delete_dictionary_key(
        dictionary_name: str,
        key: str
    ) -> Dict[str, Any]:
        """Delete key from Keyboard Maestro dictionary.
        
        Removes specified key from dictionary with confirmation.
        Provides safety checks and deletion confirmation.
        
        Args:
            dictionary_name: Name of the dictionary
            key: Key to delete
            
        Returns:
            Dict containing deletion status and confirmation
        """
        try:
            # Validate dictionary name
            name_result = DictionaryValidator.validate_dictionary_name(dictionary_name)
            if name_result.is_failure:
                return {
                    'success': False,
                    'error': name_result._error.message,
                    'error_type': 'validation_error',
                    'suggestion': name_result._error.suggestion
                }
            
            validated_name = name_result.unwrap()
            
            # Delete key through Keyboard Maestro interface
            delete_result = await km_interface.delete_dictionary_key(validated_name, key)
            
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
                'dictionary_name': dictionary_name,
                'key': key,
                'existed': existed,
                'deleted_at': datetime.now().isoformat(),
                'message': 'Key deleted successfully' if existed else 'Key did not exist'
            }
            
        except Exception as e:
            logger.error(f"Error deleting dictionary key {dictionary_name}[{key}]: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system_error',
                'suggestion': 'Check dictionary name and key parameters'
            }
