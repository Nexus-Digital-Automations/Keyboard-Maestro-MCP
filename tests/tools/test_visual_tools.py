"""
Comprehensive tests for visual automation MCP tools.

This module provides thorough testing for OCR and image recognition tools
with mock operations, synthetic data, and error handling verification.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from src.tools.ocr_operations import OCROperationTools
from src.tools.image_recognition import ImageRecognitionTools
from src.core.visual_automation import (
    VisualAutomation, OCRResult, ImageMatchResult, PixelColorResult, WaitResult,
    OCRLanguage, ImageTemplate, ImageMatch, VisualOperationStatus
)
from src.types.domain_types import OCRTextExtraction
from src.types.values import ScreenCoordinates, ScreenArea, ColorRGB, create_confidence_score, create_screen_coordinate


class TestOCROperationTools:
    """Test cases for OCR operation tools."""
    
    @pytest.fixture
    def mock_visual_automation(self):
        """Create mock visual automation."""
        return Mock(spec=VisualAutomation)
    
    @pytest.fixture
    def ocr_tools(self, mock_visual_automation):
        """Create OCR tools instance."""
        return OCROperationTools(mock_visual_automation)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_screen_success(self, ocr_tools, mock_visual_automation):
        """Test successful full screen OCR extraction."""
        # Arrange
        mock_extractions = [
            OCRTextExtraction(
                text="Hello World",
                confidence=create_confidence_score(0.95),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(100),
                    create_screen_coordinate(200)
                ),
                language="en"
            ),
            OCRTextExtraction(
                text="Test Text",
                confidence=create_confidence_score(0.85),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(300),
                    create_screen_coordinate(400)
                ),
                language="en"
            )
        ]
        
        mock_result = OCRResult(
            success=True,
            extractions=mock_extractions,
            processing_time=1.5
        )
        
        mock_visual_automation.extract_text_from_screen.return_value = mock_result
        
        # Act
        result = await ocr_tools.extract_text_from_screen(confidence_threshold=0.8, language="en")
        
        # Assert
        assert result["success"] is True
        assert result["total_extractions"] == 2
        assert result["confidence_threshold"] == 0.8
        assert result["language"] == "en"
        assert result["processing_time"] == 1.5
        assert len(result["extractions"]) == 2
        assert result["extractions"][0]["text"] == "Hello World"
        assert result["extractions"][0]["confidence"] == 0.95
        assert result["extractions"][1]["text"] == "Test Text"
        
        mock_visual_automation.extract_text_from_screen.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_text_from_screen_invalid_confidence(self, ocr_tools):
        """Test OCR with invalid confidence threshold."""
        # Act
        result = await ocr_tools.extract_text_from_screen(confidence_threshold=1.5)
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Confidence threshold must be between 0.0 and 1.0"
        assert result["error_code"] == "INVALID_CONFIDENCE"
    
    @pytest.mark.asyncio
    async def test_extract_text_from_area_success(self, ocr_tools, mock_visual_automation):
        """Test successful area OCR extraction."""
        # Arrange
        mock_extractions = [
            OCRTextExtraction(
                text="Area Text",
                confidence=create_confidence_score(0.9),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(150),
                    create_screen_coordinate(250)
                ),
                language="en"
            )
        ]
        
        mock_result = OCRResult(
            success=True,
            extractions=mock_extractions,
            processing_time=0.8
        )
        
        mock_visual_automation.extract_text_from_area.return_value = mock_result
        
        # Act
        result = await ocr_tools.extract_text_from_area(
            x1=100, y1=200, x2=400, y2=300,
            confidence_threshold=0.8, language="en"
        )
        
        # Assert
        assert result["success"] is True
        assert result["area"]["x1"] == 100
        assert result["area"]["y1"] == 200
        assert result["area"]["width"] == 300
        assert result["area"]["height"] == 100
        assert result["total_extractions"] == 1
        assert result["extractions"][0]["text"] == "Area Text"
    
    @pytest.mark.asyncio
    async def test_extract_text_from_area_invalid_coordinates(self, ocr_tools):
        """Test area OCR with invalid coordinates."""
        # Act - x2 <= x1 should fail
        result = await ocr_tools.extract_text_from_area(
            x1=400, y1=200, x2=300, y2=300
        )
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Invalid screen coordinates"
        assert result["error_code"] == "INVALID_COORDINATES"
    
    @pytest.mark.asyncio
    async def test_extract_text_multi_language_success(self, ocr_tools, mock_visual_automation):
        """Test multi-language OCR extraction."""
        # Arrange
        english_extractions = [
            OCRTextExtraction(
                text="Hello",
                confidence=create_confidence_score(0.9),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(100),
                    create_screen_coordinate(200)
                ),
                language="en"
            )
        ]
        
        spanish_extractions = [
            OCRTextExtraction(
                text="Hola",
                confidence=create_confidence_score(0.85),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(300),
                    create_screen_coordinate(400)
                ),
                language="es"
            )
        ]
        
        mock_result = OCRResult(
            success=True,
            extractions=english_extractions + spanish_extractions,
            processing_time=2.5
        )
        
        mock_visual_automation.extract_text_multi_language.return_value = mock_result
        
        # Act
        result = await ocr_tools.extract_text_multi_language(
            languages=["en", "es"],
            confidence_threshold=0.8
        )
        
        # Assert
        assert result["success"] is True
        assert result["languages_used"] == ["en", "es"]
        assert result["total_extractions"] == 2
        assert "en" in result["results_by_language"]
        assert "es" in result["results_by_language"]
        assert len(result["all_extractions"]) == 2
    
    @pytest.mark.asyncio
    async def test_find_text_on_screen_success(self, ocr_tools, mock_visual_automation):
        """Test successful text search on screen."""
        # Arrange
        mock_extractions = [
            OCRTextExtraction(
                text="Find this text here",
                confidence=create_confidence_score(0.9),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(100),
                    create_screen_coordinate(200)
                ),
                language="en"
            ),
            OCRTextExtraction(
                text="Other text",
                confidence=create_confidence_score(0.8),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(300),
                    create_screen_coordinate(400)
                ),
                language="en"
            )
        ]
        
        mock_result = OCRResult(
            success=True,
            extractions=mock_extractions,
            processing_time=1.2
        )
        
        mock_visual_automation.extract_text_from_screen.return_value = mock_result
        
        # Act
        result = await ocr_tools.find_text_on_screen(
            search_text="text",
            confidence_threshold=0.8,
            language="en",
            case_sensitive=False
        )
        
        # Assert
        assert result["success"] is True
        assert result["search_text"] == "text"
        assert result["matches_found"] == 2  # Both extractions contain "text"
        assert result["matches"][0]["text"] == "Find this text here"
        assert result["matches"][0]["match_type"] == "partial"
    
    @pytest.mark.asyncio
    async def test_find_text_on_screen_empty_search(self, ocr_tools):
        """Test text search with empty search term."""
        # Act
        result = await ocr_tools.find_text_on_screen(search_text="")
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Search text cannot be empty"
        assert result["error_code"] == "EMPTY_SEARCH_TEXT"
    
    @pytest.mark.asyncio
    async def test_get_supported_languages_success(self, ocr_tools, mock_visual_automation):
        """Test getting supported OCR languages."""
        # Arrange
        mock_languages = [
            OCRLanguage(code="en", name="English", native_name="English", quality_score=1.0),
            OCRLanguage(code="es", name="Spanish", native_name="Español", quality_score=0.95),
            OCRLanguage(code="fr", name="French", native_name="Français", quality_score=0.9)
        ]
        
        mock_visual_automation.get_supported_languages.return_value = mock_languages
        
        # Act
        result = await ocr_tools.get_supported_languages()
        
        # Assert
        assert result["success"] is True
        assert result["total_languages"] == 3
        assert len(result["languages"]) == 3
        assert result["languages"][0]["code"] == "en"
        assert result["languages"][0]["name"] == "English"
        assert result["languages"][1]["code"] == "es"


class TestImageRecognitionTools:
    """Test cases for image recognition tools."""
    
    @pytest.fixture
    def mock_visual_automation(self):
        """Create mock visual automation."""
        return Mock(spec=VisualAutomation)
    
    @pytest.fixture
    def image_tools(self, mock_visual_automation):
        """Create image recognition tools instance."""
        return ImageRecognitionTools(mock_visual_automation)
    
    @pytest.mark.asyncio
    async def test_find_image_on_screen_success(self, image_tools, mock_visual_automation):
        """Test successful image search on screen."""
        # Arrange
        mock_matches = [
            ImageMatch(
                center=ScreenCoordinates(
                    create_screen_coordinate(200),
                    create_screen_coordinate(300)
                ),
                bounding_box=ScreenArea(
                    top_left=ScreenCoordinates(
                        create_screen_coordinate(150),
                        create_screen_coordinate(250)
                    ),
                    bottom_right=ScreenCoordinates(
                        create_screen_coordinate(250),
                        create_screen_coordinate(350)
                    )
                ),
                confidence=create_confidence_score(0.9)
            )
        ]
        
        mock_result = ImageMatchResult(
            success=True,
            matches=mock_matches,
            processing_time=2.1
        )
        
        mock_visual_automation.find_image_on_screen.return_value = mock_result
        
        # Mock file validation
        with patch('src.validators.visual_validators.validate_image_file', return_value=True):
            # Act
            result = await image_tools.find_image_on_screen(
                template_path="/test/template.png",
                tolerance=0.8,
                return_all_matches=False
            )
        
        # Assert
        assert result["success"] is True
        assert result["template_path"] == "/test/template.png"
        assert result["tolerance"] == 0.8
        assert result["matches_found"] == 1
        assert result["processing_time"] == 2.1
        assert result["matches"][0]["x"] == 200
        assert result["matches"][0]["y"] == 300
        assert result["matches"][0]["confidence"] == 0.9
        assert result["best_match"]["x"] == 200
    
    @pytest.mark.asyncio
    async def test_find_image_on_screen_invalid_file(self, image_tools):
        """Test image search with invalid template file."""
        # Mock file validation to return False
        with patch('src.validators.visual_validators.validate_image_file', return_value=False):
            # Act
            result = await image_tools.find_image_on_screen(
                template_path="/invalid/file.txt"
            )
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Invalid or non-existent image file"
        assert result["error_code"] == "INVALID_IMAGE_FILE"
    
    @pytest.mark.asyncio
    async def test_find_image_in_area_success(self, image_tools, mock_visual_automation):
        """Test successful image search in area."""
        # Arrange
        mock_matches = [
            ImageMatch(
                center=ScreenCoordinates(
                    create_screen_coordinate(350),
                    create_screen_coordinate(450)
                ),
                bounding_box=ScreenArea(
                    top_left=ScreenCoordinates(
                        create_screen_coordinate(325),
                        create_screen_coordinate(425)
                    ),
                    bottom_right=ScreenCoordinates(
                        create_screen_coordinate(375),
                        create_screen_coordinate(475)
                    )
                ),
                confidence=create_confidence_score(0.85)
            )
        ]
        
        mock_result = ImageMatchResult(
            success=True,
            matches=mock_matches,
            processing_time=1.5
        )
        
        mock_visual_automation.find_image_in_area.return_value = mock_result
        
        # Mock file validation
        with patch('src.validators.visual_validators.validate_image_file', return_value=True):
            # Act
            result = await image_tools.find_image_in_area(
                template_path="/test/template.png",
                x1=300, y1=400, x2=500, y2=600,
                tolerance=0.8
            )
        
        # Assert
        assert result["success"] is True
        assert result["search_area"]["x1"] == 300
        assert result["search_area"]["y1"] == 400
        assert result["search_area"]["width"] == 200
        assert result["search_area"]["height"] == 200
        assert result["matches"][0]["x"] == 350
        assert result["matches"][0]["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_find_multiple_images_success(self, image_tools, mock_visual_automation):
        """Test searching for multiple images."""
        # Arrange
        mock_matches = [
            ImageMatch(
                center=ScreenCoordinates(
                    create_screen_coordinate(100),
                    create_screen_coordinate(200)
                ),
                bounding_box=ScreenArea(
                    top_left=ScreenCoordinates(
                        create_screen_coordinate(75),
                        create_screen_coordinate(175)
                    ),
                    bottom_right=ScreenCoordinates(
                        create_screen_coordinate(125),
                        create_screen_coordinate(225)
                    )
                ),
                confidence=create_confidence_score(0.9),
                template_index=0
            ),
            ImageMatch(
                center=ScreenCoordinates(
                    create_screen_coordinate(300),
                    create_screen_coordinate(400)
                ),
                bounding_box=ScreenArea(
                    top_left=ScreenCoordinates(
                        create_screen_coordinate(275),
                        create_screen_coordinate(375)
                    ),
                    bottom_right=ScreenCoordinates(
                        create_screen_coordinate(325),
                        create_screen_coordinate(425)
                    )
                ),
                confidence=create_confidence_score(0.8),
                template_index=1
            )
        ]
        
        mock_result = ImageMatchResult(
            success=True,
            matches=mock_matches,
            processing_time=3.2
        )
        
        mock_visual_automation.find_multiple_images.return_value = mock_result
        
        # Mock file validation
        with patch('src.validators.visual_validators.validate_image_file', return_value=True):
            # Act
            result = await image_tools.find_multiple_images(
                template_paths=["/test/template1.png", "/test/template2.png"],
                tolerance=0.8,
                timeout=5.0
            )
        
        # Assert
        assert result["success"] is True
        assert result["template_count"] == 2
        assert result["total_matches"] == 2
        assert "/test/template1.png" in result["template_results"]
        assert "/test/template2.png" in result["template_results"]
        assert result["template_results"]["/test/template1.png"]["matches_found"] == 1
        assert result["template_results"]["/test/template2.png"]["matches_found"] == 1
    
    @pytest.mark.asyncio
    async def test_match_template_fuzzy_success(self, image_tools, mock_visual_automation):
        """Test fuzzy template matching."""
        # Arrange
        mock_matches = [
            ImageMatch(
                center=ScreenCoordinates(
                    create_screen_coordinate(400),
                    create_screen_coordinate(500)
                ),
                bounding_box=ScreenArea(
                    top_left=ScreenCoordinates(
                        create_screen_coordinate(375),
                        create_screen_coordinate(475)
                    ),
                    bottom_right=ScreenCoordinates(
                        create_screen_coordinate(425),
                        create_screen_coordinate(525)
                    )
                ),
                confidence=create_confidence_score(0.7),
                similarity_score=0.75,
                scale_factor=1.1,
                rotation_angle=5.2
            )
        ]
        
        mock_result = ImageMatchResult(
            success=True,
            matches=mock_matches,
            processing_time=4.5
        )
        
        mock_visual_automation.match_template_fuzzy.return_value = mock_result
        
        # Mock file validation
        with patch('src.validators.visual_validators.validate_image_file', return_value=True):
            # Act
            result = await image_tools.match_template_fuzzy(
                template_path="/test/template.png",
                fuzzy_threshold=0.6,
                scale_tolerance=0.1,
                rotation_tolerance=10.0
            )
        
        # Assert
        assert result["success"] is True
        assert result["fuzzy_threshold"] == 0.6
        assert result["scale_tolerance"] == 0.1
        assert result["rotation_tolerance"] == 10.0
        assert result["matches"][0]["similarity_score"] == 0.75
        assert result["matches"][0]["scale_factor"] == 1.1
        assert result["matches"][0]["rotation_angle"] == 5.2
    
    @pytest.mark.asyncio
    async def test_get_pixel_color_success(self, image_tools, mock_visual_automation):
        """Test pixel color detection."""
        # Arrange
        mock_result = PixelColorResult(
            success=True,
            color=ColorRGB(red=255, green=128, blue=64)
        )
        
        mock_visual_automation.get_pixel_color.return_value = mock_result
        
        # Act
        result = await image_tools.get_pixel_color(x=100, y=200)
        
        # Assert
        assert result["success"] is True
        assert result["x"] == 100
        assert result["y"] == 200
        assert result["color"]["red"] == 255
        assert result["color"]["green"] == 128
        assert result["color"]["blue"] == 64
        assert result["color"]["hex"] == "#FF8040"
        assert result["color"]["rgb_tuple"] == [255, 128, 64]
    
    @pytest.mark.asyncio
    async def test_get_pixel_color_invalid_coordinates(self, image_tools):
        """Test pixel color with invalid coordinates."""
        # Act
        result = await image_tools.get_pixel_color(x=-10, y=200)
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Coordinates must be non-negative"
        assert result["error_code"] == "INVALID_COORDINATES"
    
    @pytest.mark.asyncio
    async def test_wait_for_image_success(self, image_tools, mock_visual_automation):
        """Test waiting for image to appear."""
        # Arrange
        mock_matches = [
            ImageMatch(
                center=ScreenCoordinates(
                    create_screen_coordinate(150),
                    create_screen_coordinate(250)
                ),
                bounding_box=ScreenArea(
                    top_left=ScreenCoordinates(
                        create_screen_coordinate(125),
                        create_screen_coordinate(225)
                    ),
                    bottom_right=ScreenCoordinates(
                        create_screen_coordinate(175),
                        create_screen_coordinate(275)
                    )
                ),
                confidence=create_confidence_score(0.85)
            )
        ]
        
        mock_result = WaitResult(
            success=True,
            elapsed_time=2.3,
            checks_performed=5,
            matches=mock_matches
        )
        
        mock_visual_automation.wait_for_image.return_value = mock_result
        
        # Mock file validation
        with patch('src.validators.visual_validators.validate_image_file', return_value=True):
            # Act
            result = await image_tools.wait_for_image(
                template_path="/test/template.png",
                timeout=10.0,
                tolerance=0.8,
                check_interval=0.5
            )
        
        # Assert
        assert result["success"] is True
        assert result["timeout"] == 10.0
        assert result["elapsed_time"] == 2.3
        assert result["checks_performed"] == 5
        assert result["found_at"]["x"] == 150
        assert result["found_at"]["y"] == 250
        assert result["found_at"]["confidence"] == 0.85
        assert result["found_at"]["found_after"] == 2.3
    
    @pytest.mark.asyncio
    async def test_wait_for_image_timeout(self, image_tools, mock_visual_automation):
        """Test waiting for image with timeout."""
        # Arrange
        mock_result = WaitResult(
            success=False,
            elapsed_time=10.0,
            checks_performed=20,
            error_message="Image not found within timeout period",
            error_code="TIMEOUT"
        )
        
        mock_visual_automation.wait_for_image.return_value = mock_result
        
        # Mock file validation
        with patch('src.validators.visual_validators.validate_image_file', return_value=True):
            # Act
            result = await image_tools.wait_for_image(
                template_path="/test/template.png",
                timeout=10.0,
                tolerance=0.8,
                check_interval=0.5
            )
        
        # Assert
        assert result["success"] is False
        assert result["elapsed_time"] == 10.0
        assert result["checks_performed"] == 20
        assert result["error"] == "Image not found within timeout period"
        assert result["error_code"] == "TIMEOUT"


class TestVisualAutomationCore:
    """Test cases for visual automation core logic."""
    
    @pytest.fixture
    def mock_km_interface(self):
        """Create mock KM interface."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_error_handler(self):
        """Create mock error handler."""
        return Mock()
    
    @pytest.fixture
    def visual_automation(self, mock_km_interface, mock_error_handler):
        """Create visual automation instance."""
        return VisualAutomation(mock_km_interface, mock_error_handler)
    
    @pytest.mark.asyncio
    async def test_language_support_caching(self, visual_automation, mock_km_interface):
        """Test language support caching mechanism."""
        # Arrange
        mock_language_data = [
            {"code": "en", "name": "English", "native_name": "English", "quality_score": 1.0},
            {"code": "es", "name": "Spanish", "native_name": "Español", "quality_score": 0.95}
        ]
        
        mock_km_interface.get_supported_ocr_languages.return_value = mock_language_data
        
        # Act - First call should hit the interface
        languages1 = await visual_automation.get_supported_languages()
        
        # Act - Second call should use cache
        languages2 = await visual_automation.get_supported_languages()
        
        # Assert
        assert len(languages1) == 2
        assert len(languages2) == 2
        assert languages1[0].code == "en"
        assert languages2[0].code == "en"
        
        # Should only call interface once due to caching
        mock_km_interface.get_supported_ocr_languages.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_duplicate_extraction_removal(self, visual_automation):
        """Test OCR duplicate extraction removal logic."""
        # Arrange
        extractions = [
            OCRTextExtraction(
                text="Hello",
                confidence=create_confidence_score(0.9),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(100),
                    create_screen_coordinate(200)
                ),
                language="en"
            ),
            OCRTextExtraction(
                text="Hello",  # Duplicate text
                confidence=create_confidence_score(0.8),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(105),  # Close coordinates
                    create_screen_coordinate(205)
                ),
                language="en"
            ),
            OCRTextExtraction(
                text="World",
                confidence=create_confidence_score(0.85),
                bounding_box=ScreenCoordinates(
                    create_screen_coordinate(300),
                    create_screen_coordinate(400)
                ),
                language="en"
            )
        ]
        
        # Act
        unique_extractions = visual_automation._remove_duplicate_extractions(extractions)
        
        # Assert
        assert len(unique_extractions) == 2  # One duplicate removed
        # Should keep the higher confidence one
        hello_extractions = [e for e in unique_extractions if e.text == "Hello"]
        assert len(hello_extractions) == 1
        assert hello_extractions[0].confidence == 0.9


