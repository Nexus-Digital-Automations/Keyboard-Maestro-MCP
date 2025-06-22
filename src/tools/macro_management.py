"""
Macro CRUD MCP tools with comprehensive validation.

This module provides MCP tools for creating, reading, updating, and deleting
Keyboard Maestro macros with contract-driven validation.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP

from src.types.domain_types import MacroIdentifier, MacroCreationData, MacroModificationData
from src.core.macro_operations import MacroOperations, MacroOperationStatus
from src.utils.macro_serialization import MacroFileManager, SerializationFormat
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_macro_identifier

logger = logging.getLogger(__name__)


class MacroManagementTools:
    """MCP tools for macro CRUD operations."""
    
    def __init__(self, macro_operations: MacroOperations):
        """Initialize with macro operations dependency."""
        self.macro_operations = macro_operations
        self.file_manager = MacroFileManager()
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register all macro management tools with the MCP server."""
        mcp_server.tool()(self.create_macro)
        mcp_server.tool()(self.get_macro_info)
        mcp_server.tool()(self.update_macro)
        mcp_server.tool()(self.delete_macro)
        mcp_server.tool()(self.list_macros)
        mcp_server.tool()(self.duplicate_macro)
        mcp_server.tool()(self.export_macro)
        mcp_server.tool()(self.import_macro)
        
        logger.info("Macro management tools registered")
    
    async def create_macro(
        self,
        name: str,
        group_uuid: Optional[str] = None,
        enabled: bool = True,
        color: Optional[str] = None,
        notes: Optional[str] = None,
        triggers: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Keyboard Maestro macro.
        
        Args:
            name: Macro name (required, unique within group)
            group_uuid: Target macro group UUID (optional)
            enabled: Whether macro starts enabled (default: True)
            color: Visual color coding (optional)
            notes: Macro documentation (optional)
            triggers: List of trigger configurations (optional)
            actions: List of action configurations (optional)
            
        Returns:
            Creation result with macro UUID
        """
        try:
            # Create macro data structure
            macro_data = MacroCreationData(
                name=name,
                group_uuid=group_uuid,
                enabled=enabled,
                color=color,
                notes=notes,
                triggers=triggers or [],
                actions=actions or []
            )
            
            # Create macro
            result = await self.macro_operations.create_macro(macro_data)
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "macro_uuid": result.macro_uuid,
                "error": result.error_details,
                "macro_name": name
            }
            
        except Exception as e:
            logger.error(f"Macro creation failed: {e}")
            return {
                "success": False,
                "error": f"Creation failed: {str(e)}",
                "error_code": "CREATION_ERROR"
            }
    
    async def get_macro_info(
        self,
        identifier: str,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive macro information.
        
        Args:
            identifier: Macro name or UUID
            include_details: Include triggers and actions (default: False)
            
        Returns:
            Macro information and metadata
        """
        try:
            if not is_valid_macro_identifier(identifier):
                return {
                    "found": False,
                    "error": "Invalid macro identifier",
                    "error_code": "INVALID_IDENTIFIER"
                }
            
            # Get macro info
            macro_info = await self.macro_operations.get_macro_info(identifier)
            if not macro_info:
                return {
                    "found": False,
                    "error": "Macro not found",
                    "error_code": "MACRO_NOT_FOUND"
                }
            
            result = {
                "found": True,
                "macro": {
                    "uuid": macro_info.uuid,
                    "name": macro_info.name,
                    "group_uuid": macro_info.group_uuid,
                    "enabled": macro_info.enabled,
                    "color": macro_info.color,
                    "notes": macro_info.notes,
                    "creation_date": macro_info.creation_date,
                    "modification_date": macro_info.modification_date,
                    "last_used": macro_info.last_used,
                    "trigger_count": macro_info.trigger_count,
                    "action_count": macro_info.action_count
                }
            }
            
            # Include detailed structure if requested
            if include_details:
                # Note: In a real implementation, this would fetch trigger/action details
                result["macro"]["triggers"] = []  # Placeholder
                result["macro"]["actions"] = []   # Placeholder
            
            return result
            
        except Exception as e:
            logger.error(f"Get macro info failed: {e}")
            return {
                "found": False,
                "error": f"Info retrieval failed: {str(e)}",
                "error_code": "INFO_ERROR"
            }
    
    async def update_macro(
        self,
        identifier: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        color: Optional[str] = None,
        notes: Optional[str] = None,
        group_uuid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update macro properties.
        
        Args:
            identifier: Macro name or UUID
            name: New macro name (optional)
            enabled: New enabled state (optional)
            color: New color (optional)
            notes: New notes (optional)
            group_uuid: New group UUID (optional)
            
        Returns:
            Update result and status
        """
        try:
            # Create update data structure
            updates = MacroModificationData()
            if name is not None:
                updates.name = name
            if enabled is not None:
                updates.enabled = enabled
            if color is not None:
                updates.color = color
            if notes is not None:
                updates.notes = notes
            if group_uuid is not None:
                updates.group_uuid = group_uuid
            
            # Apply updates
            result = await self.macro_operations.modify_macro(identifier, updates)
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "error": result.error_details,
                "updated_fields": {
                    "name": name,
                    "enabled": enabled,
                    "color": color,
                    "notes": notes,
                    "group_uuid": group_uuid
                }
            }
            
        except Exception as e:
            logger.error(f"Macro update failed: {e}")
            return {
                "success": False,
                "error": f"Update failed: {str(e)}",
                "error_code": "UPDATE_ERROR"
            }
    
    async def delete_macro(
        self,
        identifier: str,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a macro with safety confirmation.
        
        Args:
            identifier: Macro name or UUID
            confirm: Confirmation flag (required for deletion)
            
        Returns:
            Deletion result and status
        """
        try:
            if not confirm:
                return {
                    "success": False,
                    "error": "Confirmation required for deletion",
                    "error_code": "CONFIRMATION_REQUIRED",
                    "message": "Set confirm=True to proceed with deletion"
                }
            
            # Delete macro
            result = await self.macro_operations.delete_macro(identifier)
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "error": result.error_details,
                "deleted_identifier": identifier
            }
            
        except Exception as e:
            logger.error(f"Macro deletion failed: {e}")
            return {
                "success": False,
                "error": f"Deletion failed: {str(e)}",
                "error_code": "DELETION_ERROR"
            }
    
    async def list_macros(
        self,
        group_uuid: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List macros with optional filtering.
        
        Args:
            group_uuid: Filter by group UUID (optional)
            enabled_only: Show only enabled macros (default: False)
            limit: Maximum number of results (default: 100)
            
        Returns:
            List of macros with metadata
        """
        try:
            # Get macro list
            macros = await self.macro_operations.list_macros(group_uuid, enabled_only)
            
            # Apply limit
            if limit > 0:
                macros = macros[:limit]
            
            # Format results
            macro_list = []
            for macro in macros:
                macro_list.append({
                    "uuid": macro.uuid,
                    "name": macro.name,
                    "group_uuid": macro.group_uuid,
                    "enabled": macro.enabled,
                    "color": macro.color,
                    "trigger_count": macro.trigger_count,
                    "action_count": macro.action_count,
                    "last_used": macro.last_used
                })
            
            return {
                "success": True,
                "count": len(macro_list),
                "macros": macro_list,
                "filters": {
                    "group_uuid": group_uuid,
                    "enabled_only": enabled_only,
                    "limit": limit
                }
            }
            
        except Exception as e:
            logger.error(f"List macros failed: {e}")
            return {
                "success": False,
                "error": f"List operation failed: {str(e)}",
                "error_code": "LIST_ERROR"
            }
    
    async def duplicate_macro(
        self,
        identifier: str,
        new_name: str,
        group_uuid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Duplicate an existing macro.
        
        Args:
            identifier: Source macro name or UUID
            new_name: Name for the duplicated macro
            group_uuid: Target group UUID (optional, uses source group)
            
        Returns:
            Duplication result with new macro UUID
        """
        try:
            # Get source macro info
            source_info = await self.macro_operations.get_macro_info(identifier)
            if not source_info:
                return {
                    "success": False,
                    "error": "Source macro not found",
                    "error_code": "SOURCE_NOT_FOUND"
                }
            
            # Create duplication data
            macro_data = MacroCreationData(
                name=new_name,
                group_uuid=group_uuid or source_info.group_uuid,
                enabled=source_info.enabled,
                color=source_info.color,
                notes=f"Copy of {source_info.name}\n{source_info.notes or ''}".strip()
            )
            
            # Create duplicate
            result = await self.macro_operations.create_macro(macro_data)
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "new_macro_uuid": result.macro_uuid,
                "new_macro_name": new_name,
                "source_macro": identifier,
                "error": result.error_details
            }
            
        except Exception as e:
            logger.error(f"Macro duplication failed: {e}")
            return {
                "success": False,
                "error": f"Duplication failed: {str(e)}",
                "error_code": "DUPLICATION_ERROR"
            }
    
    async def export_macro(
        self,
        identifier: str,
        file_path: str,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Export macro to file.
        
        Args:
            identifier: Macro name or UUID
            file_path: Destination file path
            format_type: Export format (json, xml, kmmacros)
            
        Returns:
            Export result and file information
        """
        try:
            # Get macro data
            macro_info = await self.macro_operations.get_macro_info(identifier)
            if not macro_info:
                return {
                    "success": False,
                    "error": "Macro not found",
                    "error_code": "MACRO_NOT_FOUND"
                }
            
            # Convert format type
            format_map = {
                "json": SerializationFormat.JSON,
                "xml": SerializationFormat.XML,
                "kmmacros": SerializationFormat.KMMACROS
            }
            
            format_enum = format_map.get(format_type.lower())
            if not format_enum:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format_type}",
                    "error_code": "UNSUPPORTED_FORMAT",
                    "supported_formats": list(format_map.keys())
                }
            
            # Prepare macro data for export
            macro_data = {
                "metadata": {
                    "uuid": macro_info.uuid,
                    "name": macro_info.name,
                    "group_uuid": macro_info.group_uuid,
                    "enabled": macro_info.enabled,
                    "color": macro_info.color,
                    "notes": macro_info.notes
                },
                "triggers": [],  # Placeholder - would be populated in real implementation
                "actions": []    # Placeholder - would be populated in real implementation
            }
            
            # Export to file
            success = self.file_manager.save_macro_to_file(
                macro_data, file_path, format_enum
            )
            
            return {
                "success": success,
                "file_path": file_path,
                "format": format_type,
                "macro_name": macro_info.name,
                "error": "Export failed" if not success else None
            }
            
        except Exception as e:
            logger.error(f"Macro export failed: {e}")
            return {
                "success": False,
                "error": f"Export failed: {str(e)}",
                "error_code": "EXPORT_ERROR"
            }
    
    async def import_macro(
        self,
        file_path: str,
        group_uuid: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Import macro from file.
        
        Args:
            file_path: Source file path
            group_uuid: Target group UUID (optional)
            enabled: Override enabled state (optional)
            
        Returns:
            Import result with macro UUID
        """
        try:
            # Load macro data
            macro_data = self.file_manager.load_macro_from_file(file_path)
            if not macro_data:
                return {
                    "success": False,
                    "error": "Failed to load macro from file",
                    "error_code": "LOAD_ERROR"
                }
            
            # Override settings if specified
            if group_uuid:
                macro_data["metadata"]["group_uuid"] = group_uuid
            if enabled is not None:
                macro_data["metadata"]["enabled"] = enabled
            
            # Create import data structure
            creation_data = MacroCreationData(
                name=macro_data["metadata"]["name"],
                group_uuid=macro_data["metadata"].get("group_uuid"),
                enabled=macro_data["metadata"].get("enabled", True),
                color=macro_data["metadata"].get("color"),
                notes=macro_data["metadata"].get("notes"),
                triggers=macro_data.get("triggers", []),
                actions=macro_data.get("actions", [])
            )
            
            # Import macro
            result = await self.macro_operations.create_macro(creation_data)
            
            return {
                "success": result.status == MacroOperationStatus.SUCCESS,
                "status": result.status.value,
                "macro_uuid": result.macro_uuid,
                "macro_name": creation_data.name,
                "file_path": file_path,
                "error": result.error_details
            }
            
        except Exception as e:
            logger.error(f"Macro import failed: {e}")
            return {
                "success": False,
                "error": f"Import failed: {str(e)}",
                "error_code": "IMPORT_ERROR"
            }


def register_macro_management_tools(mcp_server: FastMCP, macro_operations: MacroOperations) -> None:
    """Register macro management tools with the FastMCP server."""
    management_tools = MacroManagementTools(macro_operations)
    management_tools.register_tools(mcp_server)
    
    logger.info("All macro management tools registered successfully")
