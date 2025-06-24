# src/types/plugin_types.py
"""
Comprehensive plugin type system with branded types and validation.

This module implements type-driven development for the plugin management system,
providing branded types, validation functions, and type-safe operations for
all plugin-related functionality with comprehensive security enforcement.

Target: Quality-first design with complete technique integration
"""

from typing import NewType, Optional, List, Dict, Any, Union, Protocol
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4
import re
import hashlib
from datetime import datetime

from .enumerations import PluginScriptType, PluginOutputHandling, PluginLifecycleState, PluginSecurityLevel
from .domain_types import PluginParameter, PluginCreationData, PluginMetadata


# Branded Types for Plugin Domain Safety

# Primary Identifiers
PluginID = NewType('PluginID', str)
PluginName = NewType('PluginName', str) 
PluginBundleID = NewType('PluginBundleID', str)
PluginExecutionID = NewType('PluginExecutionID', str)

# Content Types
ScriptContent = NewType('ScriptContent', str)
PluginDescription = NewType('PluginDescription', str)
ParameterName = NewType('ParameterName', str)
ParameterLabel = NewType('ParameterLabel', str)
VariableName = NewType('VariableName', str)

# File System Types
PluginPath = NewType('PluginPath', str)
BundlePath = NewType('BundlePath', str)
ScriptPath = NewType('ScriptPath', str)
InfoPlistContent = NewType('InfoPlistContent', bytes)

# Security Types
SecurityHash = NewType('SecurityHash', str)
PermissionToken = NewType('PermissionToken', str)
RiskScore = NewType('RiskScore', int)

# Resource Types
MemoryLimitMB = NewType('MemoryLimitMB', int)
TimeoutSeconds = NewType('TimeoutSeconds', int)
FileSizeBytes = NewType('FileSizeBytes', int)


# Validation Functions with Comprehensive Error Reporting

def create_plugin_id(base_name: str) -> PluginID:
    """Create validated plugin ID with unique generation.
    
    Args:
        base_name: Base name for plugin ID generation
        
    Returns:
        PluginID: Validated unique plugin identifier
        
    Raises:
        ValueError: If base_name is invalid
    """
    if not base_name or not base_name.strip():
        raise ValueError("Base name cannot be empty")
    
    if len(base_name) > 50:
        raise ValueError("Base name cannot exceed 50 characters")
    
    # Clean base name for ID generation
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', base_name)
    if not clean_name:
        raise ValueError("Base name must contain valid identifier characters")
    
    # Generate unique ID with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_suffix = str(uuid4())[:8]
    plugin_id = f"mcp_plugin_{clean_name}_{timestamp}_{unique_suffix}"
    
    return PluginID(plugin_id)


def create_plugin_name(name: str) -> PluginName:
    """Create validated plugin name.
    
    Args:
        name: Human-readable plugin name
        
    Returns:
        PluginName: Validated plugin name
        
    Raises:
        ValueError: If name is invalid
    """
    if not name or not name.strip():
        raise ValueError("Plugin name cannot be empty")
    
    if len(name) > 100:
        raise ValueError("Plugin name cannot exceed 100 characters")
    
    # Check for valid characters (allow Unicode for international support)
    if not re.match(r'^[a-zA-Z0-9_\s\-\.\u00C0-\u017F\u0400-\u04FF]+$', name):
        raise ValueError("Plugin name contains invalid characters")
    
    return PluginName(name.strip())


def create_script_content(content: str, script_type: PluginScriptType) -> ScriptContent:
    """Create validated script content with security checks.
    
    Args:
        content: Script source code
        script_type: Type of script for validation
        
    Returns:
        ScriptContent: Validated script content
        
    Raises:
        ValueError: If content is invalid or potentially dangerous
    """
    if not content or not content.strip():
        raise ValueError("Script content cannot be empty")
    
    if len(content) > 1_000_000:  # 1MB limit
        raise ValueError("Script content exceeds maximum size (1MB)")
    
    # Security validation
    security_issues = _validate_script_security(content, script_type)
    if security_issues:
        raise ValueError(f"Script security issues: {'; '.join(security_issues)}")
    
    return ScriptContent(content.strip())


