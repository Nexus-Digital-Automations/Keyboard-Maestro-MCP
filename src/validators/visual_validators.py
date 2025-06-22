"""
Visual operation validation framework for OCR and image recognition.

This module implements comprehensive validation for visual automation parameters
including coordinates, confidence scores, image files, and visual operation constraints.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Dict, Tuple
from enum import Enum
import os
import re
from pathlib import Path

from src.validators.input_validators import BaseValidator, ValidationResult, ValidationSeverity
from src.types.values import ScreenCoordinates, ScreenArea, ConfidenceScore
from src.types.results import OperationError, ErrorType

# Supported image formats for template matching
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif'}

# OCR language code patterns (ISO 639-1/639-2)
LANGUAGE_CODE_PATTERN = re.compile(r'^[a-z]{2,3}(-[A-Z]{2})?$')

# Common OCR language codes for validation
COMMON_LANGUAGE_CODES = {
    'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko',
    'ar', 'hi', 'th', 'vi', 'tr', 'pl', 'nl', 'sv', 'da', 'no',
    'fi', 'cs', 'hu', 'ro', 'bg', 'hr', 'sk', 'sl', 'et', 'lv',
    'lt', 'mt', 'ga', 'eu', 'ca', 'gl', 'cy', 'is', 'fo', 'he',
    'ur', 'fa', 'bn', 'ta', 'te', 'kn', 'ml', 'gu', 'pa', 'or',
    'as', 'ne', 'si', 'my', 'km', 'lo', 'ka', 'hy', 'az', 'kk',
    'ky', 'uz', 'tg', 'mn', 'bo', 'dz', 'am', 'ti', 'om', 'so',
    'sw', 'rw', 'ny', 'sn', 'zu', 'xh', 'af', 'sq', 'mk', 'be',
    'uk', 'lv', 'li', 'lb', 'rm', 'fur', 'sc', 'co', 'br', 'gd'
}


class ScreenBoundsValidator(BaseValidator):
    """Validates screen coordinates and areas are within bounds."""
    
    def __init__(self, max_width: int = 5120, max_height: int = 2880):
        """Initialize with maximum screen dimensions (default: 5K display)."""
        super().__init__("ScreenBoundsValidator")
        self.max_width = max_width
        self.max_height = max_height
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate screen coordinates or area bounds."""
        if isinstance(value, tuple) and len(value) == 4:
            # Validate coordinate tuple (x1, y1, x2, y2)
            x1, y1, x2, y2 = value
            return self._validate_area_coordinates(x1, y1, x2, y2)
        
        elif isinstance(value, tuple) and len(value) == 2:
            # Validate single coordinate (x, y)
            x, y = value
            return self._validate_single_coordinate(x, y)
        
        elif hasattr(value, 'x') and hasattr(value, 'y'):
            # Validate ScreenCoordinates object
            return self._validate_single_coordinate(value.x, value.y)
        
        elif hasattr(value, 'top_left') and hasattr(value, 'bottom_right'):
            # Validate ScreenArea object
            return self._validate_area_coordinates(
                value.top_left.x, value.top_left.y,
                value.bottom_right.x, value.bottom_right.y
            )
        
        else:
            return ValidationResult.failure([
                self._create_error(
                    f"Expected coordinates tuple, ScreenCoordinates, or ScreenArea, got {type(value).__name__}",
                    "coordinates"
                )
            ])
    
    def _validate_single_coordinate(self, x: Any, y: Any) -> ValidationResult:
        """Validate single screen coordinate."""
        errors = []
        
        # Type validation
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            errors.append(self._create_error(
                f"Coordinates must be numeric, got x: {type(x).__name__}, y: {type(y).__name__}",
                "coordinates"
            ))
            return ValidationResult.failure(errors)
        
        # Convert to integers
        x, y = int(x), int(y)
        
        # Bounds validation
        if x < 0:
            errors.append(self._create_error(f"X coordinate cannot be negative: {x}", "x_coordinate"))
        
        if y < 0:
            errors.append(self._create_error(f"Y coordinate cannot be negative: {y}", "y_coordinate"))
        
        if x >= self.max_width:
            errors.append(self._create_error(f"X coordinate exceeds maximum width {self.max_width}: {x}", "x_coordinate"))
        
        if y >= self.max_height:
            errors.append(self._create_error(f"Y coordinate exceeds maximum height {self.max_height}: {y}", "y_coordinate"))
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success((x, y))
    
    def _validate_area_coordinates(self, x1: Any, y1: Any, x2: Any, y2: Any) -> ValidationResult:
        """Validate screen area coordinates."""
        errors = []
        
        # Type validation
        coords = [x1, y1, x2, y2]
        if not all(isinstance(coord, (int, float)) for coord in coords):
            errors.append(self._create_error(
                "All area coordinates must be numeric",
                "area_coordinates"
            ))
            return ValidationResult.failure(errors)
        
        # Convert to integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Individual coordinate validation
        for coord, name in [(x1, "x1"), (y1, "y1"), (x2, "x2"), (y2, "y2")]:
            if coord < 0:
                errors.append(self._create_error(f"{name} coordinate cannot be negative: {coord}", name))
        
        if x1 >= self.max_width or x2 >= self.max_width:
            errors.append(self._create_error(f"X coordinates exceed maximum width {self.max_width}", "x_coordinates"))
        
        if y1 >= self.max_height or y2 >= self.max_height:
            errors.append(self._create_error(f"Y coordinates exceed maximum height {self.max_height}", "y_coordinates"))
        
        # Area validity checks
        if x2 <= x1:
            errors.append(self._create_error(f"x2 ({x2}) must be greater than x1 ({x1})", "area_width"))
        
        if y2 <= y1:
            errors.append(self._create_error(f"y2 ({y2}) must be greater than y1 ({y1})", "area_height"))
        
        # Minimum area size
        width = x2 - x1
        height = y2 - y1
        if width < 1 or height < 1:
            errors.append(self._create_error(f"Area too small: {width}x{height} (minimum 1x1)", "area_size"))
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success((x1, y1, x2, y2))
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for screen bounds."""
        return {
            "coordinates": "Non-negative integers within screen bounds",
            "max_width": f"Maximum X coordinate: {self.max_width}",
            "max_height": f"Maximum Y coordinate: {self.max_height}",
            "area_validity": "x2 > x1 and y2 > y1 for areas",
            "minimum_size": "Areas must be at least 1x1 pixels"
        }


class ConfidenceScoreValidator(BaseValidator):
    """Validates confidence scores and thresholds."""
    
    def __init__(self):
        super().__init__("ConfidenceScoreValidator")
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate confidence score is between 0.0 and 1.0."""
        if not isinstance(value, (int, float)):
            return ValidationResult.failure([
                self._create_error(
                    f"Confidence score must be numeric, got {type(value).__name__}",
                    "confidence_score"
                )
            ])
        
        score = float(value)
        
        if not 0.0 <= score <= 1.0:
            return ValidationResult.failure([
                self._create_error(
                    f"Confidence score must be between 0.0 and 1.0, got {score}",
                    "confidence_score"
                )
            ])
        
        return ValidationResult.success(score)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for confidence scores."""
        return {
            "range": "Must be between 0.0 and 1.0",
            "type": "Numeric value (int or float)",
            "meaning": "0.0 = no confidence, 1.0 = maximum confidence"
        }


class ToleranceValidator(BaseValidator):
    """Validates tolerance values for image matching."""
    
    def __init__(self, min_tolerance: float = 0.0, max_tolerance: float = 1.0):
        super().__init__("ToleranceValidator")
        self.min_tolerance = min_tolerance
        self.max_tolerance = max_tolerance
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate tolerance value is within acceptable range."""
        if not isinstance(value, (int, float)):
            return ValidationResult.failure([
                self._create_error(
                    f"Tolerance must be numeric, got {type(value).__name__}",
                    "tolerance"
                )
            ])
        
        tolerance = float(value)
        
        if not self.min_tolerance <= tolerance <= self.max_tolerance:
            return ValidationResult.failure([
                self._create_error(
                    f"Tolerance must be between {self.min_tolerance} and {self.max_tolerance}, got {tolerance}",
                    "tolerance"
                )
            ])
        
        return ValidationResult.success(tolerance)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for tolerance values."""
        return {
            "range": f"Must be between {self.min_tolerance} and {self.max_tolerance}",
            "type": "Numeric value (int or float)",
            "meaning": f"{self.min_tolerance} = most lenient, {self.max_tolerance} = most strict"
        }


class ImageFileValidator(BaseValidator):
    """Validates image files for template matching."""
    
    def __init__(self, require_exists: bool = True):
        super().__init__("ImageFileValidator")
        self.require_exists = require_exists
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate image file path and format."""
        if not isinstance(value, str):
            return ValidationResult.failure([
                self._create_error(
                    f"Image path must be string, got {type(value).__name__}",
                    "image_path"
                )
            ])
        
        if not value.strip():
            return ValidationResult.failure([
                self._create_error("Image path cannot be empty", "image_path")
            ])
        
        errors = []
        warnings = []
        
        try:
            path = Path(value)
        except (OSError, ValueError) as e:
            return ValidationResult.failure([
                self._create_error(f"Invalid file path: {str(e)}", "image_path")
            ])
        
        # Extension validation
        if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
            errors.append(self._create_error(
                f"Unsupported image format: {path.suffix}. Supported: {', '.join(SUPPORTED_IMAGE_FORMATS)}",
                "image_format"
            ))
        
        # Existence validation
        if self.require_exists:
            if not path.exists():
                errors.append(self._create_error(f"Image file not found: {value}", "image_path"))
            elif not path.is_file():
                errors.append(self._create_error(f"Path is not a file: {value}", "image_path"))
            elif not os.access(str(path), os.R_OK):
                errors.append(self._create_error(f"Image file not readable: {value}", "image_path"))
        
        # File size warnings
        if path.exists() and path.is_file():
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                warnings.append(f"Large image file ({size_mb:.1f}MB) may impact performance")
            elif size_mb < 0.001:
                warnings.append(f"Very small image file ({size_mb:.3f}MB) may not be reliable for matching")
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        
        return ValidationResult.success(str(path.resolve()), warnings)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for image files."""
        rules = {
            "format": f"Supported formats: {', '.join(SUPPORTED_IMAGE_FORMATS)}",
            "path": "Valid file system path",
            "size_recommendation": "Optimal size: 0.1MB - 10MB for best performance"
        }
        if self.require_exists:
            rules["existence"] = "File must exist and be readable"
        return rules


class LanguageCodeValidator(BaseValidator):
    """Validates OCR language codes."""
    
    def __init__(self, strict_mode: bool = False):
        super().__init__("LanguageCodeValidator")
        self.strict_mode = strict_mode
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate OCR language code format and support."""
        if not isinstance(value, str):
            return ValidationResult.failure([
                self._create_error(
                    f"Language code must be string, got {type(value).__name__}",
                    "language_code"
                )
            ])
        
        code = value.strip().lower()
        if not code:
            return ValidationResult.failure([
                self._create_error("Language code cannot be empty", "language_code")
            ])
        
        errors = []
        warnings = []
        
        # Format validation
        if not LANGUAGE_CODE_PATTERN.match(code):
            errors.append(self._create_error(
                f"Invalid language code format: {code}. Expected ISO 639 format (e.g., 'en', 'zh-CN')",
                "language_code"
            ))
        
        # Common language validation
        base_code = code.split('-')[0]  # Extract base language code
        if self.strict_mode and base_code not in COMMON_LANGUAGE_CODES:
            errors.append(self._create_error(
                f"Unsupported language code: {code}. Use common ISO 639 codes",
                "language_code"
            ))
        elif base_code not in COMMON_LANGUAGE_CODES:
            warnings.append(f"Language code '{code}' may not be widely supported")
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        
        return ValidationResult.success(code, warnings)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for language codes."""
        return {
            "format": "ISO 639-1/639-2 format (e.g., 'en', 'zh-CN')",
            "case": "Case insensitive",
            "support": "Common languages supported" if self.strict_mode else "Extended language support"
        }


class TimeoutValidator(BaseValidator):
    """Validates timeout values for visual operations."""
    
    def __init__(self, min_timeout: float = 0.1, max_timeout: float = 300.0):
        super().__init__("TimeoutValidator")
        self.min_timeout = min_timeout
        self.max_timeout = max_timeout
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate timeout value is reasonable."""
        if not isinstance(value, (int, float)):
            return ValidationResult.failure([
                self._create_error(
                    f"Timeout must be numeric, got {type(value).__name__}",
                    "timeout"
                )
            ])
        
        timeout = float(value)
        
        if not self.min_timeout <= timeout <= self.max_timeout:
            return ValidationResult.failure([
                self._create_error(
                    f"Timeout must be between {self.min_timeout} and {self.max_timeout} seconds, got {timeout}",
                    "timeout"
                )
            ])
        
        warnings = []
        if timeout > 60:
            warnings.append(f"Long timeout ({timeout}s) may cause responsiveness issues")
        
        return ValidationResult.success(timeout, warnings)
    
    def get_validation_rules(self) -> Dict[str, str]:
        """Get validation rules for timeout values."""
        return {
            "range": f"Must be between {self.min_timeout} and {self.max_timeout} seconds",
            "type": "Numeric value (int or float)",
            "recommendation": "Use shorter timeouts (1-10s) for better responsiveness"
        }


