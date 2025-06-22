"""
Macro import/export utilities with format support.

This module handles serialization and deserialization of macros
in various formats supported by Keyboard Maestro.
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import zipfile
import tempfile
import logging
from dataclasses import asdict

from src.types.domain_types import MacroIdentifier, MacroUUID, SerializationFormat
from src.pure.macro_transformations import (
    MacroMetadata, TriggerConfig, ActionConfig,
    convert_to_km_xml, parse_km_xml
)
from src.contracts.decorators import requires, ensures

logger = logging.getLogger(__name__)


class MacroSerializer:
    """Handles macro serialization in various formats."""
    
    SUPPORTED_FORMATS = {
        SerializationFormat.KMMACROS,
        SerializationFormat.KMLIBRARY,
        SerializationFormat.XML,
        SerializationFormat.JSON
    }
    
    @requires(lambda self, macro_data: macro_data is not None)
    @requires(lambda self, macro_data, format_type: format_type in self.SUPPORTED_FORMATS)
    def serialize_macro(
        self,
        macro_data: Dict[str, Any],
        format_type: SerializationFormat
    ) -> bytes:
        """
        Serialize macro data to specified format.
        
        Supports .kmmacros, .kmlibrary, XML, and JSON formats.
        """
        try:
            if format_type == SerializationFormat.JSON:
                return self._serialize_to_json(macro_data)
            elif format_type == SerializationFormat.XML:
                return self._serialize_to_xml(macro_data)
            elif format_type == SerializationFormat.KMMACROS:
                return self._serialize_to_kmmacros(macro_data)
            elif format_type == SerializationFormat.KMLIBRARY:
                return self._serialize_to_kmlibrary([macro_data])
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise
    
    @requires(lambda self, macros_data: isinstance(macros_data, list))
    def serialize_macro_collection(
        self,
        macros_data: List[Dict[str, Any]],
        format_type: SerializationFormat
    ) -> bytes:
        """Serialize multiple macros to library format."""
        try:
            if format_type == SerializationFormat.KMLIBRARY:
                return self._serialize_to_kmlibrary(macros_data)
            elif format_type == SerializationFormat.JSON:
                return json.dumps(macros_data, indent=2).encode('utf-8')
            else:
                raise ValueError(f"Format {format_type} does not support collections")
                
        except Exception as e:
            logger.error(f"Collection serialization failed: {e}")
            raise
    
    @requires(lambda self, data: isinstance(data, (bytes, str)))
    @ensures(lambda result: isinstance(result, dict))
    def deserialize_macro(
        self,
        data: Union[bytes, str],
        format_type: SerializationFormat
    ) -> Dict[str, Any]:
        """
        Deserialize macro data from specified format.
        
        Returns structured macro data dictionary.
        """
        try:
            if format_type == SerializationFormat.JSON:
                return self._deserialize_from_json(data)
            elif format_type == SerializationFormat.XML:
                return self._deserialize_from_xml(data)
            elif format_type == SerializationFormat.KMMACROS:
                return self._deserialize_from_kmmacros(data)
            elif format_type == SerializationFormat.KMLIBRARY:
                # Return first macro from library
                macros = self._deserialize_from_kmlibrary(data)
                return macros[0] if macros else {}
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise
    
    def deserialize_macro_collection(
        self,
        data: Union[bytes, str],
        format_type: SerializationFormat
    ) -> List[Dict[str, Any]]:
        """Deserialize multiple macros from library format."""
        try:
            if format_type == SerializationFormat.KMLIBRARY:
                return self._deserialize_from_kmlibrary(data)
            elif format_type == SerializationFormat.JSON:
                json_data = json.loads(data.decode('utf-8') if isinstance(data, bytes) else data)
                return json_data if isinstance(json_data, list) else [json_data]
            else:
                raise ValueError(f"Format {format_type} does not support collections")
                
        except Exception as e:
            logger.error(f"Collection deserialization failed: {e}")
            raise
    
    def _serialize_to_json(self, macro_data: Dict[str, Any]) -> bytes:
        """Serialize macro to JSON format."""
        return json.dumps(macro_data, indent=2).encode('utf-8')
    
    def _serialize_to_xml(self, macro_data: Dict[str, Any]) -> bytes:
        """Serialize macro to XML format."""
        metadata = MacroMetadata(**macro_data['metadata'])
        triggers = [TriggerConfig(**t) for t in macro_data.get('triggers', [])]
        actions = [ActionConfig(**a) for a in macro_data.get('actions', [])]
        
        xml_string = convert_to_km_xml(metadata, triggers, actions)
        return xml_string.encode('utf-8')
    
    def _serialize_to_kmmacros(self, macro_data: Dict[str, Any]) -> bytes:
        """Serialize macro to .kmmacros format (compressed XML)."""
        xml_data = self._serialize_to_xml(macro_data)
        
        # Create a zip file with the macro XML
        with tempfile.NamedTemporaryFile() as temp_file:
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                macro_name = macro_data['metadata']['name']
                zf.writestr(f"{macro_name}.xml", xml_data)
            
            temp_file.seek(0)
            return temp_file.read()
    
    def _serialize_to_kmlibrary(self, macros_data: List[Dict[str, Any]]) -> bytes:
        """Serialize macros to .kmlibrary format."""
        # Create library structure
        library = {
            'version': '1.0',
            'macros': macros_data,
            'groups': self._extract_groups_from_macros(macros_data)
        }
        
        library_json = json.dumps(library, indent=2)
        
        # Create zip file with library structure
        with tempfile.NamedTemporaryFile() as temp_file:
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('library.json', library_json)
                
                # Add individual macro files
                for macro_data in macros_data:
                    macro_xml = self._serialize_to_xml(macro_data)
                    macro_name = macro_data['metadata']['name']
                    zf.writestr(f"macros/{macro_name}.xml", macro_xml)
            
            temp_file.seek(0)
            return temp_file.read()
    
    def _deserialize_from_json(self, data: Union[bytes, str]) -> Dict[str, Any]:
        """Deserialize macro from JSON format."""
        json_str = data.decode('utf-8') if isinstance(data, bytes) else data
        return json.loads(json_str)
    
    def _deserialize_from_xml(self, data: Union[bytes, str]) -> Dict[str, Any]:
        """Deserialize macro from XML format."""
        xml_str = data.decode('utf-8') if isinstance(data, bytes) else data
        return parse_km_xml(xml_str)
    
    def _deserialize_from_kmmacros(self, data: bytes) -> Dict[str, Any]:
        """Deserialize macro from .kmmacros format."""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            
            with zipfile.ZipFile(temp_file, 'r') as zf:
                # Find the first XML file
                xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
                if not xml_files:
                    raise ValueError("No XML files found in .kmmacros archive")
                
                xml_content = zf.read(xml_files[0])
                return self._deserialize_from_xml(xml_content)
    
    def _deserialize_from_kmlibrary(self, data: bytes) -> List[Dict[str, Any]]:
        """Deserialize macros from .kmlibrary format."""
        macros = []
        
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            
            with zipfile.ZipFile(temp_file, 'r') as zf:
                # Try to read library.json first
                if 'library.json' in zf.namelist():
                    library_data = json.loads(zf.read('library.json').decode('utf-8'))
                    return library_data.get('macros', [])
                
                # Otherwise, read individual macro files
                xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
                for xml_file in xml_files:
                    xml_content = zf.read(xml_file)
                    macro_data = self._deserialize_from_xml(xml_content)
                    macros.append(macro_data)
        
        return macros
    
    def _extract_groups_from_macros(self, macros_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract unique groups from macro collection."""
        groups = {}
        
        for macro_data in macros_data:
            group_uuid = macro_data['metadata'].get('group_uuid')
            if group_uuid and group_uuid not in groups:
                groups[group_uuid] = {
                    'uuid': group_uuid,
                    'name': f"Group {group_uuid[:8]}",  # Default name
                    'enabled': True
                }
        
        return list(groups.values())


