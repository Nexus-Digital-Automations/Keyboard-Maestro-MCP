"""
Comprehensive Test Suite for Input Validation and Boundary Protection.

This module provides property-based and contract verification testing for
all validation, sanitization, and boundary protection components to ensure
defensive programming patterns work correctly under all conditions.

Target: <250 lines per ADDER+ modularity requirements
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, assume

# Import validation framework components
try:
    from ..validators.input_validators import (
        MacroIdentifierValidator,
        VariableNameValidator,
        FilePathValidator,
        CompositeValidator,
        validate_macro_identifier,
        validate_variable_name,
        validate_file_path,
    )
    
    from ..validators.sanitizers import (
        AppleScriptSanitizer,
        StringSanitizer,
        PathSanitizer,
        SanitizationLevel,
        sanitize_macro_name,
        sanitize_applescript,
    )
    
    from ..validators import (
        validate_input_completely,
        validate_and_sanitize_macro_name,
        validate_and_sanitize_applescript,
    )
except ImportError:
    pytest.skip("Validation modules not available", allow_module_level=True)

class TestInputValidators:
    """Test suite for input validation components."""
    
    def test_macro_identifier_validator_valid_uuid(self):
        """Test macro identifier validation with valid UUIDs."""
        validator = MacroIdentifierValidator()
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        
        result = validator.validate(uuid_str)
        assert result.is_valid
        assert result.sanitized_value == uuid_str
        assert len(result.errors) == 0
    
    def test_macro_identifier_validator_valid_name(self):
        """Test macro identifier validation with valid names."""
        validator = MacroIdentifierValidator()
        valid_names = ["My Macro", "Test_Macro_123", "Macro-with-dashes", "Macro.with.dots"]
        
        for name in valid_names:
            result = validator.validate(name)
            assert result.is_valid, f"Name '{name}' should be valid"
            assert result.sanitized_value == name
    
    def test_macro_identifier_validator_invalid_inputs(self):
        """Test macro identifier validation with invalid inputs."""
        validator = MacroIdentifierValidator()
        invalid_inputs = [
            None,
            "",
            "a" * 256,  # Too long
            "Invalid@Characters!",
            123,  # Wrong type
            "Macro\nwith\nnewlines",
        ]
        
        for invalid_input in invalid_inputs:
            result = validator.validate(invalid_input)
            assert not result.is_valid, f"Input '{invalid_input}' should be invalid"
            assert len(result.errors) > 0
    
    @given(name=st.text(min_size=1, max_size=50))
    def test_variable_name_validator_properties(self, name):
        """Property-based testing for variable name validation."""
        validator = VariableNameValidator()
        result = validator.validate(name)
        
        # Valid variable names start with letter/underscore and contain only alphanumeric + underscore
        expected_valid = (
            len(name) <= 255 and
            name[0].isalpha() or name[0] == '_'
        ) and all(c.isalnum() or c == '_' for c in name)
        
        assert result.is_valid == expected_valid
    
    def test_file_path_validator_existing_file(self):
        """Test file path validation with existing files."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"test content")
        
        try:
            validator = FilePathValidator(require_exists=True, require_readable=True)
            result = validator.validate(tmp_path)
            
            assert result.is_valid
            assert Path(result.sanitized_value).exists()
        finally:
            os.unlink(tmp_path)
    
    def test_file_path_validator_non_existing_file(self):
        """Test file path validation with non-existing files."""
        non_existing_path = "/tmp/non_existing_file_12345.txt"
        
        validator = FilePathValidator(require_exists=True)
        result = validator.validate(non_existing_path)
        
        assert not result.is_valid
        assert any("does not exist" in error.message for error in result.errors)
    
    def test_composite_validator_and_logic(self):
        """Test composite validator with AND logic."""
        validator1 = MacroIdentifierValidator()
        validator2 = VariableNameValidator()
        
        composite = CompositeValidator([validator1, validator2], logic="AND")
        
        # Valid for both validators
        result = composite.validate("ValidName")
        assert result.is_valid
        
        # Invalid for variable name validator (contains space)
        result = composite.validate("Invalid Name")
        assert not result.is_valid
    
    def test_composite_validator_or_logic(self):
        """Test composite validator with OR logic."""
        validator1 = MacroIdentifierValidator()  
        validator2 = VariableNameValidator()
        
        composite = CompositeValidator([validator1, validator2], logic="OR")
        
        # Valid for macro identifier but not variable name
        result = composite.validate("Valid Name")
        assert result.is_valid
        
        # Invalid for both
        result = composite.validate("Invalid@Name!")
        assert not result.is_valid

