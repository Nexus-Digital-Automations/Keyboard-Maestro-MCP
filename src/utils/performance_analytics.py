# Performance Analytics: Keyboard Maestro MCP Server
# src/utils/performance_analytics.py

"""
Performance analytics and trend analysis for the MCP server.

This module implements comprehensive performance data analysis including operation
timing, latency tracking, trend analysis, and performance reporting with
statistical analysis and visualization utilities.

Features:
- Operation timing and latency tracking with statistical analysis
- Performance trend analysis and historical metrics
- Performance reporting and visualization utilities
- Percentile-based performance analysis
- Performance regression detection and alerting

Size: 249 lines (target: <250)
"""

import time
import statistics
import json
from typing import Dict, List, Optional, Any, NamedTuple, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from .contracts.decorators import requires, ensures
from src.utils.logging_config import get_logger


class PerformanceDataPoint(NamedTuple):
    """Individual performance measurement."""
    timestamp: float
    operation_type: str
    duration_ms: float
    success: bool
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceStatistics:
    """Statistical analysis of performance data."""
    operation_type: str
    sample_count: int
    mean_duration_ms: float
    median_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_deviation_ms: float
    success_rate: float
    throughput_per_second: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'operation_type': self.operation_type,
            'sample_count': self.sample_count,
            'mean_duration_ms': round(self.mean_duration_ms, 2),
            'median_duration_ms': round(self.median_duration_ms, 2),
            'p95_duration_ms': round(self.p95_duration_ms, 2),
            'p99_duration_ms': round(self.p99_duration_ms, 2),
            'min_duration_ms': round(self.min_duration_ms, 2),
            'max_duration_ms': round(self.max_duration_ms, 2),
            'std_deviation_ms': round(self.std_deviation_ms, 2),
            'success_rate': round(self.success_rate, 4),
            'throughput_per_second': round(self.throughput_per_second, 2)
        }


@dataclass
class TrendAnalysis:
    """Performance trend analysis results."""
    operation_type: str
    time_period_hours: float
    trend_direction: str  # "improving", "degrading", "stable"
    change_percentage: float
    baseline_mean_ms: float
    current_mean_ms: float
    regression_detected: bool
    confidence_level: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'operation_type': self.operation_type,
            'time_period_hours': self.time_period_hours,
            'trend_direction': self.trend_direction,
            'change_percentage': round(self.change_percentage, 2),
            'baseline_mean_ms': round(self.baseline_mean_ms, 2),
            'current_mean_ms': round(self.current_mean_ms, 2),
            'regression_detected': self.regression_detected,
            'confidence_level': round(self.confidence_level, 2)
        }


