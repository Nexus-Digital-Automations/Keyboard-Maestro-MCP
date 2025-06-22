"""
Core visual automation logic with performance optimization.

This module implements the core business logic for OCR and image recognition operations,
separated from MCP tool interfaces for clean architecture and testing.
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
import time

from src.types.domain_types import OCRTextExtraction
from src.types.values import ScreenArea, ScreenCoordinates, ConfidenceScore, FilePath, ColorRGB
from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_screen_area, is_valid_confidence_threshold
from src.validators.visual_validators import validate_screen_bounds, validate_image_file
from src.core.km_interface import KMInterface
from src.core.km_error_handler import KMErrorHandler

logger = logging.getLogger(__name__)


class VisualOperationStatus(Enum):
    """Status enumeration for visual operations."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    INVALID_INPUT = "invalid_input"


@dataclass
class OCRLanguage:
    """OCR language configuration."""
    code: str
    name: str = ""
    native_name: str = ""
    quality_score: float = 1.0
    
    def __post_init__(self):
        """Set default values if not provided."""
        if not self.name:
            self.name = self.code.upper()
        if not self.native_name:
            self.native_name = self.name


@dataclass
class ImageTemplate:
    """Image template for matching operations."""
    file_path: FilePath
    name: Optional[str] = None
    
    def __post_init__(self):
        """Set default name from file path."""
        if not self.name:
            import os
            self.name = os.path.basename(self.file_path)


@dataclass
class ImageMatch:
    """Individual image match result."""
    center: ScreenCoordinates
    bounding_box: ScreenArea
    confidence: ConfidenceScore
    template_index: int = 0
    similarity_score: float = 0.0
    scale_factor: float = 1.0
    rotation_angle: float = 0.0