def create_parameter_name(name: str) -> ParameterName:
    """Create validated parameter name following Keyboard Maestro conventions.
    
    Args:
        name: Parameter variable name
        
    Returns:
        ParameterName: Validated parameter name
        
    Raises:
        ValueError: If name doesn't follow conventions
    """
    if not name or not name.strip():
        raise ValueError("Parameter name cannot be empty")
    
    if not name.startswith("KMPARAM_"):
        raise ValueError("Parameter name must start with 'KMPARAM_'")
    
    if not re.match(r'^KMPARAM_[a-zA-Z][a-zA-Z0-9_]*$', name):
        raise ValueError("Parameter name must follow KMPARAM_ValidIdentifier format")
    
    if len(name) > 100:
        raise ValueError("Parameter name cannot exceed 100 characters")
    
    return ParameterName(name)


def create_plugin_path(path: str) -> PluginPath:
    """Create validated plugin file path.
    
    Args:
        path: File system path
        
    Returns:
        PluginPath: Validated path
        
    Raises:
        ValueError: If path is invalid or unsafe
    """
    if not path or not path.strip():
        raise ValueError("Plugin path cannot be empty")
    
    # Path traversal protection
    if ".." in path or path.startswith("/"):
        raise ValueError("Path contains directory traversal patterns")
    
    # Validate path format
    try:
        Path(path)  # Validates path format
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid path format: {e}")
    
    return PluginPath(path)


def create_security_hash(content: str) -> SecurityHash:
    """Create security hash for content verification.
    
    Args:
        content: Content to hash
        
    Returns:
        SecurityHash: SHA-256 hash of content
    """
    if not content:
        raise ValueError("Content cannot be empty for hashing")
    
    hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return SecurityHash(hash_value)


def create_risk_score(script_type: PluginScriptType, 
                     security_level: PluginSecurityLevel,
                     script_content: str) -> RiskScore:
    """Calculate risk score for plugin.
    
    Args:
        script_type: Type of script
        security_level: Security classification
        script_content: Script content for analysis
        
    Returns:
        RiskScore: Calculated risk score (0-100)
    """
    base_score = 0
    
    # Script type risk
    if script_type.requires_system_access():
        base_score += 30
    elif script_type.is_interpreted_language():
        base_score += 15
    
    # Security level risk
    base_score += security_level.get_risk_level() * 20
    
    # Content analysis risk
    dangerous_patterns = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'shell_exec\s*\(',
        r'passthru\s*\(',
        r'rm\s+-rf',
        r'sudo\s+',
        r'curl\s+.*\|\s*sh',
        r'wget\s+.*\|\s*sh'
    ]
    
    content_risk = sum(
        10 for pattern in dangerous_patterns 
        if re.search(pattern, script_content, re.IGNORECASE)
    )
    
    total_score = min(100, base_score + content_risk)
    return RiskScore(total_score)


def create_memory_limit(limit_mb: int, security_level: PluginSecurityLevel) -> MemoryLimitMB:
    """Create validated memory limit based on security level.
    
    Args:
        limit_mb: Requested memory limit in MB
        security_level: Security classification
        
    Returns:
        MemoryLimitMB: Validated memory limit
        
    Raises:
        ValueError: If limit is invalid for security level
    """
    if limit_mb <= 0:
        raise ValueError("Memory limit must be positive")
    
    # Security-based maximum limits
    max_limits = {
        PluginSecurityLevel.TRUSTED: 1000,
        PluginSecurityLevel.SANDBOXED: 100,
        PluginSecurityLevel.RESTRICTED: 500,
        PluginSecurityLevel.DANGEROUS: 50
    }
    
    max_allowed = max_limits.get(security_level, 50)
    if limit_mb > max_allowed:
        raise ValueError(f"Memory limit {limit_mb}MB exceeds maximum {max_allowed}MB for {security_level.value}")
    
    return MemoryLimitMB(limit_mb)


