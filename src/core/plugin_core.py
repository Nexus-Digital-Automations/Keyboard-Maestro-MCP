# src/core/plugin_core.py
"""
Plugin Core Logic - Immutable Functions + Defensive Programming Implementation.

This module implements pure functional plugin operations with immutable data
structures, comprehensive error handling, and defensive programming patterns.
All plugin operations are side-effect-free in the functional core with clear
separation between pure logic and I/O operations.

Target: Quality-first design with complete technique integration
"""

from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import xml.etree.ElementTree as ET
import json
import tempfile
import shutil
import os
from functools import reduce
from collections.abc import Mapping

from ..types.plugin_types import (
    PluginID, PluginName, PluginPath, BundlePath, ScriptContent, InfoPlistContent,
    PluginSecurityContext, PluginResourceLimits, SecurityHash,
    create_plugin_id, create_plugin_name, create_plugin_path, create_security_hash,
    create_memory_limit, create_timeout_seconds, create_risk_score,
    plugin_id_to_bundle_id, plugin_name_to_filename
)
from ..types.domain_types import PluginCreationData, PluginMetadata, PluginValidationResult
from ..types.enumerations import PluginScriptType, PluginLifecycleState, PluginSecurityLevel
from ..types.results import Result, OperationError, ErrorType
from ..boundaries.plugin_boundaries import validate_plugin_security
from ..contracts.plugin_contracts import plugin_creation_contract, plugin_validation_contract


# Core Immutable Data Structures

@dataclass(frozen=True)
class PluginBundle:
    """Immutable plugin bundle representation."""
    plugin_id: PluginID
    name: PluginName
    bundle_path: BundlePath
    info_plist: InfoPlistContent
    script_files: Tuple[Tuple[str, bytes], ...]  # (filename, content) pairs
    metadata: PluginMetadata
    security_context: PluginSecurityContext
    
    def get_script_file(self, filename: str) -> Optional[bytes]:
        """Get script file content by name."""
        for file_name, content in self.script_files:
            if file_name == filename:
                return content
        return None
    
    def with_metadata(self, new_metadata: PluginMetadata) -> 'PluginBundle':
        """Create new bundle with updated metadata."""
        return dataclass_replace(self, metadata=new_metadata)
    
    def get_file_count(self) -> int:
        """Get total file count in bundle."""
        return len(self.script_files) + 1  # +1 for Info.plist


@dataclass(frozen=True)
class PluginInstallationPlan:
    """Immutable installation plan with rollback information."""
    plugin_bundle: PluginBundle
    target_directory: str
    installation_steps: Tuple[str, ...]
    rollback_plan: Tuple[str, ...]
    required_permissions: Tuple[str, ...]
    estimated_disk_usage: int
    
    def can_proceed(self) -> bool:
        """Check if installation can proceed."""
        return len(self.installation_steps) > 0 and len(self.required_permissions) == 0


@dataclass(frozen=True)
class PluginOperationResult:
    """Immutable result of plugin operations."""
    success: bool
    plugin_id: Optional[PluginID]
    operation_type: str
    timestamp: datetime
    details: Dict[str, Any]
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...]
    
    def with_error(self, error: str) -> 'PluginOperationResult':
        """Add error to result."""
        return dataclass_replace(
            self,
            success=False,
            errors=self.errors + (error,)
        )
    
    def with_warning(self, warning: str) -> 'PluginOperationResult':
        """Add warning to result."""
        return dataclass_replace(self, warnings=self.warnings + (warning,))


# Pure Functional Plugin Operations

