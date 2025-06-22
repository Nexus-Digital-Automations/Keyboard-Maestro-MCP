#!/usr/bin/env python3
"""
Project Initialization Script Template

TARGET: <250 lines per script
MAX: 400 lines if splitting awkward

This script demonstrates modular script organization following ADDER+ principles.
Includes contract specifications, type safety, error handling, and clear separation of concerns.
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

# ============================================================================
# CONTRACT SPECIFICATIONS (to be implemented with decorators)
# ============================================================================

# @requires(lambda project_root: project_root.exists() and project_root.is_dir())
# @ensures(lambda result: result.success or result.error_details is not None)
# async def initialize_project(project_root: Path) -> InitializationResult:
#     """Contract: Initialize project with validation and error handling."""

# ============================================================================
# CONFIGURATION AND TYPES
# ============================================================================

@dataclass(frozen=True)
class InitializationConfig:
    """Immutable configuration for project initialization."""
    project_root: Path
    create_directories: bool = True
    install_dependencies: bool = True
    setup_logging: bool = True
    validate_environment: bool = True
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not self.project_root:
            raise ValueError("Project root path is required")

@dataclass(frozen=True)
class InitializationResult:
    """Result of project initialization process."""
    success: bool
    steps_completed: List[str]
    error_details: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Validate result consistency."""
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])

# ============================================================================
# CORE INITIALIZATION FUNCTIONS (keeping each under 50 lines for modularity)
# ============================================================================

def validate_environment() -> bool:
    """Validate required environment dependencies."""
    required_python_version = (3, 10)
    current_version = sys.version_info[:2]
    
    if current_version < required_python_version:
        raise RuntimeError(
            f"Python {required_python_version[0]}.{required_python_version[1]}+ required, "
            f"found {current_version[0]}.{current_version[1]}"
        )
    
    # Check for required system dependencies
    if sys.platform != 'darwin':
        raise RuntimeError("This project requires macOS (Keyboard Maestro dependency)")
    
    return True

def setup_project_directories(project_root: Path) -> List[str]:
    """Create required project directories if they don't exist."""
    directories = [
        'logs',
        'data',
        'config',
        'temp',
    ]
    
    created_dirs = []
    for directory in directories:
        dir_path = project_root / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
    
    return created_dirs

def setup_logging_configuration(project_root: Path) -> None:
    """Configure structured logging for the project."""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / 'initialization.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr)
        ]
    )

def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available."""
    dependencies = {
        'fastmcp': False,
        'hypothesis': False,
        'structlog': False,
        'pydantic': False,
    }
    
    for package in dependencies.keys():
        try:
            __import__(package)
            dependencies[package] = True
        except ImportError:
            dependencies[package] = False
    
    return dependencies

def generate_env_template(project_root: Path) -> None:
    """Generate .env template file with default configuration."""
    env_template = """# Keyboard Maestro MCP Server Configuration

# Server Settings
KM_MCP_LOG_LEVEL=INFO
KM_MCP_SERVER_HOST=127.0.0.1
KM_MCP_SERVER_PORT=8080

# Operation Settings
KM_MCP_MAX_CONCURRENT_OPERATIONS=100
KM_MCP_OPERATION_TIMEOUT=30

# Security Settings
KM_MCP_AUTH_REQUIRED=false
KM_MCP_RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Development Settings
KM_MCP_DEBUG_MODE=false
KM_MCP_CONTRACT_CHECKING=true
KM_MCP_PROPERTY_TESTING=true
"""
    
    env_file = project_root / '.env.template'
    with open(env_file, 'w') as f:
        f.write(env_template)

# ============================================================================
# MAIN INITIALIZATION ORCHESTRATION
# ============================================================================

async def initialize_project(config: InitializationConfig) -> InitializationResult:
    """Main project initialization function with comprehensive error handling."""
    logger = logging.getLogger(__name__)
    completed_steps = []
    warnings = []
    
    try:
        # Step 1: Validate environment
        if config.validate_environment:
            logger.info("Validating environment requirements...")
            validate_environment()
            completed_steps.append("Environment validation")
        
        # Step 2: Setup logging
        if config.setup_logging:
            logger.info("Setting up logging configuration...")
            setup_logging_configuration(config.project_root)
            completed_steps.append("Logging configuration")
        
        # Step 3: Create directories
        if config.create_directories:
            logger.info("Creating project directories...")
            created_dirs = setup_project_directories(config.project_root)
            if created_dirs:
                logger.info(f"Created directories: {', '.join(created_dirs)}")
            completed_steps.append("Directory creation")
        
        # Step 4: Check dependencies
        if config.install_dependencies:
            logger.info("Checking project dependencies...")
            dependency_status = check_dependencies()
            missing_deps = [name for name, available in dependency_status.items() if not available]
            
            if missing_deps:
                warning_msg = f"Missing dependencies: {', '.join(missing_deps)}"
                warnings.append(warning_msg)
                logger.warning(warning_msg)
                logger.info("Run: uv pip install -r requirements.txt")
            
            completed_steps.append("Dependency check")
        
        # Step 5: Generate configuration template
        logger.info("Generating configuration template...")
        generate_env_template(config.project_root)
        completed_steps.append("Configuration template")
        
        logger.info("Project initialization completed successfully!")
        return InitializationResult(
            success=True,
            steps_completed=completed_steps,
            warnings=warnings
        )
    
    except Exception as e:
        error_msg = f"Initialization failed during step: {e}"
        logger.error(error_msg)
        return InitializationResult(
            success=False,
            steps_completed=completed_steps,
            error_details=error_msg,
            warnings=warnings
        )

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def parse_arguments() -> InitializationConfig:
    """Parse command line arguments and return configuration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Keyboard Maestro MCP project")
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path.cwd(),
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--no-deps',
        action='store_true',
        help='Skip dependency checking'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip environment validation'
    )
    
    args = parser.parse_args()
    
    return InitializationConfig(
        project_root=args.project_root,
        install_dependencies=not args.no_deps,
        validate_environment=not args.no_validate
    )

async def main() -> int:
    """Main entry point with error handling."""
    try:
        config = parse_arguments()
        result = await initialize_project(config)
        
        if result.success:
            print("✅ Project initialization completed successfully!")
            if result.warnings:
                print("\n⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"   • {warning}")
            print(f"\n📁 Project root: {config.project_root}")
            print("\n🚀 Next steps:")
            print("   1. Copy .env.template to .env and configure")
            print("   2. Install dependencies: uv pip install -r requirements.txt")
            print("   3. Run tests: pytest")
            return 0
        else:
            print("❌ Project initialization failed!")
            print(f"Error: {result.error_details}")
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️  Initialization cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

# ============================================================================
# MODULAR DESIGN NOTES
# ============================================================================

# This script demonstrates modular design principles:
# 1. Single responsibility per function (<50 lines each)
# 2. Total size: ~240 lines (within target)
# 3. Clear separation: config → validation → operations → CLI → main
# 4. Error handling: comprehensive with recovery information
# 5. Type safety: dataclasses and type annotations throughout
# 6. Contract integration: prepared for decorator application
# 7. Immutable config: functional programming patterns
# 8. Async support: ready for concurrent operations
