"""
Advanced OCR tools for multi-language and text search operations.

This module provides advanced OCR capabilities including multi-language support,
text search, and complex processing operations.
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


class AdvancedOCRTools:
    """Advanced OCR tools for multi-language and search operations."""
    
    def __init__(self, visual_automation: VisualAutomation):
        """Initialize with visual automation dependency."""
        self.visual_automation = visual_automation
    
    def register_tools(self, mcp_server: FastMCP) -> None:
        """Register advanced OCR tools with the MCP server."""
        mcp_server.tool()(self.extract_text_multi_language)
        mcp_server.tool()(self.find_text_on_screen)
        
        logger.info("Advanced OCR tools registered")
    
    async def extract_text_multi_language(
        self,
        languages: List[str],
        confidence_threshold: float = 0.8,
        x1: Optional[int] = None,
        y1: Optional[int] = None,
        x2: Optional[int] = None,
        y2: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract text using multiple languages for better recognition.
        
        Args:
            languages: List of language codes to try
            confidence_threshold: Minimum confidence score
            x1, y1, x2, y2: Optional area coordinates (full screen if not provided)
            
        Returns:
            Combined OCR results from all languages
        """
        try:
            # Validate languages
            invalid_languages = [lang for lang in languages if not validate_language_code(lang)]
            if invalid_languages:
                return {
                    "success": False,
                    "error": f"Invalid language codes: {invalid_languages}",
                    "error_code": "INVALID_LANGUAGES"
                }
            
            # Determine area
            area = None
            if all(coord is not None for coord in [x1, y1, x2, y2]):
                if not validate_screen_bounds(x1, y1, x2, y2):
                    return {
                        "success": False,
                        "error": "Invalid screen coordinates",
                        "error_code": "INVALID_COORDINATES"
                    }
                
                area = ScreenArea(
                    top_left=ScreenCoordinates(
                        create_screen_coordinate(x1),
                        create_screen_coordinate(y1)
                    ),
                    bottom_right=ScreenCoordinates(
                        create_screen_coordinate(x2),
                        create_screen_coordinate(y2)
                    )
                )
            
            # Perform OCR with multiple languages
            result = await self.visual_automation.extract_text_multi_language(
                languages=[OCRLanguage(lang) for lang in languages],
                confidence_threshold=create_confidence_score(confidence_threshold),
                area=area
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message,
                    "error_code": result.error_code
                }
            
            # Group results by language
            results_by_language = {}
            all_extractions = []
            
            for extraction in result.extractions:
                lang = extraction.language
                if lang not in results_by_language:
                    results_by_language[lang] = []
                
                extraction_data = {
                    "text": extraction.text,
                    "confidence": float(extraction.confidence),
                    "x": int(extraction.bounding_box.x),
                    "y": int(extraction.bounding_box.y),
                    "language": extraction.language
                }
                
                results_by_language[lang].append(extraction_data)
                all_extractions.append(extraction_data)
            
            return {
                "success": True,
                "languages_used": languages,
                "confidence_threshold": confidence_threshold,
                "total_extractions": len(all_extractions),
                "processing_time": result.processing_time,
                "results_by_language": results_by_language,
                "all_extractions": sorted(all_extractions, key=lambda x: x["confidence"], reverse=True)
            }
            
        except Exception as e:
            logger.error(f"Multi-language OCR extraction failed: {e}")
            return {
                "success": False,
                "error": f"Multi-language OCR failed: {str(e)}",
                "error_code": "OCR_ERROR"
            }
    
    async def find_text_on_screen(
        self,
        search_text: str,
        confidence_threshold: float = 0.8,
        language: str = "en",
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Search for specific text on screen using OCR.
        
        Args:
            search_text: Text to search for
            confidence_threshold: Minimum OCR confidence
            language: OCR language code
            case_sensitive: Whether search is case sensitive
            
        Returns:
            Search results with locations of found text
        """
        try:
            if not search_text.strip():
                return {
                    "success": False,
                    "error": "Search text cannot be empty",
                    "error_code": "EMPTY_SEARCH_TEXT"
                }
            
            # Perform full screen OCR first
            ocr_result = await self.visual_automation.extract_text_from_screen(
                language=OCRLanguage(language),
                confidence_threshold=create_confidence_score(confidence_threshold)
            )
            
            if not ocr_result.success:
                return {
                    "success": False,
                    "error": ocr_result.error_message,
                    "error_code": ocr_result.error_code
                }
            
            # Search for text in OCR results
            matches = []
            search_term = search_text if case_sensitive else search_text.lower()
            
            for extraction in ocr_result.extractions:
                extracted_text = extraction.text if case_sensitive else extraction.text.lower()
                
                if search_term in extracted_text:
                    matches.append({
                        "text": extraction.text,
                        "confidence": float(extraction.confidence),
                        "x": int(extraction.bounding_box.x),
                        "y": int(extraction.bounding_box.y),
                        "language": extraction.language,
                        "match_type": "exact" if search_term == extracted_text else "partial"
                    })
            
            return {
                "success": True,
                "search_text": search_text,
                "case_sensitive": case_sensitive,
                "confidence_threshold": confidence_threshold,
                "language": language,
                "matches_found": len(matches),
                "processing_time": ocr_result.processing_time,
                "matches": matches
            }
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return {
                "success": False,
                "error": f"Text search failed: {str(e)}",
                "error_code": "SEARCH_ERROR"
            }


def register_advanced_ocr_tools(mcp_server: FastMCP, visual_automation: VisualAutomation) -> None:
    """
    Register advanced OCR tools with the FastMCP server.
    
    This is a convenience function for registering advanced OCR tools.
    """
    ocr_tools = AdvancedOCRTools(visual_automation)
    ocr_tools.register_tools(mcp_server)
    
    logger.info("Advanced OCR tools registered successfully")
