#!/usr/bin/env python3
"""
Final Production Validation Script
Comprehensive end-to-end validation for Keyboard Maestro MCP Server production readiness

This script orchestrates all validation activities including:
- Documentation validation and testing
- Deployment procedure verification
- Production readiness assessment
- End-to-end testing scenarios
- Performance regression testing
- Security audit validation
- User acceptance testing scenarios

Usage:
    python scripts/validation/final_validation.py
    python scripts/validation/final_validation.py --quick-check
    python scripts/validation/final_validation.py --generate-report
"""

import os
import sys
import json
import time
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@dataclass
class ValidationSuite:
    """Results from a validation suite."""
    name: str
    passed: bool
    execution_time: float
    summary: Dict[str, Any]
    details: Optional[str] = None
    report_path: Optional[str] = None


@dataclass
class FinalValidationReport:
    """Comprehensive final validation report."""
    timestamp: str
    environment: str = "production"
    total_suites: int = 0
    passed_suites: int = 0
    failed_suites: int = 0
    total_execution_time: float = 0.0
    suites: List[ValidationSuite] = field(default_factory=list)
    overall_status: str = "UNKNOWN"
    deployment_ready: bool = False
    critical_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class FinalValidator:
    """Orchestrates comprehensive production validation."""
    
    def __init__(self, quick_check: bool = False, generate_report: bool = True):
        self.quick_check = quick_check
        self.generate_report = generate_report
        self.project_root = PROJECT_ROOT
        self.report = FinalValidationReport(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.start_time = time.time()
        
        # Validation suites to run
        self.validation_suites = [
            ("Documentation Quality", self._run_documentation_validation),
            ("Deployment Readiness", self._run_deployment_validation),
            ("Production Readiness", self._run_production_validation),
            ("Installation Procedures", self._test_installation_procedures),
            ("End-to-End Testing", self._run_end_to_end_tests),
        ]
        
        if not quick_check:
            self.validation_suites.extend([
                ("Performance Regression", self._run_performance_tests),
                ("Security Audit", self._run_security_audit),
                ("User Acceptance Testing", self._run_user_acceptance_tests),
                ("Documentation Procedures", self._test_documentation_procedures)
            ])
    
    def run_comprehensive_validation(self) -> FinalValidationReport:
        """Execute all validation suites and generate final report."""
        
        print("🚀 Starting Comprehensive Production Validation")
        print(f"📊 Running {len(self.validation_suites)} validation suites...")
        print(f"🕒 Started at: {self.report.timestamp}")
        print("=" * 70)
        
        # Run each validation suite
        for suite_name, suite_func in self.validation_suites:
            print(f"\n🔍 Executing: {suite_name}")
            print("-" * 50)
            
            suite_start = time.time()
            try:
                suite_result = suite_func()
                suite_result.execution_time = time.time() - suite_start
                self.report.suites.append(suite_result)
                
                # Update counters
                self.report.total_suites += 1
                if suite_result.passed:
                    self.report.passed_suites += 1
                    print(f"✅ {suite_name}: PASSED ({suite_result.execution_time:.2f}s)")
                else:
                    self.report.failed_suites += 1
                    print(f"❌ {suite_name}: FAILED ({suite_result.execution_time:.2f}s)")
                    if suite_result.details:
                        print(f"   Details: {suite_result.details}")
                
            except Exception as e:
                execution_time = time.time() - suite_start
                failed_suite = ValidationSuite(
                    name=suite_name,
                    passed=False,
                    execution_time=execution_time,
                    summary={"error": str(e)},
                    details=f"Suite execution failed: {e}"
                )
                self.report.suites.append(failed_suite)
                self.report.total_suites += 1
                self.report.failed_suites += 1
                print(f"💥 {suite_name}: ERROR ({execution_time:.2f}s) - {e}")
        
        # Calculate final metrics
        self.report.total_execution_time = time.time() - self.start_time
        self._assess_deployment_readiness()
        
        # Generate comprehensive report
        if self.generate_report:
            self._generate_final_report()
        
        # Print final summary
        self._print_final_summary()
        
        return self.report
    
    def _run_documentation_validation(self) -> ValidationSuite:
        """Run documentation validation suite."""
        
        try:
            # Run documentation validator
            validator_path = self.project_root / "scripts/validation/documentation_validator.py"
            
            result = subprocess.run([
                sys.executable, str(validator_path)
            ], capture_output=True, text=True, timeout=300)
            
            passed = result.returncode == 0
            
            # Parse output for summary
            output_lines = result.stdout.split('\n')
            summary = {
                "return_code": result.returncode,
                "files_processed": 0,
                "issues_found": 0,
                "errors": 0,
                "warnings": 0
            }
            
            # Extract metrics from output
            for line in output_lines:
                if "Files Processed:" in line:
                    summary["files_processed"] = int(line.split()[-1])
                elif "❌ Errors:" in line:
                    summary["errors"] = int(line.split()[-1])
                elif "⚠️ Warnings:" in line:
                    summary["warnings"] = int(line.split()[-1])
            
            details = None
            if not passed:
                details = f"Documentation validation failed with {summary['errors']} errors"
            
            return ValidationSuite(
                name="Documentation Quality",
                passed=passed,
                execution_time=0,  # Will be set by caller
                summary=summary,
                details=details,
                report_path="logs/documentation_validation_report.md"
            )
            
        except subprocess.TimeoutExpired:
            return ValidationSuite(
                name="Documentation Quality",
                passed=False,
                execution_time=0,
                summary={"error": "timeout"},
                details="Documentation validation timed out after 5 minutes"
            )
        except Exception as e:
            return ValidationSuite(
                name="Documentation Quality",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"Documentation validation failed: {e}"
            )
    
    def _run_deployment_validation(self) -> ValidationSuite:
        """Run deployment validation suite."""
        
        try:
            # Run deployment validator
            validator_path = self.project_root / "scripts/validation/deployment_validator.py"
            
            args = [sys.executable, str(validator_path), "--environment", "production"]
            if self.quick_check:
                args.append("--quick-check")
            
            result = subprocess.run(args, capture_output=True, text=True, timeout=300)
            
            passed = result.returncode == 0
            
            # Parse output for summary
            output_lines = result.stdout.split('\n')
            summary = {
                "return_code": result.returncode,
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "success_rate": 0.0
            }
            
            # Extract metrics from output
            for line in output_lines:
                if "Total:" in line and "✅ Passed:" in line:
                    parts = line.split()
                    try:
                        summary["total_checks"] = int(parts[parts.index("Total:") + 1])
                        summary["passed_checks"] = int(parts[parts.index("Passed:") + 1])
                        summary["failed_checks"] = int(parts[parts.index("Failed:") + 1])
                    except (ValueError, IndexError):
                        pass
                elif "Success Rate:" in line:
                    try:
                        rate_str = line.split("Success Rate:")[1].strip().replace("%", "")
                        summary["success_rate"] = float(rate_str)
                    except (ValueError, IndexError):
                        pass
            
            details = None
            if not passed:
                details = f"Deployment validation failed ({summary['success_rate']:.1f}% success rate)"
            
            return ValidationSuite(
                name="Deployment Readiness",
                passed=passed,
                execution_time=0,
                summary=summary,
                details=details,
                report_path="logs/deployment_validation_production.md"
            )
            
        except subprocess.TimeoutExpired:
            return ValidationSuite(
                name="Deployment Readiness",
                passed=False,
                execution_time=0,
                summary={"error": "timeout"},
                details="Deployment validation timed out after 5 minutes"
            )
        except Exception as e:
            return ValidationSuite(
                name="Deployment Readiness",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"Deployment validation failed: {e}"
            )
    
    def _run_production_validation(self) -> ValidationSuite:
        """Run production readiness validation suite."""
        
        try:
            # Run production validator
            validator_path = self.project_root / "scripts/validation/production_validator.py"
            
            args = [sys.executable, str(validator_path)]
            if not self.quick_check:
                args.append("--comprehensive")
            
            result = subprocess.run(args, capture_output=True, text=True, timeout=300)
            
            passed = result.returncode == 0
            
            # Parse output for summary
            summary = {
                "return_code": result.returncode,
                "checks_passed": 0,
                "checks_failed": 0,
                "warnings": 0
            }
            
            # Count validation results from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "✅" in line:
                    summary["checks_passed"] += 1
                elif "❌" in line:
                    summary["checks_failed"] += 1
                elif "⚠️" in line:
                    summary["warnings"] += 1
            
            details = None
            if not passed:
                details = f"Production validation failed with {summary['checks_failed']} failures"
            
            return ValidationSuite(
                name="Production Readiness",
                passed=passed,
                execution_time=0,
                summary=summary,
                details=details
            )
            
        except subprocess.TimeoutExpired:
            return ValidationSuite(
                name="Production Readiness",
                passed=False,
                execution_time=0,
                summary={"error": "timeout"},
                details="Production validation timed out after 5 minutes"
            )
        except Exception as e:
            return ValidationSuite(
                name="Production Readiness",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"Production validation failed: {e}"
            )
    
    def _test_installation_procedures(self) -> ValidationSuite:
        """Test installation procedures in clean environment."""
        
        print("  📦 Testing installation procedures...")
        
        # Create temporary directory for clean installation test
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                temp_path = Path(temp_dir)
                
                # Copy essential files for installation test
                essential_files = [
                    "requirements.txt",
                    "requirements-dev.txt",
                    "src/main.py",
                    "config/production.yaml",
                    "INSTALLATION.md"
                ]
                
                missing_files = []
                for file_path in essential_files:
                    src_file = self.project_root / file_path
                    if src_file.exists():
                        dest_file = temp_path / file_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dest_file)
                    else:
                        missing_files.append(file_path)
                
                if missing_files:
                    return ValidationSuite(
                        name="Installation Procedures",
                        passed=False,
                        execution_time=0,
                        summary={"missing_files": missing_files},
                        details=f"Missing essential files: {missing_files}"
                    )
                
                # Test requirements installation (dry run)
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "--dry-run", "-r",
                    str(temp_path / "requirements.txt")
                ], capture_output=True, text=True, timeout=60)
                
                pip_install_works = result.returncode == 0
                
                # Test Python syntax of main file
                syntax_check = subprocess.run([
                    sys.executable, "-m", "py_compile", str(temp_path / "src/main.py")
                ], capture_output=True, text=True)
                
                syntax_valid = syntax_check.returncode == 0
                
                # Check if INSTALLATION.md has required sections
                install_doc = temp_path / "INSTALLATION.md"
                required_sections = ["requirements", "installation", "configuration"]
                has_required_sections = True
                
                if install_doc.exists():
                    with open(install_doc, 'r') as f:
                        content = f.read().lower()
                    
                    missing_sections = [
                        section for section in required_sections
                        if section not in content
                    ]
                    has_required_sections = len(missing_sections) == 0
                else:
                    has_required_sections = False
                    missing_sections = required_sections
                
                passed = pip_install_works and syntax_valid and has_required_sections
                
                summary = {
                    "pip_install_works": pip_install_works,
                    "syntax_valid": syntax_valid,
                    "has_required_sections": has_required_sections,
                    "essential_files_present": len(essential_files) - len(missing_files)
                }
                
                details = None
                if not passed:
                    issues = []
                    if not pip_install_works:
                        issues.append("pip install test failed")
                    if not syntax_valid:
                        issues.append("main.py has syntax errors")
                    if not has_required_sections:
                        issues.append(f"INSTALLATION.md missing sections: {missing_sections}")
                    details = f"Installation issues: {', '.join(issues)}"
                
                return ValidationSuite(
                    name="Installation Procedures",
                    passed=passed,
                    execution_time=0,
                    summary=summary,
                    details=details
                )
                
            except subprocess.TimeoutExpired:
                return ValidationSuite(
                    name="Installation Procedures",
                    passed=False,
                    execution_time=0,
                    summary={"error": "timeout"},
                    details="Installation test timed out"
                )
            except Exception as e:
                return ValidationSuite(
                    name="Installation Procedures",
                    passed=False,
                    execution_time=0,
                    summary={"error": str(e)},
                    details=f"Installation test failed: {e}"
                )
    
    def _run_end_to_end_tests(self) -> ValidationSuite:
        """Run end-to-end testing scenarios."""
        
        print("  🔄 Running end-to-end tests...")
        
        try:
            # Test basic import and initialization
            test_script = f'''
import sys
sys.path.insert(0, "{self.project_root}/src")

try:
    # Test core imports
    from main import FastMCP
    from contracts.decorators import requires, ensures
    from types.domain_types import MacroId, VariableId
    from tools.macro_management import MacroManagementTools
    
    print("IMPORTS_SUCCESS")
    
    # Test FastMCP initialization
    mcp = FastMCP("test-server")
    print("MCP_INIT_SUCCESS")
    
    # Test tool registration (basic)
    tools = MacroManagementTools()
    print("TOOLS_INIT_SUCCESS")
    
    print("E2E_SUCCESS")
    
except ImportError as e:
    print(f"IMPORT_ERROR: {{e}}")
except Exception as e:
    print(f"ERROR: {{e}}")
'''
            
            # Run the test script
            result = subprocess.run([
                sys.executable, "-c", test_script
            ], capture_output=True, text=True, timeout=30)
            
            output = result.stdout.strip()
            
            # Parse test results
            imports_success = "IMPORTS_SUCCESS" in output
            mcp_init_success = "MCP_INIT_SUCCESS" in output
            tools_init_success = "TOOLS_INIT_SUCCESS" in output
            e2e_success = "E2E_SUCCESS" in output
            
            summary = {
                "imports_success": imports_success,
                "mcp_init_success": mcp_init_success,
                "tools_init_success": tools_init_success,
                "overall_success": e2e_success
            }
            
            passed = e2e_success and result.returncode == 0
            
            details = None
            if not passed:
                if "IMPORT_ERROR:" in output:
                    details = f"Import error: {output.split('IMPORT_ERROR:')[1].split()[0]}"
                elif "ERROR:" in output:
                    details = f"Runtime error: {output.split('ERROR:')[1].split()[0]}"
                else:
                    details = "End-to-end test failed without specific error"
            
            return ValidationSuite(
                name="End-to-End Testing",
                passed=passed,
                execution_time=0,
                summary=summary,
                details=details
            )
            
        except subprocess.TimeoutExpired:
            return ValidationSuite(
                name="End-to-End Testing",
                passed=False,
                execution_time=0,
                summary={"error": "timeout"},
                details="End-to-end test timed out"
            )
        except Exception as e:
            return ValidationSuite(
                name="End-to-End Testing",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"End-to-end test failed: {e}"
            )
    
    def _run_performance_tests(self) -> ValidationSuite:
        """Run performance regression tests."""
        
        print("  ⚡ Running performance tests...")
        
        try:
            # Basic performance test - measure import times
            import_test_script = f'''
import time
import sys
sys.path.insert(0, "{self.project_root}/src")

start_time = time.time()

# Test import performance
try:
    from main import FastMCP
    import_time = time.time() - start_time
    print(f"IMPORT_TIME:{{import_time:.3f}}")
    
    # Test initialization performance
    init_start = time.time()
    mcp = FastMCP("perf-test")
    init_time = time.time() - init_start
    print(f"INIT_TIME:{{init_time:.3f}}")
    
    print("PERF_SUCCESS")
    
except Exception as e:
    print(f"PERF_ERROR:{{e}}")
'''
            
            result = subprocess.run([
                sys.executable, "-c", import_test_script
            ], capture_output=True, text=True, timeout=30)
            
            output = result.stdout.strip()
            
            # Parse performance metrics
            import_time = 0.0
            init_time = 0.0
            
            if "IMPORT_TIME:" in output:
                import_time = float(output.split("IMPORT_TIME:")[1].split()[0])
            if "INIT_TIME:" in output:
                init_time = float(output.split("INIT_TIME:")[1].split()[0])
            
            perf_success = "PERF_SUCCESS" in output
            
            # Performance thresholds
            import_threshold = 2.0  # seconds
            init_threshold = 1.0    # seconds
            
            import_ok = import_time <= import_threshold
            init_ok = init_time <= init_threshold
            
            passed = perf_success and import_ok and init_ok
            
            summary = {
                "import_time": import_time,
                "init_time": init_time,
                "import_threshold_met": import_ok,
                "init_threshold_met": init_ok,
                "overall_success": perf_success
            }
            
            details = None
            if not passed:
                issues = []
                if not import_ok:
                    issues.append(f"Import time too slow: {import_time:.3f}s > {import_threshold}s")
                if not init_ok:
                    issues.append(f"Init time too slow: {init_time:.3f}s > {init_threshold}s")
                if not perf_success:
                    issues.append("Performance test execution failed")
                details = f"Performance issues: {', '.join(issues)}"
            
            return ValidationSuite(
                name="Performance Regression",
                passed=passed,
                execution_time=0,
                summary=summary,
                details=details
            )
            
        except subprocess.TimeoutExpired:
            return ValidationSuite(
                name="Performance Regression",
                passed=False,
                execution_time=0,
                summary={"error": "timeout"},
                details="Performance test timed out"
            )
        except Exception as e:
            return ValidationSuite(
                name="Performance Regression",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"Performance test failed: {e}"
            )
    
    def _run_security_audit(self) -> ValidationSuite:
        """Run security audit validation."""
        
        print("  🔒 Running security audit...")
        
        try:
            security_checks = {
                "sensitive_files_protected": True,
                "default_passwords_removed": True,
                "secure_configurations": True,
                "input_validation_present": True
            }
            
            # Check for sensitive files with proper permissions
            sensitive_files = [".env", "config/production.yaml"]
            for file_path in sensitive_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    import stat
                    file_mode = oct(stat.S_IMODE(full_path.stat().st_mode))
                    if file_mode not in ["0o600", "0o644"]:
                        security_checks["sensitive_files_protected"] = False
            
            # Check for default passwords in configuration
            config_files = [".env", "config/production.yaml"]
            for config_file in config_files:
                config_path = self.project_root / config_file
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        content = f.read().lower()
                    
                    if any(pattern in content for pattern in [
                        "your-secret-key-here", "changeme", "admin", "password123"
                    ]):
                        security_checks["default_passwords_removed"] = False
            
            # Check for security configurations
            prod_config = self.project_root / "config/production.yaml"
            if prod_config.exists():
                try:
                    import yaml
                    with open(prod_config, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    security_config = config.get('security', {})
                    if not security_config.get('auth_required', False):
                        security_checks["secure_configurations"] = False
                except Exception:
                    security_checks["secure_configurations"] = False
            
            # Check for input validation patterns in code
            validation_patterns = ['validation', 'sanitize', 'validate_input']
            validation_found = False
            
            try:
                src_files = list((self.project_root / "src").rglob("*.py"))
                for src_file in src_files[:10]:  # Check sample of files
                    with open(src_file, 'r') as f:
                        content = f.read().lower()
                    
                    if any(pattern in content for pattern in validation_patterns):
                        validation_found = True
                        break
                
                security_checks["input_validation_present"] = validation_found
            except Exception:
                security_checks["input_validation_present"] = False
            
            passed = all(security_checks.values())
            
            summary = security_checks
            
            details = None
            if not passed:
                failed_checks = [
                    check for check, result in security_checks.items()
                    if not result
                ]
                details = f"Security audit failed checks: {', '.join(failed_checks)}"
            
            return ValidationSuite(
                name="Security Audit",
                passed=passed,
                execution_time=0,
                summary=summary,
                details=details
            )
            
        except Exception as e:
            return ValidationSuite(
                name="Security Audit",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"Security audit failed: {e}"
            )
    
    def _run_user_acceptance_tests(self) -> ValidationSuite:
        """Run user acceptance testing scenarios."""
        
        print("  👤 Running user acceptance tests...")
        
        try:
            # Define acceptance criteria
            acceptance_tests = {
                "documentation_completeness": True,
                "api_coverage": True,
                "example_validity": True,
                "troubleshooting_coverage": True
            }
            
            # Check documentation completeness
            required_docs = [
                "README.md", "INSTALLATION.md", "API_REFERENCE.md",
                "EXAMPLES.md", "TROUBLESHOOTING.md"
            ]
            
            missing_docs = [
                doc for doc in required_docs
                if not (self.project_root / doc).exists()
            ]
            
            if missing_docs:
                acceptance_tests["documentation_completeness"] = False
            
            # Check API coverage in documentation
            api_ref = self.project_root / "API_REFERENCE.md"
            if api_ref.exists():
                with open(api_ref, 'r') as f:
                    api_content = f.read()
                
                # Check for comprehensive API documentation
                if len(api_content.split()) < 1000:  # Minimum word count
                    acceptance_tests["api_coverage"] = False
            else:
                acceptance_tests["api_coverage"] = False
            
            # Check examples documentation
            examples_doc = self.project_root / "EXAMPLES.md"
            if examples_doc.exists():
                with open(examples_doc, 'r') as f:
                    examples_content = f.read()
                
                # Look for code examples
                if "```" not in examples_content:
                    acceptance_tests["example_validity"] = False
            else:
                acceptance_tests["example_validity"] = False
            
            # Check troubleshooting documentation
            troubleshooting_doc = self.project_root / "TROUBLESHOOTING.md"
            if troubleshooting_doc.exists():
                with open(troubleshooting_doc, 'r') as f:
                    trouble_content = f.read()
                
                # Check for common troubleshooting sections
                required_sections = ["common issues", "error", "solution"]
                if not any(section in trouble_content.lower() for section in required_sections):
                    acceptance_tests["troubleshooting_coverage"] = False
            else:
                acceptance_tests["troubleshooting_coverage"] = False
            
            passed = all(acceptance_tests.values())
            
            summary = {
                **acceptance_tests,
                "missing_documentation": missing_docs
            }
            
            details = None
            if not passed:
                failed_tests = [
                    test for test, result in acceptance_tests.items()
                    if not result
                ]
                details = f"User acceptance criteria not met: {', '.join(failed_tests)}"
            
            return ValidationSuite(
                name="User Acceptance Testing",
                passed=passed,
                execution_time=0,
                summary=summary,
                details=details
            )
            
        except Exception as e:
            return ValidationSuite(
                name="User Acceptance Testing",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"User acceptance testing failed: {e}"
            )
    
    def _test_documentation_procedures(self) -> ValidationSuite:
        """Test all documentation procedures work correctly."""
        
        print("  📚 Testing documentation procedures...")
        
        try:
            procedure_tests = {
                "installation_procedure": True,
                "configuration_procedure": True,
                "deployment_procedure": True,
                "troubleshooting_procedure": True
            }
            
            # Test installation procedure steps
            install_doc = self.project_root / "INSTALLATION.md"
            if install_doc.exists():
                with open(install_doc, 'r') as f:
                    install_content = f.read()
                
                # Check for step-by-step instructions
                step_indicators = ["1.", "step", "install", "run"]
                if not any(indicator in install_content.lower() for indicator in step_indicators):
                    procedure_tests["installation_procedure"] = False
            else:
                procedure_tests["installation_procedure"] = False
            
            # Test configuration procedure
            config_references = [
                "config/production.yaml",
                "DEPLOYMENT.md"
            ]
            
            config_coverage = 0
            for config_ref in config_references:
                if (self.project_root / config_ref).exists():
                    config_coverage += 1
            
            if config_coverage < len(config_references) / 2:
                procedure_tests["configuration_procedure"] = False
            
            # Test deployment procedure
            deploy_doc = self.project_root / "DEPLOYMENT.md"
            if deploy_doc.exists():
                with open(deploy_doc, 'r') as f:
                    deploy_content = f.read()
                
                # Check for deployment steps
                deploy_keywords = ["deploy", "production", "server", "run"]
                if not any(keyword in deploy_content.lower() for keyword in deploy_keywords):
                    procedure_tests["deployment_procedure"] = False
            else:
                procedure_tests["deployment_procedure"] = False
            
            # Test troubleshooting procedure
            trouble_doc = self.project_root / "TROUBLESHOOTING.md"
            if trouble_doc.exists():
                with open(trouble_doc, 'r') as f:
                    trouble_content = f.read()
                
                # Check for solution-oriented content
                solution_keywords = ["solution", "fix", "resolve", "error"]
                if not any(keyword in trouble_content.lower() for keyword in solution_keywords):
                    procedure_tests["troubleshooting_procedure"] = False
            else:
                procedure_tests["troubleshooting_procedure"] = False
            
            passed = all(procedure_tests.values())
            
            summary = procedure_tests
            
            details = None
            if not passed:
                failed_procedures = [
                    proc for proc, result in procedure_tests.items()
                    if not result
                ]
                details = f"Documentation procedures need improvement: {', '.join(failed_procedures)}"
            
            return ValidationSuite(
                name="Documentation Procedures",
                passed=passed,
                execution_time=0,
                summary=summary,
                details=details
            )
            
        except Exception as e:
            return ValidationSuite(
                name="Documentation Procedures",
                passed=False,
                execution_time=0,
                summary={"error": str(e)},
                details=f"Documentation procedure testing failed: {e}"
            )
    
    def _assess_deployment_readiness(self) -> None:
        """Assess overall deployment readiness based on validation results."""
        
        # Calculate success rate
        if self.report.total_suites > 0:
            success_rate = (self.report.passed_suites / self.report.total_suites) * 100
        else:
            success_rate = 0.0
        
        # Identify critical suites
        critical_suites = [
            "Documentation Quality",
            "Deployment Readiness", 
            "Production Readiness",
            "Installation Procedures"
        ]
        
        critical_failures = [
            suite for suite in self.report.suites
            if suite.name in critical_suites and not suite.passed
        ]
        
        # Collect critical issues
        for suite in self.report.suites:
            if not suite.passed and suite.details:
                self.report.critical_issues.append(f"{suite.name}: {suite.details}")
        
        # Generate recommendations
        if critical_failures:
            self.report.recommendations.extend([
                f"Fix critical failure in {suite.name}" for suite in critical_failures
            ])
        
        if success_rate < 90:
            self.report.recommendations.append("Address failed validation suites before deployment")
        
        # Additional recommendations based on specific failures
        for suite in self.report.suites:
            if not suite.passed:
                if suite.name == "Documentation Quality":
                    self.report.recommendations.append("Review and fix documentation issues")
                elif suite.name == "Security Audit":
                    self.report.recommendations.append("Address security configuration issues")
                elif suite.name == "Performance Regression":
                    self.report.recommendations.append("Optimize performance bottlenecks")
        
        # Determine overall status and deployment readiness
        if success_rate >= 95 and not critical_failures:
            self.report.overall_status = "EXCELLENT"
            self.report.deployment_ready = True
        elif success_rate >= 85 and len(critical_failures) <= 1:
            self.report.overall_status = "GOOD"
            self.report.deployment_ready = True
        elif success_rate >= 70:
            self.report.overall_status = "ACCEPTABLE"
            self.report.deployment_ready = False  # Needs improvement
        else:
            self.report.overall_status = "NEEDS_IMPROVEMENT"
            self.report.deployment_ready = False
    
    def _generate_final_report(self) -> None:
        """Generate comprehensive final validation report."""
        
        report_content = f"""# Final Production Validation Report

## Executive Summary

**Validation Timestamp**: {self.report.timestamp}  
**Environment**: {self.report.environment}  
**Overall Status**: {self.report.overall_status}  
**Deployment Ready**: {'✅ YES' if self.report.deployment_ready else '❌ NO'}  
**Total Execution Time**: {self.report.total_execution_time:.2f} seconds

### Summary Statistics
- **Total Validation Suites**: {self.report.total_suites}
- **Passed Suites**: {self.report.passed_suites}
- **Failed Suites**: {self.report.failed_suites}
- **Success Rate**: {(self.report.passed_suites / self.report.total_suites * 100) if self.report.total_suites > 0 else 0:.1f}%

## Validation Suite Results

"""
        
        # Add detailed results for each suite
        for suite in self.report.suites:
            status_icon = "✅" if suite.passed else "❌"
            report_content += f"### {status_icon} {suite.name}\n"
            report_content += f"**Status**: {'PASSED' if suite.passed else 'FAILED'}  \n"
            report_content += f"**Execution Time**: {suite.execution_time:.2f}s  \n"
            
            if suite.details:
                report_content += f"**Details**: {suite.details}  \n"
            
            if suite.summary:
                report_content += f"**Summary**: {json.dumps(suite.summary, indent=2)}  \n"
            
            if suite.report_path:
                report_content += f"**Detailed Report**: {suite.report_path}  \n"
            
            report_content += "\n"
        
        # Add critical issues section
        if self.report.critical_issues:
            report_content += "## Critical Issues\n\n"
            for issue in self.report.critical_issues:
                report_content += f"- ❌ {issue}\n"
            report_content += "\n"
        
        # Add recommendations section
        if self.report.recommendations:
            report_content += "## Recommendations\n\n"
            for rec in self.report.recommendations:
                report_content += f"- 💡 {rec}\n"
            report_content += "\n"
        
        # Add deployment assessment
        report_content += f"""## Deployment Assessment

### Readiness Status: {'✅ READY' if self.report.deployment_ready else '❌ NOT READY'}

"""
        
        if self.report.deployment_ready:
            report_content += """**✅ The system is ready for production deployment.**

### Pre-Deployment Checklist
- [ ] Review all validation results
- [ ] Ensure monitoring is configured
- [ ] Backup current configuration
- [ ] Prepare rollback plan
- [ ] Schedule deployment window
- [ ] Notify stakeholders

### Post-Deployment Actions
- [ ] Verify system health
- [ ] Monitor initial performance
- [ ] Validate all features working
- [ ] Complete smoke tests
- [ ] Document any issues
"""
        else:
            report_content += """**❌ The system requires additional work before production deployment.**

### Required Actions Before Deployment
"""
            for issue in self.report.critical_issues[:5]:  # Top 5 issues
                report_content += f"- [ ] {issue}\n"
            
            report_content += """
### Recommended Steps
1. Address all critical issues listed above
2. Re-run final validation after fixes
3. Ensure all validation suites pass
4. Complete additional testing if needed
5. Review security and performance requirements
"""
        
        # Add technical details
        report_content += f"""
## Technical Details

### Validation Environment
- **Python Version**: {sys.version.split()[0]}
- **Project Root**: {self.project_root}
- **Quick Check Mode**: {self.quick_check}
- **Report Generation**: {self.generate_report}

### Performance Metrics
- **Fastest Suite**: {min(self.report.suites, key=lambda s: s.execution_time).name} ({min(s.execution_time for s in self.report.suites):.2f}s)
- **Slowest Suite**: {max(self.report.suites, key=lambda s: s.execution_time).name} ({max(s.execution_time for s in self.report.suites):.2f}s)
- **Average Suite Time**: {sum(s.execution_time for s in self.report.suites) / len(self.report.suites):.2f}s

### Quality Assurance
This validation report provides comprehensive assessment of:
- Documentation quality and completeness
- Deployment procedure reliability
- Production environment readiness
- Installation and configuration procedures
- End-to-end system functionality
- Performance and security compliance
- User acceptance criteria fulfillment

---
**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Validation Framework**: Keyboard Maestro MCP Final Validator v1.0  
**Contact**: Development Team for questions or issues
"""
        
        # Save final report
        os.makedirs("logs", exist_ok=True)
        report_path = "logs/final_production_validation.md"
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        self.report.report_path = report_path
        print(f"\n📄 Final validation report saved to: {report_path}")
    
    def _print_final_summary(self) -> None:
        """Print final validation summary."""
        
        success_rate = (self.report.passed_suites / self.report.total_suites * 100) if self.report.total_suites > 0 else 0
        
        print("\n" + "=" * 70)
        print("🏁 FINAL VALIDATION COMPLETE")
        print("=" * 70)
        
        print(f"📊 Overall Status: {self.report.overall_status}")
        print(f"🚀 Deployment Ready: {'✅ YES' if self.report.deployment_ready else '❌ NO'}")
        print(f"⏱️  Total Time: {self.report.total_execution_time:.2f}s")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Suite Results:")
        print(f"  ✅ Passed: {self.report.passed_suites}")
        print(f"  ❌ Failed: {self.report.failed_suites}")
        print(f"  📊 Total: {self.report.total_suites}")
        
        if self.report.critical_issues:
            print(f"\n🚨 Critical Issues ({len(self.report.critical_issues)}):")
            for issue in self.report.critical_issues[:3]:  # Show top 3
                print(f"  - {issue}")
            if len(self.report.critical_issues) > 3:
                print(f"  ... and {len(self.report.critical_issues) - 3} more")
        
        if self.report.recommendations:
            print(f"\n💡 Key Recommendations:")
            for rec in self.report.recommendations[:3]:  # Show top 3
                print(f"  - {rec}")
        
        print(f"\n📄 Detailed Report: {getattr(self.report, 'report_path', 'Not generated')}")
        print("=" * 70)


def main():
    """Main entry point for final validation."""
    
    parser = argparse.ArgumentParser(description="Final production validation")
    parser.add_argument("--quick-check", action="store_true",
                       help="Run essential validation checks only")
    parser.add_argument("--no-report", action="store_true",
                       help="Skip detailed report generation")
    
    args = parser.parse_args()
    
    # Initialize and run final validator
    validator = FinalValidator(
        quick_check=args.quick_check,
        generate_report=not args.no_report
    )
    
    report = validator.run_comprehensive_validation()
    
    # Exit with appropriate code
    if report.deployment_ready:
        sys.exit(0)  # Ready for deployment
    elif report.overall_status in ["GOOD", "ACCEPTABLE"]:
        sys.exit(1)  # Needs minor fixes
    else:
        sys.exit(2)  # Major issues need resolution


if __name__ == "__main__":
    main()