def create_timeout_seconds(timeout: int, security_level: PluginSecurityLevel) -> TimeoutSeconds:
    """Create validated timeout based on security level.
    
    Args:
        timeout: Requested timeout in seconds
        security_level: Security classification
        
    Returns:
        TimeoutSeconds: Validated timeout
        
    Raises:
        ValueError: If timeout is invalid for security level
    """
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    
    # Security-based maximum timeouts
    max_timeouts = {
        PluginSecurityLevel.TRUSTED: 300,  # 5 minutes
        PluginSecurityLevel.SANDBOXED: 60,  # 1 minute
        PluginSecurityLevel.RESTRICTED: 180,  # 3 minutes
        PluginSecurityLevel.DANGEROUS: 30   # 30 seconds
    }
    
    max_allowed = max_timeouts.get(security_level, 30)
    if timeout > max_allowed:
        raise ValueError(f"Timeout {timeout}s exceeds maximum {max_allowed}s for {security_level.value}")
    
    return TimeoutSeconds(timeout)


# Composite Types for Complex Operations

@dataclass(frozen=True)
class PluginIdentifier:
    """Composite identifier for flexible plugin lookup."""
    value: Union[PluginID, PluginName]
    version: Optional[str] = None
    
    def is_id(self) -> bool:
        """Check if identifier is a plugin ID."""
        return isinstance(self.value, str) and self.value.startswith("mcp_plugin_")
    
    def is_name(self) -> bool:
        """Check if identifier is a plugin name."""
        return not self.is_id()
    
    def get_lookup_key(self) -> str:
        """Get the appropriate lookup key."""
        if self.version:
            return f"{self.value}:{self.version}"
        return str(self.value)


@dataclass(frozen=True)
class PluginSecurityContext:
    """Comprehensive security context for plugin operations."""
    plugin_id: PluginID
    security_level: PluginSecurityLevel
    risk_score: RiskScore
    content_hash: SecurityHash
    allowed_operations: List[str]
    resource_limits: Dict[str, Any]
    
    def allows_operation(self, operation: str) -> bool:
        """Check if operation is allowed in this context."""
        return operation in self.allowed_operations
    
    def is_high_risk(self) -> bool:
        """Check if plugin is considered high risk."""
        return self.risk_score >= 70
    
    def requires_manual_approval(self) -> bool:
        """Check if plugin requires manual approval."""
        return self.is_high_risk() or self.security_level.requires_user_approval()


@dataclass(frozen=True)
class PluginResourceLimits:
    """Resource limits for plugin execution."""
    memory_limit: MemoryLimitMB
    timeout: TimeoutSeconds
    max_file_size: FileSizeBytes
    allowed_paths: List[str]
    network_access: bool
    
    def __post_init__(self):
        """Validate resource limits."""
        if self.memory_limit <= 0:
            raise ValueError("Memory limit must be positive")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_file_size <= 0:
            raise ValueError("File size limit must be positive")
    
    def is_within_limits(self, memory_mb: int, runtime_seconds: int, file_size_bytes: int) -> bool:
        """Check if resource usage is within limits."""
        return (memory_mb <= self.memory_limit and
                runtime_seconds <= self.timeout and
                file_size_bytes <= self.max_file_size)


# Type Guards and Validation Protocols

class PluginTypeValidator(Protocol):
    """Protocol for plugin type validation."""
    
    def validate(self, value: Any) -> bool:
        """Validate value against type requirements."""
        ...
    
    def get_error_message(self, value: Any) -> str:
        """Get descriptive error message for invalid value."""
        ...


class ScriptContentValidator:
    """Validator for script content with security analysis."""
    
    def validate(self, content: str, script_type: PluginScriptType) -> bool:
        """Validate script content for security and format."""
        try:
            create_script_content(content, script_type)
            return True
        except ValueError:
            return False
    
    def get_error_message(self, content: str) -> str:
        """Get detailed error message for invalid content."""
        if not content or not content.strip():
            return "Script content cannot be empty"
        if len(content) > 1_000_000:
            return "Script content exceeds maximum size (1MB)"
        return "Script content contains security violations"


# Helper Functions for Security Analysis

