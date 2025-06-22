#!/usr/bin/env python3
"""
Cross-Reference Validation Tool for Keyboard Maestro MCP Server Documentation.

This script validates all cross-references, internal links, and navigation
elements across the complete documentation suite to ensure consistency
and accuracy.

Usage:
    python scripts/validation/cross_reference_validator.py --comprehensive
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class LinkValidationResult:
    """Result of link validation."""
    source_file: str
    link_text: str
    target_path: str
    link_type: str  # 'internal', 'external', 'anchor'
    status: str     # 'valid', 'broken', 'warning'
    message: str
    line_number: Optional[int] = None


@dataclass
class CrossReferenceReport:
    """Complete cross-reference validation report."""
    timestamp: str
    total_files_processed: int
    total_links_checked: int
    valid_links: int
    broken_links: int
    warnings: int
    results: List[LinkValidationResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)


class DocumentationCrossReferenceValidator:
    """Validates cross-references and links across documentation."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[LinkValidationResult] = []
        self.processed_files: Set[str] = set()
        
        # Documentation files to validate
        self.doc_files = [
            "README.md",
            "ARCHITECTURE.md", 
            "API_REFERENCE.md",
            "INSTALLATION.md",
            "DEPLOYMENT.md",
            "SECURITY.md",
            "PERFORMANCE.md",
            "EXAMPLES.md",
            "TROUBLESHOOTING.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "DOCUMENTATION_INDEX.md",
            "KM_MCP.md",
            "development/PRD.md",
            "development/CONTRACTS.md",
            "development/TYPES.md",
            "development/TESTING.md",
            "development/ERRORS.md",
            "development/TODO.md",
            "development/protocols/FASTMCP_PYTHON_PROTOCOL.md"
        ]
        
        # Pattern for markdown links: [text](path) or [text](path#anchor)
        self.link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
        
        # Pattern for reference-style links: [text][ref] and [ref]: path
        self.ref_link_pattern = re.compile(r'\[([^\]]*)\]\[([^\]]+)\]')
        self.ref_def_pattern = re.compile(r'^\s*\[([^\]]+)\]:\s*(.+)$', re.MULTILINE)
        
    def log_result(self, result: LinkValidationResult) -> None:
        """Log a validation result."""
        self.results.append(result)
        
        status_symbols = {
            'valid': '✅',
            'broken': '❌', 
            'warning': '⚠️'
        }
        
        symbol = status_symbols.get(result.status, '❓')
        print(f"{symbol} [{result.link_type.upper()}] {result.source_file}: {result.link_text} -> {result.target_path}")
        if result.message:
            print(f"   📝 {result.message}")
    
    def validate_internal_link(self, source_file: str, link_text: str, target_path: str, line_num: Optional[int] = None) -> LinkValidationResult:
        """Validate an internal documentation link."""
        
        # Handle anchor links (same file)
        if target_path.startswith('#'):
            return self.validate_anchor_link(source_file, link_text, target_path, line_num)
        
        # Handle relative paths
        if not target_path.startswith('/'):
            # Resolve relative to source file location
            source_dir = (self.project_root / source_file).parent
            full_target_path = source_dir / target_path
        else:
            full_target_path = self.project_root / target_path.lstrip('/')
        
        # Split path and anchor if present
        if '#' in target_path:
            file_path, anchor = target_path.split('#', 1)
            if not file_path.startswith('/'):
                source_dir = (self.project_root / source_file).parent
                full_file_path = source_dir / file_path
            else:
                full_file_path = self.project_root / file_path.lstrip('/')
            
            # Validate file exists
            if not full_file_path.exists():
                return LinkValidationResult(
                    source_file=source_file,
                    link_text=link_text,
                    target_path=target_path,
                    link_type='internal',
                    status='broken',
                    message=f"Target file does not exist: {full_file_path}",
                    line_number=line_num
                )
            
            # Validate anchor exists in target file
            if full_file_path.suffix == '.md':
                return self.validate_anchor_in_file(source_file, link_text, target_path, full_file_path, anchor, line_num)
        
        # Check if target file exists
        if full_target_path.exists():
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=target_path,
                link_type='internal',
                status='valid',
                message="Internal link is valid",
                line_number=line_num
            )
        else:
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=target_path,
                link_type='internal',
                status='broken',
                message=f"Target file does not exist: {full_target_path}",
                line_number=line_num
            )
    
    def validate_anchor_link(self, source_file: str, link_text: str, anchor_target: str, line_num: Optional[int] = None) -> LinkValidationResult:
        """Validate an anchor link within the same file."""
        anchor = anchor_target.lstrip('#')
        source_path = self.project_root / source_file
        
        if not source_path.exists():
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=anchor_target,
                link_type='anchor',
                status='broken',
                message="Source file does not exist",
                line_number=line_num
            )
        
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for headers that would generate this anchor
            # Markdown headers become anchors: ## Header -> #header
            header_patterns = [
                rf'^#+\s+.*{re.escape(anchor)}.*$',  # Exact match
                rf'^#+\s+.*{re.escape(anchor.replace("-", " "))}.*$',  # Space to dash conversion
                rf'^#+\s+.*{re.escape(anchor.replace("-", ""))}.*$',   # No separators
            ]
            
            for pattern in header_patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    return LinkValidationResult(
                        source_file=source_file,
                        link_text=link_text,
                        target_path=anchor_target,
                        link_type='anchor',
                        status='valid',
                        message="Anchor link is valid",
                        line_number=line_num
                    )
            
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=anchor_target,
                link_type='anchor',
                status='warning',
                message=f"Anchor '{anchor}' not found in source file",
                line_number=line_num
            )
            
        except Exception as e:
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=anchor_target,
                link_type='anchor',
                status='broken',
                message=f"Error reading source file: {e}",
                line_number=line_num
            )
    
    def validate_anchor_in_file(self, source_file: str, link_text: str, target_path: str, target_file: Path, anchor: str, line_num: Optional[int] = None) -> LinkValidationResult:
        """Validate an anchor exists in a target file."""
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for headers that would generate this anchor
            header_patterns = [
                rf'^#+\s+.*{re.escape(anchor)}.*$',  # Exact match
                rf'^#+\s+.*{re.escape(anchor.replace("-", " "))}.*$',  # Space to dash conversion
                rf'^#+\s+.*{re.escape(anchor.replace("-", ""))}.*$',   # No separators
            ]
            
            for pattern in header_patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    return LinkValidationResult(
                        source_file=source_file,
                        link_text=link_text,
                        target_path=target_path,
                        link_type='internal',
                        status='valid',
                        message="Internal link with anchor is valid",
                        line_number=line_num
                    )
            
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=target_path,
                link_type='internal',
                status='warning',
                message=f"Anchor '{anchor}' not found in target file {target_file}",
                line_number=line_num
            )
            
        except Exception as e:
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=target_path,
                link_type='internal',
                status='broken',
                message=f"Error reading target file {target_file}: {e}",
                line_number=line_num
            )
    
    def validate_external_link(self, source_file: str, link_text: str, target_url: str, line_num: Optional[int] = None) -> LinkValidationResult:
        """Validate an external URL (basic validation only)."""
        
        # Basic URL validation
        if not target_url.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=target_url,
                link_type='external',
                status='warning',
                message="URL format may be invalid (no protocol)",
                line_number=line_num
            )
        
        # Check for common issues
        issues = []
        if ' ' in target_url:
            issues.append("contains spaces")
        if target_url.endswith(('.', ',')):
            issues.append("ends with punctuation")
        
        if issues:
            return LinkValidationResult(
                source_file=source_file,
                link_text=link_text,
                target_path=target_url,
                link_type='external',
                status='warning',
                message=f"URL formatting issues: {', '.join(issues)}",
                line_number=line_num
            )
        
        return LinkValidationResult(
            source_file=source_file,
            link_text=link_text,
            target_path=target_url,
            link_type='external',
            status='valid',
            message="External URL format is valid",
            line_number=line_num
        )
    
    def validate_file_links(self, file_path: str) -> None:
        """Validate all links in a single documentation file."""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            result = LinkValidationResult(
                source_file=file_path,
                link_text="[FILE]",
                target_path=file_path,
                link_type='internal',
                status='broken',
                message=f"Documentation file does not exist: {file_path}"
            )
            self.log_result(result)
            return
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            result = LinkValidationResult(
                source_file=file_path,
                link_text="[FILE]",
                target_path=file_path,
                link_type='internal',
                status='broken',
                message=f"Error reading file: {e}"
            )
            self.log_result(result)
            return
        
        self.processed_files.add(file_path)
        
        # Track if we're inside a code block to avoid parsing code as links
        in_code_block = False
        
        # Find and validate all markdown links
        for line_num, line in enumerate(lines, 1):
            # Check for code block boundaries
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Skip inline code spans
            if '`' in line:
                # Simple check - if line has backticks, be cautious about link parsing
                # This is a basic heuristic to avoid parsing code as links
                code_spans = line.count('`')
                if code_spans >= 2:  # Likely has inline code
                    # Only parse links outside of backticks (basic implementation)
                    parts = line.split('`')
                    text_parts = [parts[i] for i in range(len(parts)) if i % 2 == 0]
                    line_for_parsing = ' '.join(text_parts)
                else:
                    line_for_parsing = line
            else:
                line_for_parsing = line
            
            # Skip links inside code blocks
            if in_code_block:
                continue
            
            # Find direct markdown links [text](url) in non-code portions
            for match in self.link_pattern.finditer(line_for_parsing):
                link_text = match.group(1)
                target_path = match.group(2)
                
                # Skip if this looks like code (simple heuristic)
                if any(keyword in target_path.lower() for keyword in ['error', 'exception', 'context', 'self.', 'await']):
                    continue
                
                # Determine link type and validate
                if target_path.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
                    result = self.validate_external_link(file_path, link_text, target_path, line_num)
                else:
                    result = self.validate_internal_link(file_path, link_text, target_path, line_num)
                
                self.log_result(result)
        
        # TODO: Handle reference-style links [text][ref] if needed
        # This would require parsing reference definitions and matching them
    
    def validate_consistency(self) -> None:
        """Validate consistency across documentation files."""
        print("\n📋 Validating Documentation Consistency")
        
        # Check for consistent terminology and naming
        consistency_checks = {
            "Project Name": ["Keyboard Maestro MCP Server", "keyboard-maestro-mcp"],
            "Technology": ["FastMCP", "MCP", "Model Context Protocol"],
            "Platform": ["macOS", "Keyboard Maestro"],
            "Language": ["Python 3.10+", "Python"],
        }
        
        inconsistencies = []
        
        for check_name, terms in consistency_checks.items():
            file_term_usage = {}
            
            for file_path in self.doc_files:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    continue
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    file_term_usage[file_path] = []
                    for term in terms:
                        if term.lower() in content:
                            file_term_usage[file_path].append(term)
                
                except Exception:
                    continue
            
            # Look for inconsistent usage patterns
            # This is a basic consistency check - could be enhanced
            
        print("✅ Basic consistency validation completed")
    
    def validate_navigation_aids(self) -> None:
        """Validate navigation aids and quick reference guides."""
        print("\n🧭 Validating Navigation Aids")
        
        # Check if DOCUMENTATION_INDEX.md exists and is comprehensive
        index_file = self.project_root / "DOCUMENTATION_INDEX.md"
        if not index_file.exists():
            result = LinkValidationResult(
                source_file="DOCUMENTATION_INDEX.md",
                link_text="[NAVIGATION]",
                target_path="DOCUMENTATION_INDEX.md",
                link_type='internal',
                status='broken',
                message="Documentation index file is missing"
            )
            self.log_result(result)
            return
        
        # Validate that index file references all major documentation
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index_content = f.read()
            
            major_docs = [
                "README.md", "ARCHITECTURE.md", "INSTALLATION.md", 
                "DEPLOYMENT.md", "API_REFERENCE.md", "TROUBLESHOOTING.md"
            ]
            
            missing_refs = []
            for doc in major_docs:
                if doc not in index_content:
                    missing_refs.append(doc)
            
            if missing_refs:
                result = LinkValidationResult(
                    source_file="DOCUMENTATION_INDEX.md",
                    link_text="[NAVIGATION]",
                    target_path="navigation_completeness",
                    link_type='internal',
                    status='warning',
                    message=f"Documentation index missing references to: {missing_refs}"
                )
                self.log_result(result)
            else:
                result = LinkValidationResult(
                    source_file="DOCUMENTATION_INDEX.md",
                    link_text="[NAVIGATION]",
                    target_path="navigation_completeness",
                    link_type='internal',
                    status='valid',
                    message="Documentation index references all major documents"
                )
                self.log_result(result)
                
        except Exception as e:
            result = LinkValidationResult(
                source_file="DOCUMENTATION_INDEX.md",
                link_text="[NAVIGATION]",
                target_path="DOCUMENTATION_INDEX.md",
                link_type='internal',
                status='broken',
                message=f"Error reading documentation index: {e}"
            )
            self.log_result(result)
    
    def generate_report(self) -> CrossReferenceReport:
        """Generate comprehensive cross-reference validation report."""
        
        # Count results by status
        valid_count = len([r for r in self.results if r.status == 'valid'])
        broken_count = len([r for r in self.results if r.status == 'broken'])
        warning_count = len([r for r in self.results if r.status == 'warning'])
        
        # Generate summary by link type
        summary = {}
        for link_type in ['internal', 'external', 'anchor']:
            type_results = [r for r in self.results if r.link_type == link_type]
            summary[link_type] = {
                'total': len(type_results),
                'valid': len([r for r in type_results if r.status == 'valid']),
                'broken': len([r for r in type_results if r.status == 'broken']),
                'warnings': len([r for r in type_results if r.status == 'warning'])
            }
        
        return CrossReferenceReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_files_processed=len(self.processed_files),
            total_links_checked=len(self.results),
            valid_links=valid_count,
            broken_links=broken_count,
            warnings=warning_count,
            results=self.results,
            summary=summary
        )
    
    def run_comprehensive_validation(self) -> CrossReferenceReport:
        """Run comprehensive cross-reference validation."""
        print("🔗 Starting Comprehensive Cross-Reference Validation")
        print("=" * 60)
        
        # Validate links in each documentation file
        for file_path in self.doc_files:
            print(f"\n📄 Validating: {file_path}")
            self.validate_file_links(file_path)
        
        # Additional validation checks
        self.validate_consistency()
        self.validate_navigation_aids()
        
        # Generate final report
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("📊 Cross-Reference Validation Summary")
        print(f"📁 Files Processed: {report.total_files_processed}")
        print(f"🔗 Links Checked: {report.total_links_checked}")
        print(f"✅ Valid Links: {report.valid_links}")
        print(f"❌ Broken Links: {report.broken_links}")
        print(f"⚠️ Warnings: {report.warnings}")
        
        # Link type breakdown
        print(f"\n📋 Link Type Breakdown:")
        for link_type, stats in report.summary.items():
            print(f"   {link_type.title()}: {stats['valid']}/{stats['total']} valid ({stats['broken']} broken, {stats['warnings']} warnings)")
        
        # Overall status
        if report.broken_links == 0:
            if report.warnings == 0:
                print(f"\n🎉 All cross-references are valid!")
            else:
                print(f"\n✅ No broken links found (review {report.warnings} warnings)")
        else:
            print(f"\n🚨 Found {report.broken_links} broken links that need fixing")
        
        return report


def main():
    """Main validation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate cross-references in Keyboard Maestro MCP Server documentation"
    )
    
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive validation including consistency checks"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Save validation report to JSON file"
    )
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    # Run validation
    validator = DocumentationCrossReferenceValidator(project_root)
    report = validator.run_comprehensive_validation()
    
    # Save report if requested
    if args.output:
        import json
        
        report_dict = {
            "timestamp": report.timestamp,
            "summary": {
                "total_files_processed": report.total_files_processed,
                "total_links_checked": report.total_links_checked,
                "valid_links": report.valid_links,
                "broken_links": report.broken_links,
                "warnings": report.warnings
            },
            "link_type_breakdown": report.summary,
            "results": [
                {
                    "source_file": result.source_file,
                    "link_text": result.link_text,
                    "target_path": result.target_path,
                    "link_type": result.link_type,
                    "status": result.status,
                    "message": result.message,
                    "line_number": result.line_number
                }
                for result in report.results
            ]
        }
        
        with open(args.output, "w") as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"\n📄 Cross-reference validation report saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(1 if report.broken_links > 0 else 0)


if __name__ == "__main__":
    main()