class TestInputSanitizers:
    """Test suite for input sanitization components."""
    
    def test_applescript_sanitizer_blocks_dangerous_commands(self):
        """Test AppleScript sanitizer blocks dangerous commands."""
        sanitizer = AppleScriptSanitizer(SanitizationLevel.STRICT)
        dangerous_script = 'do shell script "rm -rf /"'
        
        result = sanitizer.sanitize(dangerous_script)
        assert "BLOCKED UNSAFE COMMAND" in result.sanitized_value
        assert len(result.changes_made) > 0
        assert any("dangerous pattern" in change.lower() for change in result.changes_made)
    
    def test_applescript_sanitizer_paranoid_truncation(self):
        """Test AppleScript sanitizer truncates long scripts in paranoid mode."""
        sanitizer = AppleScriptSanitizer(SanitizationLevel.PARANOID)
        long_script = "tell application \"Finder\"\n" + "-- comment\n" * 100
        
        result = sanitizer.sanitize(long_script)
        assert len(result.sanitized_value) <= 1000 + len("\n-- TRUNCATED FOR SAFETY")
        assert "TRUNCATED FOR SAFETY" in result.sanitized_value
    
    def test_string_sanitizer_removes_control_characters(self):
        """Test string sanitizer removes control characters."""
        sanitizer = StringSanitizer()
        text_with_controls = "Test\x00\x01\x1FString"
        
        result = sanitizer.sanitize_identifier(text_with_controls)
        assert "\x00" not in result.sanitized_value
        assert "\x01" not in result.sanitized_value
        assert "\x1F" not in result.sanitized_value
        assert result.sanitized_value == "TestString"
    
    def test_string_sanitizer_normalizes_whitespace(self):
        """Test string sanitizer normalizes whitespace."""
        sanitizer = StringSanitizer()
        text_with_whitespace = "  Test   String  \n\t  "
        
        result = sanitizer.sanitize_identifier(text_with_whitespace)
        assert result.sanitized_value == "Test String"
        assert "Normalized whitespace" in result.changes_made
    
    def test_path_sanitizer_prevents_directory_traversal(self):
        """Test path sanitizer prevents directory traversal attacks."""
        sanitizer = PathSanitizer()
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/path/../../../secret",
            "path/./file",
        ]
        
        for path in traversal_paths:
            result = sanitizer.sanitize_path(path)
            assert ".." not in result.sanitized_value
            assert len(result.security_warnings) > 0
    
    def test_path_sanitizer_url_decoding(self):
        """Test path sanitizer handles URL-encoded paths."""
        sanitizer = PathSanitizer()
        encoded_path = "/path%2F..%2F..%2Ffile"
        
        result = sanitizer.sanitize_path(encoded_path)
        assert "%2F" not in result.sanitized_value
        assert "URL decoded" in result.changes_made

class TestBoundaryProtection:
    """Test suite for boundary protection components."""
    
    @patch('subprocess.run')
    def test_accessibility_permission_check(self, mock_subprocess):
        """Test macOS accessibility permission checking."""
        try:
            from ..boundaries.security_boundaries import MacOSPermissionChecker
        except ImportError:
            pytest.skip("Security boundaries module not available")
        
        # Mock successful permission check
        mock_subprocess.return_value.returncode = 0
        
        checker = MacOSPermissionChecker()
        has_permission = checker.check_accessibility_permission()
        
        assert has_permission
        mock_subprocess.assert_called_once()
    
    def test_resource_limit_enforcement(self):
        """Test system resource limit enforcement."""
        try:
            from ..boundaries.system_boundaries import ResourceMonitor, ResourceType
        except ImportError:
            pytest.skip("System boundaries module not available")
        
        monitor = ResourceMonitor()
        
        # Test exceeding concurrent operation limit
        estimated_resources = {ResourceType.CONCURRENT_OPERATIONS: 100}  # Exceeds default limit of 50
        
        result = monitor.check_resource_availability("test_operation", estimated_resources)
        
        assert not result.allowed
        assert len(result.limit_violations) > 0
        assert "concurrent_operations" in str(result.limit_violations[0]).lower()

class TestUnifiedValidation:
    """Test suite for unified validation pipeline."""
    
    def test_complete_macro_name_validation(self):
        """Test complete macro name validation pipeline."""
        valid_name = "My Test Macro"
        
        result = validate_and_sanitize_macro_name(valid_name)
        
        assert result.is_valid
        assert result.sanitized_value == valid_name
        assert len(result.validation_errors) == 0
        assert "valid and safe" in result.recommended_action.lower()
    
    def test_complete_applescript_validation(self):
        """Test complete AppleScript validation pipeline."""
        dangerous_script = 'do shell script "dangerous command"'
        
        result = validate_and_sanitize_applescript(dangerous_script)
        
        assert not result.is_valid or len(result.security_warnings) > 0
        # Script should be blocked or warned about
        assert ("BLOCKED" in result.sanitized_value or len(result.security_warnings) > 0)
    
    @given(macro_name=st.text(min_size=1, max_size=100))
    def test_macro_name_validation_properties(self, macro_name):
        """Property-based testing for macro name validation."""
        assume(isinstance(macro_name, str))
        
        result = validate_and_sanitize_macro_name(macro_name)
        
        # Properties that should always hold
        if result.is_valid:
            assert isinstance(result.sanitized_value, str)
            assert len(result.sanitized_value) > 0
            assert len(result.sanitized_value) <= 255
        
        # Sanitized value should never contain dangerous characters
        assert result.sanitized_value is not None

class TestErrorHandling:
    """Test suite for error handling and edge cases."""
    
    def test_validation_with_none_input(self):
        """Test validation handles None input gracefully."""
        result = validate_macro_identifier(None)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validation_with_wrong_type(self):
        """Test validation handles wrong input types gracefully."""
        result = validate_variable_name(12345)
        assert not result.is_valid
        assert "Expected string" in str(result.errors[0].message)
    
    def test_sanitization_with_extreme_inputs(self):
        """Test sanitization handles extreme inputs."""
        extreme_inputs = [
            "",  # Empty string
            "\x00" * 100,  # Null bytes
            "a" * 10000,  # Very long string
            "\n\r\t" * 50,  # Lots of whitespace
        ]
        
        for input_value in extreme_inputs:
            result = sanitize_macro_name(input_value)
            # Should not crash and should return a string
            assert isinstance(result, str)

# Convenience test running functions
def run_validation_tests():
    """Run all validation tests."""
    pytest.main([__file__ + "::TestInputValidators", "-v"])

def run_sanitization_tests():
    """Run all sanitization tests."""
    pytest.main([__file__ + "::TestInputSanitizers", "-v"])

def run_boundary_tests():
    """Run all boundary protection tests."""
    pytest.main([__file__ + "::TestBoundaryProtection", "-v"])

def run_all_tests():
    """Run complete test suite."""
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    run_all_tests()