def create_plugin_metadata(creation_data: PluginCreationData) -> Result[PluginMetadata, OperationError]:
    """Pure function to create plugin metadata from creation data.
    
    Args:
        creation_data: Plugin creation parameters
        
    Returns:
        Result containing PluginMetadata or OperationError
    """
    try:
        # Generate unique plugin ID
        plugin_id = create_plugin_id(creation_data.action_name)
        
        # Create validated plugin name
        plugin_name = create_plugin_name(creation_data.action_name)
        
        # Generate security hash
        content_hash = create_security_hash(creation_data.script_content)
        
        # Calculate risk score
        risk_score = create_risk_score(
            creation_data.script_type,
            creation_data.security_level or PluginSecurityLevel.SANDBOXED,
            creation_data.script_content
        )
        
        # Create metadata
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            name=plugin_name,
            action_name=creation_data.action_name,
            script_type=creation_data.script_type,
            content_hash=content_hash,
            risk_score=risk_score,
            created_at=datetime.now(),
            state=PluginLifecycleState.CREATED,
            description=creation_data.description,
            parameters=creation_data.parameters or [],
            security_level=creation_data.security_level or PluginSecurityLevel.SANDBOXED
        )
        
        return Result.success(metadata)
        
    except ValueError as e:
        return Result.failure(OperationError(
            error_type=ErrorType.VALIDATION_ERROR,
            message=f"Plugin metadata creation failed: {e}",
            details=str(e),
            recovery_suggestion="Verify plugin creation data is valid"
        ))
    except Exception as e:
        return Result.failure(OperationError(
            error_type=ErrorType.SYSTEM_ERROR,
            message=f"Unexpected error creating plugin metadata: {e}",
            details=str(e),
            recovery_suggestion="Check system resources and try again"
        ))


def generate_info_plist_content(metadata: PluginMetadata, 
                               creation_data: PluginCreationData) -> Result[InfoPlistContent, OperationError]:
    """Pure function to generate Info.plist content for plugin.
    
    Args:
        metadata: Plugin metadata
        creation_data: Original creation data
        
    Returns:
        Result containing Info.plist bytes or OperationError
    """
    try:
        # Create root plist element
        root = ET.Element("plist", version="1.0")
        dict_elem = ET.SubElement(root, "dict")
        
        # Add bundle identifier
        bundle_id = plugin_id_to_bundle_id(metadata.plugin_id)
        _add_plist_key_value(dict_elem, "CFBundleIdentifier", bundle_id)
        
        # Add display name
        _add_plist_key_value(dict_elem, "CFBundleDisplayName", metadata.action_name)
        
        # Add version information
        _add_plist_key_value(dict_elem, "CFBundleVersion", "1.0")
        _add_plist_key_value(dict_elem, "CFBundleShortVersionString", "1.0")
        
        # Add script information
        _add_plist_key_value(dict_elem, "KMScriptType", metadata.script_type.value)
        
        # Add parameters if any
        if creation_data.parameters:
            _add_plist_parameters(dict_elem, creation_data.parameters)
        
        # Add output handling
        if creation_data.output_handling:
            _add_plist_key_value(dict_elem, "KMOutputHandling", creation_data.output_handling.value)
        
        # Add creation timestamp
        _add_plist_key_value(dict_elem, "KMCreationDate", metadata.created_at.isoformat())
        
        # Add description if present
        if metadata.description:
            _add_plist_key_value(dict_elem, "CFBundleDescription", metadata.description)
        
        # Convert to XML bytes
        ET.indent(root, space="  ")
        xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        
        return Result.success(InfoPlistContent(xml_str))
        
    except Exception as e:
        return Result.failure(OperationError(
            error_type=ErrorType.SYSTEM_ERROR,
            message=f"Info.plist generation failed: {e}",
            details=str(e),
            recovery_suggestion="Check plugin metadata is valid"
        ))


def create_plugin_bundle(metadata: PluginMetadata,
                        creation_data: PluginCreationData,
                        bundle_directory: str) -> Result[PluginBundle, OperationError]:
    """Pure function to create plugin bundle structure.
    
    Args:
        metadata: Plugin metadata
        creation_data: Creation parameters
        bundle_directory: Target bundle directory
        
    Returns:
        Result containing PluginBundle or OperationError
    """
    try:
        # Generate Info.plist content
        plist_result = generate_info_plist_content(metadata, creation_data)
        if plist_result.is_failure:
            return Result.failure(plist_result._error)
        
        info_plist = plist_result.unwrap()
        
        # Create script files
        script_filename = _get_script_filename(metadata.script_type)
        script_files = ((script_filename, creation_data.script_content.encode('utf-8')),)
        
        # Create bundle path
        bundle_filename = plugin_name_to_filename(metadata.name)
        bundle_path = BundlePath(os.path.join(bundle_directory, bundle_filename))
        
        # Create security context
        security_context = _create_security_context(metadata, creation_data)
        
        # Create bundle
        plugin_bundle = PluginBundle(
            plugin_id=metadata.plugin_id,
            name=metadata.name,
            bundle_path=bundle_path,
            info_plist=info_plist,
            script_files=script_files,
            metadata=metadata,
            security_context=security_context
        )
        
        return Result.success(plugin_bundle)
        
    except Exception as e:
        return Result.failure(OperationError(
            error_type=ErrorType.SYSTEM_ERROR,
            message=f"Plugin bundle creation failed: {e}",
            details=str(e),
            recovery_suggestion="Check bundle directory permissions and available space"
        ))


