# Advanced Error Tracking System: Keyboard Maestro MCP Server

## Error Management Philosophy

This document defines the comprehensive error tracking, classification, and recovery system for the Keyboard Maestro MCP Server. The system implements advanced error handling patterns that support defensive programming, systematic error recovery, and comprehensive audit trails for debugging and system reliability.

## Error Classification Framework

### **1. Error Taxonomy**

#### **1.1 Primary Error Categories**

```python
# src/core/error_types.py (Target: <200 lines)
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import time

class ErrorSeverity(Enum):
    """Error severity levels for classification and response."""
    CRITICAL = "critical"      # System failure, immediate attention required
    HIGH = "high"             # Major functionality impacted
    MEDIUM = "medium"         # Partial functionality affected
    LOW = "low"              # Minor issues, workarounds available
    INFO = "info"            # Informational, no action required

class ErrorCategory(Enum):
    """High-level error categorization."""
    VALIDATION = "validation"          # Input validation failures
    PERMISSION = "permission"          # Access and authorization issues
    RESOURCE = "resource"             # System resource problems
    INTEGRATION = "integration"       # External system integration failures
    CONFIGURATION = "configuration"   # Configuration and setup issues
    PERFORMANCE = "performance"       # Performance and timeout issues
    SECURITY = "security"            # Security-related errors
    BUSINESS_LOGIC = "business_logic" # Domain-specific logic violations

class ErrorType(Enum):
    """Specific error types for detailed classification."""
    # Validation Errors
    INVALID_INPUT = "invalid_input"
    MALFORMED_DATA = "malformed_data"
    CONSTRAINT_VIOLATION = "constraint_violation"
    TYPE_MISMATCH = "type_mismatch"
    
    # Permission Errors
    ACCESS_DENIED = "access_denied"
    INSUFFICIENT_PRIVILEGES = "insufficient_privileges"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHORIZATION_EXPIRED = "authorization_expired"
    
    # Resource Errors
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    RESOURCE_LOCKED = "resource_locked"
    
    # Integration Errors
    APPLESCRIPT_ERROR = "applescript_error"
    KEYBOARD_MAESTRO_UNAVAILABLE = "keyboard_maestro_unavailable"
    SYSTEM_API_ERROR = "system_api_error"
    NETWORK_ERROR = "network_error"
    
    # Configuration Errors
    MISSING_CONFIGURATION = "missing_configuration"
    INVALID_CONFIGURATION = "invalid_configuration"
    DEPENDENCY_MISSING = "dependency_missing"
    VERSION_INCOMPATIBLE = "version_incompatible"
    
    # Performance Errors
    TIMEOUT = "timeout"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MEMORY_EXHAUSTED = "memory_exhausted"
    CPU_OVERLOAD = "cpu_overload"
    
    # Security Errors
    INJECTION_ATTEMPT = "injection_attempt"
    UNAUTHORIZED_OPERATION = "unauthorized_operation"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Business Logic Errors
    INVARIANT_VIOLATION = "invariant_violation"
    STATE_TRANSITION_INVALID = "state_transition_invalid"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    WORKFLOW_ERROR = "workflow_error"
```

#### **1.2 Comprehensive Error Information Structure**

```python
@dataclass(frozen=True)
class ErrorDetails:
    """Comprehensive error information for tracking and analysis."""
    error_id: str                          # Unique error identifier
    error_type: ErrorType                  # Specific error classification
    category: ErrorCategory                # High-level category
    severity: ErrorSeverity                # Impact severity level
    message: str                          # Human-readable error message
    technical_details: Optional[str]      # Technical information for developers
    user_message: Optional[str]           # User-friendly message
    recovery_suggestion: Optional[str]     # Suggested recovery actions
    context: Dict[str, Any]              # Error context information
    timestamp: float                      # Error occurrence time
    source_location: Optional[str]        # Source code location
    stack_trace: Optional[str]           # Technical stack trace
    correlation_id: Optional[str]         # Request correlation identifier
    affected_resources: List[str]         # Resources affected by error
    
    def __post_init__(self):
        """Validate error details structure."""
        if not self.error_id or not self.message:
            raise ValueError("Error ID and message are required")
        if len(self.message) > 1000:
            raise ValueError("Error message too long (max 1000 characters)")

@dataclass(frozen=True)
class ErrorContext:
    """Contextual information for error analysis."""
    operation: str                        # Operation being performed
    user_id: Optional[str]               # User identifier
    session_id: Optional[str]            # Session identifier
    request_parameters: Dict[str, Any]   # Request parameters
    system_state: Dict[str, Any]         # Relevant system state
    environment: Dict[str, str]          # Environment information
    
    def sanitize_for_logging(self) -> 'ErrorContext':
        """Remove sensitive information for logging."""
        sanitized_params = {
            k: v for k, v in self.request_parameters.items()
            if not any(sensitive in k.lower() 
                      for sensitive in ['password', 'token', 'secret', 'key'])
        }
        
        return ErrorContext(
            operation=self.operation,
            user_id=self.user_id,
            session_id=self.session_id,
            request_parameters=sanitized_params,
            system_state=self.system_state,
            environment=self.environment
        )
```

