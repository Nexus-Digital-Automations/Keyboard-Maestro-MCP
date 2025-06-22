"""
Basic image recognition and template matching MCP tools.

This module provides core image matching capabilities including
template search, coordinate detection, and pixel operations.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP

from src.types.values import ScreenArea, ScreenCoordinates, FilePath, create_screen_coordinate, create_file_path
from src.core.visual_automation import VisualAutomation, ImageMatchResult, ImageTemplate, PixelColorResult
from src.contracts.decorators import requires, ensures
from src.validators.visual_validators import validate_screen_bounds, validate_image_file, validate_tolerance

logger = logging.getLogger(__name__)


class BasicImageTools:
    """Basic image recognition tools for template matching and pixel operations."""
    
    def __init__(self, visual_automation: VisualAutomation):
        """Initialize with visual automation dependency."""
        self.visual_automation = visual_automation
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register basic image tools with the MCP server."""
        mcp_server.tool()(self.find_image_on_screen)
        mcp_server.tool()(self.find_image_in_area)
        mcp_server.tool()(self.get_pixel_color)
        
        logger.info("Basic image tools registered")
    
    async def find_image_on_screen(
        self,
        template_path: str,
        tolerance: float = 0.8,
        return_all_matches: bool = False
    ) -> Dict[str, Any]:
        """
        Find image template on screen with specified tolerance.
        
        Args:
            template_path: Path to template image file
            tolerance: Matching tolerance (0.0-1.0, higher = more strict)
            return_all_matches: Return all matches or just the best one
            
        Returns:
            Image matching results with coordinates and confidence
        """
        try:
            # Validate template path
            if not validate_image_file(template_path):
                return {
                    "success": False,
                    "error": "Invalid or non-existent image file",
                    "error_code": "INVALID_IMAGE_FILE"
                }
            
            # Validate tolerance
            if not validate_tolerance(tolerance):
                return {
                    "success": False,
                    "error": "Tolerance must be between 0.0 and 1.0",
                    "error_code": "INVALID_TOLERANCE"
                }
            
            # Create image template
            template = ImageTemplate(create_file_path(template_path))
            
            # Perform image search
            result = await self.visual_automation.find_image_on_screen(
                template=template,
                tolerance=tolerance,
                return_all=return_all_matches
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            # Format matches
            matches = []
            for match in result.matches:
                matches.append({
                    "x": int(match.center.x),
                    "y": int(match.center.y),
                    "confidence": float(match.confidence),
                    "top_left_x": int(match.bounding_box.top_left.x),
                    "top_left_y": int(match.bounding_box.top_left.y),
                    "bottom_right_x": int(match.bounding_box.bottom_right.x),
                    "bottom_right_y": int(match.bounding_box.bottom_right.y),
                    "width": match.bounding_box.width,
                    "height": match.bounding_box.height
                })
            
            return {
                "success": True,
                "template_path": template_path,
                "tolerance": tolerance,
                "matches_found": len(matches),
                "return_all_matches": return_all_matches,
                "processing_time": result.processing_time,
                "matches": matches,
                "best_match": matches[0] if matches else None
            }
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return {
                "success": False,
                "error": f"Image search failed: {str(e)}",
                "error_code": "IMAGE_SEARCH_ERROR"
            }
    
    async def find_image_in_area(
        self,
        template_path: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        tolerance: float = 0.8
    ) -> Dict[str, Any]:
        """
        Find image template within specific screen area.
        
        Args:
            template_path: Path to template image file
            x1, y1: Top-left coordinates of search area
            x2, y2: Bottom-right coordinates of search area
            tolerance: Matching tolerance (0.0-1.0)
            
        Returns:
            Image matching results within specified area
        """
        try:
            # Validate coordinates
            if not validate_screen_bounds(x1, y1, x2, y2):
                return {
                    "success": False,
                    "error": "Invalid screen coordinates",
                    "error_code": "INVALID_COORDINATES"
                }
            
            # Validate template and tolerance
            if not validate_image_file(template_path):
                return {
                    "success": False,
                    "error": "Invalid or non-existent image file",
                    "error_code": "INVALID_IMAGE_FILE"
                }
            
            if not validate_tolerance(tolerance):
                return {
                    "success": False,
                    "error": "Tolerance must be between 0.0 and 1.0",
                    "error_code": "INVALID_TOLERANCE"
                }
            
            # Create search area and template
            search_area = ScreenArea(
                top_left=ScreenCoordinates(
                    create_screen_coordinate(x1),
                    create_screen_coordinate(y1)
                ),
                bottom_right=ScreenCoordinates(
                    create_screen_coordinate(x2),
                    create_screen_coordinate(y2)
                )
            )
            
            template = ImageTemplate(create_file_path(template_path))
            
            # Perform image search in area
            result = await self.visual_automation.find_image_in_area(
                template=template,
                area=search_area,
                tolerance=tolerance
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            # Format results
            matches = []
            for match in result.matches:
                matches.append({
                    "x": int(match.center.x),
                    "y": int(match.center.y),
                    "confidence": float(match.confidence),
                    "top_left_x": int(match.bounding_box.top_left.x),
                    "top_left_y": int(match.bounding_box.top_left.y),
                    "bottom_right_x": int(match.bounding_box.bottom_right.x),
                    "bottom_right_y": int(match.bounding_box.bottom_right.y),
                    "width": match.bounding_box.width,
                    "height": match.bounding_box.height
                })
            
            return {
                "success": True,
                "template_path": template_path,
                "search_area": {
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "width": x2 - x1, "height": y2 - y1
                },
                "tolerance": tolerance,
                "matches_found": len(matches),
                "processing_time": result.processing_time,
                "matches": matches
            }
            
        except Exception as e:
            logger.error(f"Area image search failed: {e}")
            return {
                "success": False,
                "error": f"Area image search failed: {str(e)}",
                "error_code": "IMAGE_SEARCH_ERROR"
            }
    
    async def get_pixel_color(
        self,
        x: int,
        y: int
    ) -> Dict[str, Any]:
        """
        Get pixel color at specific screen coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Pixel color information in multiple formats
        """
        try:
            # Validate coordinates
            if x < 0 or y < 0:
                return {
                    "success": False,
                    "error": "Coordinates must be non-negative",
                    "error_code": "INVALID_COORDINATES"
                }
            
            # Create coordinates
            coordinates = ScreenCoordinates(
                create_screen_coordinate(x),
                create_screen_coordinate(y)
            )
            
            # Get pixel color
            result = await self.visual_automation.get_pixel_color(coordinates)
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            return {
                "success": True,
                "x": x,
                "y": y,
                "color": {
                    "red": result.color.red,
                    "green": result.color.green,
                    "blue": result.color.blue,
                    "hex": result.color.to_hex(),
                    "rgb_tuple": [result.color.red, result.color.green, result.color.blue]
                }
            }
            
        except Exception as e:
            logger.error(f"Pixel color detection failed: {e}")
            return {
                "success": False,
                "error": f"Pixel color detection failed: {str(e)}",
                "error_code": "PIXEL_COLOR_ERROR"
            }


def register_basic_image_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Register basic image tools with the FastMCP server.
    
    This is a convenience function for registering basic image tools.
    """
    image_tools = BasicImageTools(visual_automation)
    image_tools.register_tools(mcp_server)
    
    logger.info("Basic image tools registered successfully")
