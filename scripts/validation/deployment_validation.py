#!/usr/bin/env python3
"""
Comprehensive Deployment Validation Suite for Keyboard Maestro MCP Server.

This script systematically validates all deployment components including:
- Installation procedures testing
- Configuration validation  
- Deployment script verification
- Monitoring and logging setup testing
- Performance benchmark validation

Usage:
    python scripts/validation/deployment_validation.py --comprehensive
"""

import asyncio
import json
import os
import sys
import subprocess
import tempfile
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.contracts.decorators import requires, ensures


class TestResult(Enum):
    """Test result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIP = "SKIP"


@dataclass
class DeploymentTest:
    """Individual deployment test result."""
    name: str
    category: str
    status: TestResult
    message: str
    details: Optional[str] = None
    execution_time: float = 0.0
    artifacts: List[str] = field(default_factory=list)


@dataclass 
class ValidationSuite:
    """Complete deployment validation suite results."""
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    execution_time: float
    tests: List[DeploymentTest] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class DeploymentValidator:
    """Comprehensive deployment validation framework."""
    
    def __init__(self, comprehensive: bool = False, skip_performance: bool = False):
        self.comprehensive = comprehensive
        self.skip_performance = skip_performance
        self.project_root = Path(__file__).parent.parent.parent
        self.tests: List[DeploymentTest] = []
        self.start_time = time.time()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="km-mcp-deploy-test-"))
        
    def __del__(self):
        """Cleanup temporary directory."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def log_test(self, test: DeploymentTest) -> None:
        """Log test result with formatted output."""
        self.tests.append(test)
        
        status_symbols = {
            TestResult.PASS: "✅",
            TestResult.FAIL: "❌",
            TestResult.WARNING: "⚠️", 
            TestResult.SKIP: "⏭️"
        }
        
        symbol = status_symbols.get(test.status, "❓")
        print(f"{symbol} [{test.category}] {test.name}: {test.message} ({test.execution_time:.2f}s)")
        
        if test.details:
            print(f"   📝 {test.details}")
        
        if test.artifacts:
            for artifact in test.artifacts:
                print(f"   📁 Created: {artifact}")
    
    def run_test(self, name: str, category: str, test_func) -> DeploymentTest:
        """Execute a deployment test with timing and error handling."""
        start_time = time.time()
        
        try:
            result = test_func()
            if isinstance(result, tuple):
                if len(result) == 4:
                    status, message, details, artifacts = result
                else:
                    status, message = result[:2]
                    details = result[2] if len(result) > 2 else None
                    artifacts = result[3] if len(result) > 3 else []
            else:
                status, message, details, artifacts = result, "", None, []
            
            test = DeploymentTest(
                name=name,
                category=category,
                status=status,
                message=message,
                details=details,
                execution_time=time.time() - start_time,
                artifacts=artifacts
            )
            
        except Exception as e:
            test = DeploymentTest(
                name=name,
                category=category,
                status=TestResult.FAIL,
                message=f"Test failed with exception: {e}",
                execution_time=time.time() - start_time
            )
        
        self.log_test(test)
        return test
    
    def test_installation_procedures(self) -> None:
        """Test all installation procedures and documentation accuracy."""
        print("\n📦 Installation Procedures Testing")
        
        def test_requirements_file_validity():
            """Test that requirements.txt is valid and installable."""
            req_file = self.project_root / "requirements.txt"
            if not req_file.exists():
                return (TestResult.FAIL, "requirements.txt not found")
            
            # Create test virtual environment
            test_venv = self.temp_dir / "test_venv"
            
            try:
                # Create venv
                subprocess.run([
                    sys.executable, "-m", "venv", str(test_venv)
                ], check=True, capture_output=True)
                
                # Get venv python path
                if sys.platform.startswith('win'):
                    venv_python = test_venv / "Scripts" / "python.exe"
                else:
                    venv_python = test_venv / "bin" / "python"
                
                # Test pip install dry-run
                result = subprocess.run([
                    str(venv_python), "-m", "pip", "install", "--dry-run",
                    "-r", str(req_file)
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return (TestResult.PASS, "Requirements file is valid and installable")
                else:
                    return (TestResult.FAIL, f"Requirements installation failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                return (TestResult.WARNING, "Requirements check timed out")
            except Exception as e:
                return (TestResult.FAIL, f"Requirements test failed: {e}")
        
        def test_env_template_completeness():
            """Test that .env.template contains all required variables."""
            template_file = self.project_root / "config" / ".env.template"
            if not template_file.exists():
                return (TestResult.FAIL, ".env.template not found")
            
            with open(template_file) as f:
                template_content = f.read()
            
            # Required variables for basic operation
            required_vars = [
                "KM_MCP_TRANSPORT", "KM_MCP_HOST", "KM_MCP_PORT",
                "KM_MCP_JWT_SECRET_KEY", "KM_MCP_LOG_LEVEL"
            ]
            
            missing_vars = [var for var in required_vars if var not in template_content]
            
            if missing_vars:
                return (TestResult.FAIL, f"Missing required variables: {missing_vars}")
            
            # Check for placeholder values that need replacement
            placeholder_vars = []
            for line in template_content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    var, value = line.split('=', 1)
                    if 'your-' in value or 'changeme' in value.lower():
                        placeholder_vars.append(var.strip())
            
            if placeholder_vars:
                details = f"Variables need customization: {placeholder_vars}"
            else:
                details = None
            
            return (TestResult.PASS, ".env.template is complete", details)
        
        def test_directory_structure():
            """Verify required directory structure exists."""
            required_dirs = [
                "src", "tests", "scripts", "config", "development"
            ]
            
            required_scripts = [
                "scripts/build/deploy.py",
                "scripts/setup/production_setup.py",
                "scripts/validation/production_validator.py"
            ]
            
            missing_dirs = [d for d in required_dirs if not (self.project_root / d).exists()]
            missing_scripts = [s for s in required_scripts if not (self.project_root / s).exists()]
            
            if missing_dirs or missing_scripts:
                missing = []
                if missing_dirs:
                    missing.extend([f"directory: {d}" for d in missing_dirs])
                if missing_scripts:
                    missing.extend([f"script: {s}" for s in missing_scripts])
                return (TestResult.FAIL, f"Missing required components: {missing}")
            
            return (TestResult.PASS, "Directory structure is complete")
        
        def test_installation_script_syntax():
            """Test that installation scripts have valid Python syntax."""
            scripts_to_test = [
                "scripts/setup/production_setup.py",
                "scripts/build/deploy.py",
                "scripts/validation/production_validator.py"
            ]
            
            syntax_errors = []
            for script_path in scripts_to_test:
                full_path = self.project_root / script_path
                if full_path.exists():
                    try:
                        with open(full_path) as f:
                            content = f.read()
                        compile(content, str(full_path), 'exec')
                    except SyntaxError as e:
                        syntax_errors.append(f"{script_path}: {e}")
            
            if syntax_errors:
                return (TestResult.FAIL, "Syntax errors in scripts", str(syntax_errors))
            
            return (TestResult.PASS, "All installation scripts have valid syntax")
        
        # Run installation procedure tests
        self.run_test("Requirements File Validity", "Installation", test_requirements_file_validity)
        self.run_test("Environment Template", "Installation", test_env_template_completeness)
        self.run_test("Directory Structure", "Installation", test_directory_structure)
        self.run_test("Script Syntax", "Installation", test_installation_script_syntax)
    
    def test_configuration_validation(self) -> None:
        """Validate configuration examples and templates."""
        print("\n⚙️ Configuration Validation Testing")
        
        def test_production_yaml_validity():
            """Test production.yaml is valid and complete."""
            config_file = self.project_root / "config" / "production.yaml"
            if not config_file.exists():
                return (TestResult.FAIL, "production.yaml not found")
            
            try:
                import yaml
                with open(config_file) as f:
                    config_data = yaml.safe_load(f)
                
                # Check required sections
                required_sections = ["server", "auth", "logging", "monitoring"]
                missing_sections = [s for s in required_sections if s not in config_data]
                
                if missing_sections:
                    return (TestResult.FAIL, f"Missing config sections: {missing_sections}")
                
                # Check for environment variable references
                yaml_content = config_file.read_text()
                env_refs = []
                import re
                for match in re.finditer(r'\$\{([^}]+)\}', yaml_content):
                    env_refs.append(match.group(1))
                
                details = f"Environment variables referenced: {env_refs}" if env_refs else None
                return (TestResult.PASS, "Production YAML is valid", details)
                
            except yaml.YAMLError as e:
                return (TestResult.FAIL, f"Invalid YAML syntax: {e}")
        
        def test_env_template_generation():
            """Test that a valid .env file can be generated from template."""
            template_file = self.project_root / "config" / ".env.template"
            if not template_file.exists():
                return (TestResult.FAIL, "Template file not found")
            
            # Create test .env file
            test_env_file = self.temp_dir / ".env"
            
            try:
                # Copy template and replace placeholders
                with open(template_file) as f:
                    content = f.read()
                
                # Replace common placeholders
                content = content.replace(
                    "KM_MCP_JWT_SECRET_KEY=your-generated-secret-key-here",
                    "KM_MCP_JWT_SECRET_KEY=test-secret-key-for-validation"
                )
                content = content.replace(
                    "KM_MCP_SENTRY_DSN=your-sentry-dsn-here",
                    "KM_MCP_SENTRY_DSN="
                )
                
                with open(test_env_file, 'w') as f:
                    f.write(content)
                
                # Test that it can be loaded
                from dotenv import dotenv_values
                env_vars = dotenv_values(test_env_file)
                
                required_vars = ["KM_MCP_TRANSPORT", "KM_MCP_HOST", "KM_MCP_PORT"]
                missing_vars = [var for var in required_vars if var not in env_vars]
                
                if missing_vars:
                    return (TestResult.FAIL, f"Generated .env missing variables: {missing_vars}")
                
                return (TestResult.PASS, f"Generated valid .env with {len(env_vars)} variables",
                       None, [str(test_env_file)])
                
            except Exception as e:
                return (TestResult.FAIL, f"Failed to generate .env: {e}")
        
        def test_configuration_compatibility():
            """Test that configuration files are compatible with each other."""
            try:
                # Load configuration files
                import yaml
                from dotenv import dotenv_values
                
                # Load production YAML
                yaml_file = self.project_root / "config" / "production.yaml"
                if yaml_file.exists():
                    with open(yaml_file) as f:
                        yaml_config = yaml.safe_load(f)
                else:
                    return (TestResult.SKIP, "No production.yaml to test")
                
                # Load template env
                template_file = self.project_root / "config" / ".env.template"
                if template_file.exists():
                    env_vars = dotenv_values(template_file)
                else:
                    return (TestResult.SKIP, "No .env.template to test")
                
                # Check for environment variable references in YAML that exist in template
                yaml_content = yaml_file.read_text()
                import re
                env_refs = set()
                for match in re.finditer(r'\$\{([^}]+)\}', yaml_content):
                    env_refs.add(match.group(1))
                
                missing_env_vars = env_refs - set(env_vars.keys())
                
                if missing_env_vars:
                    return (TestResult.WARNING, f"YAML references undefined env vars: {missing_env_vars}")
                
                return (TestResult.PASS, "Configuration files are compatible")
                
            except Exception as e:
                return (TestResult.FAIL, f"Configuration compatibility test failed: {e}")
        
        # Run configuration validation tests
        self.run_test("Production YAML", "Configuration", test_production_yaml_validity)
        self.run_test("Environment Generation", "Configuration", test_env_template_generation)
        self.run_test("Configuration Compatibility", "Configuration", test_configuration_compatibility)
    
    def test_deployment_scripts(self) -> None:
        """Verify deployment scripts functionality."""
        print("\n🚀 Deployment Scripts Testing")
        
        def test_deployment_script_dry_run():
            """Test deployment script dry-run functionality."""
            deploy_script = self.project_root / "scripts" / "build" / "deploy.py"
            if not deploy_script.exists():
                return (TestResult.FAIL, "deploy.py not found")
            
            try:
                # Test dry-run mode
                result = subprocess.run([
                    sys.executable, str(deploy_script),
                    "--dry-run", "--environment", "development"
                ], capture_output=True, text=True, timeout=30, cwd=self.project_root)
                
                if result.returncode == 0:
                    return (TestResult.PASS, "Deployment script dry-run successful")
                else:
                    return (TestResult.FAIL, f"Dry-run failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                return (TestResult.WARNING, "Deployment script dry-run timed out")
            except Exception as e:
                return (TestResult.FAIL, f"Deployment script test failed: {e}")
        
        def test_production_setup_help():
            """Test production setup script help and validation."""
            setup_script = self.project_root / "scripts" / "setup" / "production_setup.py"
            if not setup_script.exists():
                return (TestResult.FAIL, "production_setup.py not found")
            
            try:
                # Test help functionality
                result = subprocess.run([
                    sys.executable, str(setup_script), "--help"
                ], capture_output=True, text=True, timeout=10, cwd=self.project_root)
                
                if result.returncode == 0 and "usage:" in result.stdout.lower():
                    return (TestResult.PASS, "Production setup script help works")
                else:
                    return (TestResult.FAIL, "Production setup help failed")
                    
            except subprocess.TimeoutExpired:
                return (TestResult.WARNING, "Setup script help timed out")
            except Exception as e:
                return (TestResult.FAIL, f"Setup script test failed: {e}")
        
        def test_validator_script():
            """Test production validator script basic functionality."""
            validator_script = self.project_root / "scripts" / "validation" / "production_validator.py"
            if not validator_script.exists():
                return (TestResult.FAIL, "production_validator.py not found")
            
            try:
                # Test basic validation (skip integration tests)
                result = subprocess.run([
                    sys.executable, str(validator_script), "--skip-integration"
                ], capture_output=True, text=True, timeout=60, cwd=self.project_root)
                
                # Validator may return non-zero but should not crash
                if "Validation Summary" in result.stdout:
                    return (TestResult.PASS, "Production validator executed successfully")
                else:
                    return (TestResult.WARNING, f"Validator ran but output unexpected: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                return (TestResult.WARNING, "Production validator timed out")
            except Exception as e:
                return (TestResult.FAIL, f"Validator test failed: {e}")
        
        def test_script_dependencies():
            """Test that deployment scripts have required dependencies."""
            scripts_to_test = [
                "scripts/build/deploy.py",
                "scripts/setup/production_setup.py",
                "scripts/validation/production_validator.py"
            ]
            
            dependency_errors = []
            
            for script_path in scripts_to_test:
                full_path = self.project_root / script_path
                if full_path.exists():
                    try:
                        # Test import by running with --help or similar safe option
                        result = subprocess.run([
                            sys.executable, "-c", 
                            f"import sys; sys.path.insert(0, '{self.project_root / 'src'}'); exec(open('{full_path}').read())"
                        ], capture_output=True, text=True, timeout=10)
                        
                        # Check for import errors
                        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
                            dependency_errors.append(f"{script_path}: {result.stderr}")
                            
                    except subprocess.TimeoutExpired:
                        # Timeout is okay for this test
                        pass
                    except Exception as e:
                        dependency_errors.append(f"{script_path}: {e}")
            
            if dependency_errors:
                return (TestResult.WARNING, "Some scripts have dependency issues", str(dependency_errors))
            
            return (TestResult.PASS, "All deployment scripts have satisfied dependencies")
        
        # Run deployment script tests
        self.run_test("Deploy Script Dry-Run", "Deployment", test_deployment_script_dry_run)
        self.run_test("Setup Script Help", "Deployment", test_production_setup_help)
        self.run_test("Validator Script", "Deployment", test_validator_script)
        self.run_test("Script Dependencies", "Deployment", test_script_dependencies)
    
    def test_monitoring_logging(self) -> None:
        """Test monitoring and logging setup."""
        print("\n📊 Monitoring and Logging Testing")
        
        def test_logging_configuration():
            """Test logging configuration and directory setup."""
            # Check if logs directory can be created
            logs_dir = self.temp_dir / "logs"
            try:
                logs_dir.mkdir(exist_ok=True)
                
                # Test log file creation
                test_log = logs_dir / "test.log"
                with open(test_log, 'w') as f:
                    f.write("Test log entry\n")
                
                # Check permissions
                if test_log.exists() and test_log.stat().st_size > 0:
                    return (TestResult.PASS, "Logging directory and file creation works",
                           None, [str(test_log)])
                else:
                    return (TestResult.FAIL, "Log file creation failed")
                    
            except Exception as e:
                return (TestResult.FAIL, f"Logging setup test failed: {e}")
        
        def test_health_check_endpoint():
            """Test health check configuration in production.yaml."""
            config_file = self.project_root / "config" / "production.yaml"
            if not config_file.exists():
                return (TestResult.SKIP, "No production.yaml to test")
            
            try:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                
                # Check health check configuration
                monitoring = config.get('monitoring', {})
                health_check = monitoring.get('health_check', {})
                
                if not health_check.get('enabled', False):
                    return (TestResult.WARNING, "Health check not enabled in configuration")
                
                required_health_fields = ['path', 'interval', 'timeout']
                missing_fields = [f for f in required_health_fields if f not in health_check]
                
                if missing_fields:
                    return (TestResult.WARNING, f"Missing health check fields: {missing_fields}")
                
                return (TestResult.PASS, "Health check configuration is complete")
                
            except Exception as e:
                return (TestResult.FAIL, f"Health check config test failed: {e}")
        
        def test_metrics_configuration():
            """Test metrics and monitoring configuration."""
            config_file = self.project_root / "config" / "production.yaml"
            if not config_file.exists():
                return (TestResult.SKIP, "No production.yaml to test")
            
            try:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                
                monitoring = config.get('monitoring', {})
                metrics = monitoring.get('metrics', {})
                
                if metrics.get('enabled', False):
                    if 'port' not in metrics or 'path' not in metrics:
                        return (TestResult.WARNING, "Metrics enabled but missing port/path configuration")
                    return (TestResult.PASS, "Metrics configuration is complete")
                else:
                    return (TestResult.WARNING, "Metrics monitoring not enabled")
                    
            except Exception as e:
                return (TestResult.FAIL, f"Metrics config test failed: {e}")
        
        def test_error_reporting_config():
            """Test error reporting and alerting configuration."""
            config_file = self.project_root / "config" / "production.yaml"
            if not config_file.exists():
                return (TestResult.SKIP, "No production.yaml to test")
            
            try:
                import yaml
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                
                error_handling = config.get('error_handling', {})
                reporting = error_handling.get('reporting', {})
                alerts = error_handling.get('alerts', {})
                
                issues = []
                if reporting.get('enabled') and '${SENTRY_DSN}' in str(reporting):
                    # Good - uses environment variable
                    pass
                elif reporting.get('enabled'):
                    issues.append("Error reporting enabled but may not use env variable")
                
                if alerts.get('enabled') and 'thresholds' not in alerts:
                    issues.append("Alerts enabled but no thresholds configured")
                
                if issues:
                    return (TestResult.WARNING, "Error reporting config issues", str(issues))
                
                return (TestResult.PASS, "Error reporting configuration is appropriate")
                
            except Exception as e:
                return (TestResult.FAIL, f"Error reporting config test failed: {e}")
        
        # Run monitoring and logging tests
        self.run_test("Logging Setup", "Monitoring", test_logging_configuration)
        self.run_test("Health Check Config", "Monitoring", test_health_check_endpoint)
        self.run_test("Metrics Config", "Monitoring", test_metrics_configuration)
        self.run_test("Error Reporting Config", "Monitoring", test_error_reporting_config)
    
    def test_performance_benchmarks(self) -> None:
        """Test performance characteristics and benchmarks."""
        if self.skip_performance:
            print("\n⚡ Performance Testing (SKIPPED)")
            return
            
        print("\n⚡ Performance Benchmark Testing")
        
        def test_import_performance():
            """Test module import performance."""
            import_tests = [
                "import sys",
                "from pathlib import Path",
                "import asyncio",
                "import json"
            ]
            
            try:
                # Test critical imports
                start_time = time.time()
                for import_statement in import_tests:
                    exec(import_statement)
                import_time = time.time() - start_time
                
                if import_time > 1.0:
                    return (TestResult.WARNING, f"Slow standard imports: {import_time:.3f}s")
                else:
                    return (TestResult.PASS, f"Standard imports fast: {import_time:.3f}s")
                    
            except Exception as e:
                return (TestResult.FAIL, f"Import performance test failed: {e}")
        
        def test_file_io_performance():
            """Test file I/O performance for configuration loading."""
            try:
                # Test config file reading performance
                config_file = self.project_root / "config" / "production.yaml"
                if not config_file.exists():
                    return (TestResult.SKIP, "No config file for I/O test")
                
                start_time = time.time()
                for _ in range(10):  # Read file 10 times
                    with open(config_file) as f:
                        content = f.read()
                io_time = time.time() - start_time
                
                avg_time = io_time / 10
                if avg_time > 0.1:
                    return (TestResult.WARNING, f"Slow config file I/O: {avg_time:.3f}s average")
                else:
                    return (TestResult.PASS, f"Config file I/O fast: {avg_time:.3f}s average")
                    
            except Exception as e:
                return (TestResult.FAIL, f"File I/O performance test failed: {e}")
        
        def test_memory_baseline():
            """Test memory usage baseline."""
            try:
                import psutil
                process = psutil.Process()
                
                # Get initial memory
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # Perform some operations
                data = [i for i in range(10000)]
                result = sum(data)
                
                # Get final memory
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = final_memory - initial_memory
                
                if final_memory > 100:  # 100MB baseline threshold
                    return (TestResult.WARNING, f"High memory baseline: {final_memory:.1f}MB")
                else:
                    return (TestResult.PASS, f"Memory baseline acceptable: {final_memory:.1f}MB")
                    
            except ImportError:
                return (TestResult.SKIP, "psutil not available for memory testing")
            except Exception as e:
                return (TestResult.FAIL, f"Memory baseline test failed: {e}")
        
        def test_script_execution_time():
            """Test deployment script execution times."""
            deploy_script = self.project_root / "scripts" / "build" / "deploy.py"
            if not deploy_script.exists():
                return (TestResult.SKIP, "No deploy script to test")
            
            try:
                start_time = time.time()
                result = subprocess.run([
                    sys.executable, str(deploy_script), "--help"
                ], capture_output=True, text=True, timeout=10, cwd=self.project_root)
                execution_time = time.time() - start_time
                
                if execution_time > 5.0:
                    return (TestResult.WARNING, f"Slow script startup: {execution_time:.2f}s")
                elif result.returncode == 0:
                    return (TestResult.PASS, f"Script execution fast: {execution_time:.2f}s")
                else:
                    return (TestResult.FAIL, f"Script execution failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                return (TestResult.FAIL, "Script execution timed out")
            except Exception as e:
                return (TestResult.FAIL, f"Script performance test failed: {e}")
        
        # Run performance tests if comprehensive mode
        if self.comprehensive:
            self.run_test("Import Performance", "Performance", test_import_performance)
            self.run_test("File I/O Performance", "Performance", test_file_io_performance)
            self.run_test("Memory Baseline", "Performance", test_memory_baseline)
            self.run_test("Script Execution Time", "Performance", test_script_execution_time)
        else:
            print("⏭️ Performance tests skipped (use --comprehensive)")
    
    def generate_validation_report(self) -> ValidationSuite:
        """Generate comprehensive validation report."""
        total_time = time.time() - self.start_time
        
        status_counts = {
            TestResult.PASS: 0,
            TestResult.FAIL: 0,
            TestResult.WARNING: 0,
            TestResult.SKIP: 0
        }
        
        for test in self.tests:
            status_counts[test.status] += 1
        
        # Generate summary
        summary = {
            "overall_status": "DEPLOYMENT_READY" if status_counts[TestResult.FAIL] == 0 else "NOT_READY",
            "critical_issues": status_counts[TestResult.FAIL],
            "warnings": status_counts[TestResult.WARNING],
            "deployment_readiness": self._assess_deployment_readiness(),
            "recommendations": self._generate_deployment_recommendations()
        }
        
        return ValidationSuite(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=len(self.tests),
            passed=status_counts[TestResult.PASS],
            failed=status_counts[TestResult.FAIL], 
            warnings=status_counts[TestResult.WARNING],
            skipped=status_counts[TestResult.SKIP],
            execution_time=total_time,
            tests=self.tests,
            summary=summary
        )
    
    def _assess_deployment_readiness(self) -> str:
        """Assess overall deployment readiness."""
        failed_tests = [t for t in self.tests if t.status == TestResult.FAIL]
        warning_tests = [t for t in self.tests if t.status == TestResult.WARNING]
        
        if not failed_tests and not warning_tests:
            return "FULLY_READY"
        elif not failed_tests and len(warning_tests) <= 2:
            return "READY_WITH_WARNINGS"
        elif not failed_tests:
            return "READY_REVIEW_WARNINGS"
        elif len(failed_tests) <= 2:
            return "NEEDS_MINOR_FIXES"
        else:
            return "NEEDS_MAJOR_FIXES"
    
    def _generate_deployment_recommendations(self) -> List[str]:
        """Generate deployment-specific recommendations."""
        recommendations = []
        
        failed_tests = [t for t in self.tests if t.status == TestResult.FAIL]
        warning_tests = [t for t in self.tests if t.status == TestResult.WARNING]
        
        if failed_tests:
            recommendations.append("🚨 CRITICAL: Fix all failed tests before production deployment")
            
            # Category-specific recommendations
            installation_failures = [t for t in failed_tests if t.category == "Installation"]
            if installation_failures:
                recommendations.append("📦 INSTALLATION: Review and fix installation procedures")
            
            config_failures = [t for t in failed_tests if t.category == "Configuration"]
            if config_failures:
                recommendations.append("⚙️ CONFIGURATION: Validate and fix configuration files")
            
            deploy_failures = [t for t in failed_tests if t.category == "Deployment"]
            if deploy_failures:
                recommendations.append("🚀 DEPLOYMENT: Fix deployment script issues")
        
        if warning_tests:
            recommendations.append("⚠️ WARNINGS: Review warning conditions for production readiness")
            
            monitoring_warnings = [t for t in warning_tests if t.category == "Monitoring"]
            if monitoring_warnings:
                recommendations.append("📊 MONITORING: Enhance monitoring and alerting setup")
            
            performance_warnings = [t for t in warning_tests if t.category == "Performance"]
            if performance_warnings:
                recommendations.append("⚡ PERFORMANCE: Address performance concerns")
        
        # General recommendations
        if not failed_tests and not warning_tests:
            recommendations.append("✅ READY: All deployment validations passed")
            recommendations.append("🔄 FINAL: Run production deployment with monitoring")
        
        return recommendations
    
    async def run_comprehensive_validation(self) -> ValidationSuite:
        """Execute comprehensive deployment validation suite."""
        print("🎯 Starting Comprehensive Deployment Validation")
        print("=" * 60)
        
        # Run all validation categories
        self.test_installation_procedures()
        self.test_configuration_validation()
        self.test_deployment_scripts()
        self.test_monitoring_logging()
        self.test_performance_benchmarks()
        
        # Generate final validation report
        report = self.generate_validation_report()
        
        print("\n" + "=" * 60)
        print("📋 Deployment Validation Summary")
        print(f"✅ Passed: {report.passed}")
        print(f"❌ Failed: {report.failed}")
        print(f"⚠️ Warnings: {report.warnings}")
        print(f"⏭️ Skipped: {report.skipped}")
        print(f"⏱️ Total Time: {report.execution_time:.2f}s")
        print(f"🎯 Deployment Status: {report.summary['deployment_readiness']}")
        
        if report.summary['recommendations']:
            print("\n💡 Deployment Recommendations:")
            for rec in report.summary['recommendations']:
                print(f"   {rec}")
        
        return report


def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive deployment validation for Keyboard Maestro MCP Server"
    )
    
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive validation including performance tests"
    )
    
    parser.add_argument(
        "--skip-performance",
        action="store_true",
        help="Skip performance benchmark tests"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Save validation report to JSON file"
    )
    
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Treat warnings as failures for CI/CD"
    )
    
    return parser.parse_args()


async def main():
    """Main validation entry point."""
    args = parse_arguments()
    
    validator = DeploymentValidator(
        comprehensive=args.comprehensive,
        skip_performance=args.skip_performance
    )
    
    report = await validator.run_comprehensive_validation()
    
    # Save report if requested
    if args.output:
        report_dict = {
            "timestamp": report.timestamp,
            "summary": {
                "total_tests": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings,
                "skipped": report.skipped,
                "execution_time": report.execution_time,
                "deployment_readiness": report.summary["deployment_readiness"],
                "overall_status": report.summary["overall_status"]
            },
            "tests": [
                {
                    "name": test.name,
                    "category": test.category,
                    "status": test.status.value,
                    "message": test.message,
                    "details": test.details,
                    "execution_time": test.execution_time,
                    "artifacts": test.artifacts
                }
                for test in report.tests
            ],
            "recommendations": report.summary["recommendations"],
            "artifacts_created": [
                artifact for test in report.tests for artifact in test.artifacts
            ]
        }
        
        with open(args.output, "w") as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"\n📄 Validation report saved to: {args.output}")
    
    # Exit with appropriate code
    if report.failed > 0:
        sys.exit(1)
    elif report.warnings > 0 and args.fail_on_warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
