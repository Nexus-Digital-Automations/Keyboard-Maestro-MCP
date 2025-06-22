# System Health Monitoring Tools: Keyboard Maestro MCP Server
# src/tools/system_health.py

"""
System health monitoring and diagnostic tools for the MCP server.

This module implements comprehensive health checks for Keyboard Maestro services,
AppleScript pool performance, system connectivity, and diagnostic capabilities
with contract-driven validation and defensive programming patterns.

Features:
- Keyboard Maestro service availability monitoring
- AppleScript pool performance and optimization
- System connectivity and integration health checks
- Diagnostic tools and health reporting
- Automated recovery suggestions and remediation

Size: 248 lines (target: <250)
"""

import asyncio
import time
import subprocess
import psutil
import logging
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from src.contracts.decorators import requires, ensures
from src.types.domain_types import HealthStatus, ServiceType, DiagnosticLevel
from src.utils.logging_config import get_logger


class ServiceStatus(Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult(NamedTuple):
    """Individual health check result."""
    service_name: str
    status: ServiceStatus
    response_time_ms: float
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""
    timestamp: float
    overall_status: ServiceStatus
    keyboard_maestro_status: ServiceStatus
    applescript_pool_status: ServiceStatus
    system_integration_status: ServiceStatus
    individual_checks: List[HealthCheckResult]
    recommendations: List[str]
    
    @property
    def is_healthy(self) -> bool:
        """Check if system is overall healthy."""
        return self.overall_status == ServiceStatus.HEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'overall_status': self.overall_status.value,
            'service_status': {
                'keyboard_maestro': self.keyboard_maestro_status.value,
                'applescript_pool': self.applescript_pool_status.value,
                'system_integration': self.system_integration_status.value
            },
            'individual_checks': [
                {
                    'service': check.service_name,
                    'status': check.status.value,
                    'response_time_ms': check.response_time_ms,
                    'message': check.message,
                    'details': check.details or {}
                }
                for check in self.individual_checks
            ],
            'recommendations': self.recommendations
        }