### **2. Error Detection and Classification**

#### **2.1 Automatic Error Classification**

```python
# src/core/error_classifier.py (Target: <250 lines)
from typing import Type, Dict, Callable, Pattern
import re
import traceback
import sys

class ErrorClassifier:
    """Automatically classify errors based on content and context."""
    
    def __init__(self):
        self._classification_rules: Dict[Type[Exception], ErrorType] = {
            ValueError: ErrorType.INVALID_INPUT,
            TypeError: ErrorType.TYPE_MISMATCH,
            KeyError: ErrorType.NOT_FOUND,
            FileNotFoundError: ErrorType.NOT_FOUND,
            PermissionError: ErrorType.ACCESS_DENIED,
            TimeoutError: ErrorType.TIMEOUT,
            ConnectionError: ErrorType.NETWORK_ERROR,
        }
        
        self._message_patterns: List[Tuple[Pattern, ErrorType]] = [
            (re.compile(r'(?i)permission\s+denied'), ErrorType.ACCESS_DENIED),
            (re.compile(r'(?i)not\s+found'), ErrorType.NOT_FOUND),
            (re.compile(r'(?i)timeout|timed\s+out'), ErrorType.TIMEOUT),
            (re.compile(r'(?i)invalid\s+(input|parameter|value)'), ErrorType.INVALID_INPUT),
            (re.compile(r'(?i)applescript\s+error'), ErrorType.APPLESCRIPT_ERROR),
            (re.compile(r'(?i)keyboard\s+maestro.*unavailable'), ErrorType.KEYBOARD_MAESTRO_UNAVAILABLE),
            (re.compile(r'(?i)rate\s+limit'), ErrorType.RATE_LIMIT_EXCEEDED),
            (re.compile(r'(?i)memory\s+(exhausted|limit)'), ErrorType.MEMORY_EXHAUSTED),
        ]
        
        self._context_classifiers: List[Callable[[ErrorContext], Optional[ErrorType]]] = [
            self._classify_by_operation,
            self._classify_by_parameters,
            self._classify_by_system_state,
        ]
    
    def classify_error(self, 
                      exception: Exception, 
                      context: ErrorContext) -> ErrorDetails:
        """Classify error and create comprehensive error details."""
        error_type = self._determine_error_type(exception, context)
        category = self._determine_category(error_type)
        severity = self._determine_severity(error_type, context)
        
        error_id = self._generate_error_id(error_type, context)
        message = self._generate_message(exception, error_type)
        user_message = self._generate_user_message(error_type, context)
        recovery_suggestion = self._generate_recovery_suggestion(error_type, context)
        
        return ErrorDetails(
            error_id=error_id,
            error_type=error_type,
            category=category,
            severity=severity,
            message=message,
            technical_details=str(exception),
            user_message=user_message,
            recovery_suggestion=recovery_suggestion,
            context=context.sanitize_for_logging().__dict__,
            timestamp=time.time(),
            source_location=self._extract_source_location(),
            stack_trace=traceback.format_exc(),
            correlation_id=context.session_id,
            affected_resources=self._identify_affected_resources(context)
        )
    
    def _determine_error_type(self, 
                             exception: Exception, 
                             context: ErrorContext) -> ErrorType:
        """Determine specific error type using multiple classification methods."""
        # Try exception type classification
        error_type = self._classification_rules.get(type(exception))
        if error_type:
            return error_type
        
        # Try message pattern matching
        message = str(exception)
        for pattern, error_type in self._message_patterns:
            if pattern.search(message):
                return error_type
        
        # Try context-based classification
        for classifier in self._context_classifiers:
            error_type = classifier(context)
            if error_type:
                return error_type
        
        # Default classification
        return ErrorType.SYSTEM_API_ERROR
    
    def _classify_by_operation(self, context: ErrorContext) -> Optional[ErrorType]:
        """Classify error based on operation being performed."""
        operation = context.operation.lower()
        
        if 'execute_macro' in operation:
            return ErrorType.APPLESCRIPT_ERROR
        elif 'validate' in operation:
            return ErrorType.VALIDATION_ERROR
        elif 'permission' in operation or 'auth' in operation:
            return ErrorType.ACCESS_DENIED
        elif 'file' in operation:
            return ErrorType.RESOURCE_ERROR
        
        return None
    
    def _generate_recovery_suggestion(self, 
                                    error_type: ErrorType, 
                                    context: ErrorContext) -> str:
        """Generate context-specific recovery suggestions."""
        suggestions = {
            ErrorType.ACCESS_DENIED: "Check accessibility permissions in System Preferences > Security & Privacy",
            ErrorType.KEYBOARD_MAESTRO_UNAVAILABLE: "Ensure Keyboard Maestro is running and accessible",
            ErrorType.TIMEOUT: "Increase timeout value or check system performance",
            ErrorType.INVALID_INPUT: "Verify input parameters match expected format and constraints",
            ErrorType.NOT_FOUND: "Verify the requested resource exists and identifier is correct",
            ErrorType.RATE_LIMIT_EXCEEDED: "Reduce request frequency or implement backoff strategy",
        }
        
        base_suggestion = suggestions.get(error_type, "Check logs for detailed error information")
        
        # Add context-specific guidance
        if error_type == ErrorType.ACCESS_DENIED and 'macro' in context.operation:
            return f"{base_suggestion}. Ensure Keyboard Maestro has required permissions for macro execution."
        
        return base_suggestion
```

