"""
Basic OCR text extraction MCP tools.

This module provides core OCR tools for screen and area text extraction
with confidence scoring and language support.
"""

from typing import Optional, Dict, Any, List
import logging
from fastmcp import FastMCP

from src.types.domain_types import OCRTextExtraction
from .types.values import ScreenArea, ScreenCoordinates, create_confidence_score, create_screen_coordinate
from src.core.visual_automation import VisualAutomation, OCRResult, OCRLanguage
from src.contracts.decorators import requires, ensures
from src.validators.visual_validators import validate_screen_bounds, validate_language_code

logger = logging.getLogger(__name__)


class BasicOCRTools:
    """Basic OCR tools for screen and area text extraction."""
    
    def __init__(self, visual_automation: VisualAutomation):
        """Initialize with visual automation dependency."""
        self.visual_automation = visual_automation
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register basic OCR tools with the MCP server."""
        mcp_server.tool()(self.extract_text_from_screen)
        mcp_server.tool()(self.extract_text_from_area)
        mcp_server.tool()(self.get_supported_languages)
        
        logger.info("Basic OCR tools registered")
    
    async def extract_text_from_screen(
        self,
        confidence_threshold: float = 0.8,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Extract text from entire screen using OCR.
        
        Args:
            confidence_threshold: Minimum confidence score (0.0-1.0)
            language: OCR language code (default: en)
            
        Returns:
            OCR results with extracted text and metadata
        """
        try:
            # Validate confidence threshold
            if not 0.0 <= confidence_threshold <= 1.0:
                return {
                    "success": False,
                    "error": "Confidence threshold must be between 0.0 and 1.0",
                    "error_code": "INVALID_CONFIDENCE"
                }
            
            # Validate language
            if not validate_language_code(language):
                return {
                    "success": False,
                    "error": f"Unsupported language code: {language}",
                    "error_code": "INVALID_LANGUAGE"
                }
            
            # Perform OCR on full screen
            result = await self.visual_automation.extract_text_from_screen(
                language=OCRLanguage(language),
                confidence_threshold=create_confidence_score(confidence_threshold)
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            # Filter and format results
            filtered_extractions = [
                {
                    "text": extraction.text,
                    "confidence": float(extraction.confidence),
                    "x": int(extraction.bounding_box.x),
                    "y": int(extraction.bounding_box.y),
                    "language": extraction.language
                }
                for extraction in result.extractions
                if extraction.confidence >= confidence_threshold
            ]
            
            return {
                "success": True,
                "total_extractions": len(filtered_extractions),
                "confidence_threshold": confidence_threshold,
                "language": language,
                "processing_time": result.processing_time,
                "extractions": filtered_extractions
            }
            
        except Exception as e:
            logger.error(f"Screen OCR extraction failed: {e}")
            return {
                "success": False,
                "error": f"OCR extraction failed: {str(e)}",
                "error_code": "OCR_ERROR"
            }
    
    async def extract_text_from_area(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        confidence_threshold: float = 0.8,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Extract text from specific screen area using OCR.
        
        Args:
            x1: Top-left X coordinate
            y1: Top-left Y coordinate
            x2: Bottom-right X coordinate
            y2: Bottom-right Y coordinate
            confidence_threshold: Minimum confidence score
            language: OCR language code
            
        Returns:
            OCR results for specified area
        """
        try:
            # Validate coordinates
            if not validate_screen_bounds(x1, y1, x2, y2):
                return {
                    "success": False,
                    "error": "Invalid screen coordinates",
                    "error_code": "INVALID_COORDINATES"
                }
            
            # Create screen area
            screen_area = ScreenArea(
                top_left=ScreenCoordinates(
                    create_screen_coordinate(x1),
                    create_screen_coordinate(y1)
                ),
                bottom_right=ScreenCoordinates(
                    create_screen_coordinate(x2),
                    create_screen_coordinate(y2)
                )
            )
            
            # Validate confidence and language
            if not 0.0 <= confidence_threshold <= 1.0:
                return {
                    "success": False,
                    "error": "Confidence threshold must be between 0.0 and 1.0",
                    "error_code": "INVALID_CONFIDENCE"
                }
            
            if not validate_language_code(language):
                return {
                    "success": False,
                    "error": f"Unsupported language code: {language}",
                    "error_code": "INVALID_LANGUAGE"
                }
            
            # Perform OCR on specified area
            result = await self.visual_automation.extract_text_from_area(
                area=screen_area,
                language=OCRLanguage(language),
                confidence_threshold=create_confidence_score(confidence_threshold)
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            # Format results
            extractions = [
                {
                    "text": extraction.text,
                    "confidence": float(extraction.confidence),
                    "x": int(extraction.bounding_box.x),
                    "y": int(extraction.bounding_box.y),
                    "language": extraction.language
                }
                for extraction in result.extractions
            ]
            
            return {
                "success": True,
                "area": {
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "width": x2 - x1, "height": y2 - y1
                },
                "total_extractions": len(extractions),
                "confidence_threshold": confidence_threshold,
                "language": language,
                "processing_time": result.processing_time,
                "extractions": extractions
            }
            
        except Exception as e:
            logger.error(f"Area OCR extraction failed: {e}")
            return {
                "success": False,
                "error": f"Area OCR extraction failed: {str(e)}",
                "error_code": "OCR_ERROR"
            }
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """
        Get list of supported OCR languages.
        
        Returns:
            List of supported language codes and names
        """
        try:
            supported = await self.visual_automation.get_supported_languages()
            
            return {
                "success": True,
                "total_languages": len(supported),
                "languages": [
                    {
                        "code": lang.code,
                        "name": lang.name,
                        "native_name": lang.native_name,
                        "quality": lang.quality_score
                    }
                    for lang in supported
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return {
                "success": False,
                "error": f"Failed to get languages: {str(e)}",
                "error_code": "LANGUAGE_ERROR"
            }


def register_basic_ocr_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Register basic OCR tools with the FastMCP server.
    
    This is a convenience function for registering basic OCR tools.
    """
    ocr_tools = BasicOCRTools(visual_automation)
    ocr_tools.register_tools(mcp_server)
    
    logger.info("Basic OCR tools registered successfully")
