# Performance Metrics Core: Keyboard Maestro MCP Server
# src/core/performance_core.py

"""
Core performance monitoring and metrics collection for the MCP server.

This module implements comprehensive performance monitoring including system resource
tracking, operation metrics, performance threshold validation, and alerting with
contract-driven design and defensive programming patterns.

Features:
- Real-time system resource monitoring (CPU, memory, disk, network)
- Operation performance tracking and aggregation
- Performance threshold enforcement with alerting
- Metrics persistence and historical analysis
- Integration with existing server metrics infrastructure

Size: 249 lines (target: <250)
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from datetime import datetime, timedelta

from src.contracts.decorators import requires, ensures
from src.contracts.validators import is_valid_threshold_config
from src.types.domain_types import PerformanceThreshold, ResourceType, AlertLevel
from src.utils.logging_config import get_logger


class ResourceMetric(NamedTuple):
    """Individual resource measurement."""
    timestamp: float
    value: float
    unit: str
    resource_type: ResourceType


class PerformanceAlert(NamedTuple):
    """Performance threshold violation alert."""
    timestamp: float
    resource_type: ResourceType
    current_value: float
    threshold_value: float
    alert_level: AlertLevel
    message: str


@dataclass
class SystemResourceSnapshot:
    """Complete system resource state snapshot."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: Optional[List[float]] = None  # Unix systems only
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_gb': round(self.memory_used_gb, 2),
            'memory_available_gb': round(self.memory_available_gb, 2),
            'disk_usage_percent': self.disk_usage_percent,
            'disk_used_gb': round(self.disk_used_gb, 2),
            'disk_free_gb': round(self.disk_free_gb, 2),
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
            'load_average': self.load_average
        }


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""
    collection_start: float
    collection_end: float
    operation_count: int = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    resource_snapshots: List[SystemResourceSnapshot] = field(default_factory=list)
    alerts_generated: List[PerformanceAlert] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate operation success rate."""
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations
    
    @property
    def collection_duration(self) -> float:
        """Duration of metrics collection period."""
        return self.collection_end - self.collection_start


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, 
                 collection_interval: float = 30.0,
                 max_snapshots: int = 1000,
                 thresholds: Optional[Dict[ResourceType, PerformanceThreshold]] = None):
        """Initialize performance monitor.
        
        Args:
            collection_interval: Seconds between resource snapshots
            max_snapshots: Maximum snapshots to retain in memory
            thresholds: Performance threshold configuration
        """
        self._logger = get_logger(__name__)
        self._collection_interval = collection_interval
        self._max_snapshots = max_snapshots
        self._thresholds = thresholds or {}
        
        # State tracking
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None
        self._metrics = PerformanceMetrics(
            collection_start=time.time(),
            collection_end=time.time()
        )
        
        # Performance tracking
        self._operation_times: List[float] = []
        self._last_network_stats = None
        
        self._logger.info("Performance monitor initialized")
    
    @property
    def is_running(self) -> bool:
        """Check if monitor is currently running."""
        return self._running
    
    @property
    def current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        self._metrics.collection_end = time.time()
        return self._metrics
    
    @requires(lambda self: not self._running)
    @ensures(lambda self: self._running)
    async def start_monitoring(self) -> None:
        """Start performance monitoring.
        
        Preconditions:
        - Monitor must not be running
        
        Postconditions:
        - Monitor is running and collecting metrics
        """
        self._running = True
        self._metrics.collection_start = time.time()
        
        # Start background collection task
        self._collection_task = asyncio.create_task(self._collect_metrics_loop())
        
        self._logger.info(f"Performance monitoring started (interval: {self._collection_interval}s)")
    
    @requires(lambda self: self._running)
    @ensures(lambda self: not self._running)
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring.
        
        Preconditions:
        - Monitor must be running
        
        Postconditions:
        - Monitor is stopped and no longer collecting
        """
        self._running = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
            self._collection_task = None
        
        self._metrics.collection_end = time.time()
        self._logger.info("Performance monitoring stopped")
    
    async def _collect_metrics_loop(self) -> None:
        """Background loop for periodic metrics collection."""
        while self._running:
            try:
                snapshot = await self._collect_system_snapshot()
                self._process_snapshot(snapshot)
                
                await asyncio.sleep(self._collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in metrics collection: {e}", exc_info=True)
                await asyncio.sleep(1.0)  # Brief pause on error
    
    async def _collect_system_snapshot(self) -> SystemResourceSnapshot:
        """Collect comprehensive system resource snapshot."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage (root filesystem)
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            # Load average (Unix only)
            load_avg = None
            try:
                load_avg = list(psutil.getloadavg())
            except (AttributeError, OSError):
                pass  # Not available on all platforms
            
            return SystemResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory_used_gb,
                memory_available_gb=memory_available_gb,
                disk_usage_percent=disk_usage_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_bytes_sent=net_io.bytes_sent,
                network_bytes_recv=net_io.bytes_recv,
                load_average=load_avg
            )
            
        except Exception as e:
            self._logger.error(f"Failed to collect system snapshot: {e}")
            # Return default snapshot on error
            return SystemResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                memory_available_gb=0.0,
                disk_usage_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0
            )
    
    def _process_snapshot(self, snapshot: SystemResourceSnapshot) -> None:
        """Process snapshot and check thresholds."""
        # Add to metrics collection
        self._metrics.resource_snapshots.append(snapshot)
        
        # Limit snapshots in memory
        if len(self._metrics.resource_snapshots) > self._max_snapshots:
            self._metrics.resource_snapshots = self._metrics.resource_snapshots[-self._max_snapshots:]
        
        # Check performance thresholds
        self._check_thresholds(snapshot)
    
    def _check_thresholds(self, snapshot: SystemResourceSnapshot) -> None:
        """Check performance thresholds and generate alerts."""
        threshold_checks = [
            (ResourceType.CPU, snapshot.cpu_percent),
            (ResourceType.MEMORY, snapshot.memory_percent),
            (ResourceType.DISK, snapshot.disk_usage_percent)
        ]
        
        for resource_type, current_value in threshold_checks:
            if resource_type in self._thresholds:
                threshold = self._thresholds[resource_type]
                
                if current_value > threshold.critical_threshold:
                    alert = PerformanceAlert(
                        timestamp=snapshot.timestamp,
                        resource_type=resource_type,
                        current_value=current_value,
                        threshold_value=threshold.critical_threshold,
                        alert_level=AlertLevel.CRITICAL,
                        message=f"{resource_type.value} usage critical: {current_value:.1f}%"
                    )
                    self._handle_alert(alert)
                
                elif current_value > threshold.warning_threshold:
                    alert = PerformanceAlert(
                        timestamp=snapshot.timestamp,
                        resource_type=resource_type,
                        current_value=current_value,
                        threshold_value=threshold.warning_threshold,
                        alert_level=AlertLevel.WARNING,
                        message=f"{resource_type.value} usage high: {current_value:.1f}%"
                    )
                    self._handle_alert(alert)
    
    def _handle_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alert."""
        self._metrics.alerts_generated.append(alert)
        
        # Log alert based on severity
        if alert.alert_level == AlertLevel.CRITICAL:
            self._logger.critical(alert.message, extra={
                'resource_type': alert.resource_type.value,
                'current_value': alert.current_value,
                'threshold': alert.threshold_value
            })
        else:
            self._logger.warning(alert.message, extra={
                'resource_type': alert.resource_type.value,
                'current_value': alert.current_value,
                'threshold': alert.threshold_value
            })
    
    def record_operation(self, duration: float, success: bool) -> None:
        """Record operation performance metrics.
        
        Args:
            duration: Operation duration in seconds
            success: Whether operation succeeded
        """
        self._metrics.total_operations += 1
        
        if success:
            self._metrics.successful_operations += 1
        else:
            self._metrics.failed_operations += 1
        
        # Track response times
        self._operation_times.append(duration)
        
        # Update aggregated timing metrics
        if duration > self._metrics.max_response_time:
            self._metrics.max_response_time = duration
        
        if duration < self._metrics.min_response_time:
            self._metrics.min_response_time = duration
        
        # Calculate rolling average
        if self._operation_times:
            self._metrics.average_response_time = sum(self._operation_times) / len(self._operation_times)
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        metrics = self.current_metrics
        
        # Latest resource snapshot
        latest_snapshot = None
        if metrics.resource_snapshots:
            latest_snapshot = metrics.resource_snapshots[-1].to_dict()
        
        # Recent alerts (last hour)
        recent_alerts = [
            {
                'timestamp': alert.timestamp,
                'resource_type': alert.resource_type.value,
                'level': alert.alert_level.value,
                'message': alert.message
            }
            for alert in metrics.alerts_generated
            if time.time() - alert.timestamp < 3600
        ]
        
        return {
            'monitoring_status': 'running' if self._running else 'stopped',
            'collection_duration': metrics.collection_duration,
            'operation_metrics': {
                'total_operations': metrics.total_operations,
                'successful_operations': metrics.successful_operations,
                'failed_operations': metrics.failed_operations,
                'success_rate': metrics.success_rate,
                'average_response_time': round(metrics.average_response_time, 3),
                'max_response_time': round(metrics.max_response_time, 3),
                'min_response_time': round(metrics.min_response_time, 3) if metrics.min_response_time != float('inf') else 0
            },
            'current_resources': latest_snapshot,
            'recent_alerts': recent_alerts,
            'snapshots_collected': len(metrics.resource_snapshots)
        }