### **3. Error Recovery System**

#### **3.1 Recovery Strategy Framework**

```python
# src/core/error_recovery.py (Target: <250 lines)
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
import asyncio
import random

class RecoveryStrategy(Enum):
    """Available error recovery strategies."""
    RETRY = "retry"                    # Retry operation with backoff
    FALLBACK = "fallback"             # Use alternative implementation
    GRACEFUL_DEGRADATION = "graceful_degradation"  # Reduce functionality
    CIRCUIT_BREAKER = "circuit_breaker"  # Temporarily disable failing component
    ESCALATION = "escalation"          # Escalate to human intervention
    ABORT = "abort"                   # Gracefully abort operation

@dataclass(frozen=True)
class RecoveryConfiguration:
    """Configuration for error recovery behavior."""
    max_retry_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff."""
        delay = min(self.base_delay * (self.backoff_multiplier ** attempt), self.max_delay)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)

class ErrorRecoveryManager:
    """Manages error recovery strategies and execution."""
    
    def __init__(self, config: RecoveryConfiguration = RecoveryConfiguration()):
        self.config = config
        self._recovery_strategies: Dict[ErrorType, List[RecoveryStrategy]] = self._initialize_strategies()
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._retry_counters: Dict[str, int] = {}
    
    def _initialize_strategies(self) -> Dict[ErrorType, List[RecoveryStrategy]]:
        """Initialize recovery strategies for different error types."""
        return {
            ErrorType.TIMEOUT: [RecoveryStrategy.RETRY, RecoveryStrategy.GRACEFUL_DEGRADATION],
            ErrorType.NETWORK_ERROR: [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK],
            ErrorType.APPLESCRIPT_ERROR: [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK],
            ErrorType.RATE_LIMIT_EXCEEDED: [RecoveryStrategy.RETRY],
            ErrorType.KEYBOARD_MAESTRO_UNAVAILABLE: [RecoveryStrategy.CIRCUIT_BREAKER, RecoveryStrategy.ESCALATION],
            ErrorType.ACCESS_DENIED: [RecoveryStrategy.ESCALATION],
            ErrorType.INVALID_INPUT: [RecoveryStrategy.ABORT],
            ErrorType.RESOURCE_EXHAUSTED: [RecoveryStrategy.GRACEFUL_DEGRADATION, RecoveryStrategy.CIRCUIT_BREAKER],
        }
    
    async def attempt_recovery(self, 
                             error_details: ErrorDetails,
                             operation: Callable,
                             *args, **kwargs) -> RecoveryResult:
        """Attempt to recover from error using appropriate strategies."""
        strategies = self._recovery_strategies.get(
            error_details.error_type, 
            [RecoveryStrategy.ABORT]
        )
        
        recovery_attempts = []
        
        for strategy in strategies:
            try:
                recovery_result = await self._execute_recovery_strategy(
                    strategy, error_details, operation, *args, **kwargs
                )
                recovery_attempts.append(recovery_result)
                
                if recovery_result.success:
                    return RecoveryResult(
                        success=True,
                        strategy_used=strategy,
                        attempts=recovery_attempts,
                        result=recovery_result.result
                    )
                    
            except Exception as recovery_exception:
                recovery_attempts.append(RecoveryAttempt(
                    strategy=strategy,
                    success=False,
                    error=str(recovery_exception),
                    attempt_time=time.time()
                ))
        
        # All recovery strategies failed
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.ABORT,
            attempts=recovery_attempts,
            error_details=error_details
        )
    
    async def _execute_recovery_strategy(self,
                                       strategy: RecoveryStrategy,
                                       error_details: ErrorDetails,
                                       operation: Callable,
                                       *args, **kwargs) -> RecoveryAttempt:
        """Execute specific recovery strategy."""
        operation_key = f"{error_details.context['operation']}:{id(operation)}"
        
        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_with_backoff(operation_key, operation, *args, **kwargs)
        
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._attempt_fallback(error_details, *args, **kwargs)
        
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._graceful_degradation(error_details, operation, *args, **kwargs)
        
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            return await self._circuit_breaker_recovery(operation_key, operation, *args, **kwargs)
        
        elif strategy == RecoveryStrategy.ESCALATION:
            return await self._escalate_error(error_details)
        
        else:  # ABORT
            return RecoveryAttempt(
                strategy=strategy,
                success=False,
                error="Operation aborted due to unrecoverable error",
                attempt_time=time.time()
            )
    
    async def _retry_with_backoff(self,
                                operation_key: str,
                                operation: Callable,
                                *args, **kwargs) -> RecoveryAttempt:
        """Retry operation with exponential backoff."""
        attempt_count = self._retry_counters.get(operation_key, 0)
        
        if attempt_count >= self.config.max_retry_attempts:
            return RecoveryAttempt(
                strategy=RecoveryStrategy.RETRY,
                success=False,
                error=f"Max retry attempts ({self.config.max_retry_attempts}) exceeded",
                attempt_time=time.time()
            )
        
        # Calculate delay and wait
        delay = self.config.calculate_delay(attempt_count)
        await asyncio.sleep(delay)
        
        # Increment retry counter
        self._retry_counters[operation_key] = attempt_count + 1
        
        try:
            result = await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
            
            # Reset counter on success
            self._retry_counters.pop(operation_key, None)
            
            return RecoveryAttempt(
                strategy=RecoveryStrategy.RETRY,
                success=True,
                result=result,
                attempt_time=time.time(),
                metadata={'attempt_number': attempt_count + 1, 'delay': delay}
            )
            
        except Exception as retry_exception:
            return RecoveryAttempt(
                strategy=RecoveryStrategy.RETRY,
                success=False,
                error=str(retry_exception),
                attempt_time=time.time(),
                metadata={'attempt_number': attempt_count + 1, 'delay': delay}
            )

@dataclass(frozen=True)
class RecoveryAttempt:
    """Information about a single recovery attempt."""
    strategy: RecoveryStrategy
    success: bool
    attempt_time: float
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass(frozen=True)
class RecoveryResult:
    """Final result of error recovery process."""
    success: bool
    strategy_used: RecoveryStrategy
    attempts: List[RecoveryAttempt]
    result: Optional[Any] = None
    error_details: Optional[ErrorDetails] = None
```

