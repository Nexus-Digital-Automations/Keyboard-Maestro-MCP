#!/usr/bin/env python3
"""
Production readiness validation for Keyboard Maestro MCP Server.

This script performs comprehensive validation to ensure the server
is ready for production deployment including:
- Configuration validation
- Security checks
- Performance testing
- Integration verification
- Compliance verification

Usage:
    python scripts/validation/production_validator.py --comprehensive
"""

import argparse
import asyncio
import json
import time
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import with fallback for missing modules
try:
    from src.contracts.decorators import requires, ensures
except ImportError:
    # Fallback decorators for standalone execution
    def requires(condition):
        """Fallback decorator for requires."""
        def decorator(func):
            return func
        return decorator
    
    def ensures(condition):
        """Fallback decorator for ensures."""
        def decorator(func):
            return func
        return decorator


class ValidationResult(Enum):
    """Validation result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIP = "SKIP"


@dataclass
class ValidationCheck:
    """Individual validation check result."""
    name: str
    category: str
    status: ValidationResult
    message: str
    details: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    execution_time: float = 0.0


@dataclass
class ValidationReport:
    """Complete validation report."""
    timestamp: str
    environment: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    execution_time: float
    checks: List[ValidationCheck] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class ProductionValidator:
    """Comprehensive production readiness validator."""
    
    def __init__(self, comprehensive: bool = False, skip_integration: bool = False):
        self.comprehensive = comprehensive
        self.skip_integration = skip_integration
        self.project_root = Path(__file__).parent.parent.parent
        self.checks: List[ValidationCheck] = []
        self.start_time = time.time()
    
    def add_check(self, check: ValidationCheck) -> None:
        """Add validation check result."""
        self.checks.append(check)
        status_symbol = {
            ValidationResult.PASS: "✅",
            ValidationResult.FAIL: "❌", 
            ValidationResult.WARNING: "⚠️",
            ValidationResult.SKIP: "⏭️"
        }
        
        symbol = status_symbol.get(check.status, "❓")
        print(f"{symbol} [{check.category}] {check.name}: {check.message}")
        
        if check.suggestions:
            for suggestion in check.suggestions:
                print(f"   💡 {suggestion}")
    
    def run_check(self, name: str, category: str, check_func) -> ValidationCheck:
        """Execute a validation check with timing."""
        start_time = time.time()
        
        try:
            result = check_func()
            if isinstance(result, tuple):
                status, message, details, suggestions = result
            else:
                status, message, details, suggestions = result, "", None, []
            
            check = ValidationCheck(
                name=name,
                category=category,
                status=status,
                message=message,
                details=details,
                suggestions=suggestions,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            check = ValidationCheck(
                name=name,
                category=category,
                status=ValidationResult.FAIL,
                message=f"Check failed with exception: {e}",
                execution_time=time.time() - start_time
            )
        
        self.add_check(check)
        return check
    
    def validate_configuration(self) -> None:
        """Validate configuration files and settings."""
        print("\n🔧 Configuration Validation")
        
        def check_env_file():
            env_path = self.project_root / ".env"
            if not env_path.exists():
                return (ValidationResult.FAIL, "No .env file found", None, 
                       ["Create .env file using config/.env.template"])
            
            required_vars = [
                "KM_MCP_JWT_SECRET_KEY", "KM_MCP_TRANSPORT", 
                "KM_MCP_HOST", "KM_MCP_PORT"
            ]
            
            with open(env_path) as f:
                content = f.read()
            
            missing_vars = [var for var in required_vars if var not in content]
            if missing_vars:
                return (ValidationResult.FAIL, f"Missing environment variables: {missing_vars}")
            
            return (ValidationResult.PASS, "Environment file is properly configured")
        
        def check_production_config():
            config_path = self.project_root / "config" / "production.yaml"
            if not config_path.exists():
                return (ValidationResult.FAIL, "Production config file missing")
            
            # Basic YAML validation
            try:
                import yaml
                with open(config_path) as f:
                    yaml.safe_load(f)
                return (ValidationResult.PASS, "Production config file is valid")
            except Exception as e:
                return (ValidationResult.FAIL, f"Invalid YAML: {e}")
        
        def check_logging_config():
            logs_dir = self.project_root / "logs"
            if not logs_dir.exists():
                return (ValidationResult.WARNING, "Logs directory does not exist",
                       None, ["Create logs directory: mkdir logs"])
            
            # Check permissions
            if not os.access(logs_dir, os.W_OK):
                return (ValidationResult.FAIL, "Logs directory is not writable")
            
            return (ValidationResult.PASS, "Logging configuration is valid")
        
        # Run configuration checks
        self.run_check("Environment Variables", "Configuration", check_env_file)
        self.run_check("Production Config", "Configuration", check_production_config)
        self.run_check("Logging Setup", "Configuration", check_logging_config)
    
    def validate_security(self) -> None:
        """Validate security configuration and settings."""
        print("\n🔒 Security Validation")
        
        def check_jwt_secret():
            env_path = self.project_root / ".env"
            if not env_path.exists():
                return (ValidationResult.FAIL, "Cannot check JWT secret - no .env file")
            
            with open(env_path) as f:
                content = f.read()
            
            # Check if JWT secret is present and not default
            if "KM_MCP_JWT_SECRET_KEY=your-secret-key-here" in content:
                return (ValidationResult.FAIL, "JWT secret key is still default value",
                       None, ["Generate secure JWT secret key"])
            
            # Check secret length
            import re
            match = re.search(r'KM_MCP_JWT_SECRET_KEY=(.+)', content)
            if match:
                secret = match.group(1).strip()
                if len(secret) < 32:
                    return (ValidationResult.WARNING, "JWT secret key is shorter than recommended (32+ chars)")
            
            return (ValidationResult.PASS, "JWT secret key is properly configured")
        
        def check_file_permissions():
            env_path = self.project_root / ".env"
            if not env_path.exists():
                return (ValidationResult.SKIP, "No .env file to check")
            
            import stat
            file_mode = oct(stat.S_IMODE(env_path.stat().st_mode))
            
            if file_mode != "0o600":
                return (ValidationResult.WARNING, f"Environment file permissions too open: {file_mode}",
                       None, ["Set secure permissions: chmod 600 .env"])
            
            return (ValidationResult.PASS, "File permissions are secure")
        
        def check_default_passwords():
            # Check for any default passwords in configuration
            config_files = [
                self.project_root / ".env",
                self.project_root / "config" / "production.yaml"
            ]
            
            dangerous_patterns = [
                "password", "secret", "admin", "default", "changeme"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    with open(config_file) as f:
                        content = f.read().lower()
                    
                    for pattern in dangerous_patterns:
                        if pattern in content and "your-" in content:
                            return (ValidationResult.WARNING, 
                                   f"Possible default credentials in {config_file.name}")
            
            return (ValidationResult.PASS, "No default passwords detected")
        
        # Run security checks
        self.run_check("JWT Secret Key", "Security", check_jwt_secret)
        self.run_check("File Permissions", "Security", check_file_permissions)
        self.run_check("Default Credentials", "Security", check_default_passwords)
    
    def validate_dependencies(self) -> None:
        """Validate Python dependencies and versions."""
        print("\n📦 Dependencies Validation")
        
        def check_python_version():
            if sys.version_info < (3, 10):
                return (ValidationResult.FAIL, f"Python {sys.version} is too old (3.10+ required)")
            
            return (ValidationResult.PASS, f"Python {sys.version} is compatible")
        
        def check_required_packages():
            required_packages = [
                "fastmcp", "icontract", "hypothesis", "pydantic", 
                "structlog", "pytest", "asyncio"
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return (ValidationResult.FAIL, f"Missing packages: {missing_packages}",
                       None, ["Install requirements: pip install -r requirements.txt"])
            
            return (ValidationResult.PASS, "All required packages are installed")
        
        def check_package_versions():
            # Check for known vulnerable package versions
            try:
                subprocess.run(["safety", "check"], check=True, capture_output=True)
                return (ValidationResult.PASS, "No known security vulnerabilities in dependencies")
            except subprocess.CalledProcessError:
                return (ValidationResult.WARNING, "Security vulnerabilities detected in dependencies",
                       None, ["Run 'safety check' for details"])
            except FileNotFoundError:
                return (ValidationResult.SKIP, "Safety tool not available for vulnerability checking")
        
        # Run dependency checks
        self.run_check("Python Version", "Dependencies", check_python_version)
        self.run_check("Required Packages", "Dependencies", check_required_packages)
        self.run_check("Security Vulnerabilities", "Dependencies", check_package_versions)
    
    def validate_system_integration(self) -> None:
        """Validate system integration and permissions."""
        if self.skip_integration:
            print("\n🖥️ System Integration (SKIPPED)")
            return
        
        print("\n🖥️ System Integration Validation")
        
        def check_keyboard_maestro():
            km_path = Path("/Applications/Keyboard Maestro.app")
            if not km_path.exists():
                return (ValidationResult.WARNING, "Keyboard Maestro not found at standard location",
                       None, ["Install Keyboard Maestro for full functionality"])
            
            # Check if KM Engine is running
            try:
                result = subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to exists process "Keyboard Maestro Engine"'
                ], capture_output=True, text=True, check=True)
                
                if "true" in result.stdout:
                    return (ValidationResult.PASS, "Keyboard Maestro Engine is running")
                else:
                    return (ValidationResult.WARNING, "Keyboard Maestro Engine is not running",
                           None, ["Start Keyboard Maestro application"])
                
            except subprocess.CalledProcessError:
                return (ValidationResult.WARNING, "Unable to check Keyboard Maestro status")
        
        def check_accessibility_permissions():
            # Test accessibility permissions with a simple AppleScript
            test_script = '''
            tell application "System Events"
                try
                    set appList to name of every application process
                    return "success"
                on error
                    return "error"
                end try
            end tell
            '''
            
            try:
                result = subprocess.run([
                    "osascript", "-e", test_script
                ], capture_output=True, text=True, check=True)
                
                if "success" in result.stdout:
                    return (ValidationResult.PASS, "Accessibility permissions are properly configured")
                else:
                    return (ValidationResult.FAIL, "Accessibility permissions not granted",
                           None, ["Enable accessibility permissions in System Preferences"])
                    
            except subprocess.CalledProcessError:
                return (ValidationResult.FAIL, "Accessibility permissions check failed")
        
        def check_network_connectivity():
            import socket
            
            try:
                # Test if we can bind to the configured port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', 8080))
                sock.close()
                return (ValidationResult.PASS, "Network port is available")
            except OSError:
                return (ValidationResult.WARNING, "Port 8080 is already in use",
                       None, ["Stop other services using port 8080 or configure different port"])
        
        # Run system integration checks
        self.run_check("Keyboard Maestro", "System", check_keyboard_maestro)
        self.run_check("Accessibility Permissions", "System", check_accessibility_permissions)
        self.run_check("Network Port", "System", check_network_connectivity)
    
    def validate_performance(self) -> None:
        """Validate performance characteristics."""
        if not self.comprehensive:
            print("\n⚡ Performance Validation (SKIPPED - use --comprehensive)")
            return
        
        print("\n⚡ Performance Validation")
        
        def check_startup_time():
            # Test server startup time
            start_time = time.time()
            try:
                # Import main modules to test import time
                from src.core.mcp_server import KeyboardMaestroMCPServer
                from src.utils.configuration import ServerConfiguration
                
                import_time = time.time() - start_time
                
                if import_time > 5.0:
                    return (ValidationResult.WARNING, f"Slow module imports: {import_time:.2f}s")
                elif import_time > 2.0:
                    return (ValidationResult.WARNING, f"Moderate import time: {import_time:.2f}s")
                else:
                    return (ValidationResult.PASS, f"Fast module imports: {import_time:.2f}s")
                    
            except Exception as e:
                return (ValidationResult.FAIL, f"Import test failed: {e}")
        
        def check_memory_usage():
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                if memory_mb > 500:
                    return (ValidationResult.WARNING, f"High memory usage: {memory_mb:.1f}MB")
                else:
                    return (ValidationResult.PASS, f"Memory usage: {memory_mb:.1f}MB")
                    
            except ImportError:
                return (ValidationResult.SKIP, "psutil not available for memory check")
        
        # Run performance checks
        self.run_check("Module Import Time", "Performance", check_startup_time)
        self.run_check("Memory Usage", "Performance", check_memory_usage)
    
    def generate_report(self) -> ValidationReport:
        """Generate comprehensive validation report."""
        total_time = time.time() - self.start_time
        
        status_counts = {
            ValidationResult.PASS: 0,
            ValidationResult.FAIL: 0,
            ValidationResult.WARNING: 0,
            ValidationResult.SKIP: 0
        }
        
        for check in self.checks:
            status_counts[check.status] += 1
        
        # Generate summary
        summary = {
            "overall_status": "READY" if status_counts[ValidationResult.FAIL] == 0 else "NOT_READY",
            "critical_issues": status_counts[ValidationResult.FAIL],
            "warnings": status_counts[ValidationResult.WARNING],
            "recommendations": self._generate_recommendations()
        }
        
        return ValidationReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            environment="production",
            total_checks=len(self.checks),
            passed=status_counts[ValidationResult.PASS],
            failed=status_counts[ValidationResult.FAIL],
            warnings=status_counts[ValidationResult.WARNING],
            skipped=status_counts[ValidationResult.SKIP],
            execution_time=total_time,
            checks=self.checks,
            summary=summary
        )
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        failed_checks = [check for check in self.checks if check.status == ValidationResult.FAIL]
        warning_checks = [check for check in self.checks if check.status == ValidationResult.WARNING]
        
        if failed_checks:
            recommendations.append("⚠️ CRITICAL: Address all failed checks before production deployment")
            
        if warning_checks:
            recommendations.append("💡 RECOMMENDED: Review and address warning conditions")
            
        # Category-specific recommendations
        categories = set(check.category for check in self.checks)
        
        if "Security" in categories:
            security_issues = [c for c in failed_checks + warning_checks if c.category == "Security"]
            if security_issues:
                recommendations.append("🔒 SECURITY: Review and strengthen security configuration")
        
        if "System" in categories:
            system_issues = [c for c in failed_checks if c.category == "System"]
            if system_issues:
                recommendations.append("🖥️ SYSTEM: Verify system integration and permissions")
        
        return recommendations
    
    async def run_validation(self) -> ValidationReport:
        """Execute complete validation suite."""
        print("🚀 Starting Production Readiness Validation")
        print("=" * 50)
        
        # Run validation categories
        self.validate_configuration()
        self.validate_security()
        self.validate_dependencies()
        self.validate_system_integration()
        self.validate_performance()
        
        # Generate final report
        report = self.generate_report()
        
        print("\n" + "=" * 50)
        print("📊 Validation Summary")
        print(f"✅ Passed: {report.passed}")
        print(f"❌ Failed: {report.failed}")
        print(f"⚠️ Warnings: {report.warnings}")
        print(f"⏭️ Skipped: {report.skipped}")
        print(f"⏱️ Total Time: {report.execution_time:.2f}s")
        print(f"📈 Overall Status: {report.summary['overall_status']}")
        
        if report.summary['recommendations']:
            print("\n💡 Recommendations:")
            for rec in report.summary['recommendations']:
                print(f"   {rec}")
        
        return report


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate production readiness of Keyboard Maestro MCP Server"
    )
    
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive validation including performance tests"
    )
    
    parser.add_argument(
        "--skip-integration",
        action="store_true",
        help="Skip system integration tests"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output report to JSON file"
    )
    
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Treat warnings as failures"
    )
    
    return parser.parse_args()


async def main():
    """Main validation entry point."""
    args = parse_arguments()
    
    validator = ProductionValidator(
        comprehensive=args.comprehensive,
        skip_integration=args.skip_integration
    )
    
    report = await validator.run_validation()
    
    # Save report if requested
    if args.output:
        report_dict = {
            "timestamp": report.timestamp,
            "environment": report.environment,
            "summary": {
                "total_checks": report.total_checks,
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings,
                "skipped": report.skipped,
                "execution_time": report.execution_time,
                "overall_status": report.summary["overall_status"]
            },
            "checks": [
                {
                    "name": check.name,
                    "category": check.category,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "suggestions": check.suggestions,
                    "execution_time": check.execution_time
                }
                for check in report.checks
            ],
            "recommendations": report.summary["recommendations"]
        }
        
        with open(args.output, "w") as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"\n📄 Report saved to: {args.output}")
    
    # Exit with appropriate code
    if report.failed > 0:
        sys.exit(1)
    elif report.warnings > 0 and args.fail_on_warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
