"""Pure data transformation functions for variable and data operations.

This module provides pure, side-effect-free transformation functions for
variable data, dictionaries, and clipboard content. Implements functional
programming patterns with immutability and type safety.

Key Features:
- Pure transformation functions without side effects
- Immutable data structure transformations
- Type-safe conversions and mappings
- Functional composition patterns for complex transformations
"""

from typing import Dict, Any, List, Optional, Tuple, Callable, TypeVar, FrozenSet
from dataclasses import replace
import json
import re
from datetime import datetime

from src.types.domain_types import VariableName, VariableValue
from src.types.enumerations import VariableScope
from src.core.variable_operations import (
    VariableEntry, VariableMetadata, VariableSnapshot,
    DictionaryEntry, ClipboardEntry, ClipboardSnapshot
)

T = TypeVar('T')
U = TypeVar('U')


class VariableTransformations:
    """Pure transformations for variable data."""
    
    @staticmethod
    def transform_variable_for_scope(
        entry: VariableEntry,
        target_scope: VariableScope,
        instance_id: Optional[str] = None
    ) -> Optional[VariableEntry]:
        """Transform variable entry for different scope context."""
        if not entry.is_accessible_in_scope(target_scope, instance_id):
            return None
        
        # Create new metadata with target scope
        new_metadata = replace(
            entry.metadata,
            scope=target_scope,
            instance_id=instance_id if target_scope == VariableScope.INSTANCE else None,
            modified_at=datetime.now()
        )
        
        return replace(entry, metadata=new_metadata)
    
    @staticmethod
    def filter_variables_by_pattern(
        snapshot: VariableSnapshot,
        name_pattern: str,
        use_regex: bool = False
    ) -> FrozenSet[VariableEntry]:
        """Filter variables by name pattern."""
        if use_regex:
            try:
                pattern = re.compile(name_pattern, re.IGNORECASE)
                return frozenset(
                    entry for entry in snapshot.variables
                    if pattern.search(entry.metadata.name)
                )
            except re.error:
                return frozenset()
        else:
            # Simple substring matching
            pattern_lower = name_pattern.lower()
            return frozenset(
                entry for entry in snapshot.variables
                if pattern_lower in entry.metadata.name.lower()
            )
    
    @staticmethod
    def group_variables_by_scope(
        snapshot: VariableSnapshot
    ) -> Dict[VariableScope, FrozenSet[VariableEntry]]:
        """Group variables by their scope."""
        groups: Dict[VariableScope, List[VariableEntry]] = {
            scope: [] for scope in VariableScope
        }
        
        for entry in snapshot.variables:
            groups[entry.metadata.scope].append(entry)
        
        return {
            scope: frozenset(entries)
            for scope, entries in groups.items()
        }
    
    @staticmethod
    def create_variable_summary(
        snapshot: VariableSnapshot
    ) -> Dict[str, Any]:
        """Create summary statistics for variable snapshot."""
        scope_groups = VariableTransformations.group_variables_by_scope(snapshot)
        
        return {
            'total_variables': len(snapshot.variables),
            'by_scope': {
                scope.value: len(entries)
                for scope, entries in scope_groups.items()
            },
            'password_variables': len([
                entry for entry in snapshot.variables
                if entry.is_password_variable()
            ]),
            'snapshot_time': snapshot.snapshot_time.isoformat(),
            'scoped_variables': len([
                entry for entry in snapshot.variables
                if entry.metadata.is_scoped_variable()
            ])
        }
    
    @staticmethod
    def merge_variable_snapshots(
        primary: VariableSnapshot,
        secondary: VariableSnapshot,
        conflict_resolver: Callable[[VariableEntry, VariableEntry], VariableEntry] = None
    ) -> VariableSnapshot:
        """Merge two variable snapshots with conflict resolution."""
        if conflict_resolver is None:
            # Default: prefer newer modification time
            def default_resolver(entry1: VariableEntry, entry2: VariableEntry) -> VariableEntry:
                if entry1.metadata.modified_at >= entry2.metadata.modified_at:
                    return entry1
                return entry2
            conflict_resolver = default_resolver
        
        # Build lookup for secondary variables
        secondary_lookup: Dict[Tuple[str, VariableScope, Optional[str]], VariableEntry] = {}
        for entry in secondary.variables:
            key = (entry.metadata.name, entry.metadata.scope, entry.metadata.instance_id)
            secondary_lookup[key] = entry
        
        # Merge variables
        merged_vars = []
        processed_keys = set()
        
        # Process primary variables
        for entry in primary.variables:
            key = (entry.metadata.name, entry.metadata.scope, entry.metadata.instance_id)
            if key in secondary_lookup:
                # Conflict resolution
                merged_entry = conflict_resolver(entry, secondary_lookup[key])
                merged_vars.append(merged_entry)
                processed_keys.add(key)
            else:
                merged_vars.append(entry)
                processed_keys.add(key)
        
        # Add remaining secondary variables
        for key, entry in secondary_lookup.items():
            if key not in processed_keys:
                merged_vars.append(entry)
        
        return VariableSnapshot(
            variables=frozenset(merged_vars),
            snapshot_time=max(primary.snapshot_time, secondary.snapshot_time)
        )


