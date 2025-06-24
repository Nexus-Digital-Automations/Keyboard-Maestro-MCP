# src/boundaries/plugin_boundaries.py
"""
Plugin Security Boundaries - Multi-layered Defense Implementation.

This module implements comprehensive security boundary protection for the
plugin system using defensive programming and negative space programming
principles to prevent security violations and system compromise.

Target: <250 lines with comprehensive security coverage
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Any, Pattern
from pathlib import Path
import re
import ast
import os
import subprocess
from enum import Enum

from ..types.plugin_types import (
    PluginID, ScriptContent, SecurityHash, RiskScore,
    create_risk_score, SECURITY_RISK_THRESHOLDS
)
from ..types.domain_types import PluginCreationData, PluginValidationResult
from ..types.enumerations import PluginScriptType, PluginSecurityLevel
from .security_boundaries import SecurityBoundaryResult, SecurityContext


class PluginThreatType(Enum):
    """Categories of plugin security threats."""
    CODE_INJECTION = "code_injection"
    SYSTEM_COMPROMISE = "system_compromise"
    DATA_EXFILTRATION = "data_exfiltration"
    RESOURCE_ABUSE = "resource_abuse"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    NETWORK_ATTACK = "network_attack"
    FILE_SYSTEM_ATTACK = "file_system_attack"


@dataclass(frozen=True)
class SecurityPattern:
    """Security threat pattern definition."""
    pattern: Pattern[str]
    threat_type: PluginThreatType
    severity: int  # 1-10 scale
    description: str
    mitigation: str


@dataclass(frozen=True)
class PluginSecurityAnalysis:
    """Comprehensive security analysis result."""
    is_safe: bool
    risk_score: RiskScore
    threats_detected: List[PluginThreatType]
    security_violations: List[str]
    warnings: List[str]
    required_permissions: Set[str]
    recommended_sandbox_level: PluginSecurityLevel


class PluginSecurityValidator(ABC):
    """Abstract base for plugin security validation."""
    
    @abstractmethod
    def validate_security(self, content: ScriptContent, script_type: PluginScriptType) -> PluginSecurityAnalysis:
        """Validate script content for security threats."""
        ...


class ScriptContentSecurityValidator(PluginSecurityValidator):
    """Multi-layered script content security validator."""
    
    def __init__(self):
        self._initialize_threat_patterns()
    
    def _initialize_threat_patterns(self) -> None:
        """Initialize comprehensive threat detection patterns."""
        self.threat_patterns = [
            # Code Injection Patterns
            SecurityPattern(
                re.compile(r'eval\s*\(', re.IGNORECASE),
                PluginThreatType.CODE_INJECTION, 9,
                "Dynamic code evaluation detected",
                "Use static code analysis and avoid eval()"
            ),
            SecurityPattern(
                re.compile(r'exec\s*\(', re.IGNORECASE),
                PluginThreatType.CODE_INJECTION, 9,
                "Dynamic code execution detected",
                "Use predefined functions instead of exec()"
            ),
            
            # System Compromise Patterns
            SecurityPattern(
                re.compile(r'rm\s+-rf\s+/', re.IGNORECASE),
                PluginThreatType.SYSTEM_COMPROMISE, 10,
                "Recursive file deletion of system directories",
                "Restrict file operations to specific directories"
            ),
            SecurityPattern(
                re.compile(r'sudo\s+', re.IGNORECASE),
                PluginThreatType.PRIVILEGE_ESCALATION, 8,
                "Privilege escalation attempt",
                "Run plugins with limited privileges"
            ),
            
            # Network Attack Patterns
            SecurityPattern(
                re.compile(r'curl\s+.*\|\s*sh', re.IGNORECASE),
                PluginThreatType.NETWORK_ATTACK, 10,
                "Network download and execution",
                "Validate and sandbox downloaded content"
            ),
            SecurityPattern(
                re.compile(r'wget\s+.*\|\s*sh', re.IGNORECASE),
                PluginThreatType.NETWORK_ATTACK, 10,
                "Network download and execution",
                "Validate and sandbox downloaded content"
            ),
            
            # Data Exfiltration Patterns
            SecurityPattern(
                re.compile(r'scp\s+.*\s+.*@', re.IGNORECASE),
                PluginThreatType.DATA_EXFILTRATION, 7,
                "Secure copy to remote host",
                "Monitor and approve data transfers"
            ),
            SecurityPattern(
                re.compile(r'rsync\s+.*\s+.*@', re.IGNORECASE),
                PluginThreatType.DATA_EXFILTRATION, 7,
                "Remote synchronization detected",
                "Monitor and approve data transfers"
            ),
            
            # File System Attack Patterns
            SecurityPattern(
                re.compile(r'/etc/passwd|/etc/shadow', re.IGNORECASE),
                PluginThreatType.FILE_SYSTEM_ATTACK, 9,
                "Access to system password files",
                "Restrict access to system files"
            ),
            SecurityPattern(
                re.compile(r'\.ssh/id_rsa|\.ssh/id_dsa', re.IGNORECASE),
                PluginThreatType.FILE_SYSTEM_ATTACK, 8,
                "Access to SSH private keys",
                "Protect SSH credentials"
            ),
            
            # Resource Abuse Patterns
            SecurityPattern(
                re.compile(r'while\s+true|for\s*\(\s*;\s*;\s*\)', re.IGNORECASE),
                PluginThreatType.RESOURCE_ABUSE, 6,
                "Infinite loop detected",
                "Implement execution timeouts"
            ),
            SecurityPattern(
                re.compile(r'fork\s*\(|spawn\s*\(', re.IGNORECASE),
                PluginThreatType.RESOURCE_ABUSE, 7,
                "Process spawning detected",
                "Limit process creation"
            )
        ]
    
    def validate_security(self, content: ScriptContent, script_type: PluginScriptType) -> PluginSecurityAnalysis:
        """Perform comprehensive security analysis."""
        violations = []
        warnings = []
        threats = set()
        required_permissions = set()
        
        # Pattern-based threat detection
        for pattern in self.threat_patterns:
            if pattern.pattern.search(content):
                violations.append(pattern.description)
                threats.add(pattern.threat_type)
                
                # Add required permissions based on threat type
                if pattern.threat_type == PluginThreatType.SYSTEM_COMPROMISE:
                    required_permissions.add("system_access")
                elif pattern.threat_type == PluginThreatType.NETWORK_ATTACK:
                    required_permissions.add("network_access")
                elif pattern.threat_type == PluginThreatType.FILE_SYSTEM_ATTACK:
                    required_permissions.add("file_system_access")
        
        # Script-type specific validation
        script_warnings = self._validate_script_type_specific(content, script_type)
        warnings.extend(script_warnings)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(content, script_type, len(violations))
        
        # Determine sandbox level
        sandbox_level = self._recommend_sandbox_level(risk_score, threats)
        
        # Determine if safe
        is_safe = len(violations) == 0 and risk_score < SECURITY_RISK_THRESHOLDS["MEDIUM"]
        
        return PluginSecurityAnalysis(
            is_safe=is_safe,
            risk_score=risk_score,
            threats_detected=list(threats),
            security_violations=violations,
            warnings=warnings,
            required_permissions=required_permissions,
            recommended_sandbox_level=sandbox_level
        )
    
    def _validate_script_type_specific(self, content: str, script_type: PluginScriptType) -> List[str]:
        """Validate script-type specific security concerns."""
        warnings = []
        
        if script_type == PluginScriptType.PYTHON:
            warnings.extend(self._validate_python_security(content))
        elif script_type == PluginScriptType.SHELL:
            warnings.extend(self._validate_shell_security(content))
        elif script_type == PluginScriptType.JAVASCRIPT:
            warnings.extend(self._validate_javascript_security(content))
        
        return warnings
    
    def _validate_python_security(self, content: str) -> List[str]:
        """Validate Python-specific security concerns."""
        warnings = []
        
        dangerous_imports = [
            'os', 'sys', 'subprocess', 'importlib', 'ctypes',
            'pickle', 'marshal', 'shelve', 'dill'
        ]
        
        for module in dangerous_imports:
            if re.search(rf'import\s+{module}|from\s+{module}', content):
                warnings.append(f"Potentially dangerous import: {module}")
        
        # Check for dynamic imports
        if re.search(r'__import__\s*\(|importlib\.import_module', content):
            warnings.append("Dynamic import detected")
        
        return warnings
    
    def _validate_shell_security(self, content: str) -> List[str]:
        """Validate shell script security concerns."""
        warnings = []
        
        dangerous_commands = [
            'dd', 'mkfs', 'fdisk', 'parted', 'chown', 'chmod 777',
            'iptables', 'netstat', 'ps aux', 'kill -9'
        ]
        
        for cmd in dangerous_commands:
            if cmd in content.lower():
                warnings.append(f"Potentially dangerous command: {cmd}")
        
        # Check for command substitution
        if re.search(r'\$\([^)]*\)|`[^`]*`', content):
            warnings.append("Command substitution detected")
        
        return warnings
    
    def _validate_javascript_security(self, content: str) -> List[str]:
        """Validate JavaScript security concerns."""
        warnings = []
        
        if 'require(' in content:
            warnings.append("Node.js require() detected")
        
        if re.search(r'document\.|window\.|global\.', content):
            warnings.append("DOM/Global object access detected")
        
        return warnings
    
    def _calculate_risk_score(self, content: str, script_type: PluginScriptType, violation_count: int) -> RiskScore:
        """Calculate comprehensive risk score."""
        try:
            return create_risk_score(script_type, PluginSecurityLevel.SANDBOXED, content)
        except Exception:
            # Fallback calculation
            base_score = violation_count * 20
            return RiskScore(min(100, base_score))
    
    def _recommend_sandbox_level(self, risk_score: RiskScore, threats: Set[PluginThreatType]) -> PluginSecurityLevel:
        """Recommend appropriate sandbox level based on analysis."""
        if risk_score >= SECURITY_RISK_THRESHOLDS["CRITICAL"]:
            return PluginSecurityLevel.DANGEROUS
        elif risk_score >= SECURITY_RISK_THRESHOLDS["HIGH"]:
            return PluginSecurityLevel.RESTRICTED
        elif risk_score >= SECURITY_RISK_THRESHOLDS["MEDIUM"]:
            return PluginSecurityLevel.SANDBOXED
        else:
            return PluginSecurityLevel.TRUSTED


class PluginInstallationBoundary:
    """Security boundary for plugin installation operations."""
    
    def __init__(self):
        self.allowed_extensions = {'.kmsync', '.plist', '.py', '.js', '.sh', '.scpt', '.php'}
        self.max_bundle_size = 10 * 1024 * 1024  # 10MB
        self.protected_paths = {
            '/System', '/usr', '/bin', '/sbin',
            '/Library/LaunchDaemons', '/Library/LaunchAgents'
        }
    
    def validate_installation_boundary(self, bundle_path: str, target_dir: str) -> SecurityBoundaryResult:
        """Validate plugin installation boundaries."""
        warnings = []
        violations = []
        
        # Validate bundle path
        try:
            bundle = Path(bundle_path)
            if not bundle.exists():
                violations.append("Bundle path does not exist")
            elif not bundle.is_dir():
                violations.append("Bundle path is not a directory")
            elif bundle.stat().st_size > self.max_bundle_size:
                violations.append(f"Bundle size exceeds limit ({self.max_bundle_size} bytes)")
        except Exception as e:
            violations.append(f"Bundle path validation failed: {e}")
        
        # Validate target directory
        target_path = Path(target_dir)
        if any(str(target_path).startswith(protected) for protected in self.protected_paths):
            violations.append(f"Installation to protected path denied: {target_dir}")
        
        # Validate file extensions
        if bundle_path:
            try:
                for file_path in Path(bundle_path).rglob('*'):
                    if file_path.is_file() and file_path.suffix not in self.allowed_extensions:
                        warnings.append(f"Unexpected file type: {file_path.suffix}")
            except Exception:
                warnings.append("Could not validate file extensions")
        
        return SecurityBoundaryResult(
            allowed=len(violations) == 0,
            required_permissions=set(),
            missing_permissions=set(),
            security_warnings=warnings,
            denial_reason="; ".join(violations) if violations else None
        )


class ComprehensivePluginBoundary:
    """Comprehensive plugin security boundary management."""
    
    def __init__(self):
        self.content_validator = ScriptContentSecurityValidator()
        self.installation_boundary = PluginInstallationBoundary()
        self.approval_cache = {}  # Cache for approved plugins
    
    def validate_plugin_creation(self, plugin_data: PluginCreationData) -> PluginValidationResult:
        """Comprehensive validation for plugin creation."""
        # Security analysis
        security_analysis = self.content_validator.validate_security(
            plugin_data.script_content, plugin_data.script_type
        )
        
        # Structure validation
        structure_issues = self._validate_plugin_structure(plugin_data)
        
        # Combine results
        all_violations = security_analysis.security_violations + structure_issues
        is_valid = len(all_violations) == 0 and security_analysis.is_safe
        
        return PluginValidationResult(
            is_valid=is_valid,
            security_issues=security_analysis.security_violations,
            warnings=security_analysis.warnings,
            required_permissions=list(security_analysis.required_permissions),
            estimated_risk_level=min(3, security_analysis.risk_score // 25),
            validation_errors=all_violations if not is_valid else None
        )
    
    def validate_plugin_installation(self, plugin_id: PluginID, bundle_path: str, target_dir: str) -> SecurityBoundaryResult:
        """Validate plugin installation security."""
        return self.installation_boundary.validate_installation_boundary(bundle_path, target_dir)
    
    def is_plugin_approved(self, plugin_id: PluginID, content_hash: SecurityHash) -> bool:
        """Check if plugin is pre-approved for installation."""
        cache_key = f"{plugin_id}:{content_hash}"
        return self.approval_cache.get(cache_key, False)
    
    def approve_plugin(self, plugin_id: PluginID, content_hash: SecurityHash) -> None:
        """Mark plugin as approved for installation."""
        cache_key = f"{plugin_id}:{content_hash}"
        self.approval_cache[cache_key] = True
    
    def _validate_plugin_structure(self, plugin_data: PluginCreationData) -> List[str]:
        """Validate plugin data structure."""
        issues = []
        
        # Validate action name
        if not plugin_data.action_name or len(plugin_data.action_name.strip()) == 0:
            issues.append("Action name cannot be empty")
        elif len(plugin_data.action_name) > 100:
            issues.append("Action name exceeds maximum length")
        
        # Validate script content
        if not plugin_data.script_content or len(plugin_data.script_content.strip()) == 0:
            issues.append("Script content cannot be empty")
        elif len(plugin_data.script_content) > 1_000_000:
            issues.append("Script content exceeds maximum size")
        
        # Validate parameters
        if plugin_data.parameters:
            param_names = [p.name for p in plugin_data.parameters]
            if len(param_names) != len(set(param_names)):
                issues.append("Parameter names must be unique")
            
            for param in plugin_data.parameters:
                if not param.name.startswith("KMPARAM_"):
                    issues.append(f"Invalid parameter name format: {param.name}")
        
        return issues


# Default plugin boundary instance
DEFAULT_PLUGIN_BOUNDARY = ComprehensivePluginBoundary()


def validate_plugin_security(plugin_data: PluginCreationData) -> PluginValidationResult:
    """Convenience function for plugin security validation."""
    return DEFAULT_PLUGIN_BOUNDARY.validate_plugin_creation(plugin_data)


def validate_plugin_installation_security(plugin_id: PluginID, bundle_path: str, target_dir: str) -> SecurityBoundaryResult:
    """Convenience function for installation security validation."""
    return DEFAULT_PLUGIN_BOUNDARY.validate_plugin_installation(plugin_id, bundle_path, target_dir)
