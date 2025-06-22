"""
Input Sanitization Utilities for Keyboard Maestro MCP Server.

This module provides comprehensive input sanitization to prevent injection attacks,
normalize data formats, and ensure safe processing of external inputs.
All user-provided data should be sanitized before validation and processing.

Target: <200 lines per ADDER+ modularity requirements
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Import validation types
try:
    from .input_validators import ValidationResult
    from ..contracts.decorators import requires, ensures
except ImportError:
    @dataclass
    class ValidationResult:
        is_valid: bool
        sanitized_value: Any = None
        warnings: List[str] = None

class SanitizationLevel(Enum):
    """Levels of input sanitization strictness."""
    MINIMAL = "minimal"       # Basic safety only
    STANDARD = "standard"     # Recommended for most inputs
    STRICT = "strict"         # Maximum security for sensitive inputs
    PARANOID = "paranoid"     # Ultra-strict for high-risk scenarios

@dataclass(frozen=True)
class SanitizationResult:
    """Result of input sanitization with metadata."""
    sanitized_value: Any
    original_value: Any
    changes_made: List[str]
    security_warnings: List[str]
    sanitization_level: SanitizationLevel

class AppleScriptSanitizer:
    """Sanitizes AppleScript code to prevent injection attacks."""
    
    # Dangerous AppleScript patterns that should be blocked or escaped
    DANGEROUS_PATTERNS = [
        r'do\s+shell\s+script',           # Shell execution
        r'system\s+events',               # System events access
        r'activate\s+application',        # Unauthorized app activation
        r'tell\s+application\s+"Finder"', # Finder manipulation
        r'delete\s+',                     # File deletion
        r'move\s+.+\s+to\s+trash',       # Trash operations
        r'restart\s+computer',            # System restart
        r'shut\s+down',                   # System shutdown
        r'set\s+volume',                  # Volume control
    ]
    
    def __init__(self, level: SanitizationLevel = SanitizationLevel.STANDARD):
        self.level = level
    
    def sanitize(self, script: str) -> SanitizationResult:
        """Sanitize AppleScript code for safe execution."""
        if not isinstance(script, str):
            raise ValueError(f"Expected string script, got {type(script).__name__}")
        
        original_script = script
        changes_made = []
        warnings = []
        
        # Remove or escape dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, script, re.IGNORECASE):
                if self.level in (SanitizationLevel.STRICT, SanitizationLevel.PARANOID):
                    # Block entirely
                    script = re.sub(pattern, '-- BLOCKED UNSAFE COMMAND', script, flags=re.IGNORECASE)
                    changes_made.append(f"Blocked dangerous pattern: {pattern}")
                else:
                    warnings.append(f"Potentially dangerous pattern detected: {pattern}")
        
        # Escape special characters based on level
        if self.level in (SanitizationLevel.STRICT, SanitizationLevel.PARANOID):
            # Escape quotes and backslashes
            script = script.replace('\\', '\\\\').replace('"', '\\"')
            if script != original_script:
                changes_made.append("Escaped special characters")
        
        # Length limits for paranoid mode
        if self.level == SanitizationLevel.PARANOID and len(script) > 1000:
            script = script[:1000] + "\n-- TRUNCATED FOR SAFETY"
            changes_made.append("Truncated script to 1000 characters")
            warnings.append("Script was truncated due to length limits")
        
        return SanitizationResult(
            sanitized_value=script,
            original_value=original_script,
            changes_made=changes_made,
            security_warnings=warnings,
            sanitization_level=self.level
        )

class StringSanitizer:
    """Sanitizes general string inputs for safe processing."""
    
    def __init__(self, level: SanitizationLevel = SanitizationLevel.STANDARD):
        self.level = level
    
    def sanitize_identifier(self, value: str) -> SanitizationResult:
        """Sanitize identifier strings (macro names, variable names)."""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value).__name__}")
        
        original_value = value
        changes_made = []
        warnings = []
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', value)
        if sanitized != value:
            changes_made.append("Removed control characters")
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        if sanitized != value:
            changes_made.append("Normalized whitespace")
        
        # Length limits
        max_length = 255
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            changes_made.append(f"Truncated to {max_length} characters")
            warnings.append("Input was truncated due to length limits")
        
        # Character restrictions based on level
        if self.level in (SanitizationLevel.STRICT, SanitizationLevel.PARANOID):
            # Only allow alphanumeric, spaces, and safe punctuation
            sanitized = re.sub(r'[^a-zA-Z0-9\s\-_\.]', '', sanitized)
            if sanitized != original_value:
                changes_made.append("Removed unsafe characters")
        
        return SanitizationResult(
            sanitized_value=sanitized,
            original_value=original_value,
            changes_made=changes_made,
            security_warnings=warnings,
            sanitization_level=self.level
        )
    
    def sanitize_text_content(self, value: str) -> SanitizationResult:
        """Sanitize text content for safe storage and display."""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value).__name__}")
        
        original_value = value
        changes_made = []
        warnings = []
        
        # HTML escape if needed
        if '<' in value or '>' in value or '&' in value:
            sanitized = html.escape(value)
            changes_made.append("HTML escaped special characters")
        else:
            sanitized = value
        
        # Remove null bytes
        if '\x00' in sanitized:
            sanitized = sanitized.replace('\x00', '')
            changes_made.append("Removed null bytes")
            warnings.append("Null bytes detected and removed")
        
        # Length limits for large content
        max_length = 10000 if self.level == SanitizationLevel.MINIMAL else 5000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            changes_made.append(f"Truncated to {max_length} characters")
            warnings.append("Content was truncated due to length limits")
        
        return SanitizationResult(
            sanitized_value=sanitized,
            original_value=original_value,
            changes_made=changes_made,
            security_warnings=warnings,
            sanitization_level=self.level
        )

class PathSanitizer:
    """Sanitizes file paths to prevent directory traversal attacks."""
    
    def __init__(self, level: SanitizationLevel = SanitizationLevel.STANDARD):
        self.level = level
    
    def sanitize_path(self, path: str) -> SanitizationResult:
        """Sanitize file path to prevent directory traversal."""
        if not isinstance(path, str):
            raise ValueError(f"Expected string path, got {type(path).__name__}")
        
        original_path = path
        changes_made = []
        warnings = []
        
        # URL decode if needed
        if '%' in path:
            decoded = urllib.parse.unquote(path)
            if decoded != path:
                path = decoded
                changes_made.append("URL decoded path")
        
        # Remove dangerous patterns
        dangerous_patterns = ['../', '..\\', './', '.\\']
        for pattern in dangerous_patterns:
            if pattern in path:
                path = path.replace(pattern, '')
                changes_made.append(f"Removed directory traversal pattern: {pattern}")
                warnings.append("Directory traversal attempt detected and blocked")
        
        # Remove null bytes
        if '\x00' in path:
            path = path.replace('\x00', '')
            changes_made.append("Removed null bytes")
            warnings.append("Null bytes in path detected and removed")
        
        # Normalize path separators
        normalized = path.replace('\\', '/')
        if normalized != path:
            path = normalized
            changes_made.append("Normalized path separators")
        
        # Length limits
        max_length = 260  # Windows MAX_PATH compatibility
        if len(path) > max_length:
            path = path[:max_length]
            changes_made.append(f"Truncated path to {max_length} characters")
            warnings.append("Path was truncated due to length limits")
        
        return SanitizationResult(
            sanitized_value=path,
            original_value=original_path,
            changes_made=changes_made,
            security_warnings=warnings,
            sanitization_level=self.level
        )

class CompositeSanitizer:
    """Combine multiple sanitizers for comprehensive input cleaning."""
    
    def __init__(self, level: SanitizationLevel = SanitizationLevel.STANDARD):
        self.level = level
        self.string_sanitizer = StringSanitizer(level)
        self.path_sanitizer = PathSanitizer(level)
        self.applescript_sanitizer = AppleScriptSanitizer(level)
    
    def sanitize_input(self, value: Any, input_type: str = "string") -> SanitizationResult:
        """Sanitize input based on its intended type and usage."""
        if value is None:
            return SanitizationResult(
                sanitized_value=None,
                original_value=None,
                changes_made=[],
                security_warnings=[],
                sanitization_level=self.level
            )
        
        if input_type == "identifier":
            return self.string_sanitizer.sanitize_identifier(str(value))
        elif input_type == "path":
            return self.path_sanitizer.sanitize_path(str(value))
        elif input_type == "applescript":
            return self.applescript_sanitizer.sanitize(str(value))
        elif input_type == "text":
            return self.string_sanitizer.sanitize_text_content(str(value))
        else:
            # Default string sanitization
            return self.string_sanitizer.sanitize_identifier(str(value))

# Pre-configured sanitizer instances
MINIMAL_SANITIZER = CompositeSanitizer(SanitizationLevel.MINIMAL)
STANDARD_SANITIZER = CompositeSanitizer(SanitizationLevel.STANDARD)
STRICT_SANITIZER = CompositeSanitizer(SanitizationLevel.STRICT)
PARANOID_SANITIZER = CompositeSanitizer(SanitizationLevel.PARANOID)

def sanitize_macro_name(name: str) -> str:
    """Convenience function to sanitize macro names."""
    result = STANDARD_SANITIZER.sanitize_input(name, "identifier")
    return result.sanitized_value

def sanitize_variable_name(name: str) -> str:
    """Convenience function to sanitize variable names."""
    result = STANDARD_SANITIZER.sanitize_input(name, "identifier")
    return result.sanitized_value

def sanitize_file_path(path: str, strict: bool = False) -> str:
    """Convenience function to sanitize file paths."""
    sanitizer = STRICT_SANITIZER if strict else STANDARD_SANITIZER
    result = sanitizer.sanitize_input(path, "path")
    return result.sanitized_value

def sanitize_applescript(script: str, strict: bool = True) -> SanitizationResult:
    """Convenience function to sanitize AppleScript with full result."""
    sanitizer = STRICT_SANITIZER if strict else STANDARD_SANITIZER
    return sanitizer.sanitize_input(script, "applescript")
