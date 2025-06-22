#!/usr/bin/env python3
"""
Production deployment script for Keyboard Maestro MCP Server.

This script automates the deployment process including:
- Environment validation
- Dependency installation  
- Configuration validation
- Service deployment
- Health verification

Usage:
    python scripts/build/deploy.py --environment production --host 0.0.0.0 --port 8080
"""

import argparse
import asyncio
import os
import sys
import subprocess
import time
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import with fallback for missing modules
try:
    from src.utils.configuration import ServerConfiguration, load_configuration
    from src.contracts.decorators import requires, ensures
except ImportError:
    # Fallback imports for standalone execution
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
    
    # Mock ServerConfiguration for standalone use
    class ServerConfiguration:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    def load_configuration(path):
        """Mock configuration loader."""
        return {}


@dataclass
class DeploymentConfig:
    """Deployment configuration parameters."""
    environment: str
    host: str
    port: int
    config_file: Optional[str]
    docker: bool
    dry_run: bool
    verify_health: bool
    timeout: int


class DeploymentError(Exception):
    """Exception raised during deployment process."""
    pass


class ProductionDeployment:
    """Handles production deployment of the MCP server."""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent.parent
        self.deployment_log: List[str] = []
    
    def log(self, message: str) -> None:
        """Log deployment message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
    
    @requires(lambda self: self.project_root.exists())
    def validate_environment(self) -> None:
        """Validate deployment environment and requirements."""
        self.log("Validating deployment environment...")
        
        # Check Python version
        if sys.version_info < (3, 10):
            raise DeploymentError("Python 3.10+ required for deployment")
        
        # Check required files exist
        required_files = [
            "requirements.txt",
            "src/main.py",
            "config/production.yaml"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                raise DeploymentError(f"Required file missing: {file_path}")
        
        # Check if Keyboard Maestro is available (for local deployment)
        if not self.config.docker:
            km_path = Path("/Applications/Keyboard Maestro.app")
            if not km_path.exists():
                self.log("WARNING: Keyboard Maestro not found - server will have limited functionality")
        
        self.log("Environment validation complete")
    
    def install_dependencies(self) -> None:
        """Install production dependencies."""
        if self.config.dry_run:
            self.log("DRY RUN: Would install dependencies")
            return
        
        self.log("Installing production dependencies...")
        
        try:
            # Install production requirements
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", str(self.project_root / "requirements.txt")
            ], check=True, capture_output=True, text=True)
            
            self.log("Dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to install dependencies: {e.stderr}")
    
    def validate_configuration(self) -> ServerConfiguration:
        """Load and validate server configuration."""
        self.log("Validating server configuration...")
        
        # Load configuration file
        if self.config.config_file:
            config_path = Path(self.config.config_file)
        else:
            config_path = self.project_root / "config" / "production.yaml"
        
        if not config_path.exists():
            raise DeploymentError(f"Configuration file not found: {config_path}")
        
        # Load and validate configuration
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Override with command line arguments
            if hasattr(config_data, 'server'):
                config_data['server']['transport']['host'] = self.config.host
                config_data['server']['transport']['port'] = self.config.port
            
            # Validate environment variables are set
            required_env_vars = ['JWT_SECRET_KEY']
            if config_data.get('error_handling', {}).get('reporting', {}).get('enabled'):
                required_env_vars.append('SENTRY_DSN')
            
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            if missing_vars:
                raise DeploymentError(f"Missing required environment variables: {missing_vars}")
            
            self.log("Configuration validation complete")
            return config_data
            
        except Exception as e:
            raise DeploymentError(f"Configuration validation failed: {e}")
    
    async def deploy_docker(self) -> None:
        """Deploy using Docker container."""
        if self.config.dry_run:
            self.log("DRY RUN: Would deploy Docker container")
            return
        
        self.log("Building Docker image...")
        
        try:
            # Build Docker image
            build_cmd = [
                "docker", "build",
                "-f", str(self.project_root / "docker" / "Dockerfile"),
                "-t", f"keyboard-maestro-mcp:{self.config.environment}",
                str(self.project_root)
            ]
            
            subprocess.run(build_cmd, check=True)
            self.log("Docker image built successfully")
            
            # Run container
            run_cmd = [
                "docker", "run", "-d",
                "--name", f"km-mcp-{self.config.environment}",
                "-p", f"{self.config.port}:8080",
                "--env-file", str(self.project_root / "config" / ".env"),
                f"keyboard-maestro-mcp:{self.config.environment}"
            ]
            
            subprocess.run(run_cmd, check=True)
            self.log(f"Container started on port {self.config.port}")
            
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Docker deployment failed: {e}")
    
    async def deploy_local(self, server_config: Dict[str, Any]) -> None:
        """Deploy locally without Docker."""
        if self.config.dry_run:
            self.log("DRY RUN: Would start local server")
            return
        
        self.log("Starting local server...")
        
        # Set environment variables
        os.environ["MCP_TRANSPORT"] = "streamable-http"
        os.environ["MCP_HOST"] = self.config.host
        os.environ["MCP_PORT"] = str(self.config.port)
        os.environ["MCP_DEV_MODE"] = "false"
        
        # Start server process
        try:
            server_cmd = [sys.executable, "-m", "src.main"]
            
            process = subprocess.Popen(
                server_cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give server time to start
            await asyncio.sleep(5)
            
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise DeploymentError(f"Server failed to start: {stderr}")
            
            self.log(f"Server started with PID {process.pid}")
            return process
            
        except Exception as e:
            raise DeploymentError(f"Local deployment failed: {e}")
    
    async def verify_health(self) -> None:
        """Verify server health after deployment."""
        if self.config.dry_run:
            self.log("DRY RUN: Would verify server health")
            return
        
        self.log("Verifying server health...")
        
        import aiohttp
        
        health_url = f"http://{self.config.host}:{self.config.port}/health"
        
        for attempt in range(self.config.timeout):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(health_url, timeout=5) as response:
                        if response.status == 200:
                            self.log("Health check passed")
                            return
                        else:
                            self.log(f"Health check failed with status {response.status}")
                            
            except Exception as e:
                self.log(f"Health check attempt {attempt + 1} failed: {e}")
                
            if attempt < self.config.timeout - 1:
                await asyncio.sleep(1)
        
        raise DeploymentError("Health check failed after maximum attempts")
    
    async def deploy(self) -> None:
        """Execute complete deployment process."""
        try:
            self.log(f"Starting {self.config.environment} deployment...")
            
            # Validation phase
            self.validate_environment()
            server_config = self.validate_configuration()
            
            # Installation phase
            self.install_dependencies()
            
            # Deployment phase
            if self.config.docker:
                await self.deploy_docker()
            else:
                await self.deploy_local(server_config)
            
            # Verification phase
            if self.config.verify_health:
                await self.verify_health()
            
            self.log("Deployment completed successfully!")
            
        except DeploymentError as e:
            self.log(f"Deployment failed: {e}")
            sys.exit(1)
        except Exception as e:
            self.log(f"Unexpected error during deployment: {e}")
            sys.exit(1)
    
    def generate_deployment_report(self) -> str:
        """Generate deployment report."""
        report = {
            "deployment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": self.config.environment,
            "configuration": {
                "host": self.config.host,
                "port": self.config.port,
                "docker": self.config.docker,
                "dry_run": self.config.dry_run
            },
            "log": self.deployment_log
        }
        
        return json.dumps(report, indent=2)


def parse_arguments() -> DeploymentConfig:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy Keyboard Maestro MCP Server"
    )
    
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="production",
        help="Deployment environment"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host address"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Server port"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Deploy using Docker"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate deployment without executing"
    )
    
    parser.add_argument(
        "--no-health-check",
        action="store_true",
        help="Skip health verification"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Health check timeout in seconds"
    )
    
    args = parser.parse_args()
    
    return DeploymentConfig(
        environment=args.environment,
        host=args.host,
        port=args.port,
        config_file=args.config,
        docker=args.docker,
        dry_run=args.dry_run,
        verify_health=not args.no_health_check,
        timeout=args.timeout
    )


async def main():
    """Main deployment entry point."""
    config = parse_arguments()
    deployment = ProductionDeployment(config)
    
    await deployment.deploy()
    
    # Generate deployment report
    report = deployment.generate_deployment_report()
    report_path = Path("deployment-report.json")
    
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\nDeployment report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