#### **3.2 Circuit Breaker Implementation**

```python
# src/core/circuit_breaker.py (Target: <200 lines)
from enum import Enum
import time
from typing import Dict, Optional, Callable, Any

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker pattern implementation for error handling."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker is open. Last failure: {self.last_failure_time}"
                )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass
```

### **4. Error Logging and Monitoring**

#### **4.1 Structured Error Logging**

```python
# src/core/error_logger.py (Target: <250 lines)
import structlog
import json
from typing import Optional, Dict, Any
from pathlib import Path
import sys

class ErrorLogger:
    """Structured logging for comprehensive error tracking."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.logger = self._configure_logger(log_level, log_file)
        self._error_counters: Dict[str, int] = {}
        self._error_patterns: Dict[str, List[ErrorDetails]] = {}
    
    def _configure_logger(self, log_level: str, log_file: Optional[str]):
        """Configure structured logger with appropriate processors."""
        processors = [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            self._add_error_context,
            structlog.processors.JSONRenderer()
        ]
        
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configure file logging
            import logging
            logging.basicConfig(
                filename=log_file,
                level=getattr(logging, log_level.upper()),
                format='%(message)s'
            )
            logger_factory = structlog.stdlib.LoggerFactory()
        else:
            # Configure stderr logging
            logger_factory = structlog.WriteLoggerFactory(file=sys.stderr)
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(structlog, log_level.upper())
            ),
            logger_factory=logger_factory,
            cache_logger_on_first_use=True,
        )
        
        return structlog.get_logger()
    
    def _add_error_context(self, logger, method_name, event_dict):
        """Add additional context to error log entries."""
        event_dict['service'] = 'keyboard-maestro-mcp'
        event_dict['version'] = '1.0.0'  # Should be dynamic
        return event_dict
    
    def log_error(self, error_details: ErrorDetails, additional_context: Optional[Dict[str, Any]] = None):
        """Log error with comprehensive structured information."""
        # Update error counters
        error_key = f"{error_details.category.value}:{error_details.error_type.value}"
        self._error_counters[error_key] = self._error_counters.get(error_key, 0) + 1
        
        # Track error patterns
        if error_key not in self._error_patterns:
            self._error_patterns[error_key] = []
        self._error_patterns[error_key].append(error_details)
        
        # Keep only recent errors for pattern analysis
        if len(self._error_patterns[error_key]) > 100:
            self._error_patterns[error_key] = self._error_patterns[error_key][-50:]
        
        # Prepare log entry
        log_entry = {
            'error_id': error_details.error_id,
            'error_type': error_details.error_type.value,
            'category': error_details.category.value,
            'severity': error_details.severity.value,
            'message': error_details.message,
            'technical_details': error_details.technical_details,
            'user_message': error_details.user_message,
            'recovery_suggestion': error_details.recovery_suggestion,
            'context': error_details.context,
            'timestamp': error_details.timestamp,
            'source_location': error_details.source_location,
            'correlation_id': error_details.correlation_id,
            'affected_resources': error_details.affected_resources,
            'error_count': self._error_counters[error_key],
        }
        
        if additional_context:
            log_entry.update(additional_context)
        
        # Log based on severity
        if error_details.severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred", **log_entry)
        elif error_details.severity == ErrorSeverity.HIGH:
            self.logger.error("High severity error", **log_entry)
        elif error_details.severity == ErrorSeverity.MEDIUM:
            self.logger.warning("Medium severity error", **log_entry)
        else:
            self.logger.info("Low severity error", **log_entry)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring and analysis."""
        return {
            'total_errors': sum(self._error_counters.values()),
            'error_counts_by_type': dict(self._error_counters),
            'most_common_errors': sorted(
                self._error_counters.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'pattern_analysis': self._analyze_error_patterns()
        }
    
    def _analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns for insights."""
        patterns = {}
        
        for error_key, errors in self._error_patterns.items():
            if len(errors) >= 3:  # Need minimum errors for pattern analysis
                # Analyze timing patterns
                timestamps = [error.timestamp for error in errors[-10:]]
                if len(timestamps) > 1:
                    intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                    avg_interval = sum(intervals) / len(intervals)
                    
                    patterns[error_key] = {
                        'frequency': len(errors),
                        'avg_interval_seconds': avg_interval,
                        'recent_burst': len([t for t in timestamps if time.time() - t < 300])  # Last 5 minutes
                    }
        
        return patterns
```

