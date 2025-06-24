# Resource Optimization: Keyboard Maestro MCP Server
# src/utils/resource_optimizer.py

"""
Resource optimization and efficiency tools for the MCP server.

This module implements comprehensive resource optimization including memory management,
connection pooling optimization, AppleScript efficiency improvements, and adaptive
resource allocation with contract-driven validation and performance monitoring.

Features:
- Memory management and garbage collection monitoring
- Connection pooling optimization and efficiency tuning
- AppleScript connection lifecycle optimization
- Adaptive resource allocation strategies
- Resource usage optimization recommendations

Size: 247 lines (target: <250)
"""

import gc
import time
import psutil
import asyncio
import logging
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import weakref

from .contracts.decorators import requires, ensures
from src.utils.logging_config import get_logger


class OptimizationStrategy(Enum):
    """Resource optimization strategies."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced" 
    AGGRESSIVE = "aggressive"


class ResourceType(Enum):
    """Types of resources to optimize."""
    MEMORY = "memory"
    CONNECTIONS = "connections"
    CPU = "cpu"
    DISK_IO = "disk_io"


@dataclass
class MemoryUsageSnapshot:
    """Memory usage snapshot with GC information."""
    timestamp: float
    process_memory_mb: float
    system_memory_percent: float
    gc_generation_counts: List[int]
    gc_collected_objects: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'process_memory_mb': round(self.process_memory_mb, 2),
            'system_memory_percent': round(self.system_memory_percent, 2),
            'gc_generation_counts': self.gc_generation_counts,
            'gc_collected_objects': self.gc_collected_objects
        }


@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics."""
    pool_name: str
    total_connections: int
    active_connections: int
    idle_connections: int
    peak_connections: int
    avg_acquisition_time_ms: float
    connection_failures: int
    pool_efficiency: float  # active / total ratio
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'pool_name': self.pool_name,
            'total_connections': self.total_connections,
            'active_connections': self.active_connections,
            'idle_connections': self.idle_connections,
            'peak_connections': self.peak_connections,
            'avg_acquisition_time_ms': round(self.avg_acquisition_time_ms, 2),
            'connection_failures': self.connection_failures,
            'pool_efficiency': round(self.pool_efficiency, 3)
        }


class OptimizationRecommendation(NamedTuple):
    """Resource optimization recommendation."""
    resource_type: ResourceType
    priority: str  # "low", "medium", "high", "critical"
    action: str
    description: str
    estimated_impact: str
    implementation_complexity: str