def _validate_script_security(content: str, script_type: PluginScriptType) -> List[str]:
    """Validate script content for security issues.
    
    Args:
        content: Script content to validate
        script_type: Type of script
        
    Returns:
        List of security issues found
    """
    issues = []
    
    # Common dangerous patterns
    dangerous_patterns = {
        r'eval\s*\(': "Use of eval() function detected",
        r'exec\s*\(': "Use of exec() function detected", 
        r'system\s*\(': "System command execution detected",
        r'shell_exec\s*\(': "Shell execution detected",
        r'passthru\s*\(': "Passthru execution detected",
        r'rm\s+-rf': "Recursive file deletion detected",
        r'sudo\s+': "Privilege escalation detected",
        r'curl\s+.*\|\s*sh': "Network download and execution detected",
        r'wget\s+.*\|\s*sh': "Network download and execution detected"
    }
    
    for pattern, message in dangerous_patterns.items():
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(message)
    
    # Script-type specific validation
    if script_type == PluginScriptType.SHELL:
        shell_issues = _validate_shell_script(content)
        issues.extend(shell_issues)
    elif script_type == PluginScriptType.PYTHON:
        python_issues = _validate_python_script(content)
        issues.extend(python_issues)
    
    return issues


def _validate_shell_script(content: str) -> List[str]:
    """Validate shell script specific security issues."""
    issues = []
    
    shell_patterns = {
        r'\$\([^)]*\)': "Command substitution detected",
        r'`[^`]*`': "Backtick command execution detected",
        r'>\s*/dev/null\s*2>&1\s*&': "Background process execution detected"
    }
    
    for pattern, message in shell_patterns.items():
        if re.search(pattern, content):
            issues.append(message)
    
    return issues


def _validate_python_script(content: str) -> List[str]:
    """Validate Python script specific security issues."""
    issues = []
    
    python_patterns = {
        r'import\s+os': "OS module import detected",
        r'import\s+subprocess': "Subprocess module import detected",
        r'import\s+sys': "Sys module import detected",
        r'__import__\s*\(': "Dynamic import detected",
        r'getattr\s*\(': "Dynamic attribute access detected"
    }
    
    for pattern, message in python_patterns.items():
        if re.search(pattern, content):
            issues.append(message)
    
    return issues


# Type Conversion Utilities

def plugin_id_to_bundle_id(plugin_id: PluginID) -> PluginBundleID:
    """Convert plugin ID to bundle identifier."""
    clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '', plugin_id)
    bundle_id = f"com.mcp.generated.{clean_id}"
    return PluginBundleID(bundle_id)


def plugin_name_to_filename(name: PluginName) -> str:
    """Convert plugin name to safe filename."""
    # Clean name for filesystem use
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    clean_name = re.sub(r'\s+', '_', clean_name).strip('_')
    return f"{clean_name}.kmsync"


def validate_plugin_compatibility(creation_data: PluginCreationData) -> List[str]:
    """Validate plugin compatibility and return warnings."""
    warnings = []
    
    # Check script type compatibility
    if creation_data.script_type.requires_system_access():
        warnings.append("Plugin requires system access permissions")
    
    # Check output handling compatibility
    if creation_data.output_handling.modifies_system_state():
        warnings.append("Plugin modifies system state")
    
    # Check security level compatibility
    if creation_data.is_high_risk():
        warnings.append("Plugin is classified as high risk")
    
    return warnings


# Constants for Plugin System

MAX_PLUGIN_NAME_LENGTH = 100
MAX_SCRIPT_CONTENT_SIZE = 1_000_000
MAX_PARAMETER_COUNT = 20
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MEMORY_LIMIT_MB = 100

PLUGIN_FILE_EXTENSIONS = {
    PluginScriptType.APPLESCRIPT: "scpt",
    PluginScriptType.SHELL: "sh", 
    PluginScriptType.PYTHON: "py",
    PluginScriptType.JAVASCRIPT: "js",
    PluginScriptType.PHP: "php"
}

SECURITY_RISK_THRESHOLDS = {
    "LOW": 25,
    "MEDIUM": 50,
    "HIGH": 75,
    "CRITICAL": 90
}
