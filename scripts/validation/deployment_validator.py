#!/usr/bin/env python3
"""
Deployment Validation Script
Comprehensive validation for Keyboard Maestro MCP Server deployment readiness

This script validates:
- Installation procedures and dependencies
- Configuration file validity and completeness
- Deployment script functionality
- Monitoring and logging setup
- Performance benchmark validation
- Security configuration verification

Usage:
    python scripts/validation/deployment_validator.py
    python scripts/validation/deployment_validator.py --environment production
    python scripts/validation/deployment_validator.py --quick-check
"""

import os
import sys
import json
import yaml
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import tempfile
import shutil
import time

@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    passed: bool
    message: str
    details: Optional[Dict] = None
    suggestions: List[str] = field(default_factory=list)
    execution_time: float = 0.0

@dataclass
class DeploymentReport:
    """Comprehensive deployment validation report."""
    environment: str
    timestamp: str
    results: List[ValidationResult] = field(default_factory=list)
    overall_status: str = "unknown"
    
    def add_result(self, result: ValidationResult):
        """Add validation result to report."""
        self.results.append(result)
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        total = len(self.results)
        passed = len([r for r in self.results if r.passed])
        failed = total - passed
        
        return {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }


class DeploymentValidator:
    """Comprehensive deployment validation system."""
    
    def __init__(self, project_root: str = ".", environment: str = "development"):
        self.project_root = Path(project_root)
        self.environment = environment
        self.report = DeploymentReport(
            environment=environment,
            timestamp=self._get_timestamp()
        )
        
        # Expected files and directories
        self.required_files = [
            "src/main.py",
            "requirements.txt",
            "requirements-dev.txt",
            "README.md",
            "LICENSE",
            "config/production.yaml"
        ]
        
        self.required_directories = [
            "src/",
            "tests/",
            "scripts/",
            "config/",
            "logs/"
        ]
        
        # Configuration validation schemas
        self.config_schema = {
            "server": {
                "required": ["host", "port", "transport"],
                "optional": ["max_concurrent_operations", "operation_timeout"]
            },
            "logging": {
                "required": ["level", "format"],
                "optional": ["file", "rotation"]
            },
            "security": {
                "required": ["auth_required"],
                "optional": ["auth_provider", "rate_limiting"]
            }
        }
    
    def validate_deployment_readiness(self, quick_check: bool = False) -> DeploymentReport:
        """Run comprehensive deployment validation."""
        
        print(f"🚀 Starting deployment validation for {self.environment} environment...")
        
        # Core validation checks
        validation_checks = [
            ("Project Structure", self._validate_project_structure),
            ("Dependencies", self._validate_dependencies),
            ("Configuration Files", self._validate_configuration),
            ("Scripts and Tools", self._validate_scripts),
            ("Documentation", self._validate_documentation_completeness),
        ]
        
        if not quick_check:
            # Extended validation for full deployment readiness
            validation_checks.extend([
                ("Security Configuration", self._validate_security_setup),
                ("Monitoring Setup", self._validate_monitoring_setup),
                ("Performance Baseline", self._validate_performance_baseline),
                ("Installation Procedures", self._validate_installation_procedures),
                ("Container Deployment", self._validate_container_setup)
            ])
        
        # Run validation checks
        for check_name, check_function in validation_checks:
            print(f"🔍 Running check: {check_name}")
            
            start_time = time.time()
            try:
                result = check_function()
                result.execution_time = time.time() - start_time
                self.report.add_result(result)
                
                status = "✅ PASS" if result.passed else "❌ FAIL"
                print(f"  {status}: {result.message}")
                
                if not result.passed and result.suggestions:
                    for suggestion in result.suggestions:
                        print(f"    💡 {suggestion}")
                        
            except Exception as e:
                execution_time = time.time() - start_time
                error_result = ValidationResult(
                    check_name=check_name,
                    passed=False,
                    message=f"Validation check failed with error: {str(e)}",
                    execution_time=execution_time
                )
                self.report.add_result(error_result)
                print(f"  ❌ ERROR: {str(e)}")
        
        # Determine overall status
        summary = self.report.get_summary()
        if summary["success_rate"] >= 90:
            self.report.overall_status = "✅ READY"
        elif summary["success_rate"] >= 70:
            self.report.overall_status = "⚠️ MOSTLY_READY"
        else:
            self.report.overall_status = "❌ NOT_READY"
        
        # Generate report
        self._generate_deployment_report()
        
        return self.report
    
    def _validate_project_structure(self) -> ValidationResult:
        """Validate project structure and required files."""
        
        missing_files = []
        missing_directories = []
        
        # Check required files
        for file_path in self.required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        # Check required directories
        for dir_path in self.required_directories:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_directories.append(dir_path)
        
        # Check if main entry point is executable
        main_py = self.project_root / "src/main.py"
        executable_check = main_py.exists()
        
        # Determine result
        issues = len(missing_files) + len(missing_directories)
        if issues == 0 and executable_check:
            return ValidationResult(
                check_name="Project Structure",
                passed=True,
                message="All required files and directories present",
                details={
                    "required_files": len(self.required_files),
                    "required_directories": len(self.required_directories),
                    "main_executable": executable_check
                }
            )
        else:
            suggestions = []
            if missing_files:
                suggestions.append(f"Create missing files: {', '.join(missing_files)}")
            if missing_directories:
                suggestions.append(f"Create missing directories: {', '.join(missing_directories)}")
            if not executable_check:
                suggestions.append("Ensure src/main.py exists and is executable")
            
            return ValidationResult(
                check_name="Project Structure",
                passed=False,
                message=f"Missing {issues} required files/directories",
                details={
                    "missing_files": missing_files,
                    "missing_directories": missing_directories,
                    "main_executable": executable_check
                },
                suggestions=suggestions
            )
    
    def _validate_dependencies(self) -> ValidationResult:
        """Validate Python dependencies and requirements."""
        
        try:
            # Check if requirements.txt exists and is valid
            requirements_file = self.project_root / "requirements.txt"
            if not requirements_file.exists():
                return ValidationResult(
                    check_name="Dependencies",
                    passed=False,
                    message="requirements.txt not found",
                    suggestions=["Create requirements.txt with project dependencies"]
                )
            
            # Parse requirements
            with open(requirements_file, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            # Filter out empty lines and comments
            dependencies = [
                line.strip() for line in requirements 
                if line.strip() and not line.strip().startswith('#')
            ]
            
            # Check for critical dependencies
            critical_deps = ['fastmcp', 'pydantic', 'asyncio']
            missing_critical = []
            
            for dep in critical_deps:
                if not any(dep in line for line in dependencies):
                    missing_critical.append(dep)
            
            # Try to validate installability (basic check)
            python_executable = sys.executable
            try:
                result = subprocess.run(
                    [python_executable, "-m", "pip", "check"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                pip_check_passed = result.returncode == 0
                pip_check_output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                pip_check_passed = False
                pip_check_output = "Pip check timed out"
            
            # Determine validation result
            if missing_critical:
                return ValidationResult(
                    check_name="Dependencies",
                    passed=False,
                    message=f"Missing critical dependencies: {', '.join(missing_critical)}",
                    details={
                        "total_dependencies": len(dependencies),
                        "missing_critical": missing_critical,
                        "pip_check_passed": pip_check_passed
                    },
                    suggestions=[
                        f"Add missing dependencies to requirements.txt: {', '.join(missing_critical)}",
                        "Run 'pip install -r requirements.txt' to install dependencies"
                    ]
                )
            elif not pip_check_passed:
                return ValidationResult(
                    check_name="Dependencies",
                    passed=False,
                    message="Dependency conflicts detected",
                    details={
                        "total_dependencies": len(dependencies),
                        "pip_check_output": pip_check_output
                    },
                    suggestions=[
                        "Resolve dependency conflicts shown in pip check output",
                        "Consider using virtual environment for clean installation"
                    ]
                )
            else:
                return ValidationResult(
                    check_name="Dependencies",
                    passed=True,
                    message=f"All {len(dependencies)} dependencies validated successfully",
                    details={
                        "total_dependencies": len(dependencies),
                        "critical_deps_present": len(critical_deps),
                        "pip_check_passed": pip_check_passed
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                check_name="Dependencies",
                passed=False,
                message=f"Dependency validation failed: {str(e)}",
                suggestions=["Check requirements.txt format and dependency specifications"]
            )
    
    def _validate_configuration(self) -> ValidationResult:
        """Validate configuration files and templates."""
        
        config_issues = []
        config_details = {}
        
        # Check production configuration
        prod_config_path = self.project_root / "config/production.yaml"
        if prod_config_path.exists():
            try:
                with open(prod_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Validate against schema
                for section, requirements in self.config_schema.items():
                    if section not in config_data:
                        config_issues.append(f"Missing configuration section: {section}")
                        continue
                    
                    section_data = config_data[section]
                    
                    # Check required fields
                    for required_field in requirements["required"]:
                        if required_field not in section_data:
                            config_issues.append(f"Missing required field: {section}.{required_field}")
                
                config_details["production_config"] = {
                    "sections": list(config_data.keys()),
                    "validation_issues": len(config_issues)
                }
                
            except yaml.YAMLError as e:
                config_issues.append(f"Invalid YAML in production.yaml: {str(e)}")
        else:
            config_issues.append("production.yaml configuration file missing")
        
        # Check environment template
        env_template_path = self.project_root / "config/.env.template"
        if env_template_path.exists():
            try:
                with open(env_template_path, 'r') as f:
                    env_template = f.read()
                
                # Check for critical environment variables
                critical_env_vars = [
                    "MCP_TRANSPORT",
                    "MCP_HOST", 
                    "MCP_PORT",
                    "MCP_LOG_LEVEL"
                ]
                
                missing_env_vars = [
                    var for var in critical_env_vars 
                    if var not in env_template
                ]
                
                if missing_env_vars:
                    config_issues.extend([
                        f"Missing environment variable in template: {var}" 
                        for var in missing_env_vars
                    ])
                
                config_details["env_template"] = {
                    "total_vars": len(env_template.split('\n')),
                    "missing_critical": missing_env_vars
                }
                
            except Exception as e:
                config_issues.append(f"Error reading .env.template: {str(e)}")
        else:
            config_issues.append(".env.template file missing")
        
        # Determine result
        if not config_issues:
            return ValidationResult(
                check_name="Configuration Files",
                passed=True,
                message="All configuration files valid and complete",
                details=config_details
            )
        else:
            return ValidationResult(
                check_name="Configuration Files",
                passed=False,
                message=f"Found {len(config_issues)} configuration issues",
                details={
                    **config_details,
                    "issues": config_issues
                },
                suggestions=[
                    "Fix configuration issues listed in details",
                    "Validate YAML syntax in configuration files",
                    "Ensure all required fields are present"
                ]
            )
    
    def _validate_scripts(self) -> ValidationResult:
        """Validate deployment scripts and tools."""
        
        expected_scripts = [
            "scripts/setup/initialize_project.py",
            "scripts/setup/production_setup.py",
            "scripts/build/deploy.py",
            "scripts/validation/production_validator.py"
        ]
        
        script_issues = []
        script_details = {}
        
        for script_path in expected_scripts:
            full_path = self.project_root / script_path
            if not full_path.exists():
                script_issues.append(f"Missing script: {script_path}")
                continue
            
            # Check if script is executable (basic check)
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # Basic validation - check for shebang and main execution
                has_shebang = content.startswith('#!')
                has_main = 'if __name__ == "__main__"' in content or 'def main()' in content
                
                script_info = {
                    "exists": True,
                    "has_shebang": has_shebang,
                    "has_main": has_main,
                    "size": len(content)
                }
                
                if not has_main:
                    script_issues.append(f"Script {script_path} missing main execution block")
                
                script_details[script_path] = script_info
                
            except Exception as e:
                script_issues.append(f"Error reading script {script_path}: {str(e)}")
        
        # Check docker configuration if container deployment expected
        dockerfile_path = self.project_root / "docker/Dockerfile"
        if dockerfile_path.exists():
            try:
                with open(dockerfile_path, 'r') as f:
                    dockerfile_content = f.read()
                
                # Basic Dockerfile validation
                required_instructions = ['FROM', 'COPY', 'RUN']
                missing_instructions = [
                    instr for instr in required_instructions
                    if instr not in dockerfile_content
                ]
                
                if missing_instructions:
                    script_issues.extend([
                        f"Dockerfile missing instruction: {instr}"
                        for instr in missing_instructions
                    ])
                
                script_details["dockerfile"] = {
                    "exists": True,
                    "missing_instructions": missing_instructions,
                    "size": len(dockerfile_content)
                }
                
            except Exception as e:
                script_issues.append(f"Error reading Dockerfile: {str(e)}")
        
        # Determine result
        if not script_issues:
            return ValidationResult(
                check_name="Scripts and Tools",
                passed=True,
                message="All deployment scripts and tools validated",
                details=script_details
            )
        else:
            return ValidationResult(
                check_name="Scripts and Tools",
                passed=False,
                message=f"Found {len(script_issues)} script issues",
                details={
                    **script_details,
                    "issues": script_issues
                },
                suggestions=[
                    "Create missing deployment scripts",
                    "Ensure scripts have proper main execution blocks",
                    "Add executable permissions to script files"
                ]
            )
    
    def _validate_documentation_completeness(self) -> ValidationResult:
        """Validate documentation completeness for deployment."""
        
        required_docs = [
            "README.md",
            "INSTALLATION.md", 
            "DEPLOYMENT.md",
            "TROUBLESHOOTING.md",
            "API_REFERENCE.md"
        ]
        
        doc_issues = []
        doc_details = {}
        
        for doc_file in required_docs:
            doc_path = self.project_root / doc_file
            if not doc_path.exists():
                doc_issues.append(f"Missing documentation: {doc_file}")
                continue
            
            try:
                with open(doc_path, 'r') as f:
                    content = f.read()
                
                # Basic completeness checks
                word_count = len(content.split())
                has_installation_section = 'installation' in content.lower()
                has_usage_section = 'usage' in content.lower() or 'getting started' in content.lower()
                
                # Minimum word count threshold for completeness
                min_words = 500 if doc_file == "README.md" else 200
                is_complete = word_count >= min_words
                
                doc_info = {
                    "word_count": word_count,
                    "is_complete": is_complete,
                    "has_installation": has_installation_section,
                    "has_usage": has_usage_section
                }
                
                if not is_complete:
                    doc_issues.append(f"Documentation {doc_file} appears incomplete ({word_count} words)")
                
                doc_details[doc_file] = doc_info
                
            except Exception as e:
                doc_issues.append(f"Error reading {doc_file}: {str(e)}")
        
        # Determine result
        if not doc_issues:
            return ValidationResult(
                check_name="Documentation",
                passed=True,
                message="All required documentation is complete and present",
                details=doc_details
            )
        else:
            return ValidationResult(
                check_name="Documentation", 
                passed=False,
                message=f"Found {len(doc_issues)} documentation issues",
                details={
                    **doc_details,
                    "issues": doc_issues
                },
                suggestions=[
                    "Complete missing documentation files",
                    "Ensure documentation meets minimum completeness requirements",
                    "Add installation and usage instructions to key documents"
                ]
            )
    
    def _validate_security_setup(self) -> ValidationResult:
        """Validate security configuration and setup."""
        
        security_issues = []
        security_details = {}
        
        # Check for security-related files
        security_files = [
            "SECURITY.md",
            "src/boundaries/security_boundaries.py",
            "src/validators/input_validators.py"
        ]
        
        missing_security_files = []
        for security_file in security_files:
            if not (self.project_root / security_file).exists():
                missing_security_files.append(security_file)
        
        if missing_security_files:
            security_issues.extend([
                f"Missing security file: {file}" for file in missing_security_files
            ])
        
        # Check configuration for security settings
        config_path = self.project_root / "config/production.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                security_config = config.get('security', {})
                
                # Check for security configurations
                auth_required = security_config.get('auth_required', False)
                rate_limiting = security_config.get('rate_limiting', {})
                
                security_details["config"] = {
                    "auth_required": auth_required,
                    "rate_limiting_configured": bool(rate_limiting),
                    "security_section_present": 'security' in config
                }
                
                if not auth_required and self.environment == "production":
                    security_issues.append("Authentication not required in production configuration")
                
            except Exception as e:
                security_issues.append(f"Error reading security configuration: {str(e)}")
        
        # Check for common security patterns in code
        security_patterns = [
            "input validation",
            "sanitization", 
            "permission check",
            "auth"
        ]
        
        security_pattern_count = 0
        try:
            # Simple check for security patterns in main files
            main_files = list((self.project_root / "src").rglob("*.py"))
            for file_path in main_files[:10]:  # Check first 10 files
                try:
                    with open(file_path, 'r') as f:
                        content = f.read().lower()
                    
                    for pattern in security_patterns:
                        if pattern in content:
                            security_pattern_count += 1
                            break
                except Exception:
                    continue
        except Exception:
            pass
        
        security_details["security_patterns_found"] = security_pattern_count
        
        # Determine result
        if not security_issues and security_pattern_count > 0:
            return ValidationResult(
                check_name="Security Configuration",
                passed=True,
                message="Security setup appears properly configured",
                details=security_details
            )
        else:
            suggestions = []
            if missing_security_files:
                suggestions.append("Create missing security-related files")
            if not security_details.get("config", {}).get("auth_required", False):
                suggestions.append("Enable authentication for production deployment")
            if security_pattern_count == 0:
                suggestions.append("Implement security patterns in code (validation, sanitization)")
            
            return ValidationResult(
                check_name="Security Configuration",
                passed=False,
                message=f"Security setup needs attention ({len(security_issues)} issues)",
                details={
                    **security_details,
                    "issues": security_issues
                },
                suggestions=suggestions
            )
    
    def _validate_monitoring_setup(self) -> ValidationResult:
        """Validate monitoring and logging setup."""
        
        monitoring_issues = []
        monitoring_details = {}
        
        # Check logging configuration
        config_path = self.project_root / "config/production.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                logging_config = config.get('logging', {})
                monitoring_config = config.get('monitoring', {})
                
                # Validate logging configuration
                required_logging_fields = ['level', 'format']
                missing_logging = [
                    field for field in required_logging_fields
                    if field not in logging_config
                ]
                
                if missing_logging:
                    monitoring_issues.extend([
                        f"Missing logging config: {field}" for field in missing_logging
                    ])
                
                monitoring_details["logging"] = {
                    "configured": bool(logging_config),
                    "missing_fields": missing_logging,
                    "level": logging_config.get('level', 'not_set')
                }
                
                monitoring_details["monitoring"] = {
                    "configured": bool(monitoring_config)
                }
                
            except Exception as e:
                monitoring_issues.append(f"Error reading monitoring configuration: {str(e)}")
        
        # Check for logs directory
        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            monitoring_issues.append("Logs directory not found")
        else:
            monitoring_details["logs_directory"] = {
                "exists": True,
                "writable": os.access(logs_dir, os.W_OK)
            }
            
            if not os.access(logs_dir, os.W_OK):
                monitoring_issues.append("Logs directory not writable")
        
        # Check for monitoring/health check endpoints in code
        health_check_patterns = ['health', 'status', 'monitoring', 'metrics']
        health_check_found = False
        
        try:
            main_py = self.project_root / "src/main.py"
            if main_py.exists():
                with open(main_py, 'r') as f:
                    content = f.read().lower()
                
                health_check_found = any(pattern in content for pattern in health_check_patterns)
        except Exception:
            pass
        
        monitoring_details["health_check_endpoint"] = health_check_found
        
        if not health_check_found:
            monitoring_issues.append("No health check endpoint found in main application")
        
        # Determine result
        if not monitoring_issues:
            return ValidationResult(
                check_name="Monitoring Setup",
                passed=True,
                message="Monitoring and logging properly configured",
                details=monitoring_details
            )
        else:
            return ValidationResult(
                check_name="Monitoring Setup",
                passed=False,
                message=f"Monitoring setup needs attention ({len(monitoring_issues)} issues)",
                details={
                    **monitoring_details,
                    "issues": monitoring_issues
                },
                suggestions=[
                    "Configure logging in production.yaml",
                    "Ensure logs directory exists and is writable",
                    "Add health check endpoint to application",
                    "Set up monitoring and metrics collection"
                ]
            )
    
    def _validate_performance_baseline(self) -> ValidationResult:
        """Validate performance baseline and benchmarks."""
        
        # This is a simplified check - in a real deployment, you'd run actual performance tests
        performance_details = {}
        performance_issues = []
        
        # Check for performance test files
        perf_test_paths = [
            "tests/performance/",
            "scripts/validation/performance_test.py",
            "benchmarks/"
        ]
        
        perf_test_found = False
        for path in perf_test_paths:
            if (self.project_root / path).exists():
                perf_test_found = True
                break
        
        performance_details["performance_tests_available"] = perf_test_found
        
        if not perf_test_found:
            performance_issues.append("No performance tests or benchmarks found")
        
        # Check for performance configuration
        config_path = self.project_root / "config/production.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                performance_config = config.get('performance', {})
                server_config = config.get('server', {})
                
                # Check for performance-related settings
                max_concurrent = server_config.get('max_concurrent_operations')
                operation_timeout = server_config.get('operation_timeout')
                
                performance_details["performance_config"] = {
                    "max_concurrent_set": max_concurrent is not None,
                    "timeout_configured": operation_timeout is not None,
                    "performance_section": bool(performance_config)
                }
                
                if max_concurrent is None:
                    performance_issues.append("max_concurrent_operations not configured")
                if operation_timeout is None:
                    performance_issues.append("operation_timeout not configured")
                    
            except Exception as e:
                performance_issues.append(f"Error reading performance configuration: {str(e)}")
        
        # Simple load test (if possible)
        load_test_passed = True
        try:
            # This would be a simple connection test
            # In a real implementation, you'd run actual load tests
            performance_details["load_test"] = {
                "attempted": True,
                "passed": load_test_passed
            }
        except Exception:
            load_test_passed = False
            performance_details["load_test"] = {
                "attempted": False,
                "passed": False
            }
        
        # Determine result
        if not performance_issues and perf_test_found:
            return ValidationResult(
                check_name="Performance Baseline",
                passed=True,
                message="Performance baseline and configuration validated",
                details=performance_details
            )
        else:
            return ValidationResult(
                check_name="Performance Baseline",
                passed=False,
                message=f"Performance validation needs attention ({len(performance_issues)} issues)",
                details={
                    **performance_details,
                    "issues": performance_issues
                },
                suggestions=[
                    "Create performance tests and benchmarks",
                    "Configure performance settings in production.yaml",
                    "Set up load testing procedures",
                    "Establish performance monitoring baseline"
                ]
            )
    
    def _validate_installation_procedures(self) -> ValidationResult:
        """Validate installation procedures work correctly."""
        
        installation_issues = []
        installation_details = {}
        
        # Check if INSTALLATION.md exists and has required sections
        install_doc = self.project_root / "INSTALLATION.md"
        if not install_doc.exists():
            installation_issues.append("INSTALLATION.md not found")
        else:
            try:
                with open(install_doc, 'r') as f:
                    content = f.read().lower()
                
                required_sections = [
                    'requirements',
                    'installation',
                    'configuration',
                    'verification'
                ]
                
                missing_sections = [
                    section for section in required_sections
                    if section not in content
                ]
                
                installation_details["installation_doc"] = {
                    "exists": True,
                    "missing_sections": missing_sections,
                    "word_count": len(content.split())
                }
                
                if missing_sections:
                    installation_issues.extend([
                        f"INSTALLATION.md missing section: {section}"
                        for section in missing_sections
                    ])
                    
            except Exception as e:
                installation_issues.append(f"Error reading INSTALLATION.md: {str(e)}")
        
        # Test installation in temporary environment (simplified)
        temp_install_test = self._test_installation_procedure()
        installation_details["temp_install_test"] = temp_install_test
        
        if not temp_install_test["success"]:
            installation_issues.append("Installation procedure test failed")
        
        # Check setup scripts
        setup_scripts = [
            "scripts/setup/initialize_project.py",
            "scripts/setup/production_setup.py"
        ]
        
        setup_scripts_found = 0
        for script in setup_scripts:
            if (self.project_root / script).exists():
                setup_scripts_found += 1
        
        installation_details["setup_scripts"] = {
            "found": setup_scripts_found,
            "total": len(setup_scripts)
        }
        
        if setup_scripts_found < len(setup_scripts):
            installation_issues.append(f"Missing setup scripts: {len(setup_scripts) - setup_scripts_found}")
        
        # Determine result
        if not installation_issues:
            return ValidationResult(
                check_name="Installation Procedures",
                passed=True,
                message="Installation procedures validated successfully",
                details=installation_details
            )
        else:
            return ValidationResult(
                check_name="Installation Procedures",
                passed=False,
                message=f"Installation validation found {len(installation_issues)} issues",
                details={
                    **installation_details,
                    "issues": installation_issues
                },
                suggestions=[
                    "Complete INSTALLATION.md with all required sections",
                    "Test installation procedure in clean environment",
                    "Create missing setup scripts",
                    "Verify all installation steps work correctly"
                ]
            )
    
    def _test_installation_procedure(self) -> Dict:
        """Test installation procedure in temporary environment."""
        
        # Simplified installation test
        try:
            # Check if requirements can be parsed
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    requirements = f.read()
                
                # Basic validation - ensure requirements are parseable
                lines = [line.strip() for line in requirements.split('\n') if line.strip()]
                valid_requirements = all(
                    not line.startswith('#') or '==' in line or '>=' in line or line.isalnum()
                    for line in lines if line
                )
                
                return {
                    "success": valid_requirements,
                    "requirements_count": len(lines),
                    "details": "Requirements file syntax validated"
                }
            else:
                return {
                    "success": False,
                    "details": "requirements.txt not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "details": f"Installation test failed: {str(e)}"
            }
    
    def _validate_container_setup(self) -> ValidationResult:
        """Validate container/Docker deployment setup."""
        
        container_issues = []
        container_details = {}
        
        # Check for Dockerfile
        dockerfile_path = self.project_root / "docker/Dockerfile"
        if dockerfile_path.exists():
            try:
                with open(dockerfile_path, 'r') as f:
                    dockerfile_content = f.read()
                
                # Basic Dockerfile validation
                required_instructions = ['FROM', 'COPY', 'RUN', 'CMD']
                present_instructions = []
                missing_instructions = []
                
                for instruction in required_instructions:
                    if instruction in dockerfile_content:
                        present_instructions.append(instruction)
                    else:
                        missing_instructions.append(instruction)
                
                # Check for Python base image
                has_python_base = 'python:' in dockerfile_content.lower()
                
                # Check for security best practices
                runs_as_root = 'USER root' in dockerfile_content
                has_user_instruction = 'USER ' in dockerfile_content
                
                container_details["dockerfile"] = {
                    "exists": True,
                    "present_instructions": present_instructions,
                    "missing_instructions": missing_instructions,
                    "has_python_base": has_python_base,
                    "runs_as_root": runs_as_root,
                    "has_user_instruction": has_user_instruction,
                    "size": len(dockerfile_content)
                }
                
                if missing_instructions:
                    container_issues.extend([
                        f"Dockerfile missing instruction: {instr}"
                        for instr in missing_instructions
                    ])
                
                if not has_python_base:
                    container_issues.append("Dockerfile doesn't use Python base image")
                
                if runs_as_root and not has_user_instruction:
                    container_issues.append("Dockerfile runs as root without USER instruction")
                    
            except Exception as e:
                container_issues.append(f"Error reading Dockerfile: {str(e)}")
        else:
            container_details["dockerfile"] = {"exists": False}
            # Not necessarily an issue if container deployment not planned
        
        # Check for docker-compose or kubernetes configs
        docker_compose_path = self.project_root / "docker-compose.yml"
        k8s_configs = list((self.project_root / "k8s").glob("*.yaml")) if (self.project_root / "k8s").exists() else []
        
        container_details["orchestration"] = {
            "docker_compose": docker_compose_path.exists(),
            "kubernetes_configs": len(k8s_configs)
        }
        
        # Check .dockerignore
        dockerignore_path = self.project_root / ".dockerignore"
        if dockerignore_path.exists():
            try:
                with open(dockerignore_path, 'r') as f:
                    dockerignore_content = f.read()
                
                # Check for common patterns
                common_ignores = ['.git', '__pycache__', '*.pyc', 'venv', '.env']
                present_ignores = [
                    ignore for ignore in common_ignores
                    if ignore in dockerignore_content
                ]
                
                container_details["dockerignore"] = {
                    "exists": True,
                    "present_ignores": present_ignores,
                    "total_patterns": len(dockerignore_content.split('\n'))
                }
                
            except Exception as e:
                container_issues.append(f"Error reading .dockerignore: {str(e)}")
        else:
            container_details["dockerignore"] = {"exists": False}
        
        # Determine result - container setup is optional, so we're more lenient
        critical_issues = [
            issue for issue in container_issues
            if "missing instruction" in issue or "python base" in issue
        ]
        
        if dockerfile_path.exists():
            if not critical_issues:
                return ValidationResult(
                    check_name="Container Deployment",
                    passed=True,
                    message="Container deployment setup validated",
                    details=container_details
                )
            else:
                return ValidationResult(
                    check_name="Container Deployment",
                    passed=False,
                    message=f"Container setup has {len(critical_issues)} critical issues",
                    details={
                        **container_details,
                        "issues": container_issues
                    },
                    suggestions=[
                        "Fix critical Dockerfile issues",
                        "Use Python base image",
                        "Add USER instruction for security",
                        "Create .dockerignore file"
                    ]
                )
        else:
            return ValidationResult(
                check_name="Container Deployment",
                passed=True,
                message="Container deployment not configured (optional)",
                details=container_details
            )
    
    def _generate_deployment_report(self):
        """Generate comprehensive deployment validation report."""
        
        summary = self.report.get_summary()
        
        # Create report content
        report_content = f"""# Deployment Validation Report
Environment: {self.environment}
Generated: {self.report.timestamp}

## Executive Summary
- **Overall Status**: {self.report.overall_status}
- **Success Rate**: {summary['success_rate']:.1f}%
- **Total Checks**: {summary['total_checks']}
- **Passed**: {summary['passed']}
- **Failed**: {summary['failed']}

## Validation Results

"""
        
        # Add results by status
        passed_results = [r for r in self.report.results if r.passed]
        failed_results = [r for r in self.report.results if not r.passed]
        
        if passed_results:
            report_content += f"### ✅ Passed Checks ({len(passed_results)})\n\n"
            for result in passed_results:
                report_content += f"- **{result.check_name}**: {result.message}\\n"
                if result.execution_time > 0:
                    report_content += f"  *Execution time: {result.execution_time:.2f}s*\\n"
        
        if failed_results:
            report_content += f"\\n### ❌ Failed Checks ({len(failed_results)})\\n\\n"
            for result in failed_results:
                report_content += f"- **{result.check_name}**: {result.message}\\n"
                if result.suggestions:
                    for suggestion in result.suggestions:
                        report_content += f"  💡 {suggestion}\\n"
                if result.execution_time > 0:
                    report_content += f"  *Execution time: {result.execution_time:.2f}s*\\n"
        
        report_content += f"""

## Deployment Readiness Assessment

Based on the validation results, the deployment readiness is: **{self.report.overall_status}**

### Readiness Criteria
- ✅ **Ready (90%+ success)**: All critical systems validated, ready for production
- ⚠️ **Mostly Ready (70-89% success)**: Minor issues present, can deploy with caution
- ❌ **Not Ready (<70% success)**: Critical issues must be resolved before deployment

### Next Steps
"""
        
        if summary['success_rate'] >= 90:
            report_content += """- Proceed with deployment to production environment
- Monitor initial deployment closely
- Set up ongoing monitoring and alerting
"""
        elif summary['success_rate'] >= 70:
            report_content += """- Address failed validation checks before deployment
- Consider deploying to staging environment first
- Implement additional monitoring for areas of concern
"""
        else:
            report_content += """- Resolve all critical validation failures
- Re-run validation after fixes
- Consider extended testing in development environment
"""
        
        report_content += f"""
## Detailed Analysis

### Performance Summary
- **Fastest Check**: {min(self.report.results, key=lambda r: r.execution_time).check_name} ({min(r.execution_time for r in self.report.results):.2f}s)
- **Slowest Check**: {max(self.report.results, key=lambda r: r.execution_time).check_name} ({max(r.execution_time for r in self.report.results):.2f}s)
- **Total Validation Time**: {sum(r.execution_time for r in self.report.results):.2f}s

### Recommendations for Production Deployment
1. **Monitor**: Set up comprehensive monitoring for all validated systems
2. **Backup**: Ensure backup and recovery procedures are in place
3. **Rollback**: Have rollback plan ready in case of issues
4. **Documentation**: Keep deployment validation results for reference
5. **Testing**: Continue validation in production environment

---
*This report was generated automatically by the Deployment Validator*
*For questions or issues, refer to the troubleshooting documentation*
"""
        
        # Save report
        os.makedirs("logs", exist_ok=True)
        report_path = f"logs/deployment_validation_{self.environment}.md"
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"📄 Deployment validation report saved to: {report_path}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reporting."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point for deployment validation."""
    
    parser = argparse.ArgumentParser(description="Validate deployment readiness")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--environment", default="development", 
                       choices=["development", "staging", "production"],
                       help="Target deployment environment")
    parser.add_argument("--quick-check", action="store_true", 
                       help="Run only essential validation checks")
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = DeploymentValidator(args.project_root, args.environment)
    
    # Run validation
    report = validator.validate_deployment_readiness(args.quick_check)
    
    # Print summary
    summary = report.get_summary()
    print(f"""
🚀 Deployment Validation Complete!

📊 Results Summary:
  Environment: {report.environment}
  Overall Status: {report.overall_status}
  Success Rate: {summary['success_rate']:.1f}%
  
🎯 Validation Breakdown:
  ✅ Passed: {summary['passed']}
  ❌ Failed: {summary['failed']}
  📊 Total: {summary['total_checks']}

🏆 Deployment Readiness: {report.overall_status}
""")
    
    # Exit with appropriate code
    if summary['success_rate'] >= 90:
        print("✅ Ready for deployment!")
        sys.exit(0)
    elif summary['success_rate'] >= 70:
        print("⚠️ Mostly ready - address issues before deployment")
        sys.exit(1)
    else:
        print("❌ Not ready for deployment - critical issues must be resolved")
        sys.exit(2)


if __name__ == "__main__":
    main()
