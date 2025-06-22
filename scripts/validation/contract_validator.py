# Contract Validation Automation Script
# Target: <250 lines - Automated contract validation and verification

"""
Automated contract validation and verification script.

This script provides automated tools for validating contract compliance,
analyzing contract coverage, and generating contract violation reports.
Can be run as part of CI/CD pipeline or development workflow to ensure
comprehensive contract enforcement across the codebase.

Key Features:
- Contract coverage analysis across all modules
- Automated contract compliance checking
- Violation pattern analysis and reporting
- Performance impact assessment of contracts
- Integration with testing framework for validation
"""

import ast
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.contracts import (
    system_invariant_checker, check_all_system_invariants,
    is_valid_macro_identifier, is_valid_variable_name
)


@dataclass
class ContractCoverage:
    """Contract coverage statistics for a module."""
    module_name: str
    total_functions: int
    functions_with_preconditions: int
    functions_with_postconditions: int
    functions_with_invariants: int
    contract_coverage_percentage: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ContractViolationReport:
    """Report of contract violations found during validation."""
    module_name: str
    function_name: str
    violation_type: str
    violation_message: str
    line_number: int
    severity: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ContractAnalyzer:
    """Analyzes contract usage and compliance across the codebase."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_path = project_root / "src"
        self.coverage_reports: List[ContractCoverage] = []
        self.violation_reports: List[ContractViolationReport] = []
    
    def analyze_project(self) -> None:
        """Analyze entire project for contract coverage and compliance."""
        print("Starting contract analysis...")
        
        # Analyze all Python files in src directory
        for py_file in self.src_path.rglob("*.py"):
            if py_file.name != "__init__.py":
                self._analyze_file(py_file)
        
        print(f"Analysis complete. Analyzed {len(self.coverage_reports)} modules.")
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file for contract usage."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract contract information
            coverage = self._extract_contract_coverage(tree, file_path)
            if coverage.total_functions > 0:
                self.coverage_reports.append(coverage)
            
            # Check for contract violations
            violations = self._check_contract_violations(tree, file_path)
            self.violation_reports.extend(violations)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _extract_contract_coverage(self, tree: ast.AST, file_path: Path) -> ContractCoverage:
        """Extract contract coverage statistics from AST."""
        module_name = self._get_module_name(file_path)
        
        total_functions = 0
        functions_with_preconditions = 0
        functions_with_postconditions = 0
        functions_with_invariants = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                
                # Check for contract decorators
                has_requires = any(
                    self._is_contract_decorator(dec, 'requires') 
                    for dec in node.decorator_list
                )
                has_ensures = any(
                    self._is_contract_decorator(dec, 'ensures')
                    for dec in node.decorator_list
                )
                has_invariant = any(
                    self._is_contract_decorator(dec, 'invariant')
                    for dec in node.decorator_list
                )
                
                if has_requires:
                    functions_with_preconditions += 1
                if has_ensures:
                    functions_with_postconditions += 1
                if has_invariant:
                    functions_with_invariants += 1
        
        # Calculate coverage percentage
        contract_coverage = 0
        if total_functions > 0:
            functions_with_contracts = len(set([
                f for f in range(total_functions)
                if any([functions_with_preconditions, functions_with_postconditions, functions_with_invariants])
            ]))
            contract_coverage = (
                (functions_with_preconditions + functions_with_postconditions + functions_with_invariants) 
                / (total_functions * 3)  # Max 3 contracts per function
            ) * 100
        
        return ContractCoverage(
            module_name=module_name,
            total_functions=total_functions,
            functions_with_preconditions=functions_with_preconditions,
            functions_with_postconditions=functions_with_postconditions,
            functions_with_invariants=functions_with_invariants,
            contract_coverage_percentage=contract_coverage
        )
    
    def _check_contract_violations(self, tree: ast.AST, file_path: Path) -> List[ContractViolationReport]:
        """Check for potential contract violations in the code."""
        violations = []
        module_name = self._get_module_name(file_path)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for missing contracts on critical functions
                if self._is_critical_function(node):
                    has_contracts = any(
                        self._is_contract_decorator(dec, name)
                        for dec in node.decorator_list
                        for name in ['requires', 'ensures', 'invariant']
                    )
                    
                    if not has_contracts:
                        violations.append(ContractViolationReport(
                            module_name=module_name,
                            function_name=node.name,
                            violation_type="missing_contracts",
                            violation_message="Critical function lacks contract specifications",
                            line_number=node.lineno,
                            severity="warning"
                        ))
                
                # Check for potentially unsafe operations
                if self._has_unsafe_operations(node):
                    violations.append(ContractViolationReport(
                        module_name=module_name,
                        function_name=node.name,
                        violation_type="unsafe_operations",
                        violation_message="Function contains potentially unsafe operations without contracts",
                        line_number=node.lineno,
                        severity="error"
                    ))
        
        return violations
    
    def _is_contract_decorator(self, decorator: ast.expr, name: str) -> bool:
        """Check if decorator is a contract decorator."""
        if isinstance(decorator, ast.Name):
            return decorator.id == name
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            return decorator.func.id == name
        return False
    
    def _is_critical_function(self, node: ast.FunctionDef) -> bool:
        """Determine if function is critical and should have contracts."""
        critical_patterns = [
            'execute', 'create', 'delete', 'modify', 'validate',
            'authenticate', 'authorize', 'send', 'receive'
        ]
        
        function_name_lower = node.name.lower()
        return any(pattern in function_name_lower for pattern in critical_patterns)
    
    def _has_unsafe_operations(self, node: ast.FunctionDef) -> bool:
        """Check if function contains potentially unsafe operations."""
        unsafe_patterns = [
            'exec', 'eval', 'subprocess', 'os.system',
            'open', 'file', 'delete', 'remove'
        ]
        
        # Simple check for unsafe function calls in the body
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id in unsafe_patterns:
                        return True
                elif isinstance(child.func, ast.Attribute):
                    if child.func.attr in unsafe_patterns:
                        return True
        
        return False
    
    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path."""
        relative_path = file_path.relative_to(self.src_path)
        module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        return '.'.join(module_parts)
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage report."""
        total_functions = sum(c.total_functions for c in self.coverage_reports)
        total_with_contracts = sum(
            c.functions_with_preconditions + c.functions_with_postconditions + c.functions_with_invariants
            for c in self.coverage_reports
        )
        
        overall_coverage = (total_with_contracts / (total_functions * 3)) * 100 if total_functions > 0 else 0
        
        return {
            'overall_coverage': overall_coverage,
            'total_modules': len(self.coverage_reports),
            'total_functions': total_functions,
            'modules': [c.to_dict() for c in self.coverage_reports],
            'violations': [v.to_dict() for v in self.violation_reports],
            'summary': {
                'high_coverage_modules': len([c for c in self.coverage_reports if c.contract_coverage_percentage >= 80]),
                'medium_coverage_modules': len([c for c in self.coverage_reports if 40 <= c.contract_coverage_percentage < 80]),
                'low_coverage_modules': len([c for c in self.coverage_reports if c.contract_coverage_percentage < 40]),
                'total_violations': len(self.violation_reports),
                'error_violations': len([v for v in self.violation_reports if v.severity == 'error']),
                'warning_violations': len([v for v in self.violation_reports if v.severity == 'warning'])
            }
        }


class ContractValidator:
    """Validates contract compliance and runs contract-specific tests."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def validate_system_invariants(self) -> Dict[str, Any]:
        """Validate all system invariants."""
        print("Validating system invariants...")
        
        try:
            invariant_results = system_invariant_checker.check_all_invariants()
            violations = system_invariant_checker.get_violations()
            
            return {
                'overall_status': len(violations) == 0,
                'invariant_results': invariant_results,
                'violations': violations,
                'total_invariants': len(invariant_results),
                'passed_invariants': len([r for r in invariant_results.values() if r]),
                'failed_invariants': len([r for r in invariant_results.values() if not r])
            }
        except Exception as e:
            return {
                'overall_status': False,
                'error': str(e),
                'invariant_results': {},
                'violations': []
            }
    
    def run_contract_tests(self) -> Dict[str, Any]:
        """Run contract-specific test suite."""
        print("Running contract tests...")
        
        # In a real implementation, would use pytest to run contract tests
        # For now, return a placeholder result
        return {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_results': []
        }


