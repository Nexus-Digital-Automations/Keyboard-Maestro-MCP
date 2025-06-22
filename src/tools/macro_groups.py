"""
Macro group management tools with activation control.

This module provides MCP tools for managing Keyboard Maestro macro groups,
including creation, activation methods, and application targeting.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP

from src.types.identifiers import GroupUUID
from src.core.macro_operations import MacroOperations
from src.contracts.decorators import requires, ensures

logger = logging.getLogger(__name__)


class MacroGroupTools:
    """MCP tools for macro group operations."""
    
    def __init__(self, macro_operations: MacroOperations):
        """Initialize with macro operations dependency."""
        self.macro_operations = macro_operations
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register all macro group tools with the MCP server."""
        mcp_server.tool()(self.create_macro_group)
        mcp_server.tool()(self.update_macro_group)
        mcp_server.tool()(self.delete_macro_group)
        mcp_server.tool()(self.list_macro_groups)
        mcp_server.tool()(self.create_smart_group)
        mcp_server.tool()(self.set_group_activation)
        
        logger.info("Macro group tools registered")
    
    async def create_macro_group(
        self,
        name: str,
        activation_method: str = "always",
        enabled: bool = True,
        applications: Optional[List[str]] = None,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new macro group.
        
        Args:
            name: Group name (required)
            activation_method: always|one_action|show_palette (default: always)
            enabled: Whether group starts enabled (default: True)
            applications: Bundle IDs for app-specific groups (optional)
            icon: Custom icon specification (optional)
            
        Returns:
            Creation result with group UUID
        """
        try:
            # Validate activation method
            valid_methods = ["always", "one_action", "show_palette"]
            if activation_method not in valid_methods:
                return {
                    "success": False,
                    "error": f"Invalid activation method: {activation_method}",
                    "error_code": "INVALID_ACTIVATION_METHOD",
                    "valid_methods": valid_methods
                }
            
            # Create group data structure
            group_data = {
                "name": name,
                "activation_method": activation_method,
                "enabled": enabled,
                "applications": applications or [],
                "icon": icon
            }
            
            # Create group via KM interface
            result = await self.macro_operations.km_interface.create_macro_group(group_data)
            
            return {
                "success": result.get("success", False),
                "group_uuid": result.get("group_uuid"),
                "group_name": name,
                "activation_method": activation_method,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Group creation failed: {e}")
            return {
                "success": False,
                "error": f"Creation failed: {str(e)}",
                "error_code": "CREATION_ERROR"
            }
    
    async def update_macro_group(
        self,
        group_uuid: str,
        name: Optional[str] = None,
        activation_method: Optional[str] = None,
        enabled: Optional[bool] = None,
        applications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update macro group properties.
        
        Args:
            group_uuid: Group UUID to update
            name: New group name (optional)
            activation_method: New activation method (optional)
            enabled: New enabled state (optional)
            applications: New application list (optional)
            
        Returns:
            Update result and status
        """
        try:
            # Validate activation method if provided
            if activation_method:
                valid_methods = ["always", "one_action", "show_palette"]
                if activation_method not in valid_methods:
                    return {
                        "success": False,
                        "error": f"Invalid activation method: {activation_method}",
                        "error_code": "INVALID_ACTIVATION_METHOD",
                        "valid_methods": valid_methods
                    }
            
            # Build update data
            updates = {}
            if name is not None:
                updates["name"] = name
            if activation_method is not None:
                updates["activation_method"] = activation_method
            if enabled is not None:
                updates["enabled"] = enabled
            if applications is not None:
                updates["applications"] = applications
            
            # Apply updates
            result = await self.macro_operations.km_interface.update_macro_group(
                group_uuid, updates
            )
            
            return {
                "success": result.get("success", False),
                "group_uuid": group_uuid,
                "updated_fields": updates,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Group update failed: {e}")
            return {
                "success": False,
                "error": f"Update failed: {str(e)}",
                "error_code": "UPDATE_ERROR"
            }
    
    async def delete_macro_group(
        self,
        group_uuid: str,
        confirm: bool = False,
        move_macros_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a macro group with safety checks.
        
        Args:
            group_uuid: Group UUID to delete
            confirm: Confirmation flag (required)
            move_macros_to: Target group UUID for existing macros (optional)
            
        Returns:
            Deletion result and status
        """
        try:
            if not confirm:
                return {
                    "success": False,
                    "error": "Confirmation required for group deletion",
                    "error_code": "CONFIRMATION_REQUIRED",
                    "message": "Set confirm=True to proceed with deletion"
                }
            
            # Check for existing macros
            macros = await self.macro_operations.list_macros(group_uuid)
            if macros and not move_macros_to:
                return {
                    "success": False,
                    "error": "Group contains macros - specify move_macros_to target",
                    "error_code": "GROUP_NOT_EMPTY",
                    "macro_count": len(macros)
                }
            
            # Move macros if target specified
            if macros and move_macros_to:
                for macro in macros:
                    await self.macro_operations.modify_macro(
                        macro.uuid,
                        {"group_uuid": move_macros_to}
                    )
            
            # Delete group
            result = await self.macro_operations.km_interface.delete_macro_group(group_uuid)
            
            return {
                "success": result.get("success", False),
                "group_uuid": group_uuid,
                "macros_moved": len(macros) if macros and move_macros_to else 0,
                "move_target": move_macros_to,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Group deletion failed: {e}")
            return {
                "success": False,
                "error": f"Deletion failed: {str(e)}",
                "error_code": "DELETION_ERROR"
            }
    
    async def list_macro_groups(
        self,
        enabled_only: bool = False,
        include_macro_count: bool = True
    ) -> Dict[str, Any]:
        """
        List all macro groups with metadata.
        
        Args:
            enabled_only: Show only enabled groups (default: False)
            include_macro_count: Include macro count per group (default: True)
            
        Returns:
            List of groups with information
        """
        try:
            # Get groups from KM interface
            groups = await self.macro_operations.km_interface.list_macro_groups(enabled_only)
            
            # Enhance with macro counts if requested
            if include_macro_count:
                for group in groups:
                    macros = await self.macro_operations.list_macros(group["uuid"])
                    group["macro_count"] = len(macros)
            
            return {
                "success": True,
                "count": len(groups),
                "groups": groups,
                "filters": {
                    "enabled_only": enabled_only,
                    "include_macro_count": include_macro_count
                }
            }
            
        except Exception as e:
            logger.error(f"List groups failed: {e}")
            return {
                "success": False,
                "error": f"List operation failed: {str(e)}",
                "error_code": "LIST_ERROR"
            }
    
    async def create_smart_group(
        self,
        name: str,
        search_criteria: List[str],
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a smart group with search criteria.
        
        Args:
            name: Smart group name
            search_criteria: Array of search strings for dynamic membership
            icon: Custom icon specification (optional)
            
        Returns:
            Creation result with smart group UUID
        """
        try:
            if not search_criteria:
                return {
                    "success": False,
                    "error": "Search criteria required for smart groups",
                    "error_code": "MISSING_CRITERIA"
                }
            
            # Create smart group data
            smart_group_data = {
                "name": name,
                "type": "smart",
                "search_criteria": search_criteria,
                "icon": icon
            }
            
            # Create smart group
            result = await self.macro_operations.km_interface.create_smart_group(smart_group_data)
            
            return {
                "success": result.get("success", False),
                "group_uuid": result.get("group_uuid"),
                "group_name": name,
                "search_criteria": search_criteria,
                "type": "smart",
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Smart group creation failed: {e}")
            return {
                "success": False,
                "error": f"Smart group creation failed: {str(e)}",
                "error_code": "SMART_GROUP_ERROR"
            }
    
    async def set_group_activation(
        self,
        group_uuid: str,
        activation_method: str,
        applications: Optional[List[str]] = None,
        palette_style: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Configure group activation settings.
        
        Args:
            group_uuid: Group UUID to configure
            activation_method: always|one_action|show_palette
            applications: Bundle IDs for app-specific activation (optional)
            palette_style: Palette configuration for show_palette method (optional)
            
        Returns:
            Configuration result
        """
        try:
            # Validate activation method
            valid_methods = ["always", "one_action", "show_palette"]
            if activation_method not in valid_methods:
                return {
                    "success": False,
                    "error": f"Invalid activation method: {activation_method}",
                    "error_code": "INVALID_ACTIVATION_METHOD",
                    "valid_methods": valid_methods
                }
            
            # Build activation configuration
            activation_config = {
                "activation_method": activation_method
            }
            
            if applications:
                activation_config["applications"] = applications
            
            if palette_style and activation_method == "show_palette":
                activation_config["palette_style"] = palette_style
            
            # Apply configuration
            result = await self.macro_operations.km_interface.set_group_activation(
                group_uuid, activation_config
            )
            
            return {
                "success": result.get("success", False),
                "group_uuid": group_uuid,
                "activation_method": activation_method,
                "applications": applications,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Group activation setup failed: {e}")
            return {
                "success": False,
                "error": f"Activation setup failed: {str(e)}",
                "error_code": "ACTIVATION_ERROR"
            }


def register_macro_group_tools(mcp_server: FastMCP, macro_operations: MacroOperations) -> None:
    """Register macro group tools with the FastMCP server."""
    group_tools = MacroGroupTools(macro_operations)
    group_tools.register_tools(mcp_server)
    
    logger.info("All macro group tools registered successfully")