def create_installation_plan(plugin_bundle: PluginBundle,
                           target_directory: str) -> Result[PluginInstallationPlan, OperationError]:
    """Pure function to create installation plan with rollback strategy.
    
    Args:
        plugin_bundle: Bundle to install
        target_directory: Installation target
        
    Returns:
        Result containing PluginInstallationPlan or OperationError
    """
    try:
        # Validate target directory
        target_path = Path(target_directory)
        if not target_path.exists():
            return Result.failure(OperationError(
                error_type=ErrorType.NOT_FOUND_ERROR,
                message=f"Target directory does not exist: {target_directory}",
                recovery_suggestion="Create target directory or use existing path"
            ))
        
        # Calculate installation steps
        installation_steps = (
            f"Create bundle directory: {plugin_bundle.bundle_path}",
            f"Write Info.plist: {len(plugin_bundle.info_plist)} bytes",
            f"Write script files: {len(plugin_bundle.script_files)} files",
            "Set bundle permissions",
            "Verify installation integrity"
        )
        
        # Create rollback plan
        rollback_steps = (
            f"Remove bundle directory: {plugin_bundle.bundle_path}",
            "Restore previous state",
            "Verify rollback completion"
        )
        
        # Determine required permissions
        required_permissions = _analyze_required_permissions(plugin_bundle)
        
        # Calculate disk usage
        disk_usage = _calculate_bundle_size(plugin_bundle)
        
        installation_plan = PluginInstallationPlan(
            plugin_bundle=plugin_bundle,
            target_directory=target_directory,
            installation_steps=installation_steps,
            rollback_plan=rollback_steps,
            required_permissions=required_permissions,
            estimated_disk_usage=disk_usage
        )
        
        return Result.success(installation_plan)
        
    except Exception as e:
        return Result.failure(OperationError(
            error_type=ErrorType.SYSTEM_ERROR,
            message=f"Installation plan creation failed: {e}",
            details=str(e),
            recovery_suggestion="Check target directory permissions"
        ))


