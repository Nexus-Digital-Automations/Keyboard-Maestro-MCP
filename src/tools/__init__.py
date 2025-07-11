"""MCP Tools Module - Keyboard Maestro automation tools.

This module exports all MCP tool registration functions for the Keyboard Maestro
MCP server. Provides comprehensive automation capabilities through FastMCP tools.

Key Features:
- Macro execution and management tools
- Variable and data management tools  
- Dictionary operations and JSON import/export
- Clipboard operations with multiple format support
- System integration and automation tools
- Plugin management and custom action creation
"""

from .macro_execution import register_macro_execution_tools
from .macro_management import register_macro_management_tools
from .macro_groups import register_macro_group_tools
from .variable_management import register_variable_tools
from .dictionary_management import register_dictionary_tools
from .clipboard_operations import register_clipboard_tools
from .audio_operations import register_audio_tools
from .plugin_management import (
    PLUGIN_MANAGEMENT_TOOLS,
    km_create_plugin_action,
    km_install_plugin,
    km_list_custom_plugins,
    km_validate_plugin,
    km_remove_plugin,
    km_plugin_status
)

__all__ = [
    'register_macro_execution_tools',
    'register_macro_management_tools', 
    'register_macro_group_tools',
    'register_variable_tools',
    'register_dictionary_tools',
    'register_clipboard_tools',
    'register_audio_tools',
    'register_plugin_management_tools',
    'PLUGIN_MANAGEMENT_TOOLS',
    'km_create_plugin_action',
    'km_install_plugin',
    'km_list_custom_plugins',
    'km_validate_plugin',
    'km_remove_plugin',
    'km_plugin_status'
]


def register_plugin_management_tools(mcp, km_interface):
    """Register plugin management tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance
        km_interface: Keyboard Maestro interface instance
    """
    # Register all plugin management tools
    for tool_func in PLUGIN_MANAGEMENT_TOOLS:
        mcp.tool()(tool_func)


def register_all_tools(mcp, km_interface):
    """Register all available MCP tools with the server.
    
    Args:
        mcp: FastMCP server instance
        km_interface: Keyboard Maestro interface instance
    """
    # Macro operation tools
    register_macro_execution_tools(mcp, km_interface)
    register_macro_management_tools(mcp, km_interface)
    register_macro_group_tools(mcp, km_interface)
    
    # Variable and data management tools
    register_variable_tools(mcp, km_interface)
    register_dictionary_tools(mcp, km_interface)
    register_clipboard_tools(mcp, km_interface)
    
    # Audio and speech tools
    register_audio_tools(mcp, km_interface)
    
    # Plugin management tools
    register_plugin_management_tools(mcp, km_interface)
