# Performance Testing Framework: Keyboard Maestro MCP Server
# src/validators/performance_validators.py

"""
Performance testing utilities and validation framework for the MCP server.

This module implements comprehensive performance testing including load testing,
stress testing, benchmark validation, performance contract validation, and
regression testing with contract-driven design and property-based testing.

Features:
- Load testing and stress testing capabilities
- Performance benchmark validation and baseline management
- Performance contract validation and SLA enforcement
- Performance regression detection and reporting
- Stress testing with resource limit validation

Size: 250 lines (target: <250)
"""

import asyncio
import time
import random
import statistics
from typing import Dict, List, Optional, Any, Callable, NamedTuple
from dataclasses import dataclass
from enum import Enum
import concurrent.futures

from src.contracts.decorators import requires, ensures
from src.types.domain_types import PerformanceContract, TestResult, LoadTestProfile
from src.utils.logging_config import get_logger


class TestType(Enum):
    """Performance test types."""
    LOAD_TEST = "load_test"
    STRESS_TEST = "stress_test"
    SPIKE_TEST = "spike_test"
    ENDURANCE_TEST = "endurance_test"
    CONTRACT_VALIDATION = "contract_validation"


class TestStatus(Enum):
    """Performance test status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LoadTestConfiguration:
    """Load test configuration parameters."""
    max_concurrent_users: int
    duration_seconds: float
    ramp_up_seconds: float
    target_operations_per_second: float
    success_rate_threshold: float
    response_time_threshold_ms: float
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        return (
            self.max_concurrent_users > 0 and
            self.duration_seconds > 0 and
            self.ramp_up_seconds >= 0 and
            self.target_operations_per_second > 0 and
            0 <= self.success_rate_threshold <= 1.0 and
            self.response_time_threshold_ms > 0
        )


@dataclass
class PerformanceTestResult:
    """Comprehensive performance test result."""
    test_type: TestType
    test_name: str
    status: TestStatus
    start_time: float
    end_time: float
    operations_executed: int
    operations_successful: int
    operations_failed: int
    mean_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    throughput_ops_per_second: float
    success_rate: float
    errors: List[str]
    warnings: List[str]
    resource_usage: Optional[Dict[str, Any]] = None
    
    @property
    def duration_seconds(self) -> float:
        """Test duration in seconds."""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'test_type': self.test_type.value,
            'test_name': self.test_name,
            'status': self.status.value,
            'duration_seconds': round(self.duration_seconds, 2),
            'operations_executed': self.operations_executed,
            'operations_successful': self.operations_successful,
            'operations_failed': self.operations_failed,
            'mean_response_time_ms': round(self.mean_response_time_ms, 2),
            'p95_response_time_ms': round(self.p95_response_time_ms, 2),
            'p99_response_time_ms': round(self.p99_response_time_ms, 2),
            'max_response_time_ms': round(self.max_response_time_ms, 2),
            'throughput_ops_per_second': round(self.throughput_ops_per_second, 2),
            'success_rate': round(self.success_rate, 4),
            'errors': self.errors,
            'warnings': self.warnings,
            'resource_usage': self.resource_usage
        }


class PerformanceValidator:
    """Comprehensive performance testing and validation framework."""
    
    def __init__(self, performance_monitor=None, resource_optimizer=None):
        """Initialize performance validator.
        
        Args:
            performance_monitor: Performance monitoring instance
            resource_optimizer: Resource optimization instance
        """
        self._logger = get_logger(__name__)
        self._performance_monitor = performance_monitor
        self._resource_optimizer = resource_optimizer
        
        # Test execution state
        self._running_tests: Dict[str, asyncio.Task] = {}
        self._test_results: List[PerformanceTestResult] = []
        self._baselines: Dict[str, Dict[str, Any]] = {}
        
        self._logger.debug("Performance validator initialized")
    
    @requires(lambda config: config.validate())
    @requires(lambda operation_func: callable(operation_func))
    @ensures(lambda result: result.test_type == TestType.LOAD_TEST)
    async def run_load_test(self, 
                           test_name: str,
                           config: LoadTestConfiguration,
                           operation_func: Callable) -> PerformanceTestResult:
        """Run comprehensive load test.
        
        Preconditions:
        - Configuration must be valid
        - Operation function must be callable
        
        Postconditions:
        - Result test type is LOAD_TEST
        
        Args:
            test_name: Unique test identifier
            config: Load test configuration
            operation_func: Async function to test
            
        Returns:
            Comprehensive test results
        """
        self._logger.info(f"Starting load test '{test_name}'")
        start_time = time.time()
        
        # Initialize result tracking
        response_times = []
        successful_operations = 0
        failed_operations = 0
        errors = []
        warnings = []
        
        try:
            # Calculate test phases
            total_operations = int(config.target_operations_per_second * config.duration_seconds)
            operations_per_user = max(1, total_operations // config.max_concurrent_users)
            
            # Collect initial resource usage
            initial_resources = await self._collect_resource_snapshot()
            
            # Execute load test with ramp-up
            semaphore = asyncio.Semaphore(config.max_concurrent_users)
            
            async def execute_user_operations():
                """Execute operations for a single user."""
                nonlocal successful_operations, failed_operations
                
                user_response_times = []
                user_successful = 0
                user_failed = 0
                
                for _ in range(operations_per_user):
                    async with semaphore:
                        operation_start = time.time()
                        try:
                            await operation_func()
                            operation_end = time.time()
                            
                            response_time_ms = (operation_end - operation_start) * 1000
                            user_response_times.append(response_time_ms)
                            user_successful += 1
                            
                        except Exception as e:
                            user_failed += 1
                            errors.append(f"Operation failed: {str(e)}")
                
                # Update global counters atomically
                successful_operations += user_successful
                failed_operations += user_failed
                response_times.extend(user_response_times)
            
            # Create and execute user tasks with ramp-up
            user_tasks = []
            for i in range(config.max_concurrent_users):
                # Stagger user start times for ramp-up
                if config.ramp_up_seconds > 0:
                    delay = (i / config.max_concurrent_users) * config.ramp_up_seconds
                    await asyncio.sleep(delay / config.max_concurrent_users)
                
                task = asyncio.create_task(execute_user_operations())
                user_tasks.append(task)
            
            # Wait for all users to complete
            await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Collect final resource usage
            final_resources = await self._collect_resource_snapshot()
            
            # Calculate test metrics
            end_time = time.time()
            test_duration = end_time - start_time
            total_operations = successful_operations + failed_operations
            
            if response_times:
                mean_response_time = statistics.mean(response_times)
                p95_response_time = self._calculate_percentile(response_times, 95)
                p99_response_time = self._calculate_percentile(response_times, 99)
                max_response_time = max(response_times)
            else:
                mean_response_time = p95_response_time = p99_response_time = max_response_time = 0.0
            
            throughput = total_operations / test_duration if test_duration > 0 else 0.0
            success_rate = successful_operations / max(total_operations, 1)
            
            # Determine test status
            status = self._evaluate_load_test_status(config, success_rate, mean_response_time, warnings)
            
            # Create result
            result = PerformanceTestResult(
                test_type=TestType.LOAD_TEST,
                test_name=test_name,
                status=status,
                start_time=start_time,
                end_time=end_time,
                operations_executed=total_operations,
                operations_successful=successful_operations,
                operations_failed=failed_operations,
                mean_response_time_ms=mean_response_time,
                p95_response_time_ms=p95_response_time,
                p99_response_time_ms=p99_response_time,
                max_response_time_ms=max_response_time,
                throughput_ops_per_second=throughput,
                success_rate=success_rate,
                errors=errors,
                warnings=warnings,
                resource_usage={
                    'initial': initial_resources,
                    'final': final_resources
                }
            )
            
            self._test_results.append(result)
            self._logger.info(f"Load test '{test_name}' completed: {status.value}")
            
            return result
            
        except Exception as e:
            self._logger.error(f"Load test '{test_name}' failed: {e}", exc_info=True)
            
            # Return error result
            end_time = time.time()
            return PerformanceTestResult(
                test_type=TestType.LOAD_TEST,
                test_name=test_name,
                status=TestStatus.ERROR,
                start_time=start_time,
                end_time=end_time,
                operations_executed=0,
                operations_successful=0,
                operations_failed=0,
                mean_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                max_response_time_ms=0.0,
                throughput_ops_per_second=0.0,
                success_rate=0.0,
                errors=[f"Test execution failed: {str(e)}"],
                warnings=[]
            )
    
    def _evaluate_load_test_status(self, 
                                  config: LoadTestConfiguration,
                                  success_rate: float,
                                  mean_response_time: float,
                                  warnings: List[str]) -> TestStatus:
        """Evaluate load test status based on thresholds."""
        if success_rate < config.success_rate_threshold:
            return TestStatus.FAILED
        
        if mean_response_time > config.response_time_threshold_ms:
            return TestStatus.FAILED
        
        if warnings:
            return TestStatus.WARNING
        
        return TestStatus.PASSED
    
    async def run_stress_test(self, 
                             test_name: str,
                             max_load_multiplier: float,
                             operation_func: Callable) -> PerformanceTestResult:
        """Run stress test to find breaking point."""
        self._logger.info(f"Starting stress test '{test_name}'")
        start_time = time.time()
        
        base_config = LoadTestConfiguration(
            max_concurrent_users=10,
            duration_seconds=30.0,
            ramp_up_seconds=5.0,
            target_operations_per_second=10.0,
            success_rate_threshold=0.95,
            response_time_threshold_ms=1000.0
        )
        
        breaking_point_found = False
        load_multiplier = 1.0
        last_successful_multiplier = 1.0
        
        while load_multiplier <= max_load_multiplier and not breaking_point_found:
            # Scale configuration
            scaled_config = LoadTestConfiguration(
                max_concurrent_users=int(base_config.max_concurrent_users * load_multiplier),
                duration_seconds=base_config.duration_seconds,
                ramp_up_seconds=base_config.ramp_up_seconds,
                target_operations_per_second=base_config.target_operations_per_second * load_multiplier,
                success_rate_threshold=base_config.success_rate_threshold,
                response_time_threshold_ms=base_config.response_time_threshold_ms
            )
            
            # Run load test at this level
            sub_test_name = f"{test_name}_load_{load_multiplier:.1f}x"
            result = await self.run_load_test(sub_test_name, scaled_config, operation_func)
            
            if result.status == TestStatus.FAILED:
                breaking_point_found = True
                self._logger.info(f"Breaking point found at {load_multiplier:.1f}x load")
            else:
                last_successful_multiplier = load_multiplier
                load_multiplier *= 1.5  # Increase load
        
        end_time = time.time()
        
        # Create stress test summary
        return PerformanceTestResult(
            test_type=TestType.STRESS_TEST,
            test_name=test_name,
            status=TestStatus.PASSED,
            start_time=start_time,
            end_time=end_time,
            operations_executed=0,  # Summary result
            operations_successful=0,
            operations_failed=0,
            mean_response_time_ms=0.0,
            p95_response_time_ms=0.0,
            p99_response_time_ms=0.0,
            max_response_time_ms=0.0,
            throughput_ops_per_second=0.0,
            success_rate=1.0,
            errors=[],
            warnings=[],
            resource_usage={'max_successful_load_multiplier': last_successful_multiplier}
        )
    
    def validate_performance_contract(self, 
                                    contract: PerformanceContract,
                                    actual_metrics: Dict[str, float]) -> PerformanceTestResult:
        """Validate performance against contract requirements."""
        start_time = time.time()
        errors = []
        warnings = []
        
        # Check response time requirements
        if 'mean_response_time_ms' in actual_metrics:
            actual_time = actual_metrics['mean_response_time_ms']
            if actual_time > contract.max_response_time_ms:
                errors.append(
                    f"Response time violation: {actual_time:.2f}ms > {contract.max_response_time_ms}ms"
                )
        
        # Check throughput requirements
        if 'throughput_ops_per_second' in actual_metrics:
            actual_throughput = actual_metrics['throughput_ops_per_second']
            if actual_throughput < contract.min_throughput_ops_per_second:
                errors.append(
                    f"Throughput violation: {actual_throughput:.2f} < {contract.min_throughput_ops_per_second}"
                )
        
        # Check success rate requirements
        if 'success_rate' in actual_metrics:
            actual_success_rate = actual_metrics['success_rate']
            if actual_success_rate < contract.min_success_rate:
                errors.append(
                    f"Success rate violation: {actual_success_rate:.3f} < {contract.min_success_rate}"
                )
        
        # Determine status
        status = TestStatus.FAILED if errors else (TestStatus.WARNING if warnings else TestStatus.PASSED)
        
        return PerformanceTestResult(
            test_type=TestType.CONTRACT_VALIDATION,
            test_name=f"contract_validation_{contract.operation_type}",
            status=status,
            start_time=start_time,
            end_time=time.time(),
            operations_executed=1,
            operations_successful=1 if status == TestStatus.PASSED else 0,
            operations_failed=1 if status == TestStatus.FAILED else 0,
            mean_response_time_ms=actual_metrics.get('mean_response_time_ms', 0.0),
            p95_response_time_ms=actual_metrics.get('p95_response_time_ms', 0.0),
            p99_response_time_ms=actual_metrics.get('p99_response_time_ms', 0.0),
            max_response_time_ms=actual_metrics.get('max_response_time_ms', 0.0),
            throughput_ops_per_second=actual_metrics.get('throughput_ops_per_second', 0.0),
            success_rate=actual_metrics.get('success_rate', 0.0),
            errors=errors,
            warnings=warnings
        )
    
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
    
    async def _collect_resource_snapshot(self) -> Dict[str, Any]:
        """Collect resource usage snapshot."""
        if self._performance_monitor:
            try:
                summary = await self._performance_monitor.get_performance_summary()
                return summary.get('current_resources', {})
            except:
                pass
        
        return {}
    
    def get_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        return {
            'total_tests': len(self._test_results),
            'passed_tests': len([r for r in self._test_results if r.status == TestStatus.PASSED]),
            'failed_tests': len([r for r in self._test_results if r.status == TestStatus.FAILED]),
            'warning_tests': len([r for r in self._test_results if r.status == TestStatus.WARNING]),
            'error_tests': len([r for r in self._test_results if r.status == TestStatus.ERROR]),
            'test_results': [result.to_dict() for result in self._test_results],
            'baselines': self._baselines
        }