def validate_plugin_bundle(plugin_bundle: PluginBundle) -> Result[PluginValidationResult, OperationError]:
    """Pure function to validate plugin bundle integrity.
    
    Args:
        plugin_bundle: Bundle to validate
        
    Returns:
        Result containing PluginValidationResult or OperationError
    """
    try:
        validation_errors = []
        warnings = []
        
        # Validate Info.plist content
        plist_errors = _validate_plist_content(plugin_bundle.info_plist)
        validation_errors.extend(plist_errors)
        
        # Validate script files
        script_errors = _validate_script_files(plugin_bundle.script_files, plugin_bundle.metadata.script_type)
        validation_errors.extend(script_errors)
        
        # Validate bundle structure
        structure_errors = _validate_bundle_structure(plugin_bundle)
        validation_errors.extend(structure_errors)
        
        # Security validation
        security_result = validate_plugin_security(PluginCreationData(
            action_name=plugin_bundle.metadata.action_name,
            script_type=plugin_bundle.metadata.script_type,
            script_content=plugin_bundle.get_script_file(_get_script_filename(plugin_bundle.metadata.script_type)).decode('utf-8'),
            description=plugin_bundle.metadata.description
        ))
        
        if security_result.security_issues:
            validation_errors.extend(security_result.security_issues)
        if security_result.warnings:
            warnings.extend(security_result.warnings)
        
        # Calculate risk level
        risk_level = min(3, plugin_bundle.metadata.risk_score // 25)
        
        validation_result = PluginValidationResult(
            is_valid=len(validation_errors) == 0,
            security_issues=security_result.security_issues or [],
            warnings=warnings,
            required_permissions=security_result.required_permissions or [],
            estimated_risk_level=risk_level,
            validation_errors=validation_errors if validation_errors else None
        )
        
        return Result.success(validation_result)
        
    except Exception as e:
        return Result.failure(OperationError(
            error_type=ErrorType.SYSTEM_ERROR,
            message=f"Plugin validation failed: {e}",
            details=str(e),
            recovery_suggestion="Check plugin bundle integrity"
        ))


def transform_plugin_bundle(plugin_bundle: PluginBundle,
                          transformation: Callable[[PluginBundle], PluginBundle]) -> Result[PluginBundle, OperationError]:
    """Pure function to transform plugin bundle with error handling.
    
    Args:
        plugin_bundle: Original bundle
        transformation: Pure transformation function
        
    Returns:
        Result containing transformed PluginBundle or OperationError
    """
    try:
        transformed_bundle = transformation(plugin_bundle)
        
        # Validate transformation preserved bundle integrity
        if (transformed_bundle.plugin_id != plugin_bundle.plugin_id or
            transformed_bundle.name != plugin_bundle.name):
            return Result.failure(OperationError(
                error_type=ErrorType.VALIDATION_ERROR,
                message="Transformation violated bundle identity invariants",
                recovery_suggestion="Ensure transformation preserves plugin ID and name"
            ))
        
        return Result.success(transformed_bundle)
        
    except Exception as e:
        return Result.failure(OperationError(
            error_type=ErrorType.SYSTEM_ERROR,
            message=f"Bundle transformation failed: {e}",
            details=str(e),
            recovery_suggestion="Check transformation function is valid"
        ))


def compose_plugin_transformations(*transformations: Callable[[PluginBundle], PluginBundle]) -> Callable[[PluginBundle], PluginBundle]:
    """Compose multiple bundle transformations into single function.
    
    Args:
        *transformations: Series of transformation functions
        
    Returns:
        Composed transformation function
    """
    def composed_transformation(bundle: PluginBundle) -> PluginBundle:
        return reduce(lambda b, transform: transform(b), transformations, bundle)
    
    return composed_transformation


def get_plugin_dependencies(plugin_bundle: PluginBundle) -> Tuple[str, ...]:
    """Pure function to extract plugin dependencies.
    
    Args:
        plugin_bundle: Bundle to analyze
        
    Returns:
        Tuple of dependency identifiers
    """
    dependencies = []
    
    # Analyze script content for dependencies
    for filename, content in plugin_bundle.script_files:
        script_content = content.decode('utf-8')
        deps = _extract_script_dependencies(script_content, plugin_bundle.metadata.script_type)
        dependencies.extend(deps)
    
    return tuple(set(dependencies))  # Remove duplicates


def calculate_plugin_metrics(plugin_bundle: PluginBundle) -> Dict[str, Any]:
    """Pure function to calculate plugin metrics.
    
    Args:
        plugin_bundle: Bundle to analyze
        
    Returns:
        Dictionary of plugin metrics
    """
    total_size = len(plugin_bundle.info_plist)
    for _, content in plugin_bundle.script_files:
        total_size += len(content)
    
    script_lines = 0
    for _, content in plugin_bundle.script_files:
        script_lines += len(content.decode('utf-8').splitlines())
    
    return {
        'total_size_bytes': total_size,
        'script_file_count': len(plugin_bundle.script_files),
        'script_lines': script_lines,
        'risk_score': plugin_bundle.metadata.risk_score,
        'security_level': plugin_bundle.security_context.security_level.value,
        'parameter_count': len(plugin_bundle.metadata.parameters),
        'bundle_file_count': plugin_bundle.get_file_count(),
        'creation_date': plugin_bundle.metadata.created_at.isoformat(),
        'has_description': bool(plugin_bundle.metadata.description)
    }


# Helper Functions for Pure Functional Operations

def _add_plist_key_value(dict_elem: ET.Element, key: str, value: str) -> None:
    """Add key-value pair to plist dictionary element."""
    key_elem = ET.SubElement(dict_elem, "key")
    key_elem.text = key
    
    string_elem = ET.SubElement(dict_elem, "string")
    string_elem.text = value


def _add_plist_parameters(dict_elem: ET.Element, parameters: List[Any]) -> None:
    """Add parameters array to plist dictionary."""
    key_elem = ET.SubElement(dict_elem, "key")
    key_elem.text = "KMParameters"
    
    array_elem = ET.SubElement(dict_elem, "array")
    
    for param in parameters:
        param_dict = ET.SubElement(array_elem, "dict")
        _add_plist_key_value(param_dict, "KMParameterName", param.name)
        _add_plist_key_value(param_dict, "KMParameterLabel", param.label)
        _add_plist_key_value(param_dict, "KMParameterType", param.parameter_type)
        if param.default_value:
            _add_plist_key_value(param_dict, "KMParameterDefault", param.default_value)


def _get_script_filename(script_type: PluginScriptType) -> str:
    """Get appropriate script filename for script type."""
    extensions = {
        PluginScriptType.APPLESCRIPT: "script.scpt",
        PluginScriptType.SHELL: "script.sh",
        PluginScriptType.PYTHON: "script.py",
        PluginScriptType.JAVASCRIPT: "script.js",
        PluginScriptType.PHP: "script.php"
    }
    return extensions.get(script_type, "script.txt")


def _create_security_context(metadata: PluginMetadata, creation_data: PluginCreationData) -> PluginSecurityContext:
    """Create security context for plugin."""
    return PluginSecurityContext(
        plugin_id=metadata.plugin_id,
        security_level=metadata.security_level,
        risk_score=metadata.risk_score,
        content_hash=metadata.content_hash,
        allowed_operations=["execute", "read", "write_output"],
        resource_limits={
            'memory_mb': 100,
            'timeout_seconds': 30,
            'max_file_size': 1024 * 1024  # 1MB
        }
    )


def _analyze_required_permissions(plugin_bundle: PluginBundle) -> Tuple[str, ...]:
    """Analyze plugin bundle for required permissions."""
    permissions = []
    
    # Check script content for permission requirements
    for _, content in plugin_bundle.script_files:
        script_content = content.decode('utf-8')
        if 'file://' in script_content or 'open(' in script_content:
            permissions.append('file_access')
        if 'http://' in script_content or 'https://' in script_content:
            permissions.append('network_access')
        if 'sudo' in script_content or 'admin' in script_content:
            permissions.append('admin_access')
    
    return tuple(set(permissions))


def _calculate_bundle_size(plugin_bundle: PluginBundle) -> int:
    """Calculate total bundle size in bytes."""
    total_size = len(plugin_bundle.info_plist)
    for _, content in plugin_bundle.script_files:
        total_size += len(content)
    return total_size


def _validate_plist_content(plist_content: InfoPlistContent) -> List[str]:
    """Validate Info.plist content structure."""
    errors = []
    
    try:
        root = ET.fromstring(plist_content)
        if root.tag != "plist":
            errors.append("Invalid plist root element")
        
        dict_elem = root.find("dict")
        if dict_elem is None:
            errors.append("Missing plist dictionary")
        
        # Check for required keys
        required_keys = ["CFBundleIdentifier", "CFBundleDisplayName", "KMScriptType"]
        if dict_elem is not None:
            keys = [key.text for key in dict_elem.findall("key")]
            for required_key in required_keys:
                if required_key not in keys:
                    errors.append(f"Missing required plist key: {required_key}")
    
    except ET.ParseError as e:
        errors.append(f"Invalid XML in plist: {e}")
    
    return errors


def _validate_script_files(script_files: Tuple[Tuple[str, bytes], ...], script_type: PluginScriptType) -> List[str]:
    """Validate script files content and structure."""
    errors = []
    
    if not script_files:
        errors.append("No script files found in bundle")
        return errors
    
    for filename, content in script_files:
        try:
            script_content = content.decode('utf-8')
            if not script_content.strip():
                errors.append(f"Empty script file: {filename}")
        except UnicodeDecodeError:
            errors.append(f"Invalid UTF-8 encoding in script file: {filename}")
    
    return errors


def _validate_bundle_structure(plugin_bundle: PluginBundle) -> List[str]:
    """Validate overall bundle structure."""
    errors = []
    
    # Check plugin ID format
    if not plugin_bundle.plugin_id.startswith("mcp_plugin_"):
        errors.append("Invalid plugin ID format")
    
    # Check bundle path format
    if not str(plugin_bundle.bundle_path).endswith(".kmsync"):
        errors.append("Bundle path must end with .kmsync")
    
    # Check metadata consistency
    if not plugin_bundle.metadata.action_name:
        errors.append("Missing action name in metadata")
    
    return errors


def _extract_script_dependencies(script_content: str, script_type: PluginScriptType) -> List[str]:
    """Extract dependencies from script content."""
    dependencies = []
    
    if script_type == PluginScriptType.PYTHON:
        import_lines = [line.strip() for line in script_content.splitlines() if line.strip().startswith('import ')]
        for line in import_lines:
            if ' ' in line:
                module = line.split()[1].split('.')[0]
                dependencies.append(f"python:{module}")
    
    elif script_type == PluginScriptType.JAVASCRIPT:
        require_lines = [line for line in script_content.splitlines() if 'require(' in line]
        for line in require_lines:
            # Simple extraction - could be more sophisticated
            if "'" in line:
                module = line.split("'")[1]
                dependencies.append(f"javascript:{module}")
    
    return dependencies


# Functional Core Composition Functions

def create_plugin_pipeline(creation_data: PluginCreationData,
                          bundle_directory: str) -> Result[PluginBundle, OperationError]:
    """Compose complete plugin creation pipeline.
    
    Args:
        creation_data: Plugin creation parameters
        bundle_directory: Target bundle directory
        
    Returns:
        Result containing PluginBundle or OperationError
    """
    # Create metadata
    metadata_result = create_plugin_metadata(creation_data)
    if metadata_result.is_failure:
        return Result.failure(metadata_result._error)
    
    metadata = metadata_result.unwrap()
    
    # Create bundle
    bundle_result = create_plugin_bundle(metadata, creation_data, bundle_directory)
    if bundle_result.is_failure:
        return Result.failure(bundle_result._error)
    
    bundle = bundle_result.unwrap()
    
    # Validate bundle
    validation_result = validate_plugin_bundle(bundle)
    if validation_result.is_failure:
        return Result.failure(validation_result._error)
    
    validation = validation_result.unwrap()
    if not validation.is_valid:
        return Result.failure(OperationError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Plugin bundle validation failed",
            details="; ".join(validation.validation_errors or []),
            recovery_suggestion="Fix validation errors and retry"
        ))
    
    return Result.success(bundle)