# Integration tests with synthetic data
class TestVisualToolsIntegration:
    """Integration tests with synthetic visual data."""
    
    @pytest.mark.asyncio
    async def test_ocr_workflow_integration(self):
        """Test complete OCR workflow with mock data."""
        # This would test: screen capture -> OCR -> text extraction -> validation
        # Implementation would use synthetic screen data
        pass
    
    @pytest.mark.asyncio
    async def test_image_recognition_workflow(self):
        """Test complete image recognition workflow."""
        # This would test: template loading -> screen capture -> matching -> coordinate return
        # Implementation would use synthetic image templates and screen data
        pass
    
    @pytest.mark.asyncio
    async def test_performance_with_large_operations(self):
        """Test performance with large-scale operations."""
        # This would test: multiple concurrent OCR/image operations
        # Performance monitoring and resource usage validation
        pass
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self):
        """Test error recovery in visual operations."""
        # This would test: network failures, permission errors, file corruption
        # Error propagation through tool layers
        pass


# Property-based testing for validation
class TestVisualValidationProperties:
    """Property-based tests for visual validation logic."""
    
    def test_coordinate_validation_properties(self):
        """Test coordinate validation with generated values."""
        # This would use hypothesis to generate test coordinates
        # Verify validation properties hold for all valid/invalid inputs
        pass
    
    def test_confidence_score_properties(self):
        """Test confidence score validation properties."""
        # This would use hypothesis to test confidence score edge cases
        pass


if __name__ == "__main__":
    pytest.main([__file__])