# Pre-configured validator instances
SCREEN_BOUNDS_VALIDATOR = ScreenBoundsValidator()
CONFIDENCE_SCORE_VALIDATOR = ConfidenceScoreValidator()
TOLERANCE_VALIDATOR = ToleranceValidator()
IMAGE_FILE_VALIDATOR = ImageFileValidator()
LANGUAGE_CODE_VALIDATOR = LanguageCodeValidator()
TIMEOUT_VALIDATOR = TimeoutValidator()


# Convenience validation functions
def validate_screen_bounds(x1: int, y1: int, x2: int, y2: int) -> bool:
    """Quick validation for screen area bounds."""
    result = SCREEN_BOUNDS_VALIDATOR.validate((x1, y1, x2, y2))
    return result.is_valid


def validate_confidence_threshold(score: float) -> bool:
    """Quick validation for confidence scores."""
    result = CONFIDENCE_SCORE_VALIDATOR.validate(score)
    return result.is_valid


def validate_tolerance(tolerance: float) -> bool:
    """Quick validation for tolerance values."""
    result = TOLERANCE_VALIDATOR.validate(tolerance)
    return result.is_valid


def validate_image_file(file_path: str) -> bool:
    """Quick validation for image files."""
    result = IMAGE_FILE_VALIDATOR.validate(file_path)
    return result.is_valid


def validate_language_code(code: str) -> bool:
    """Quick validation for language codes."""
    result = LANGUAGE_CODE_VALIDATOR.validate(code)
    return result.is_valid


def validate_timeout(timeout: float) -> bool:
    """Quick validation for timeout values."""
    result = TIMEOUT_VALIDATOR.validate(timeout)
    return result.is_valid


def validate_coordinates(x: int, y: int) -> bool:
    """Quick validation for single coordinates."""
    result = SCREEN_BOUNDS_VALIDATOR.validate((x, y))
    return result.is_valid