### **5. Error Metrics and Alerting**

#### **5.1 Error Metrics Collection**

```python
# src/core/error_metrics.py (Target: <200 lines)
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time
from collections import defaultdict, deque

@dataclass
class ErrorMetrics:
    """Comprehensive error metrics for monitoring."""
    total_errors: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_severity: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_hour: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=1000))
    error_rate_per_minute: List[int] = field(default_factory=lambda: [0] * 60)
    
    def record_error(self, error_details: ErrorDetails):
        """Record error occurrence for metrics."""
        self.total_errors += 1
        self.errors_by_type[error_details.error_type.value] += 1
        self.errors_by_severity[error_details.severity.value] += 1
        
        # Record by hour
        error_hour = int(error_details.timestamp // 3600)
        self.errors_by_hour[error_hour] += 1
        
        # Add to recent errors
        self.recent_errors.append({
            'timestamp': error_details.timestamp,
            'type': error_details.error_type.value,
            'severity': error_details.severity.value,
            'message': error_details.message[:100]  # Truncate for storage
        })
        
        # Update error rate
        current_minute = int(time.time() // 60) % 60
        self.error_rate_per_minute[current_minute] += 1
    
    def get_error_rate(self, window_minutes: int = 5) -> float:
        """Calculate error rate over specified window."""
        current_minute = int(time.time() // 60) % 60
        
        total_errors = 0
        for i in range(window_minutes):
            minute_index = (current_minute - i) % 60
            total_errors += self.error_rate_per_minute[minute_index]
        
        return total_errors / window_minutes
    
    def get_top_errors(self, limit: int = 10) -> List[tuple]:
        """Get most frequent error types."""
        return sorted(
            self.errors_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

class AlertManager:
    """Manages error-based alerting and notifications."""
    
    def __init__(self, metrics: ErrorMetrics):
        self.metrics = metrics
        self.alert_thresholds = {
            'error_rate_per_minute': 10,
            'critical_errors_per_hour': 5,
            'consecutive_failures': 3,
        }
        self.alert_history: List[Dict] = []
    
    def check_alerts(self) -> List[str]:
        """Check for alert conditions and return alert messages."""
        alerts = []
        
        # Check error rate
        current_rate = self.metrics.get_error_rate(5)
        if current_rate > self.alert_thresholds['error_rate_per_minute']:
            alerts.append(f"High error rate detected: {current_rate:.1f} errors/minute")
        
        # Check critical errors
        critical_count = self.metrics.errors_by_severity.get('critical', 0)
        if critical_count > self.alert_thresholds['critical_errors_per_hour']:
            alerts.append(f"Critical error threshold exceeded: {critical_count} critical errors")
        
        # Check for consecutive failures (same error type)
        if self._detect_consecutive_failures():
            alerts.append("Consecutive failures detected - possible systematic issue")
        
        # Record alerts
        for alert in alerts:
            self.alert_history.append({
                'timestamp': time.time(),
                'message': alert,
                'metrics_snapshot': {
                    'total_errors': self.metrics.total_errors,
                    'error_rate': current_rate,
                    'top_errors': self.metrics.get_top_errors(5)
                }
            })
        
        return alerts
    
    def _detect_consecutive_failures(self) -> bool:
        """Detect consecutive failures of the same type."""
        if len(self.metrics.recent_errors) < 3:
            return False
        
        # Check last 3 errors
        last_errors = list(self.metrics.recent_errors)[-3:]
        error_types = [error['type'] for error in last_errors]
        
        # All same type and within 5 minutes
        if len(set(error_types)) == 1:
            time_span = last_errors[-1]['timestamp'] - last_errors[0]['timestamp']
            return time_span < 300  # 5 minutes
        
        return False
```

