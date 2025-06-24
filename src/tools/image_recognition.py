"""
Image recognition orchestrator - combines basic and advanced image tools.

This module serves as the main entry point for all image recognition operations,
combining basic and advanced image capabilities into a unified interface.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP

from .core.visual_automation import VisualAutomation
from src.tools.image_basic import register_basic_image_tools
from src.tools.image_advanced import register_advanced_image_tools

logger = logging.getLogger(__name__)


def register_all_image_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Register all image recognition tools with the FastMCP server.
    
    This function registers both basic and advanced image tools,
    providing complete image recognition functionality.
    
    Args:
        mcp_server: FastMCP server instance
        visual_automation: Visual automation core instance
    """
    # Register basic image tools
    register_basic_image_tools(mcp_server, visual_automation)
    
    # Register advanced image tools
    register_advanced_image_tools(mcp_server, visual_automation)
    
    logger.info("All image recognition tools registered successfully")


# Backward compatibility - maintain original interface
class ImageRecognitionTools:
    """Legacy image recognition tools class for backward compatibility."""
    
    def __init__(self, visual_automation: VisualAutomation):
        """Initialize with visual automation dependency."""
        self.visual_automation = visual_automation
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register all image tools with the MCP server."""
        register_all_image_tools(mcp_server, self.visual_automation)


def register_image_recognition_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Legacy function for backward compatibility.
    
    Args:
        mcp_server: FastMCP server instance
        visual_automation: Visual automation core instance
    """
    register_all_image_tools(mcp_server, visual_automation)