def plugin_operation_chain(*operations: Callable[[PluginBundle], Result[PluginBundle, OperationError]]) -> Callable[[PluginBundle], Result[PluginBundle, OperationError]]:
    """Chain multiple plugin operations with error propagation.
    
    Args:
        *operations: Series of plugin operations
        
    Returns:
        Chained operation function
    """
    def chained_operation(bundle: PluginBundle) -> Result[PluginBundle, OperationError]:
        current_bundle = bundle
        for operation in operations:
            result = operation(current_bundle)
            if result.is_failure:
                return result
            current_bundle = result.unwrap()
        return Result.success(current_bundle)
    
    return chained_operation


# Default plugin core operations instance
@dataclass(frozen=True)
class PluginCoreOperations:
    """Immutable plugin core operations with all pure functions."""
    
    def create_metadata(self, creation_data: PluginCreationData) -> Result[PluginMetadata, OperationError]:
        return create_plugin_metadata(creation_data)
    
    def generate_plist(self, metadata: PluginMetadata, creation_data: PluginCreationData) -> Result[InfoPlistContent, OperationError]:
        return generate_info_plist_content(metadata, creation_data)
    
    def create_bundle(self, metadata: PluginMetadata, creation_data: PluginCreationData, bundle_dir: str) -> Result[PluginBundle, OperationError]:
        return create_plugin_bundle(metadata, creation_data, bundle_dir)
    
    def validate_bundle(self, bundle: PluginBundle) -> Result[PluginValidationResult, OperationError]:
        return validate_plugin_bundle(bundle)
    
    def create_installation_plan(self, bundle: PluginBundle, target_dir: str) -> Result[PluginInstallationPlan, OperationError]:
        return create_installation_plan(bundle, target_dir)
    
    def get_metrics(self, bundle: PluginBundle) -> Dict[str, Any]:
        return calculate_plugin_metrics(bundle)
    
    def get_dependencies(self, bundle: PluginBundle) -> Tuple[str, ...]:
        return get_plugin_dependencies(bundle)


# Default instance for use across the system
DEFAULT_PLUGIN_CORE = PluginCoreOperations()