### **6. Error Reporting and Dashboard**

#### **6.1 Error Report Generation**

```python
# src/core/error_reporting.py (Target: <200 lines)
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta

class ErrorReportGenerator:
    """Generate comprehensive error reports for analysis."""
    
    def __init__(self, error_logger: ErrorLogger, metrics: ErrorMetrics):
        self.error_logger = error_logger
        self.metrics = metrics
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate daily error report."""
        if date is None:
            date = datetime.now()
        
        statistics = self.error_logger.get_error_statistics()
        
        return {
            'report_date': date.isoformat(),
            'summary': {
                'total_errors': statistics['total_errors'],
                'error_rate': self.metrics.get_error_rate(60 * 24),  # 24 hours
                'most_common_errors': statistics['most_common_errors'],
                'critical_errors': self.metrics.errors_by_severity.get('critical', 0),
                'high_severity_errors': self.metrics.errors_by_severity.get('high', 0),
            },
            'patterns': statistics['pattern_analysis'],
            'recommendations': self._generate_recommendations(statistics),
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_incident_report(self, error_details: ErrorDetails) -> Dict[str, Any]:
        """Generate detailed incident report for specific error."""
        return {
            'incident_id': error_details.error_id,
            'timestamp': datetime.fromtimestamp(error_details.timestamp).isoformat(),
            'error_classification': {
                'type': error_details.error_type.value,
                'category': error_details.category.value,
                'severity': error_details.severity.value,
            },
            'description': {
                'message': error_details.message,
                'technical_details': error_details.technical_details,
                'user_impact': error_details.user_message,
            },
            'context': error_details.context,
            'recovery': {
                'suggestion': error_details.recovery_suggestion,
                'affected_resources': error_details.affected_resources,
            },
            'investigation': {
                'source_location': error_details.source_location,
                'stack_trace': error_details.stack_trace,
                'correlation_id': error_details.correlation_id,
            }
        }
    
    def _generate_recommendations(self, statistics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on error patterns."""
        recommendations = []
        
        # Check for high error rates
        if statistics['total_errors'] > 100:
            recommendations.append(
                "High error volume detected. Consider implementing additional input validation."
            )
        
        # Check for permission errors
        permission_errors = sum(
            count for error_type, count in statistics['error_counts_by_type'].items()
            if 'permission' in error_type or 'access' in error_type
        )
        
        if permission_errors > 10:
            recommendations.append(
                "Multiple permission errors detected. Review accessibility settings and user permissions."
            )
        
        # Check for timeout patterns
        timeout_errors = sum(
            count for error_type, count in statistics['error_counts_by_type'].items()
            if 'timeout' in error_type
        )
        
        if timeout_errors > 5:
            recommendations.append(
                "Timeout errors detected. Consider increasing timeout values or optimizing operations."
            )
        
        return recommendations

    def export_error_data(self, format: str = 'json', filename: Optional[str] = None) -> str:
        """Export error data for external analysis."""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'statistics': self.error_logger.get_error_statistics(),
            'metrics': {
                'total_errors': self.metrics.total_errors,
                'errors_by_type': dict(self.metrics.errors_by_type),
                'errors_by_severity': dict(self.metrics.errors_by_severity),
                'recent_errors': list(self.metrics.recent_errors),
            }
        }
        
        if format == 'json':
            output = json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        if filename:
            with open(filename, 'w') as f:
                f.write(output)
        
        return output
```