class SystemHealthMonitor:
    """Comprehensive system health monitoring and diagnostics."""
    
    def __init__(self, km_interface=None, applescript_pool=None):
        """Initialize health monitor.
        
        Args:
            km_interface: Keyboard Maestro interface instance
            applescript_pool: AppleScript connection pool instance
        """
        self._logger = get_logger(__name__)
        self._km_interface = km_interface
        self._applescript_pool = applescript_pool
        
        # Health check configuration
        self._check_timeout = 10.0  # seconds
        self._km_engine_process_name = "Keyboard Maestro Engine"
        self._km_app_process_name = "Keyboard Maestro"
        
        self._logger.debug("System health monitor initialized")
    
    @requires(lambda self: True)  # No preconditions for health checks
    @ensures(lambda result: result.overall_status in ServiceStatus)
    async def perform_comprehensive_health_check(self) -> SystemHealthReport:
        """Perform comprehensive system health assessment.
        
        Returns:
            Complete health report with recommendations
        """
        start_time = time.time()
        individual_checks = []
        recommendations = []
        
        try:
            # Perform individual health checks
            km_engine_check = await self._check_keyboard_maestro_engine()
            individual_checks.append(km_engine_check)
            
            km_app_check = await self._check_keyboard_maestro_app()
            individual_checks.append(km_app_check)
            
            applescript_check = await self._check_applescript_connectivity()
            individual_checks.append(applescript_check)
            
            pool_check = await self._check_applescript_pool_health()
            individual_checks.append(pool_check)
            
            permissions_check = await self._check_system_permissions()
            individual_checks.append(permissions_check)
            
            # Determine service-level statuses
            km_status = self._determine_km_status([km_engine_check, km_app_check])
            applescript_status = self._determine_applescript_status([applescript_check, pool_check])
            system_status = self._determine_system_status([permissions_check])
            
            # Determine overall status
            overall_status = self._determine_overall_status([km_status, applescript_status, system_status])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(individual_checks)
            
            return SystemHealthReport(
                timestamp=time.time(),
                overall_status=overall_status,
                keyboard_maestro_status=km_status,
                applescript_pool_status=applescript_status,
                system_integration_status=system_status,
                individual_checks=individual_checks,
                recommendations=recommendations
            )
            
        except Exception as e:
            self._logger.error(f"Health check failed: {e}", exc_info=True)
            
            # Return unhealthy status on error
            return SystemHealthReport(
                timestamp=time.time(),
                overall_status=ServiceStatus.UNHEALTHY,
                keyboard_maestro_status=ServiceStatus.UNKNOWN,
                applescript_pool_status=ServiceStatus.UNKNOWN,
                system_integration_status=ServiceStatus.UNKNOWN,
                individual_checks=individual_checks,
                recommendations=["System health check failed - see logs for details"]
            )
    
    async def _check_keyboard_maestro_engine(self) -> HealthCheckResult:
        """Check Keyboard Maestro Engine availability."""
        start_time = time.time()
        
        try:
            # Check if Keyboard Maestro Engine process is running
            km_engine_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] == self._km_engine_process_name:
                        km_engine_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            response_time = (time.time() - start_time) * 1000
            
            if km_engine_running:
                return HealthCheckResult(
                    service_name="keyboard_maestro_engine",
                    status=ServiceStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Keyboard Maestro Engine is running",
                    details={"process_found": True}
                )
            else:
                return HealthCheckResult(
                    service_name="keyboard_maestro_engine",
                    status=ServiceStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Keyboard Maestro Engine is not running",
                    details={"process_found": False}
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="keyboard_maestro_engine",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=response_time,
                message=f"Failed to check engine status: {e}",
                details={"error": str(e)}
            )
    
    async def _check_keyboard_maestro_app(self) -> HealthCheckResult:
        """Check Keyboard Maestro application availability."""
        start_time = time.time()
        
        try:
            # Check if Keyboard Maestro app is running
            km_app_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] == self._km_app_process_name:
                        km_app_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            response_time = (time.time() - start_time) * 1000
            
            if km_app_running:
                return HealthCheckResult(
                    service_name="keyboard_maestro_app",
                    status=ServiceStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Keyboard Maestro application is running",
                    details={"process_found": True}
                )
            else:
                # App not running is degraded, not unhealthy (engine is more critical)
                return HealthCheckResult(
                    service_name="keyboard_maestro_app",
                    status=ServiceStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="Keyboard Maestro application is not running",
                    details={"process_found": False}
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="keyboard_maestro_app",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=response_time,
                message=f"Failed to check app status: {e}",
                details={"error": str(e)}
            )
    
    async def _check_applescript_connectivity(self) -> HealthCheckResult:
        """Check basic AppleScript connectivity."""
        start_time = time.time()
        
        try:
            # Test basic AppleScript execution
            script = 'tell application "System Events" to return name of current user'
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self._check_timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if process.returncode == 0 and stdout:
                return HealthCheckResult(
                    service_name="applescript_connectivity",
                    status=ServiceStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="AppleScript connectivity working",
                    details={"test_result": stdout.decode().strip()}
                )
            else:
                return HealthCheckResult(
                    service_name="applescript_connectivity",
                    status=ServiceStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="AppleScript connectivity failed",
                    details={"error": stderr.decode() if stderr else "Unknown error"}
                )
                
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="applescript_connectivity",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="AppleScript connectivity timeout",
                details={"timeout": self._check_timeout}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="applescript_connectivity",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=response_time,
                message=f"Failed to test AppleScript: {e}",
                details={"error": str(e)}
            )
    
    async def _check_applescript_pool_health(self) -> HealthCheckResult:
        """Check AppleScript connection pool health."""
        start_time = time.time()
        
        try:
            if not self._applescript_pool:
                response_time = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    service_name="applescript_pool",
                    status=ServiceStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="AppleScript pool not configured",
                    details={"pool_available": False}
                )
            
            # Check pool status through interface
            pool_stats = await self._applescript_pool.get_pool_statistics()
            response_time = (time.time() - start_time) * 1000
            
            total_connections = pool_stats.get('total_connections', 0)
            active_connections = pool_stats.get('active_connections', 0)
            available_connections = pool_stats.get('available_connections', 0)
            
            if total_connections > 0 and available_connections > 0:
                status = ServiceStatus.HEALTHY
                message = f"AppleScript pool healthy ({available_connections} available)"
            elif total_connections > 0:
                status = ServiceStatus.DEGRADED
                message = f"AppleScript pool degraded (no available connections)"
            else:
                status = ServiceStatus.UNHEALTHY
                message = "AppleScript pool has no connections"
            
            return HealthCheckResult(
                service_name="applescript_pool",
                status=status,
                response_time_ms=response_time,
                message=message,
                details=pool_stats
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="applescript_pool",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=response_time,
                message=f"Failed to check pool health: {e}",
                details={"error": str(e)}
            )
    
    async def _check_system_permissions(self) -> HealthCheckResult:
        """Check system permissions for automation."""
        start_time = time.time()
        
        try:
            # Test accessibility permissions through AppleScript
            script = '''
            tell application "System Events"
                try
                    get processes
                    return "accessible"
                on error
                    return "not_accessible"
                end try
            end tell
            '''
            
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self._check_timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if process.returncode == 0:
                result = stdout.decode().strip()
                if result == "accessible":
                    return HealthCheckResult(
                        service_name="system_permissions",
                        status=ServiceStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="System accessibility permissions granted",
                        details={"accessibility_granted": True}
                    )
                else:
                    return HealthCheckResult(
                        service_name="system_permissions",
                        status=ServiceStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message="System accessibility permissions denied",
                        details={"accessibility_granted": False}
                    )
            else:
                return HealthCheckResult(
                    service_name="system_permissions",
                    status=ServiceStatus.UNKNOWN,
                    response_time_ms=response_time,
                    message="Failed to check permissions",
                    details={"error": stderr.decode() if stderr else "Unknown error"}
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="system_permissions",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=response_time,
                message=f"Permission check failed: {e}",
                details={"error": str(e)}
            )
    
    def _determine_km_status(self, checks: List[HealthCheckResult]) -> ServiceStatus:
        """Determine Keyboard Maestro overall status."""
        engine_status = next((c.status for c in checks if c.service_name == "keyboard_maestro_engine"), ServiceStatus.UNKNOWN)
        app_status = next((c.status for c in checks if c.service_name == "keyboard_maestro_app"), ServiceStatus.UNKNOWN)
        
        # Engine is critical, app is less critical
        if engine_status == ServiceStatus.UNHEALTHY:
            return ServiceStatus.UNHEALTHY
        elif engine_status == ServiceStatus.DEGRADED or app_status == ServiceStatus.UNHEALTHY:
            return ServiceStatus.DEGRADED
        elif engine_status == ServiceStatus.HEALTHY:
            return ServiceStatus.HEALTHY
        else:
            return ServiceStatus.UNKNOWN
    
    def _determine_applescript_status(self, checks: List[HealthCheckResult]) -> ServiceStatus:
        """Determine AppleScript overall status."""
        connectivity_status = next((c.status for c in checks if c.service_name == "applescript_connectivity"), ServiceStatus.UNKNOWN)
        pool_status = next((c.status for c in checks if c.service_name == "applescript_pool"), ServiceStatus.UNKNOWN)
        
        # Connectivity is critical, pool is optimization
        if connectivity_status == ServiceStatus.UNHEALTHY:
            return ServiceStatus.UNHEALTHY
        elif connectivity_status == ServiceStatus.DEGRADED or pool_status == ServiceStatus.UNHEALTHY:
            return ServiceStatus.DEGRADED
        elif connectivity_status == ServiceStatus.HEALTHY:
            return ServiceStatus.HEALTHY
        else:
            return ServiceStatus.UNKNOWN
    
    def _determine_system_status(self, checks: List[HealthCheckResult]) -> ServiceStatus:
        """Determine system integration status."""
        permissions_status = next((c.status for c in checks if c.service_name == "system_permissions"), ServiceStatus.UNKNOWN)
        return permissions_status
    
    def _determine_overall_status(self, service_statuses: List[ServiceStatus]) -> ServiceStatus:
        """Determine overall system status."""
        if any(status == ServiceStatus.UNHEALTHY for status in service_statuses):
            return ServiceStatus.UNHEALTHY
        elif any(status == ServiceStatus.DEGRADED for status in service_statuses):
            return ServiceStatus.DEGRADED
        elif all(status == ServiceStatus.HEALTHY for status in service_statuses):
            return ServiceStatus.HEALTHY
        else:
            return ServiceStatus.UNKNOWN
    
    def _generate_recommendations(self, checks: List[HealthCheckResult]) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []
        
        for check in checks:
            if check.status == ServiceStatus.UNHEALTHY:
                if check.service_name == "keyboard_maestro_engine":
                    recommendations.append("Start Keyboard Maestro Engine application")
                elif check.service_name == "applescript_connectivity":
                    recommendations.append("Check AppleScript permissions and system configuration")
                elif check.service_name == "system_permissions":
                    recommendations.append("Grant accessibility permissions in System Preferences > Security & Privacy")
            elif check.status == ServiceStatus.DEGRADED:
                if check.service_name == "keyboard_maestro_app":
                    recommendations.append("Consider starting Keyboard Maestro application for full functionality")
                elif check.service_name == "applescript_pool":
                    recommendations.append("AppleScript pool may need restart or configuration adjustment")
        
        return recommendations