@dataclass
class OCRResult:
    """OCR operation result container."""
    success: bool
    extractions: List[OCRTextExtraction]
    processing_time: float
    error_message: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class ImageMatchResult:
    """Image matching operation result container."""
    success: bool
    matches: List[ImageMatch]
    processing_time: float
    error_message: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class PixelColorResult:
    """Pixel color detection result."""
    success: bool
    color: Optional[ColorRGB] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class WaitResult:
    """Wait operation result container."""
    success: bool
    elapsed_time: float
    checks_performed: int
    matches: List[ImageMatch] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class VisualAutomation:
    """Core visual automation operations with performance optimization."""
    
    def __init__(self, km_interface: KMInterface, error_handler: KMErrorHandler):
        """Initialize visual automation with required dependencies."""
        self.km_interface = km_interface
        self.error_handler = error_handler
        self._supported_languages = None
        self._cache_timeout = 60  # Language cache timeout in seconds
        self._last_cache_update = 0
    
    @requires(lambda self, language: isinstance(language, OCRLanguage))
    @requires(lambda self, language, confidence_threshold: 0.0 <= confidence_threshold <= 1.0)
    async def extract_text_from_screen(
        self,
        language: OCRLanguage,
        confidence_threshold: ConfidenceScore
    ) -> OCRResult:
        """
        Extract text from entire screen using OCR.
        
        Preconditions:
        - Language must be valid OCR language
        - Confidence threshold must be between 0.0 and 1.0
        
        Postconditions:
        - All returned text meets minimum confidence threshold
        """
        try:
            logger.info(f"Starting full screen OCR with language: {language.code}")
            start_time = time.time()
            
            # Validate language support
            if not await self._is_language_supported(language):
                return OCRResult(
                    success=False,
                    extractions=[],
                    processing_time=0.0,
                    error_message=f"Unsupported language: {language.code}",
                    error_code="UNSUPPORTED_LANGUAGE"
                )
            
            # Perform OCR via Keyboard Maestro
            ocr_data = await self.km_interface.extract_text_from_screen(
                language=language.code,
                confidence_filter=float(confidence_threshold)
            )
            
            # Process OCR results
            extractions = self._process_ocr_data(ocr_data, confidence_threshold, language)
            processing_time = time.time() - start_time
            
            logger.info(f"Screen OCR completed: {len(extractions)} extractions in {processing_time:.2f}s")
            
            return OCRResult(
                success=True,
                extractions=extractions,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Screen OCR failed: {e}")
            return OCRResult(
                success=False,
                extractions=[],
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error_message=str(e),
                error_code="OCR_ERROR"
            )
    
    @requires(lambda self, area: isinstance(area, ScreenArea))
    @requires(lambda self, area, language: isinstance(language, OCRLanguage))
    async def extract_text_from_area(
        self,
        area: ScreenArea,
        language: OCRLanguage,
        confidence_threshold: ConfidenceScore
    ) -> OCRResult:
        """Extract text from specific screen area using OCR."""
        try:
            logger.info(f"Starting area OCR: {area.width}x{area.height} at ({area.top_left.x}, {area.top_left.y})")
            start_time = time.time()
            
            # Validate language support
            if not await self._is_language_supported(language):
                return OCRResult(
                    success=False,
                    extractions=[],
                    processing_time=0.0,
                    error_message=f"Unsupported language: {language.code}",
                    error_code="UNSUPPORTED_LANGUAGE"
                )
            
            # Perform area OCR
            ocr_data = await self.km_interface.extract_text_from_area(
                area=area,
                language=language.code,
                confidence_filter=float(confidence_threshold)
            )
            
            # Process results
            extractions = self._process_ocr_data(ocr_data, confidence_threshold, language)
            processing_time = time.time() - start_time
            
            logger.info(f"Area OCR completed: {len(extractions)} extractions in {processing_time:.2f}s")
            
            return OCRResult(
                success=True,
                extractions=extractions,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Area OCR failed: {e}")
            return OCRResult(
                success=False,
                extractions=[],
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error_message=str(e),
                error_code="OCR_ERROR"
            )
    
    async def extract_text_multi_language(
        self,
        languages: List[OCRLanguage],
        confidence_threshold: ConfidenceScore,
        area: Optional[ScreenArea] = None
    ) -> OCRResult:
        """Extract text using multiple languages for better recognition."""
        try:
            logger.info(f"Starting multi-language OCR with {len(languages)} languages")
            start_time = time.time()
            
            all_extractions = []
            
            # Process each language sequentially for better performance
            for language in languages:
                if area:
                    result = await self.extract_text_from_area(area, language, confidence_threshold)
                else:
                    result = await self.extract_text_from_screen(language, confidence_threshold)
                
                if result.success:
                    all_extractions.extend(result.extractions)
            
            # Remove duplicates based on coordinates and text similarity
            unique_extractions = self._remove_duplicate_extractions(all_extractions)
            processing_time = time.time() - start_time
            
            logger.info(f"Multi-language OCR completed: {len(unique_extractions)} unique extractions")
            
            return OCRResult(
                success=True,
                extractions=unique_extractions,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Multi-language OCR failed: {e}")
            return OCRResult(
                success=False,
                extractions=[],
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error_message=str(e),
                error_code="MULTI_OCR_ERROR"
            )
    
    @requires(lambda self, template: isinstance(template, ImageTemplate))
    async def find_image_on_screen(
        self,
        template: ImageTemplate,
        tolerance: float,
        return_all: bool = False
    ) -> ImageMatchResult:
        """Find image template on screen with specified tolerance."""
        try:
            logger.info(f"Searching for image: {template.name} with tolerance {tolerance}")
            start_time = time.time()
            
            # Validate template file
            if not validate_image_file(template.file_path):
                return ImageMatchResult(
                    success=False,
                    matches=[],
                    processing_time=0.0,
                    error_message=f"Invalid template file: {template.file_path}",
                    error_code="INVALID_TEMPLATE"
                )
            
            # Perform image search via Keyboard Maestro
            match_data = await self.km_interface.find_image_on_screen(
                template_path=template.file_path,
                tolerance=tolerance,
                return_all=return_all
            )
            
            # Process matches
            matches = self._process_image_matches(match_data)
            processing_time = time.time() - start_time
            
            logger.info(f"Image search completed: {len(matches)} matches in {processing_time:.2f}s")
            
            return ImageMatchResult(
                success=True,
                matches=matches,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return ImageMatchResult(
                success=False,
                matches=[],
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error_message=str(e),
                error_code="IMAGE_SEARCH_ERROR"
            )
    
    async def find_image_in_area(
        self,
        template: ImageTemplate,
        area: ScreenArea,
        tolerance: float
    ) -> ImageMatchResult:
        """Find image template within specific screen area."""
        try:
            logger.info(f"Searching for {template.name} in area: {area.width}x{area.height}")
            start_time = time.time()
            
            # Perform area-specific image search
            match_data = await self.km_interface.find_image_in_area(
                template_path=template.file_path,
                area=area,
                tolerance=tolerance
            )
            
            matches = self._process_image_matches(match_data)
            processing_time = time.time() - start_time
            
            return ImageMatchResult(
                success=True,
                matches=matches,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Area image search failed: {e}")
            return ImageMatchResult(
                success=False,
                matches=[],
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error_message=str(e),
                error_code="AREA_SEARCH_ERROR"
            )
    
    async def find_multiple_images(
        self,
        templates: List[ImageTemplate],
        tolerance: float,
        timeout: float
    ) -> ImageMatchResult:
        """Search for multiple image templates simultaneously."""
        try:
            logger.info(f"Searching for {len(templates)} images with timeout {timeout}s")
            start_time = time.time()
            
            # Use asyncio to search for images concurrently with timeout
            search_tasks = []
            for i, template in enumerate(templates):
                task = self._search_single_template(template, tolerance, i)
                search_tasks.append(task)
            
            # Wait for all searches to complete or timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*search_tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return ImageMatchResult(
                    success=False,
                    matches=[],
                    processing_time=timeout,
                    error_message="Multi-image search timed out",
                    error_code="TIMEOUT"
                )
            
            # Collect all successful matches
            all_matches = []
            for result in results:
                if isinstance(result, ImageMatchResult) and result.success:
                    all_matches.extend(result.matches)
            
            processing_time = time.time() - start_time
            
            return ImageMatchResult(
                success=True,
                matches=all_matches,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Multi-image search failed: {e}")
            return ImageMatchResult(
                success=False,
                matches=[],
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error_message=str(e),
                error_code="MULTI_SEARCH_ERROR"
            )
    
    async def match_template_fuzzy(
        self,
        template: ImageTemplate,
        fuzzy_threshold: float,
        scale_tolerance: float,
        rotation_tolerance: float
    ) -> ImageMatchResult:
        """Perform fuzzy template matching with scale and rotation tolerance."""
        try:
            logger.info(f"Fuzzy matching {template.name} with scale±{scale_tolerance}, rotation±{rotation_tolerance}°")
            start_time = time.time()
            
            # Perform fuzzy matching via enhanced algorithms
            match_data = await self.km_interface.match_template_fuzzy(
                template_path=template.file_path,
                fuzzy_threshold=fuzzy_threshold,
                scale_tolerance=scale_tolerance,
                rotation_tolerance=rotation_tolerance
            )
            
            matches = self._process_fuzzy_matches(match_data)
            processing_time = time.time() - start_time
            
            return ImageMatchResult(
                success=True,
                matches=matches,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {e}")
            return ImageMatchResult(
                success=False,
                matches=[],
                processing_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error_message=str(e),
                error_code="FUZZY_MATCH_ERROR"
            )
    
    async def get_pixel_color(self, coordinates: ScreenCoordinates) -> PixelColorResult:
        """Get pixel color at specific screen coordinates."""
        try:
            color_data = await self.km_interface.get_pixel_color(coordinates)
            color = ColorRGB(
                red=color_data['red'],
                green=color_data['green'],
                blue=color_data['blue']
            )
            
            return PixelColorResult(success=True, color=color)
            
        except Exception as e:
            logger.error(f"Pixel color detection failed: {e}")
            return PixelColorResult(
                success=False,
                error_message=str(e),
                error_code="PIXEL_COLOR_ERROR"
            )
    
    async def wait_for_image(
        self,
        template: ImageTemplate,
        timeout: float,
        tolerance: float,
        check_interval: float
    ) -> WaitResult:
        """Wait for image to appear on screen within timeout period."""
        try:
            logger.info(f"Waiting for {template.name} (timeout: {timeout}s, interval: {check_interval}s)")
            start_time = time.time()
            checks_performed = 0
            
            while (time.time() - start_time) < timeout:
                checks_performed += 1
                
                # Search for image
                result = await self.find_image_on_screen(template, tolerance, return_all=False)
                
                if result.success and result.matches:
                    elapsed_time = time.time() - start_time
                    return WaitResult(
                        success=True,
                        elapsed_time=elapsed_time,
                        checks_performed=checks_performed,
                        matches=result.matches
                    )
                
                # Wait before next check
                await asyncio.sleep(check_interval)
            
            # Timeout reached
            elapsed_time = time.time() - start_time
            return WaitResult(
                success=False,
                elapsed_time=elapsed_time,
                checks_performed=checks_performed,
                error_message="Image not found within timeout period",
                error_code="TIMEOUT"
            )
            
        except Exception as e:
            logger.error(f"Wait for image failed: {e}")
            elapsed_time = time.time() - start_time if 'start_time' in locals() else 0.0
            return WaitResult(
                success=False,
                elapsed_time=elapsed_time,
                checks_performed=checks_performed if 'checks_performed' in locals() else 0,
                error_message=str(e),
                error_code="WAIT_ERROR"
            )
    
    async def get_supported_languages(self) -> List[OCRLanguage]:
        """Get list of supported OCR languages with caching."""
        current_time = time.time()
        
        # Return cached results if still valid
        if (self._supported_languages and 
            current_time - self._last_cache_update < self._cache_timeout):
            return self._supported_languages
        
        try:
            language_data = await self.km_interface.get_supported_ocr_languages()
            
            languages = []
            for lang_info in language_data:
                languages.append(OCRLanguage(
                    code=lang_info['code'],
                    name=lang_info.get('name', ''),
                    native_name=lang_info.get('native_name', ''),
                    quality_score=lang_info.get('quality_score', 1.0)
                ))
            
            # Update cache
            self._supported_languages = languages
            self._last_cache_update = current_time
            
            return languages
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            # Return default English if cache is empty
            if not self._supported_languages:
                return [OCRLanguage(code="en", name="English")]
            return self._supported_languages
    
    # Private helper methods
    
    async def _is_language_supported(self, language: OCRLanguage) -> bool:
        """Check if language is supported for OCR."""
        supported = await self.get_supported_languages()
        return any(lang.code == language.code for lang in supported)
    
    async def _search_single_template(
        self, 
        template: ImageTemplate, 
        tolerance: float, 
        index: int
    ) -> ImageMatchResult:
        """Search for single template with index tracking."""
        result = await self.find_image_on_screen(template, tolerance)
        
        # Add template index to matches
        for match in result.matches:
            match.template_index = index
        
        return result
    
    def _process_ocr_data(
        self, 
        ocr_data: List[Dict[str, Any]], 
        threshold: ConfidenceScore,
        language: OCRLanguage
    ) -> List[OCRTextExtraction]:
        """Process raw OCR data into extraction objects."""
        extractions = []
        
        for item in ocr_data:
            if item.get('confidence', 0.0) >= threshold:
                try:
                    extraction = OCRTextExtraction(
                        text=item['text'],
                        confidence=item['confidence'],
                        bounding_box=ScreenCoordinates(
                            item['x'], item['y']
                        ),
                        language=language.code
                    )
                    extractions.append(extraction)
                except Exception as e:
                    logger.warning(f"Failed to process OCR item: {e}")
        
        return extractions
    
    def _process_image_matches(self, match_data: List[Dict[str, Any]]) -> List[ImageMatch]:
        """Process raw image match data into match objects."""
        matches = []
        
        for item in match_data:
            try:
                match = ImageMatch(
                    center=ScreenCoordinates(item['x'], item['y']),
                    bounding_box=ScreenArea(
                        top_left=ScreenCoordinates(item['left'], item['top']),
                        bottom_right=ScreenCoordinates(item['right'], item['bottom'])
                    ),
                    confidence=item['confidence']
                )
                matches.append(match)
            except Exception as e:
                logger.warning(f"Failed to process image match: {e}")
        
        return matches
    
    def _process_fuzzy_matches(self, match_data: List[Dict[str, Any]]) -> List[ImageMatch]:
        """Process fuzzy match data with transformation information."""
        matches = []
        
        for item in match_data:
            try:
                match = ImageMatch(
                    center=ScreenCoordinates(item['x'], item['y']),
                    bounding_box=ScreenArea(
                        top_left=ScreenCoordinates(item['left'], item['top']),
                        bottom_right=ScreenCoordinates(item['right'], item['bottom'])
                    ),
                    confidence=item['confidence'],
                    similarity_score=item.get('similarity', 0.0),
                    scale_factor=item.get('scale', 1.0),
                    rotation_angle=item.get('rotation', 0.0)
                )
                matches.append(match)
            except Exception as e:
                logger.warning(f"Failed to process fuzzy match: {e}")
        
        return matches
    
    def _remove_duplicate_extractions(
        self, 
        extractions: List[OCRTextExtraction]
    ) -> List[OCRTextExtraction]:
        """Remove duplicate OCR extractions based on similarity."""
        if not extractions:
            return []
        
        unique_extractions = []
        coordinate_threshold = 10  # Pixels
        text_similarity_threshold = 0.8
        
        for extraction in extractions:
            is_duplicate = False
            
            for existing in unique_extractions:
                # Check coordinate proximity
                distance = abs(extraction.bounding_box.x - existing.bounding_box.x) + \
                          abs(extraction.bounding_box.y - existing.bounding_box.y)
                
                # Check text similarity
                text_similarity = self._calculate_text_similarity(
                    extraction.text, existing.text
                )
                
                if (distance <= coordinate_threshold and 
                    text_similarity >= text_similarity_threshold):
                    is_duplicate = True
                    
                    # Keep the one with higher confidence
                    if extraction.confidence > existing.confidence:
                        unique_extractions.remove(existing)
                        unique_extractions.append(extraction)
                    break
            
            if not is_duplicate:
                unique_extractions.append(extraction)
        
        return unique_extractions
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple ratio."""
        if not text1 or not text2:
            return 0.0
        
        # Simple similarity calculation
        longer = text1 if len(text1) > len(text2) else text2
        shorter = text2 if longer == text1 else text1
        
        if len(longer) == 0:
            return 1.0
        
        matches = sum(1 for i, char in enumerate(shorter) 
                     if i < len(longer) and char.lower() == longer[i].lower())
        
        return matches / len(longer)