## Error System Integration

### **1. Global Error Handler**

```python
# src/core/global_error_handler.py (Target: <150 lines)
import asyncio
from typing import Optional, Callable, Any

class GlobalErrorHandler:
    """Global error handling system for the MCP server."""
    
    def __init__(self):
        self.error_classifier = ErrorClassifier()
        self.error_logger = ErrorLogger(log_file="logs/errors.log")
        self.metrics = ErrorMetrics()
        self.recovery_manager = ErrorRecoveryManager()
        self.alert_manager = AlertManager(self.metrics)
        self.report_generator = ErrorReportGenerator(self.error_logger, self.metrics)
        
        # Set up periodic monitoring
        asyncio.create_task(self._periodic_monitoring())
    
    async def handle_error(self, 
                          exception: Exception,
                          context: ErrorContext,
                          operation: Optional[Callable] = None,
                          *args, **kwargs) -> Optional[Any]:
        """Comprehensive error handling with classification, logging, and recovery."""
        
        # Classify error
        error_details = self.error_classifier.classify_error(exception, context)
        
        # Log error
        self.error_logger.log_error(error_details)
        
        # Update metrics
        self.metrics.record_error(error_details)
        
        # Check for alerts
        alerts = self.alert_manager.check_alerts()
        for alert in alerts:
            await self._send_alert(alert)
        
        # Attempt recovery if operation provided
        if operation:
            recovery_result = await self.recovery_manager.attempt_recovery(
                error_details, operation, *args, **kwargs
            )
            
            if recovery_result.success:
                return recovery_result.result
        
        # Re-raise if no recovery or recovery failed
        raise exception
    
    async def _periodic_monitoring(self):
        """Periodic monitoring and alerting."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            alerts = self.alert_manager.check_alerts()
            for alert in alerts:
                await self._send_alert(alert)
    
    async def _send_alert(self, alert_message: str):
        """Send alert notification."""
        # For now, just log the alert
        # In production, could send to monitoring system, email, etc.
        self.error_logger.logger.warning("ALERT", alert=alert_message)
```

This comprehensive error tracking system provides the foundation for robust error handling, systematic recovery, and continuous monitoring of the Keyboard Maestro MCP Server's reliability and performance.