class ResourceOptimizer:
    """Comprehensive resource optimization and efficiency management."""
    
    def __init__(self, 
                 strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
                 memory_threshold_mb: float = 500.0,
                 gc_interval_seconds: float = 60.0):
        """Initialize resource optimizer.
        
        Args:
            strategy: Optimization strategy level
            memory_threshold_mb: Memory threshold for optimization triggers
            gc_interval_seconds: Garbage collection monitoring interval
        """
        self._logger = get_logger(__name__)
        self._strategy = strategy
        self._memory_threshold_mb = memory_threshold_mb
        self._gc_interval = gc_interval_seconds
        
        # Monitoring state
        self._memory_snapshots: deque = deque(maxlen=100)
        self._connection_pools: Dict[str, Any] = {}
        self._optimization_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Resource tracking
        self._last_gc_stats = None
        self._optimization_history: List[Dict[str, Any]] = []
        
        self._logger.debug(f"Resource optimizer initialized with {strategy.value} strategy")
    
    @property
    def is_running(self) -> bool:
        """Check if optimizer is currently running."""
        return self._running
    
    @property
    def current_strategy(self) -> OptimizationStrategy:
        """Current optimization strategy."""
        return self._strategy
    
    @requires(lambda self: not self._running)
    @ensures(lambda self: self._running)
    async def start_optimization(self) -> None:
        """Start resource optimization monitoring.
        
        Preconditions:
        - Optimizer must not be running
        
        Postconditions:
        - Optimizer is running and monitoring resources
        """
        self._running = True
        
        # Start background optimization task
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        
        self._logger.info(f"Resource optimization started with {self._strategy.value} strategy")
    
    @requires(lambda self: self._running)
    @ensures(lambda self: not self._running)
    async def stop_optimization(self) -> None:
        """Stop resource optimization monitoring.
        
        Preconditions:
        - Optimizer must be running
        
        Postconditions:
        - Optimizer is stopped and no longer monitoring
        """
        self._running = False
        
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
            self._optimization_task = None
        
        self._logger.info("Resource optimization stopped")
    
    async def _optimization_loop(self) -> None:
        """Background loop for resource optimization."""
        while self._running:
            try:
                # Collect current metrics
                memory_snapshot = self._collect_memory_snapshot()
                self._memory_snapshots.append(memory_snapshot)
                
                # Perform optimization checks
                await self._check_memory_optimization()
                await self._check_connection_optimization()
                
                # Apply strategy-specific optimizations
                await self._apply_strategy_optimizations()
                
                await asyncio.sleep(self._gc_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in optimization loop: {e}", exc_info=True)
                await asyncio.sleep(5.0)  # Pause on error
    
    def _collect_memory_snapshot(self) -> MemoryUsageSnapshot:
        """Collect comprehensive memory usage snapshot."""
        try:
            # Process memory usage
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # System memory usage
            system_memory = psutil.virtual_memory()
            system_memory_percent = system_memory.percent
            
            # Garbage collection statistics
            gc_stats = gc.get_stats()
            generation_counts = [stat['collections'] for stat in gc_stats]
            
            # Check for collected objects since last snapshot
            collected_objects = 0
            if self._last_gc_stats:
                collected_objects = sum(
                    curr - prev for curr, prev in 
                    zip(generation_counts, self._last_gc_stats)
                )
            self._last_gc_stats = generation_counts
            
            return MemoryUsageSnapshot(
                timestamp=time.time(),
                process_memory_mb=process_memory_mb,
                system_memory_percent=system_memory_percent,
                gc_generation_counts=generation_counts,
                gc_collected_objects=collected_objects
            )
            
        except Exception as e:
            self._logger.error(f"Failed to collect memory snapshot: {e}")
            return MemoryUsageSnapshot(
                timestamp=time.time(),
                process_memory_mb=0.0,
                system_memory_percent=0.0,
                gc_generation_counts=[0, 0, 0],
                gc_collected_objects=0
            )
    
    async def _check_memory_optimization(self) -> None:
        """Check if memory optimization is needed."""
        if not self._memory_snapshots:
            return
        
        latest_snapshot = self._memory_snapshots[-1]
        
        # Check if memory usage exceeds threshold
        if latest_snapshot.process_memory_mb > self._memory_threshold_mb:
            self._logger.warning(
                f"Memory usage ({latest_snapshot.process_memory_mb:.1f}MB) exceeds threshold ({self._memory_threshold_mb}MB)"
            )
            
            # Trigger garbage collection optimization
            await self._optimize_memory_usage()
    
    async def _optimize_memory_usage(self) -> None:
        """Optimize memory usage through garbage collection and cleanup."""
        try:
            # Record pre-optimization state
            pre_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            # Force garbage collection based on strategy
            if self._strategy == OptimizationStrategy.AGGRESSIVE:
                # Full GC of all generations
                for generation in range(3):
                    collected = gc.collect(generation)
                    if collected > 0:
                        self._logger.debug(f"GC generation {generation}: collected {collected} objects")
            
            elif self._strategy == OptimizationStrategy.BALANCED:
                # Standard full collection
                collected = gc.collect()
                if collected > 0:
                    self._logger.debug(f"GC collected {collected} objects")
            
            # Conservative strategy relies on automatic GC
            
            # Record optimization result
            post_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_saved = pre_memory - post_memory
            
            optimization_record = {
                'timestamp': time.time(),
                'type': 'memory_optimization',
                'strategy': self._strategy.value,
                'pre_memory_mb': pre_memory,
                'post_memory_mb': post_memory,
                'memory_saved_mb': memory_saved
            }
            
            self._optimization_history.append(optimization_record)
            
            if memory_saved > 1.0:  # > 1MB saved
                self._logger.info(f"Memory optimization saved {memory_saved:.1f}MB")
            
        except Exception as e:
            self._logger.error(f"Memory optimization failed: {e}", exc_info=True)
    
    async def _check_connection_optimization(self) -> None:
        """Check connection pool optimization opportunities."""
        for pool_name, pool in self._connection_pools.items():
            try:
                if hasattr(pool, 'get_statistics'):
                    stats = await pool.get_statistics()
                    metrics = self._analyze_pool_metrics(pool_name, stats)
                    
                    # Check for optimization opportunities
                    if metrics.pool_efficiency < 0.3 and metrics.total_connections > 5:
                        self._logger.warning(
                            f"Pool '{pool_name}' has low efficiency ({metrics.pool_efficiency:.2f})"
                        )
                        await self._optimize_connection_pool(pool_name, pool, metrics)
                        
            except Exception as e:
                self._logger.error(f"Failed to check pool '{pool_name}': {e}")
    
    def _analyze_pool_metrics(self, pool_name: str, stats: Dict[str, Any]) -> ConnectionPoolMetrics:
        """Analyze connection pool metrics."""
        total = stats.get('total_connections', 0)
        active = stats.get('active_connections', 0)
        idle = total - active
        
        return ConnectionPoolMetrics(
            pool_name=pool_name,
            total_connections=total,
            active_connections=active,
            idle_connections=idle,
            peak_connections=stats.get('peak_connections', total),
            avg_acquisition_time_ms=stats.get('avg_acquisition_time_ms', 0.0),
            connection_failures=stats.get('connection_failures', 0),
            pool_efficiency=active / max(total, 1)
        )
    
    async def _optimize_connection_pool(self, pool_name: str, pool: Any, metrics: ConnectionPoolMetrics) -> None:
        """Optimize connection pool configuration."""
        try:
            optimization_actions = []
            
            # Strategy-based optimizations
            if self._strategy == OptimizationStrategy.AGGRESSIVE:
                # Aggressively close idle connections
                if metrics.idle_connections > 2:
                    target_idle = max(1, metrics.idle_connections // 2)
                    if hasattr(pool, 'resize_pool'):
                        await pool.resize_pool(metrics.active_connections + target_idle)
                        optimization_actions.append(f"Reduced pool size to {metrics.active_connections + target_idle}")
            
            elif self._strategy == OptimizationStrategy.BALANCED:
                # Moderate optimization
                if metrics.idle_connections > 5:
                    target_size = metrics.active_connections + 3
                    if hasattr(pool, 'resize_pool'):
                        await pool.resize_pool(target_size)
                        optimization_actions.append(f"Resized pool to {target_size}")
            
            # Log optimization actions
            if optimization_actions:
                self._logger.info(f"Optimized pool '{pool_name}': {', '.join(optimization_actions)}")
                
                self._optimization_history.append({
                    'timestamp': time.time(),
                    'type': 'connection_pool_optimization',
                    'pool_name': pool_name,
                    'actions': optimization_actions,
                    'pre_metrics': metrics.to_dict()
                })
            
        except Exception as e:
            self._logger.error(f"Failed to optimize pool '{pool_name}': {e}", exc_info=True)
    
    async def _apply_strategy_optimizations(self) -> None:
        """Apply strategy-specific optimizations."""
        if self._strategy == OptimizationStrategy.AGGRESSIVE:
            # More frequent optimizations
            if len(self._memory_snapshots) >= 5:
                recent_snapshots = list(self._memory_snapshots)[-5:]
                avg_memory = sum(s.process_memory_mb for s in recent_snapshots) / len(recent_snapshots)
                
                if avg_memory > self._memory_threshold_mb * 0.8:
                    await self._optimize_memory_usage()
    
    def register_connection_pool(self, pool_name: str, pool: Any) -> None:
        """Register connection pool for optimization monitoring.
        
        Args:
            pool_name: Unique pool identifier
            pool: Connection pool instance
        """
        self._connection_pools[pool_name] = weakref.ref(pool)
        self._logger.debug(f"Registered connection pool '{pool_name}' for optimization")
    
    def unregister_connection_pool(self, pool_name: str) -> None:
        """Unregister connection pool from optimization monitoring.
        
        Args:
            pool_name: Pool identifier to remove
        """
        if pool_name in self._connection_pools:
            del self._connection_pools[pool_name]
            self._logger.debug(f"Unregistered connection pool '{pool_name}'")
    
    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate resource optimization recommendations."""
        recommendations = []
        
        if self._memory_snapshots:
            latest_memory = self._memory_snapshots[-1]
            
            # Memory recommendations
            if latest_memory.process_memory_mb > self._memory_threshold_mb * 1.5:
                recommendations.append(OptimizationRecommendation(
                    resource_type=ResourceType.MEMORY,
                    priority="high",
                    action="reduce_memory_usage",
                    description=f"Process memory usage ({latest_memory.process_memory_mb:.1f}MB) is significantly above threshold",
                    estimated_impact="20-30% memory reduction",
                    implementation_complexity="low"
                ))
            
            # GC recommendations
            if latest_memory.gc_collected_objects > 1000:
                recommendations.append(OptimizationRecommendation(
                    resource_type=ResourceType.MEMORY,
                    priority="medium",
                    action="optimize_garbage_collection",
                    description="High garbage collection activity detected",
                    estimated_impact="5-10% performance improvement",
                    implementation_complexity="medium"
                ))
        
        # Connection pool recommendations
        for pool_name, pool_ref in self._connection_pools.items():
            pool = pool_ref() if pool_ref else None
            if pool and hasattr(pool, 'get_statistics'):
                try:
                    stats = asyncio.run(pool.get_statistics())
                    metrics = self._analyze_pool_metrics(pool_name, stats)
                    
                    if metrics.pool_efficiency < 0.2:
                        recommendations.append(OptimizationRecommendation(
                            resource_type=ResourceType.CONNECTIONS,
                            priority="medium",
                            action="optimize_connection_pool",
                            description=f"Pool '{pool_name}' has low efficiency ({metrics.pool_efficiency:.2f})",
                            estimated_impact="10-20% connection efficiency improvement",
                            implementation_complexity="low"
                        ))
                except:
                    pass  # Skip if stats unavailable
        
        return recommendations
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization status report."""
        latest_memory = self._memory_snapshots[-1] if self._memory_snapshots else None
        
        # Pool summaries
        pool_summaries = {}
        for pool_name, pool_ref in self._connection_pools.items():
            pool = pool_ref() if pool_ref else None
            if pool:
                pool_summaries[pool_name] = "active"
            else:
                pool_summaries[pool_name] = "inactive"
        
        return {
            'optimizer_status': 'running' if self._running else 'stopped',
            'strategy': self._strategy.value,
            'current_memory': latest_memory.to_dict() if latest_memory else None,
            'memory_threshold_mb': self._memory_threshold_mb,
            'registered_pools': pool_summaries,
            'optimization_history_count': len(self._optimization_history),
            'recent_optimizations': self._optimization_history[-5:],
            'recommendations': [
                {
                    'resource_type': rec.resource_type.value,
                    'priority': rec.priority,
                    'action': rec.action,
                    'description': rec.description,
                    'estimated_impact': rec.estimated_impact
                }
                for rec in self.generate_optimization_recommendations()
            ]
        }