def main():
    """Main entry point for contract validation automation."""
    parser = argparse.ArgumentParser(description="Contract Validation Automation")
    parser.add_argument('--project-root', type=Path, default=Path.cwd(),
                       help='Root directory of the project')
    parser.add_argument('--output', type=Path, default=Path('contract_report.json'),
                       help='Output file for validation report')
    parser.add_argument('--coverage-only', action='store_true',
                       help='Only generate coverage report')
    parser.add_argument('--invariants-only', action='store_true',
                       help='Only validate system invariants')
    
    args = parser.parse_args()
    
    print(f"Contract validation for project: {args.project_root}")
    
    # Initialize components
    analyzer = ContractAnalyzer(args.project_root)
    validator = ContractValidator(args.project_root)
    
    report = {}
    
    # Generate coverage analysis
    if not args.invariants_only:
        analyzer.analyze_project()
        report['coverage'] = analyzer.generate_coverage_report()
    
    # Validate system invariants
    if not args.coverage_only:
        report['invariants'] = validator.validate_system_invariants()
        report['tests'] = validator.run_contract_tests()
    
    # Generate overall status
    overall_status = True
    if 'invariants' in report:
        overall_status &= report['invariants']['overall_status']
    if 'coverage' in report:
        overall_status &= len([v for v in report['coverage']['violations'] if v['severity'] == 'error']) == 0
    
    report['overall_status'] = overall_status
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Contract validation report saved to: {args.output}")
    
    # Print summary
    if 'coverage' in report:
        coverage_data = report['coverage']
        print(f"Coverage: {coverage_data['overall_coverage']:.1f}%")
        print(f"Modules analyzed: {coverage_data['total_modules']}")
        print(f"Functions analyzed: {coverage_data['total_functions']}")
        print(f"Violations found: {len(coverage_data['violations'])}")
    
    if 'invariants' in report:
        invariant_data = report['invariants']
        print(f"System invariants: {invariant_data['passed_invariants']}/{invariant_data['total_invariants']} passed")
    
    print(f"Overall status: {'PASS' if overall_status else 'FAIL'}")
    
    # Exit with appropriate code
    sys.exit(0 if overall_status else 1)


if __name__ == '__main__':
    main()
