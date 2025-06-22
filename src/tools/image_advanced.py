"""
Advanced image recognition tools for complex matching operations.

This module provides advanced image recognition capabilities including
multi-image search, fuzzy matching, and wait operations.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP

from src.types.values import FilePath, create_file_path
from src.core.visual_automation import VisualAutomation, ImageMatchResult, ImageTemplate, WaitResult
from src.contracts.decorators import requires, ensures
from src.validators.visual_validators import validate_image_file, validate_tolerance

logger = logging.getLogger(__name__)


class AdvancedImageTools:
    """Advanced image recognition tools for complex matching operations."""
    
    def __init__(self, visual_automation: VisualAutomation):
        """Initialize with visual automation dependency."""
        self.visual_automation = visual_automation
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register advanced image tools with the MCP server."""
        mcp_server.tool()(self.find_multiple_images)
        mcp_server.tool()(self.match_template_fuzzy)
        mcp_server.tool()(self.wait_for_image)
        
        logger.info("Advanced image tools registered")
    
    async def find_multiple_images(
        self,
        template_paths: List[str],
        tolerance: float = 0.8,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Search for multiple image templates simultaneously.
        
        Args:
            template_paths: List of template image file paths
            tolerance: Matching tolerance for all templates
            timeout: Maximum search time in seconds
            
        Returns:
            Results for all template searches
        """
        try:
            if not template_paths:
                return {
                    "success": False,
                    "error": "Template paths list cannot be empty",
                    "error_code": "EMPTY_TEMPLATE_LIST"
                }
            
            # Validate all template files
            invalid_templates = [path for path in template_paths if not validate_image_file(path)]
            if invalid_templates:
                return {
                    "success": False,
                    "error": f"Invalid template files: {invalid_templates}",
                    "error_code": "INVALID_TEMPLATE_FILES"
                }
            
            # Validate tolerance and timeout
            if not validate_tolerance(tolerance):
                return {
                    "success": False,
                    "error": "Tolerance must be between 0.0 and 1.0",
                    "error_code": "INVALID_TOLERANCE"
                }
            
            if timeout <= 0 or timeout > 60:
                return {
                    "success": False,
                    "error": "Timeout must be between 0 and 60 seconds",
                    "error_code": "INVALID_TIMEOUT"
                }
            
            # Create templates
            templates = [ImageTemplate(create_file_path(path)) for path in template_paths]
            
            # Perform multi-image search
            result = await self.visual_automation.find_multiple_images(
                templates=templates,
                tolerance=tolerance,
                timeout=timeout
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            # Format results by template
            template_results = {}
            total_matches = 0
            
            for i, template_path in enumerate(template_paths):
                template_matches = [
                    match for match in result.matches
                    if match.template_index == i
                ]
                
                matches = []
                for match in template_matches:
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
                
                template_results[template_path] = {
                    "matches_found": len(matches),
                    "matches": matches
                }
                total_matches += len(matches)
            
            return {
                "success": True,
                "template_count": len(template_paths),
                "tolerance": tolerance,
                "timeout": timeout,
                "total_matches": total_matches,
                "processing_time": result.processing_time,
                "template_results": template_results
            }
            
        except Exception as e:
            logger.error(f"Multi-image search failed: {e}")
            return {
                "success": False,
                "error": f"Multi-image search failed: {str(e)}",
                "error_code": "MULTI_IMAGE_ERROR"
            }
    
    async def match_template_fuzzy(
        self,
        template_path: str,
        fuzzy_threshold: float = 0.6,
        scale_tolerance: float = 0.1,
        rotation_tolerance: float = 5.0
    ) -> Dict[str, Any]:
        """
        Perform fuzzy template matching with scale and rotation tolerance.
        
        Args:
            template_path: Path to template image file
            fuzzy_threshold: Minimum similarity score (0.0-1.0)
            scale_tolerance: Scale variation tolerance (0.0-1.0)
            rotation_tolerance: Rotation tolerance in degrees
            
        Returns:
            Fuzzy matching results with transformation data
        """
        try:
            # Validate template
            if not validate_image_file(template_path):
                return {
                    "success": False,
                    "error": "Invalid or non-existent image file",
                    "error_code": "INVALID_IMAGE_FILE"
                }
            
            # Validate parameters
            if not 0.0 <= fuzzy_threshold <= 1.0:
                return {
                    "success": False,
                    "error": "Fuzzy threshold must be between 0.0 and 1.0",
                    "error_code": "INVALID_THRESHOLD"
                }
            
            if not 0.0 <= scale_tolerance <= 1.0:
                return {
                    "success": False,
                    "error": "Scale tolerance must be between 0.0 and 1.0",
                    "error_code": "INVALID_SCALE_TOLERANCE"
                }
            
            if not 0.0 <= rotation_tolerance <= 360.0:
                return {
                    "success": False,
                    "error": "Rotation tolerance must be between 0.0 and 360.0 degrees",
                    "error_code": "INVALID_ROTATION_TOLERANCE"
                }
            
            # Create template
            template = ImageTemplate(create_file_path(template_path))
            
            # Perform fuzzy matching
            result = await self.visual_automation.match_template_fuzzy(
                template=template,
                fuzzy_threshold=fuzzy_threshold,
                scale_tolerance=scale_tolerance,
                rotation_tolerance=rotation_tolerance
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            # Format fuzzy matches
            matches = []
            for match in result.matches:
                matches.append({
                    "x": int(match.center.x),
                    "y": int(match.center.y),
                    "confidence": float(match.confidence),
                    "similarity_score": float(match.similarity_score),
                    "scale_factor": float(match.scale_factor),
                    "rotation_angle": float(match.rotation_angle),
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
                "fuzzy_threshold": fuzzy_threshold,
                "scale_tolerance": scale_tolerance,
                "rotation_tolerance": rotation_tolerance,
                "matches_found": len(matches),
                "processing_time": result.processing_time,
                "matches": matches
            }
            
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {e}")
            return {
                "success": False,
                "error": f"Fuzzy matching failed: {str(e)}",
                "error_code": "FUZZY_MATCH_ERROR"
            }
    
    async def wait_for_image(
        self,
        template_path: str,
        timeout: float = 10.0,
        tolerance: float = 0.8,
        check_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Wait for image to appear on screen within timeout period.
        
        Args:
            template_path: Path to template image file
            timeout: Maximum wait time in seconds
            tolerance: Matching tolerance
            check_interval: Time between checks in seconds
            
        Returns:
            Result indicating whether image was found within timeout
        """
        try:
            # Validate parameters
            if not validate_image_file(template_path):
                return {
                    "success": False,
                    "error": "Invalid or non-existent image file",
                    "error_code": "INVALID_IMAGE_FILE"
                }
            
            if timeout <= 0 or timeout > 300:
                return {
                    "success": False,
                    "error": "Timeout must be between 0 and 300 seconds",
                    "error_code": "INVALID_TIMEOUT"
                }
            
            if not validate_tolerance(tolerance):
                return {
                    "success": False,
                    "error": "Tolerance must be between 0.0 and 1.0",
                    "error_code": "INVALID_TOLERANCE"
                }
            
            if check_interval <= 0 or check_interval > 10:
                return {
                    "success": False,
                    "error": "Check interval must be between 0 and 10 seconds",
                    "error_code": "INVALID_INTERVAL"
                }
            
            # Create template
            template = ImageTemplate(create_file_path(template_path))
            
            # Wait for image
            result = await self.visual_automation.wait_for_image(
                template=template,
                timeout=timeout,
                tolerance=tolerance,
                check_interval=check_interval
            )
            
            if not result.success and result.error_code != "TIMEOUT":
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            response = {
                "success": result.success,
                "template_path": template_path,
                "timeout": timeout,
                "tolerance": tolerance,
                "check_interval": check_interval,
                "elapsed_time": result.elapsed_time,
                "checks_performed": result.checks_performed
            }
            
            if result.success and result.matches:
                best_match = result.matches[0]
                response["found_at"] = {
                    "x": int(best_match.center.x),
                    "y": int(best_match.center.y),
                    "confidence": float(best_match.confidence),
                    "found_after": result.elapsed_time
                }
            else:
                response["error"] = "Image not found within timeout period"
                response["error_code"] = "TIMEOUT"
            
            return response
            
        except Exception as e:
            logger.error(f"Wait for image failed: {e}")
            return {
                "success": False,
                "error": f"Wait for image failed: {str(e)}",
                "error_code": "WAIT_ERROR"
            }


def register_advanced_image_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Register advanced image tools with the FastMCP server.
    
    This is a convenience function for registering advanced image tools.
    """
    image_tools = AdvancedImageTools(visual_automation)
    image_tools.register_tools(mcp_server)
    
    logger.info("Advanced image tools registered successfully")
