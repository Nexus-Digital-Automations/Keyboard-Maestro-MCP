"""
OCR operations orchestrator - combines basic and advanced OCR tools.

This module serves as the main entry point for all OCR operations,
combining basic and advanced OCR capabilities into a unified interface.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP

from .core.visual_automation import VisualAutomation
from src.tools.ocr_basic import register_basic_ocr_tools
from src.tools.ocr_advanced import register_advanced_ocr_tools

logger = logging.getLogger(__name__)


def register_all_ocr_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Register all OCR tools with the FastMCP server.
    
    This function registers both basic and advanced OCR tools,
    providing complete OCR functionality.
    
    Args:
        mcp_server: FastMCP server instance
        visual_automation: Visual automation core instance
    """
    # Register basic OCR tools
    register_basic_ocr_tools(mcp_server, visual_automation)
    
    # Register advanced OCR tools
    register_advanced_ocr_tools(mcp_server, visual_automation)
    
    logger.info("All OCR tools registered successfully")


# Backward compatibility - maintain original interface
class OCROperationTools:
    """Legacy OCR operation tools class for backward compatibility."""
    
    def __init__(self, visual_automation: VisualAutomation):
        """Initialize with visual automation dependency."""
        self.visual_automation = visual_automation
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register all OCR tools with the MCP server."""
        register_all_ocr_tools(mcp_server, self.visual_automation)


def register_ocr_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Legacy function for backward compatibility.
    
    Args:
        mcp_server: FastMCP server instance
        visual_automation: Visual automation core instance
    """
    register_all_ocr_tools(mcp_server, visual_automation)