class DictionaryTransformations:
    """Pure transformations for dictionary data."""
    
    @staticmethod
    def transform_keys(
        entry: DictionaryEntry,
        key_transformer: Callable[[str], str]
    ) -> DictionaryEntry:
        """Transform dictionary keys using provided function."""
        new_data = {
            key_transformer(key): value
            for key, value in entry.data.items()
        }
        
        return replace(
            entry,
            data=new_data,
            modified_at=datetime.now()
        )
    
    @staticmethod
    def transform_values(
        entry: DictionaryEntry,
        value_transformer: Callable[[Any], Any]
    ) -> DictionaryEntry:
        """Transform dictionary values using provided function."""
        new_data = {
            key: value_transformer(value)
            for key, value in entry.data.items()
        }
        
        return replace(
            entry,
            data=new_data,
            modified_at=datetime.now()
        )
    
    @staticmethod
    def filter_dictionary(
        entry: DictionaryEntry,
        key_predicate: Callable[[str], bool] = None,
        value_predicate: Callable[[Any], bool] = None
    ) -> DictionaryEntry:
        """Filter dictionary entries by key and/or value predicates."""
        new_data = {}
        
        for key, value in entry.data.items():
            include_key = key_predicate(key) if key_predicate else True
            include_value = value_predicate(value) if value_predicate else True
            
            if include_key and include_value:
                new_data[key] = value
        
        return replace(
            entry,
            data=new_data,
            modified_at=datetime.now()
        )
    
    @staticmethod
    def flatten_nested_dictionary(
        entry: DictionaryEntry,
        separator: str = "."
    ) -> DictionaryEntry:
        """Flatten nested dictionary structure."""
        def _flatten(obj: Any, parent_key: str = "") -> Dict[str, Any]:
            items = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{separator}{key}" if parent_key else key
                    items.extend(_flatten(value, new_key).items())
            else:
                return {parent_key: obj}
            
            return dict(items)
        
        flattened_data = _flatten(entry.data)
        
        return replace(
            entry,
            data=flattened_data,
            modified_at=datetime.now()
        )
    
    @staticmethod
    def merge_dictionaries(
        primary: DictionaryEntry,
        secondary: DictionaryEntry,
        deep_merge: bool = True
    ) -> DictionaryEntry:
        """Merge two dictionary entries."""
        def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
            result = dict1.copy()
            
            for key, value in dict2.items():
                if (key in result and 
                    isinstance(result[key], dict) and 
                    isinstance(value, dict) and 
                    deep_merge):
                    result[key] = _deep_merge(result[key], value)
                else:
                    result[key] = value
            
            return result
        
        if deep_merge:
            merged_data = _deep_merge(primary.data, secondary.data)
        else:
            merged_data = {**primary.data, **secondary.data}
        
        return replace(
            primary,
            data=merged_data,
            modified_at=datetime.now()
        )
    
    @staticmethod
    def extract_schema(entry: DictionaryEntry) -> Dict[str, str]:
        """Extract type schema from dictionary data."""
        def _get_type_name(value: Any) -> str:
            if value is None:
                return "null"
            elif isinstance(value, bool):
                return "boolean"
            elif isinstance(value, int):
                return "integer"
            elif isinstance(value, float):
                return "number"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, list):
                if value:
                    element_types = {_get_type_name(item) for item in value}
                    if len(element_types) == 1:
                        return f"array<{element_types.pop()}>"
                    return "array<mixed>"
                return "array<unknown>"
            elif isinstance(value, dict):
                return "object"
            else:
                return "unknown"
        
        return {
            key: _get_type_name(value)
            for key, value in entry.data.items()
        }