class MacroFileManager:
    """Manages macro file operations with path validation."""
    
    @requires(lambda self, file_path: file_path is not None)
    def save_macro_to_file(
        self,
        macro_data: Dict[str, Any],
        file_path: str,
        format_type: Optional[SerializationFormat] = None
    ) -> bool:
        """Save macro to file with format auto-detection."""
        try:
            path = Path(file_path)
            
            # Auto-detect format if not specified
            if format_type is None:
                format_type = self._detect_format_from_extension(path.suffix)
            
            # Serialize macro
            serializer = MacroSerializer()
            serialized_data = serializer.serialize_macro(macro_data, format_type)
            
            # Write to file
            with open(path, 'wb') as f:
                f.write(serialized_data)
            
            logger.info(f"Macro saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save macro to {file_path}: {e}")
            return False
    
    @requires(lambda self, file_path: file_path is not None)
    @ensures(lambda result: isinstance(result, (dict, type(None))))
    def load_macro_from_file(
        self,
        file_path: str,
        format_type: Optional[SerializationFormat] = None
    ) -> Optional[Dict[str, Any]]:
        """Load macro from file with format auto-detection."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            # Auto-detect format if not specified
            if format_type is None:
                format_type = self._detect_format_from_extension(path.suffix)
            
            # Read file
            with open(path, 'rb') as f:
                data = f.read()
            
            # Deserialize macro
            serializer = MacroSerializer()
            macro_data = serializer.deserialize_macro(data, format_type)
            
            logger.info(f"Macro loaded from {file_path}")
            return macro_data
            
        except Exception as e:
            logger.error(f"Failed to load macro from {file_path}: {e}")
            return None
    
    def save_macro_collection(
        self,
        macros_data: List[Dict[str, Any]],
        file_path: str,
        format_type: Optional[SerializationFormat] = None
    ) -> bool:
        """Save multiple macros to library file."""
        try:
            path = Path(file_path)
            
            if format_type is None:
                format_type = self._detect_format_from_extension(path.suffix)
            
            serializer = MacroSerializer()
            serialized_data = serializer.serialize_macro_collection(macros_data, format_type)
            
            with open(path, 'wb') as f:
                f.write(serialized_data)
            
            logger.info(f"Macro collection saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save macro collection to {file_path}: {e}")
            return False
    
    def load_macro_collection(
        self,
        file_path: str,
        format_type: Optional[SerializationFormat] = None
    ) -> List[Dict[str, Any]]:
        """Load multiple macros from library file."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return []
            
            if format_type is None:
                format_type = self._detect_format_from_extension(path.suffix)
            
            with open(path, 'rb') as f:
                data = f.read()
            
            serializer = MacroSerializer()
            macros_data = serializer.deserialize_macro_collection(data, format_type)
            
            logger.info(f"Macro collection loaded from {file_path}")
            return macros_data
            
        except Exception as e:
            logger.error(f"Failed to load macro collection from {file_path}: {e}")
            return []
    
    def _detect_format_from_extension(self, extension: str) -> SerializationFormat:
        """Detect serialization format from file extension."""
        extension_map = {
            '.kmmacros': SerializationFormat.KMMACROS,
            '.kmlibrary': SerializationFormat.KMLIBRARY,
            '.xml': SerializationFormat.XML,
            '.json': SerializationFormat.JSON
        }
        
        return extension_map.get(extension.lower(), SerializationFormat.JSON)