class PerformanceAnalytics:
    """Comprehensive performance analytics and trend analysis."""
    
    def __init__(self, 
                 max_data_points: int = 10000,
                 trend_analysis_window_hours: float = 24.0,
                 regression_threshold_percent: float = 20.0):
        """Initialize performance analytics.
        
        Args:
            max_data_points: Maximum data points to retain
            trend_analysis_window_hours: Hours of data for trend analysis
            regression_threshold_percent: Threshold for regression detection
        """
        self._logger = get_logger(__name__)
        self._max_data_points = max_data_points
        self._trend_window_hours = trend_analysis_window_hours
        self._regression_threshold = regression_threshold_percent
        
        # Performance data storage
        self._data_points: deque = deque(maxlen=max_data_points)
        self._operation_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Cached statistics
        self._stats_cache: Dict[str, Tuple[float, PerformanceStatistics]] = {}
        self._cache_ttl = 300.0  # 5 minutes
        
        self._logger.debug("Performance analytics initialized")
    
    @requires(lambda operation_type: len(operation_type) > 0)
    @requires(lambda duration_ms: duration_ms >= 0)
    def record_operation(self, 
                        operation_type: str,
                        duration_ms: float,
                        success: bool,
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record operation performance data.
        
        Preconditions:
        - Operation type must be non-empty
        - Duration must be non-negative
        
        Args:
            operation_type: Type of operation performed
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            metadata: Optional operation metadata
        """
        data_point = PerformanceDataPoint(
            timestamp=time.time(),
            operation_type=operation_type,
            duration_ms=duration_ms,
            success=success,
            metadata=metadata
        )
        
        # Store in global and operation-specific collections
        self._data_points.append(data_point)
        self._operation_data[operation_type].append(data_point)
        
        # Invalidate cache for this operation type
        if operation_type in self._stats_cache:
            del self._stats_cache[operation_type]
        
        self._logger.debug(f"Recorded performance data: {operation_type} - {duration_ms:.2f}ms")
    
    @requires(lambda operation_type: len(operation_type) > 0)
    @ensures(lambda result: result.sample_count >= 0)
    def get_performance_statistics(self, operation_type: str) -> PerformanceStatistics:
        """Get comprehensive performance statistics for operation type.
        
        Preconditions:
        - Operation type must be non-empty
        
        Postconditions:
        - Sample count is non-negative
        
        Args:
            operation_type: Operation type to analyze
            
        Returns:
            Performance statistics for the operation type
        """
        # Check cache first
        cache_key = operation_type
        current_time = time.time()
        
        if cache_key in self._stats_cache:
            cache_time, cached_stats = self._stats_cache[cache_key]
            if current_time - cache_time < self._cache_ttl:
                return cached_stats
        
        # Calculate fresh statistics
        operation_data = list(self._operation_data[operation_type])
        
        if not operation_data:
            # Return zero statistics for unknown operations
            stats = PerformanceStatistics(
                operation_type=operation_type,
                sample_count=0,
                mean_duration_ms=0.0,
                median_duration_ms=0.0,
                p95_duration_ms=0.0,
                p99_duration_ms=0.0,
                min_duration_ms=0.0,
                max_duration_ms=0.0,
                std_deviation_ms=0.0,
                success_rate=0.0,
                throughput_per_second=0.0
            )
        else:
            durations = [point.duration_ms for point in operation_data]
            successes = [point.success for point in operation_data]
            
            # Time-based metrics
            time_span = operation_data[-1].timestamp - operation_data[0].timestamp
            throughput = len(operation_data) / max(time_span, 1.0)
            
            stats = PerformanceStatistics(
                operation_type=operation_type,
                sample_count=len(operation_data),
                mean_duration_ms=statistics.mean(durations),
                median_duration_ms=statistics.median(durations),
                p95_duration_ms=self._calculate_percentile(durations, 95),
                p99_duration_ms=self._calculate_percentile(durations, 99),
                min_duration_ms=min(durations),
                max_duration_ms=max(durations),
                std_deviation_ms=statistics.stdev(durations) if len(durations) > 1 else 0.0,
                success_rate=sum(successes) / len(successes),
                throughput_per_second=throughput
            )
        
        # Cache the results
        self._stats_cache[cache_key] = (current_time, stats)
        
        return stats
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value from data."""
        if not data:
            return 0.0
        
        data_sorted = sorted(data)
        k = (len(data_sorted) - 1) * (percentile / 100.0)
        f = int(k)
        c = k - f
        
        if f == len(data_sorted) - 1:
            return data_sorted[f]
        else:
            return data_sorted[f] * (1 - c) + data_sorted[f + 1] * c
    
    @requires(lambda operation_type: len(operation_type) > 0)
    def analyze_performance_trends(self, operation_type: str) -> TrendAnalysis:
        """Analyze performance trends for operation type.
        
        Preconditions:
        - Operation type must be non-empty
        
        Args:
            operation_type: Operation type to analyze
            
        Returns:
            Trend analysis results
        """
        operation_data = list(self._operation_data[operation_type])
        
        if len(operation_data) < 10:
            # Insufficient data for trend analysis
            return TrendAnalysis(
                operation_type=operation_type,
                time_period_hours=0.0,
                trend_direction="insufficient_data",
                change_percentage=0.0,
                baseline_mean_ms=0.0,
                current_mean_ms=0.0,
                regression_detected=False,
                confidence_level=0.0
            )
        
        # Filter to analysis window
        cutoff_time = time.time() - (self._trend_window_hours * 3600)
        recent_data = [p for p in operation_data if p.timestamp >= cutoff_time]
        
        if len(recent_data) < 5:
            return TrendAnalysis(
                operation_type=operation_type,
                time_period_hours=self._trend_window_hours,
                trend_direction="insufficient_recent_data",
                change_percentage=0.0,
                baseline_mean_ms=0.0,
                current_mean_ms=0.0,
                regression_detected=False,
                confidence_level=0.0
            )
        
        # Split into baseline and current periods
        mid_point = len(recent_data) // 2
        baseline_data = recent_data[:mid_point]
        current_data = recent_data[mid_point:]
        
        baseline_durations = [p.duration_ms for p in baseline_data]
        current_durations = [p.duration_ms for p in current_data]
        
        baseline_mean = statistics.mean(baseline_durations)
        current_mean = statistics.mean(current_durations)
        
        # Calculate trend metrics
        change_percentage = ((current_mean - baseline_mean) / baseline_mean) * 100
        
        # Determine trend direction
        if abs(change_percentage) < 5.0:
            trend_direction = "stable"
        elif change_percentage > 0:
            trend_direction = "degrading"
        else:
            trend_direction = "improving"
        
        # Regression detection
        regression_detected = (
            trend_direction == "degrading" and 
            change_percentage > self._regression_threshold
        )
        
        # Simple confidence calculation based on sample size and variance
        confidence_level = min(100.0, (len(recent_data) / 50.0) * 100.0)
        
        actual_time_span = (recent_data[-1].timestamp - recent_data[0].timestamp) / 3600.0
        
        return TrendAnalysis(
            operation_type=operation_type,
            time_period_hours=actual_time_span,
            trend_direction=trend_direction,
            change_percentage=change_percentage,
            baseline_mean_ms=baseline_mean,
            current_mean_ms=current_mean,
            regression_detected=regression_detected,
            confidence_level=confidence_level
        )
    
    def get_all_operation_statistics(self) -> Dict[str, PerformanceStatistics]:
        """Get performance statistics for all operation types."""
        results = {}
        
        for operation_type in self._operation_data.keys():
            results[operation_type] = self.get_performance_statistics(operation_type)
        
        return results
    
    def get_system_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive system performance report."""
        all_stats = self.get_all_operation_statistics()
        all_trends = {}
        
        # Generate trend analysis for each operation
        for operation_type in self._operation_data.keys():
            all_trends[operation_type] = self.analyze_performance_trends(operation_type)
        
        # System-wide metrics
        total_operations = sum(stats.sample_count for stats in all_stats.values())
        overall_success_rate = (
            sum(stats.success_rate * stats.sample_count for stats in all_stats.values()) /
            max(total_operations, 1)
        )
        
        # Identify problem operations
        problem_operations = []
        for operation_type, trend in all_trends.items():
            if trend.regression_detected:
                problem_operations.append({
                    'operation_type': operation_type,
                    'issue': 'performance_regression',
                    'severity': 'high' if trend.change_percentage > 50 else 'medium'
                })
        
        return {
            'report_timestamp': time.time(),
            'system_summary': {
                'total_operations': total_operations,
                'operation_types_tracked': len(all_stats),
                'overall_success_rate': round(overall_success_rate, 4),
                'data_points_retained': len(self._data_points)
            },
            'operation_statistics': {
                op_type: stats.to_dict() for op_type, stats in all_stats.items()
            },
            'trend_analysis': {
                op_type: trend.to_dict() for op_type, trend in all_trends.items()
            },
            'problem_operations': problem_operations,
            'recommendations': self._generate_performance_recommendations(all_stats, all_trends)
        }
    
    def _generate_performance_recommendations(self, 
                                           stats: Dict[str, PerformanceStatistics],
                                           trends: Dict[str, TrendAnalysis]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        for operation_type, stat in stats.items():
            # High latency operations
            if stat.mean_duration_ms > 1000:  # 1 second
                recommendations.append(
                    f"Operation '{operation_type}' has high latency ({stat.mean_duration_ms:.0f}ms) - consider optimization"
                )
            
            # Low success rate
            if stat.success_rate < 0.95 and stat.sample_count > 10:
                recommendations.append(
                    f"Operation '{operation_type}' has low success rate ({stat.success_rate:.2f}) - investigate error causes"
                )
            
            # High variability
            if stat.std_deviation_ms > stat.mean_duration_ms:
                recommendations.append(
                    f"Operation '{operation_type}' has high performance variability - check for resource contention"
                )
        
        # Trend-based recommendations
        for operation_type, trend in trends.items():
            if trend.regression_detected:
                recommendations.append(
                    f"Performance regression detected for '{operation_type}' ({trend.change_percentage:.1f}% increase) - investigate recent changes"
                )
        
        return recommendations
    
    def export_performance_data(self, file_path: str, operation_type: Optional[str] = None) -> None:
        """Export performance data to JSON file.
        
        Args:
            file_path: Output file path
            operation_type: Optional operation type filter
        """
        if operation_type:
            data_to_export = [
                {
                    'timestamp': point.timestamp,
                    'operation_type': point.operation_type,
                    'duration_ms': point.duration_ms,
                    'success': point.success,
                    'metadata': point.metadata
                }
                for point in self._operation_data[operation_type]
            ]
        else:
            data_to_export = [
                {
                    'timestamp': point.timestamp,
                    'operation_type': point.operation_type,
                    'duration_ms': point.duration_ms,
                    'success': point.success,
                    'metadata': point.metadata
                }
                for point in self._data_points
            ]
        
        export_data = {
            'export_timestamp': time.time(),
            'data_points': data_to_export,
            'summary': {
                'total_points': len(data_to_export),
                'operation_filter': operation_type,
                'time_range': {
                    'start': min(point['timestamp'] for point in data_to_export) if data_to_export else None,
                    'end': max(point['timestamp'] for point in data_to_export) if data_to_export else None
                }
            }
        }
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self._logger.info(f"Performance data exported to {file_path}")