class ClipboardTransformations:
    """Pure transformations for clipboard data."""
    
    @staticmethod
    def filter_clipboard_by_format(
        snapshot: ClipboardSnapshot,
        format_type: str
    ) -> ClipboardSnapshot:
        """Filter clipboard entries by format type."""
        filtered_entries = tuple(
            entry for entry in snapshot.entries
            if entry.format_type == format_type
        )
        
        # Update current index if necessary
        new_current_index = 0
        if filtered_entries and snapshot.current_index < len(snapshot.entries):
            current_entry = snapshot.entries[snapshot.current_index]
            if current_entry.format_type == format_type:
                # Find new index in filtered list
                for i, entry in enumerate(filtered_entries):
                    if entry.timestamp == current_entry.timestamp:
                        new_current_index = i
                        break
        
        return replace(
            snapshot,
            entries=filtered_entries,
            current_index=new_current_index
        )
    
    @staticmethod
    def transform_clipboard_content(
        entry: ClipboardEntry,
        content_transformer: Callable[[str], str]
    ) -> ClipboardEntry:
        """Transform clipboard content using provided function."""
        return replace(
            entry,
            content=content_transformer(entry.content),
            timestamp=datetime.now()
        )
    
    @staticmethod
    def deduplicate_clipboard_history(
        snapshot: ClipboardSnapshot
    ) -> ClipboardSnapshot:
        """Remove duplicate entries from clipboard history."""
        seen_content = set()
        unique_entries = []
        
        for entry in snapshot.entries:
            content_key = (entry.content, entry.format_type)
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_entries.append(entry)
        
        # Reassign indices
        reindexed_entries = tuple(
            replace(entry, index=i)
            for i, entry in enumerate(unique_entries)
        )
        
        # Update current index
        new_current_index = min(snapshot.current_index, len(reindexed_entries) - 1)
        
        return replace(
            snapshot,
            entries=reindexed_entries,
            current_index=max(0, new_current_index)
        )
    
    @staticmethod
    def create_content_summary(entry: ClipboardEntry) -> Dict[str, Any]:
        """Create summary of clipboard entry content."""
        content_length = len(entry.content)
        
        summary = {
            'format': entry.format_type,
            'length': content_length,
            'timestamp': entry.timestamp.isoformat(),
            'index': entry.index
        }
        
        # Format-specific analysis
        if entry.is_text_format():
            lines = entry.content.count('\n') + 1
            words = len(entry.content.split())
            summary.update({
                'lines': lines,
                'words': words,
                'preview': entry.content[:100] + '...' if content_length > 100 else entry.content
            })
        elif entry.is_file_format():
            summary.update({
                'file_path': entry.content,
                'is_absolute': entry.content.startswith('/') or ':' in entry.content[:3]
            })
        
        return summary


class FormatTransformations:
    """Pure transformations for data format conversions."""
    
    @staticmethod
    def variable_to_json(entry: VariableEntry) -> str:
        """Convert variable entry to JSON representation."""
        return json.dumps({
            'name': entry.metadata.name,
            'value': entry.value,
            'scope': entry.metadata.scope.value,
            'instance_id': entry.metadata.instance_id,
            'created_at': entry.metadata.created_at.isoformat(),
            'modified_at': entry.metadata.modified_at.isoformat(),
            'is_password': entry.metadata.is_password
        }, indent=2)
    
    @staticmethod
    def variables_to_csv_format(variables: FrozenSet[VariableEntry]) -> str:
        """Convert variables to CSV format."""
        lines = ['name,value,scope,instance_id,created_at,modified_at,is_password']
        
        for entry in sorted(variables, key=lambda e: e.metadata.name):
            # Escape CSV values
            def escape_csv(value: str) -> str:
                if ',' in value or '"' in value or '\n' in value:
                    return f'"{value.replace(\'"\', \'""\')}"\''
                return value
            
            line = ','.join([
                escape_csv(entry.metadata.name),
                escape_csv(entry.value or ''),
                escape_csv(entry.metadata.scope.value),
                escape_csv(entry.metadata.instance_id or ''),
                escape_csv(entry.metadata.created_at.isoformat()),
                escape_csv(entry.metadata.modified_at.isoformat()),
                str(entry.metadata.is_password).lower()
            ])
            lines.append(line)
        
        return '\n'.join(lines)
    
    @staticmethod
    def dictionary_to_flat_format(entry: DictionaryEntry) -> Dict[str, str]:
        """Convert dictionary to flat key-value string format."""
        def _flatten_value(value: Any) -> str:
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            elif value is None:
                return ''
            else:
                return str(value)
        
        flattened = DictionaryTransformations.flatten_nested_dictionary(entry)
        
        return {
            key: _flatten_value(value)
            for key, value in flattened.data.items()
        }
    
    @staticmethod
    def create_backup_format(
        variables: FrozenSet[VariableEntry],
        dictionaries: List[DictionaryEntry],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create comprehensive backup format for all data."""
        backup_data = {
            'metadata': {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'variable_count': len(variables),
                'dictionary_count': len(dictionaries),
                **(metadata or {})
            },
            'variables': [
                {
                    'name': entry.metadata.name,
                    'value': entry.value,
                    'scope': entry.metadata.scope.value,
                    'instance_id': entry.metadata.instance_id,
                    'created_at': entry.metadata.created_at.isoformat(),
                    'modified_at': entry.metadata.modified_at.isoformat(),
                    'is_password': entry.metadata.is_password
                }
                for entry in variables
            ],
            'dictionaries': [
                {
                    'name': entry.name,
                    'data': entry.data,
                    'created_at': entry.created_at.isoformat(),
                    'modified_at': entry.modified_at.isoformat()
                }
                for entry in dictionaries
            ]
        }
        
        return json.dumps(backup_data, indent=2, sort_keys=True)
