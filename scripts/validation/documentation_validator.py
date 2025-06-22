#!/usr/bin/env python3
"""
Documentation Validation Script
Comprehensive quality assurance for Keyboard Maestro MCP Server documentation

This script performs:
- Link validation across all documentation files
- Code example syntax verification
- Format consistency checking
- Table of contents generation
- Basic spelling and grammar validation
- Cross-reference verification

Usage:
    python scripts/validation/documentation_validator.py
    python scripts/validation/documentation_validator.py --fix-issues
    python scripts/validation/documentation_validator.py --generate-toc
"""

import os
import re
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urlparse
from dataclasses import dataclass, field
import subprocess
from collections import defaultdict

# External dependencies for enhanced validation
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️ requests not available - external link checking disabled")

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    print("⚠️ markdown not available - advanced parsing disabled")


@dataclass
class ValidationIssue:
    """Represents a documentation validation issue."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # error, warning, info
    message: str
    suggestion: Optional[str] = None
    context: Optional[str] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    total_files: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    links_checked: int = 0
    broken_links: int = 0
    code_examples: int = 0
    syntax_errors: int = 0
    consistency_checks: int = 0
    format_issues: int = 0
    
    def add_issue(self, issue: ValidationIssue):
        """Add validation issue to report."""
        self.issues.append(issue)
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        return {
            "total_files": self.total_files,
            "total_issues": len(self.issues),
            "errors": len([i for i in self.issues if i.severity == "error"]),
            "warnings": len([i for i in self.issues if i.severity == "warning"]),
            "info": len([i for i in self.issues if i.severity == "info"]),
            "links_checked": self.links_checked,
            "broken_links": self.broken_links,
            "code_examples": self.code_examples,
            "syntax_errors": self.syntax_errors
        }


class DocumentationValidator:
    """Comprehensive documentation validation system."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.report = ValidationReport()
        
        # File patterns to validate
        self.doc_patterns = [
            "*.md",
            "*.rst", 
            "*.txt"
        ]
        
        # Exclude patterns
        self.exclude_patterns = [
            ".git/",
            "node_modules/",
            "__pycache__/",
            ".pytest_cache/",
            "*.pyc"
        ]
        
        # Link validation cache
        self.link_cache = {}
        
        # Code block extractors
        self.code_block_patterns = {
            "python": r"```python\n(.*?)\n```",
            "bash": r"```bash\n(.*?)\n```", 
            "json": r"```json\n(.*?)\n```",
            "javascript": r"```javascript\n(.*?)\n```",
            "yaml": r"```yaml\n(.*?)\n```"
        }
        
        # Common spelling errors (basic dictionary)
        self.common_misspellings = {
            "recieve": "receive",
            "seperate": "separate", 
            "occured": "occurred",
            "sucessful": "successful",
            "accesible": "accessible",
            "recomendation": "recommendation",
            "enviroment": "environment",
            "existance": "existence",
            "maintainance": "maintenance",
            "performace": "performance"
        }
    
    def validate_all_documentation(self) -> ValidationReport:
        """Run comprehensive validation on all documentation."""
        
        print("🔍 Starting comprehensive documentation validation...")
        
        # Find all documentation files
        doc_files = self._find_documentation_files()
        self.report.total_files = len(doc_files)
        
        print(f"📄 Found {len(doc_files)} documentation files to validate")
        
        # Validate each file
        for file_path in doc_files:
            self._validate_single_file(file_path)
        
        # Cross-file validation
        self._validate_cross_references(doc_files)
        
        # Generate validation report
        self._generate_validation_report()
        
        return self.report
    
    def _find_documentation_files(self) -> List[Path]:
        """Find all documentation files in the project."""
        
        doc_files = []
        
        for pattern in self.doc_patterns:
            files = self.project_root.rglob(pattern)
            for file_path in files:
                # Check if file should be excluded
                relative_path = file_path.relative_to(self.project_root)
                if not any(exclude in str(relative_path) for exclude in self.exclude_patterns):
                    doc_files.append(file_path)
        
        return sorted(doc_files)
    
    def _validate_single_file(self, file_path: Path):
        """Validate a single documentation file."""
        
        print(f"📝 Validating: {file_path.relative_to(self.project_root)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Run validation checks
            self._check_markdown_syntax(file_path, content, lines)
            self._check_links(file_path, content, lines)
            self._validate_code_examples(file_path, content, lines)
            self._check_formatting_consistency(file_path, content, lines)
            self._check_spelling_grammar(file_path, content, lines)
            self._validate_table_of_contents(file_path, content, lines)
            
        except Exception as e:
            self.report.add_issue(ValidationIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="file_error",
                severity="error",
                message=f"Failed to read file: {e}"
            ))
    
    def _check_markdown_syntax(self, file_path: Path, content: str, lines: List[str]):
        """Check Markdown syntax and structure."""
        
        if not file_path.suffix == '.md':
            return
        
        # Check for common Markdown issues
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Check for unmatched code blocks
            if line.strip().startswith('```'):
                # Count code block delimiters
                code_blocks = content.count('```')
                if code_blocks % 2 != 0:
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="markdown_syntax",
                        severity="error",
                        message="Unmatched code block delimiter",
                        suggestion="Ensure all ``` blocks are properly closed"
                    ))
            
            # Check for malformed links
            link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'
            for match in re.finditer(link_pattern, line):
                link_text, link_url = match.groups()
                if not link_text.strip():
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="markdown_link",
                        severity="warning", 
                        message="Link has empty text",
                        context=match.group(0)
                    ))
                
                if not link_url.strip():
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="markdown_link",
                        severity="error",
                        message="Link has empty URL", 
                        context=match.group(0)
                    ))
            
            # Check heading structure
            if line.startswith('#'):
                heading_level = len(line) - len(line.lstrip('#'))
                if heading_level > 6:
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="markdown_heading",
                        severity="warning",
                        message=f"Heading level {heading_level} exceeds maximum (6)",
                        context=line.strip()
                    ))
        
        # Add issues to report
        for issue in issues:
            self.report.add_issue(issue)
    
    def _check_links(self, file_path: Path, content: str, lines: List[str]):
        """Validate all links in the document."""
        
        # Extract all links
        link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'
        internal_link_pattern = r'\[([^\]]*)\]\(#([^)]*)\)'
        
        for i, line in enumerate(lines, 1):
            # Check markdown links
            for match in re.finditer(link_pattern, line):
                link_text, link_url = match.groups()
                self.report.links_checked += 1
                
                if link_url.startswith('http://') or link_url.startswith('https://'):
                    # External link
                    if not self._validate_external_link(link_url):
                        self.report.broken_links += 1
                        self.report.add_issue(ValidationIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="broken_link",
                            severity="error",
                            message=f"External link not accessible: {link_url}",
                            context=match.group(0)
                        ))
                
                elif link_url.startswith('#'):
                    # Internal anchor link
                    if not self._validate_internal_anchor(file_path, content, link_url[1:]):
                        self.report.add_issue(ValidationIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="broken_anchor",
                            severity="warning",
                            message=f"Internal anchor not found: {link_url}",
                            context=match.group(0)
                        ))
                
                elif link_url.startswith('/') or not '://' in link_url:
                    # Internal file link
                    if not self._validate_internal_file_link(file_path, link_url):
                        self.report.add_issue(ValidationIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="broken_file_link",
                            severity="error",
                            message=f"Internal file link not found: {link_url}",
                            context=match.group(0)
                        ))
    
    def _validate_external_link(self, url: str) -> bool:
        """Validate external link accessibility."""
        
        if not HAS_REQUESTS:
            return True  # Skip if requests not available
        
        # Check cache first
        if url in self.link_cache:
            return self.link_cache[url]
        
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            is_valid = response.status_code < 400
            self.link_cache[url] = is_valid
            return is_valid
        except Exception:
            self.link_cache[url] = False
            return False
    
    def _validate_internal_anchor(self, file_path: Path, content: str, anchor: str) -> bool:
        """Validate internal anchor link."""
        
        # Look for heading that matches anchor
        anchor_variations = [
            anchor,
            anchor.lower(),
            anchor.replace('-', ' '),
            anchor.replace('_', ' '),
            re.sub(r'[^a-zA-Z0-9\s]', '', anchor).lower()
        ]
        
        # Check headings in content
        heading_pattern = r'^#+\s+(.+)$'
        for line in content.split('\n'):
            heading_match = re.match(heading_pattern, line)
            if heading_match:
                heading_text = heading_match.group(1).strip()
                heading_anchor = re.sub(r'[^a-zA-Z0-9\s]', '', heading_text).lower().replace(' ', '-')
                
                if any(var == heading_anchor for var in anchor_variations):
                    return True
        
        return False
    
    def _validate_internal_file_link(self, current_file: Path, link_url: str) -> bool:
        """Validate internal file link."""
        
        # Resolve relative path
        if link_url.startswith('/'):
            target_path = self.project_root / link_url[1:]
        else:
            target_path = current_file.parent / link_url
        
        # Handle anchor in link
        if '#' in link_url:
            file_part = link_url.split('#')[0]
            if file_part:
                if file_part.startswith('/'):
                    target_path = self.project_root / file_part[1:]
                else:
                    target_path = current_file.parent / file_part
        
        return target_path.exists()
    
    def _validate_code_examples(self, file_path: Path, content: str, lines: List[str]):
        """Validate code examples in documentation."""
        
        for language, pattern in self.code_block_patterns.items():
            matches = re.findall(pattern, content, re.DOTALL)
            
            for match in matches:
                self.report.code_examples += 1
                
                if language == "python":
                    if not self._validate_python_syntax(match):
                        self.report.syntax_errors += 1
                        # Find line number for the code block
                        line_num = self._find_code_block_line(lines, match)
                        
                        self.report.add_issue(ValidationIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            issue_type="python_syntax_error",
                            severity="error",
                            message="Python code block has syntax errors",
                            context=match[:100] + "..." if len(match) > 100 else match
                        ))
                
                elif language == "json":
                    if not self._validate_json_syntax(match):
                        self.report.syntax_errors += 1
                        line_num = self._find_code_block_line(lines, match)
                        
                        self.report.add_issue(ValidationIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            issue_type="json_syntax_error",
                            severity="error",
                            message="JSON code block has syntax errors",
                            context=match[:100] + "..." if len(match) > 100 else match
                        ))
    
    def _validate_python_syntax(self, code: str) -> bool:
        """Validate Python code syntax."""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
    
    def _validate_json_syntax(self, json_str: str) -> bool:
        """Validate JSON syntax."""
        try:
            json.loads(json_str)
            return True
        except json.JSONDecodeError:
            return False
    
    def _find_code_block_line(self, lines: List[str], code_content: str) -> int:
        """Find the line number where a code block starts."""
        # Simple heuristic - find first few lines of code content
        code_lines = code_content.strip().split('\n')
        if not code_lines:
            return 0
        
        first_code_line = code_lines[0].strip()
        
        for i, line in enumerate(lines, 1):
            if first_code_line in line:
                return i
        
        return 0
    
    def _check_formatting_consistency(self, file_path: Path, content: str, lines: List[str]):
        """Check formatting consistency across documentation."""
        
        self.report.consistency_checks += 1
        
        # Check for consistent heading styles
        heading_styles = set()
        for line in lines:
            if line.startswith('#'):
                # Extract heading pattern
                heading_pattern = re.match(r'^(#+)\s+(.+)$', line)
                if heading_pattern:
                    level = len(heading_pattern.group(1))
                    heading_styles.add(level)
        
        # Check for skipped heading levels
        if heading_styles:
            sorted_levels = sorted(heading_styles)
            for i in range(len(sorted_levels) - 1):
                if sorted_levels[i+1] - sorted_levels[i] > 1:
                    self.report.format_issues += 1
                    self.report.add_issue(ValidationIssue(
                        file_path=str(file_path),
                        line_number=0,
                        issue_type="heading_structure",
                        severity="warning",
                        message=f"Heading level skip detected: {sorted_levels[i]} to {sorted_levels[i+1]}",
                        suggestion="Use consecutive heading levels for better structure"
                    ))
        
        # Check for consistent list formatting
        list_styles = set()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- '):
                list_styles.add('dash')
            elif stripped.startswith('* '):
                list_styles.add('asterisk')
            elif re.match(r'^\d+\.\s', stripped):
                list_styles.add('numbered')
        
        if len(list_styles) > 2:  # Allow some variation
            self.report.add_issue(ValidationIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="list_formatting",
                severity="info",
                message="Multiple list formatting styles used",
                suggestion="Consider using consistent list formatting throughout document"
            ))
    
    def _check_spelling_grammar(self, file_path: Path, content: str, lines: List[str]):
        """Basic spelling and grammar checking."""
        
        # Check for common misspellings
        for i, line in enumerate(lines, 1):
            # Skip code blocks and URLs
            if '```' in line or 'http' in line:
                continue
            
            words = re.findall(r'\b[a-zA-Z]+\b', line.lower())
            for word in words:
                if word in self.common_misspellings:
                    self.report.add_issue(ValidationIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="spelling",
                        severity="warning",
                        message=f"Possible misspelling: '{word}'",
                        suggestion=f"Did you mean '{self.common_misspellings[word]}'?",
                        context=line.strip()
                    ))
        
        # Check for very long sentences (basic readability)
        for i, line in enumerate(lines, 1):
            if len(line) > 200:  # Very long line
                sentences = re.split(r'[.!?]+', line)
                for sentence in sentences:
                    if len(sentence.strip()) > 150:  # Long sentence
                        self.report.add_issue(ValidationIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="readability",
                            severity="info",
                            message="Very long sentence detected",
                            suggestion="Consider breaking into shorter sentences",
                            context=sentence.strip()[:100] + "..."
                        ))
    
    def _validate_table_of_contents(self, file_path: Path, content: str, lines: List[str]):
        """Validate and optionally generate table of contents."""
        
        # Extract all headings
        headings = []
        for i, line in enumerate(lines, 1):
            heading_match = re.match(r'^(#+)\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(1).strip()
                anchor = re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().replace(' ', '-')
                headings.append({
                    'level': level,
                    'title': title,
                    'anchor': anchor,
                    'line': i
                })
        
        # Check if TOC exists and is accurate
        if '## Table of Contents' in content or '# Table of Contents' in content:
            # TODO: Validate existing TOC accuracy
            pass
        elif len(headings) > 5:  # Suggest TOC for long documents
            self.report.add_issue(ValidationIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="missing_toc",
                severity="info",
                message="Document has many headings but no table of contents",
                suggestion="Consider adding a table of contents for better navigation"
            ))
    
    def _validate_cross_references(self, doc_files: List[Path]):
        """Validate cross-references between documentation files."""
        
        print("🔗 Validating cross-references between files...")
        
        # Build index of all files and their headings
        file_index = {}
        for doc_file in doc_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract headings
                headings = []
                for line in content.split('\n'):
                    heading_match = re.match(r'^#+\s+(.+)$', line)
                    if heading_match:
                        title = heading_match.group(1).strip()
                        anchor = re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().replace(' ', '-')
                        headings.append(anchor)
                
                file_index[doc_file] = {
                    'content': content,
                    'headings': headings
                }
                
            except Exception as e:
                print(f"⚠️ Could not read {doc_file}: {e}")
        
        # Check cross-references
        for doc_file in doc_files:
            if doc_file not in file_index:
                continue
            
            content = file_index[doc_file]['content']
            
            # Find references to other files
            file_ref_pattern = r'\[([^\]]*)\]\(([^)#]*\.md)(?:#([^)]*))\?\)'
            
            for match in re.finditer(file_ref_pattern, content):
                link_text, target_file, anchor = match.groups()
                
                # Resolve target file path
                if target_file.startswith('/'):
                    target_path = self.project_root / target_file[1:]
                else:
                    target_path = doc_file.parent / target_file
                
                # Check if target file exists
                if target_path not in file_index:
                    self.report.add_issue(ValidationIssue(
                        file_path=str(doc_file),
                        line_number=0,
                        issue_type="broken_cross_reference",
                        severity="error",
                        message=f"Cross-reference to missing file: {target_file}",
                        context=match.group(0)
                    ))
                
                # Check if anchor exists in target file
                elif anchor and anchor not in file_index[target_path]['headings']:
                    self.report.add_issue(ValidationIssue(
                        file_path=str(doc_file),
                        line_number=0,
                        issue_type="broken_cross_reference_anchor",
                        severity="warning",
                        message=f"Cross-reference to missing anchor: {target_file}#{anchor}",
                        context=match.group(0)
                    ))
    
    def _generate_validation_report(self):
        """Generate and save comprehensive validation report."""
        
        print("\n📊 Generating validation report...")
        
        # Summary statistics
        summary = self.report.get_summary()
        
        # Group issues by type
        issues_by_type = defaultdict(list)
        for issue in self.report.issues:
            issues_by_type[issue.issue_type].append(issue)
        
        # Group issues by severity
        issues_by_severity = defaultdict(list)
        for issue in self.report.issues:
            issues_by_severity[issue.severity].append(issue)
        
        # Create report content
        report_content = f"""# Documentation Validation Report
Generated: {self._get_timestamp()}

## Summary Statistics
- **Total Files Validated**: {summary['total_files']}
- **Total Issues Found**: {summary['total_issues']}
- **Errors**: {summary['errors']}
- **Warnings**: {summary['warnings']}
- **Info**: {summary['info']}
- **Links Checked**: {summary['links_checked']}
- **Broken Links**: {summary['broken_links']}
- **Code Examples**: {summary['code_examples']}
- **Syntax Errors**: {summary['syntax_errors']}

## Issues by Severity

### Errors ({summary['errors']})
"""
        
        for issue in issues_by_severity['error']:
            report_content += f"- **{issue.file_path}:{issue.line_number}** - {issue.message}\\n"
            if issue.suggestion:
                report_content += f"  *Suggestion: {issue.suggestion}*\\n"
        
        report_content += f"""
### Warnings ({summary['warnings']})
"""
        
        for issue in issues_by_severity['warning']:
            report_content += f"- **{issue.file_path}:{issue.line_number}** - {issue.message}\\n"
            if issue.suggestion:
                report_content += f"  *Suggestion: {issue.suggestion}*\\n"
        
        report_content += f"""
### Information ({summary['info']})
"""
        
        for issue in issues_by_severity['info']:
            report_content += f"- **{issue.file_path}:{issue.line_number}** - {issue.message}\\n"
            if issue.suggestion:
                report_content += f"  *Suggestion: {issue.suggestion}*\\n"
        
        report_content += """

## Issues by Type
"""
        
        for issue_type, issues in issues_by_type.items():
            report_content += f"\\n### {issue_type.replace('_', ' ').title()} ({len(issues)})\\n"
            for issue in issues:
                report_content += f"- {issue.file_path}:{issue.line_number} - {issue.message}\\n"
        
        # Save report
        os.makedirs("logs", exist_ok=True)
        report_path = "logs/documentation_validation_report.md"
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"📄 Validation report saved to: {report_path}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reporting."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_table_of_contents(self, file_path: Path) -> str:
        """Generate table of contents for a markdown file."""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract headings
        headings = []
        for line in content.split('\\n'):
            heading_match = re.match(r'^(#+)\\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(1).strip()
                anchor = re.sub(r'[^a-zA-Z0-9\\s]', '', title).lower().replace(' ', '-')
                headings.append({
                    'level': level,
                    'title': title,
                    'anchor': anchor
                })
        
        # Generate TOC
        toc_lines = ["## Table of Contents", ""]
        
        for heading in headings:
            if heading['level'] <= 3:  # Only include up to h3
                indent = "  " * (heading['level'] - 1)
                toc_lines.append(f"{indent}- [{heading['title']}](#{heading['anchor']})")
        
        return "\\n".join(toc_lines)
    
    def fix_common_issues(self):
        """Automatically fix common documentation issues."""
        
        print("🔧 Attempting to fix common issues...")
        
        fixes_applied = 0
        
        for issue in self.report.issues:
            if issue.issue_type == "spelling" and issue.suggestion:
                # Auto-fix spelling errors
                try:
                    with open(issue.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple find-replace for spelling
                    # This is a basic implementation - in production, more sophisticated logic needed
                    misspelled_word = issue.message.split("'")[1]
                    correct_word = issue.suggestion.split("'")[1]
                    
                    if misspelled_word in content:
                        content = content.replace(misspelled_word, correct_word)
                        
                        with open(issue.file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        fixes_applied += 1
                        print(f"✅ Fixed spelling: {misspelled_word} → {correct_word} in {issue.file_path}")
                
                except Exception as e:
                    print(f"❌ Could not fix {issue.file_path}: {e}")
        
        print(f"🎯 Applied {fixes_applied} automatic fixes")


def main():
    """Main entry point for documentation validation."""
    
    parser = argparse.ArgumentParser(description="Validate documentation quality")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--fix-issues", action="store_true", help="Attempt to fix common issues")
    parser.add_argument("--generate-toc", help="Generate TOC for specific file")
    parser.add_argument("--external-links", action="store_true", help="Check external links (requires internet)")
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = DocumentationValidator(args.project_root)
    
    if args.generate_toc:
        # Generate TOC for specific file
        file_path = Path(args.generate_toc)
        if file_path.exists():
            toc = validator.generate_table_of_contents(file_path)
            print(f"\\n📋 Table of Contents for {file_path}:")
            print(toc)
        else:
            print(f"❌ File not found: {file_path}")
        return
    
    # Run full validation
    report = validator.validate_all_documentation()
    
    # Print summary
    summary = report.get_summary()
    print(f"""
📊 Validation Complete!

📄 Files Processed: {summary['total_files']}
🔗 Links Checked: {summary['links_checked']}
💻 Code Examples: {summary['code_examples']}

🎯 Results:
  ✅ No Issues: {summary['total_files'] - len([f for f in report.issues if f.severity == 'error'])}
  ⚠️  Warnings: {summary['warnings']}
  ❌ Errors: {summary['errors']}
  ℹ️  Info: {summary['info']}

🔗 Link Status:
  ✅ Working: {summary['links_checked'] - summary['broken_links']}
  ❌ Broken: {summary['broken_links']}

💻 Code Quality:
  ✅ Valid: {summary['code_examples'] - summary['syntax_errors']}
  ❌ Syntax Errors: {summary['syntax_errors']}
""")
    
    # Apply fixes if requested
    if args.fix_issues:
        validator.fix_common_issues()
    
    # Exit with error code if critical issues found
    if summary['errors'] > 0:
        print("❌ Critical issues found - see validation report for details")
        sys.exit(1)
    elif summary['warnings'] > 5:
        print("⚠️ Multiple warnings found - consider reviewing")
        sys.exit(2)
    else:
        print("✅ Documentation validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
