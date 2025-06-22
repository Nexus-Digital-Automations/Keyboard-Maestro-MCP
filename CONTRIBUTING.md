# Contributing to Keyboard Maestro MCP Server

## Welcome Contributors! 🚀

Thank you for your interest in contributing to the Keyboard Maestro MCP Server project. This guide will help you understand our development process, coding standards, and contribution workflow.

**🎯 Project Vision**: Building the most comprehensive, reliable, and performant MCP server for Keyboard Maestro automation, following ADDER+ (Advanced Development, Documentation & Error Resolution) principles.

**📋 Quick Links:**
- [Development Setup](#development-setup)
- [Code Standards](#code-standards-adder)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Architecture](#project-architecture)
- [Performance Guidelines](#performance-guidelines)

---

## Development Setup

### Prerequisites

**Required Software:**
- **macOS 10.15+** (Catalina or later)
- **Python 3.10+** with pip
- **Keyboard Maestro 10.0+** (latest version recommended)
- **Git** for version control
- **VS Code** or **PyCharm** (recommended IDEs)

**Optional but Recommended:**
- **Docker** for containerized testing
- **Poetry** for advanced dependency management
- **pytest-cov** for coverage reporting
- **black** for code formatting
- **mypy** for type checking

### Step-by-Step Setup

#### 1. Clone and Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/keyboard-maestro-mcp.git
cd keyboard-maestro-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
python -c "import fastmcp; print('FastMCP installed successfully')"
```

#### 2. Configure Development Environment

```bash
# Set up environment variables
cp config/.env.template config/.env.dev

# Edit config/.env.dev with your settings
export MCP_DEV_MODE=true
export MCP_LOG_LEVEL=DEBUG
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Initialize development database (if applicable)
python scripts/setup/initialize_project.py
```

#### 3. Keyboard Maestro Configuration

**Grant Required Permissions:**
1. System Preferences → Security & Privacy → Privacy → Accessibility
   - Add and enable "Keyboard Maestro Engine"
   - Add and enable your Terminal application
   - Add and enable your IDE (VS Code/PyCharm)

2. System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add and enable "Keyboard Maestro Engine"
   - Add and enable your development tools

**Install Test Macros:**
```bash
# Install development test macros
python scripts/setup/install_test_macros.py
```

#### 4. Verify Development Setup

```bash
# Run setup verification
python scripts/validation/development_validator.py

# Start development server
MCP_DEV_MODE=true python src/main.py

# Run basic tests
pytest tests/integration/ -v
```

### IDE Configuration

#### VS Code Setup

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- Python Test Explorer
- Black Formatter
- MyPy Type Checker
- GitLens

**VS Code Settings (.vscode/settings.json):**
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.associations": {
        "*.md": "markdown"
    },
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm Setup

**Configuration Steps:**
1. Open project in PyCharm
2. Configure Python interpreter: File → Settings → Project → Python Interpreter
3. Set up pytest: File → Settings → Tools → Python Integrated Tools → Testing
4. Enable type checking: File → Settings → Editor → Inspections → Python → Type checker
5. Configure code style: File → Settings → Editor → Code Style → Python

---

## Code Standards (ADDER+)

### ADDER+ Principles

Our project follows **ADDER+ (Advanced Development, Documentation & Error Resolution)** methodology:

1. **Design by Contract**: All functions have explicit preconditions, postconditions, and invariants
2. **Type-Driven Development**: Comprehensive type hints and branded types for domain safety
3. **Defensive Programming**: Robust input validation and boundary protection
4. **Property-Based Testing**: Automated testing with generated test cases
5. **Immutable Functions**: Pure functions where possible, clear separation of concerns
6. **Modular Organization**: Clean architecture with logical component separation

### Code Style Guidelines

#### File Organization

```
src/
├── contracts/          # Design by contract decorators and validators
├── types/             # Domain types and type definitions
├── validators/        # Input validation and sanitization
├── pure/              # Pure functions and data transformations
├── boundaries/        # Security and permission boundaries
├── core/              # Core business logic
├── tools/             # MCP tool implementations
├── utils/             # Utility functions
└── interfaces/        # External interfaces and adapters
```

#### Naming Conventions

```python
# Classes: PascalCase
class MacroExecutionEngine:
    pass

# Functions and variables: snake_case
def execute_macro_with_validation():
    user_input = get_sanitized_input()

# Constants: UPPER_SNAKE_CASE
MAX_EXECUTION_TIMEOUT = 300
DEFAULT_RETRY_COUNT = 3

# Type aliases: PascalCase
MacroId = NewType('MacroId', str)
UserId = NewType('UserId', str)

# Private members: leading underscore
def _internal_helper_function():
    pass
```

#### Function Structure Template

```python
from src.contracts.decorators import requires, ensures
from src.types.domain_types import MacroId, ExecutionResult
from src.validators.input_validators import validate_macro_identifier

@requires(lambda macro_id: validate_macro_identifier(macro_id))
@ensures(lambda result: isinstance(result, ExecutionResult) and result.is_valid())
def execute_macro(macro_id: MacroId, timeout: int = 30) -> ExecutionResult:
    """Execute a Keyboard Maestro macro with comprehensive validation.
    
    Preconditions:
    - macro_id must be valid (non-empty, proper format)
    - timeout must be positive integer
    
    Postconditions:
    - Returns valid ExecutionResult
    - No side effects on system state
    
    Invariants:
    - Function is idempotent for read operations
    - Execution time bounded by timeout parameter
    
    Args:
        macro_id: Unique identifier for the macro
        timeout: Maximum execution time in seconds
        
    Returns:
        ExecutionResult containing execution details and status
        
    Raises:
        ValidationError: If macro_id is invalid
        TimeoutError: If execution exceeds timeout
        MacroNotFoundError: If macro doesn't exist
        
    Example:
        >>> result = execute_macro(MacroId("Daily Setup"))
        >>> assert result.success
        >>> assert result.execution_time < 30.0
    """
    # Implementation with error handling
    try:
        # Input validation at function boundary
        validated_id = validate_macro_identifier(macro_id)
        
        # Core business logic
        execution_result = _perform_macro_execution(validated_id, timeout)
        
        # Post-condition validation
        if not execution_result.is_valid():
            raise ContractViolationError("Invalid execution result")
            
        return execution_result
        
    except Exception as e:
        # Defensive error handling
        logger.error(f"Macro execution failed: {e}", extra={"macro_id": macro_id})
        raise MacroExecutionError(f"Failed to execute macro {macro_id}") from e
```

### Type System Guidelines

#### Branded Types for Domain Safety

```python
# Domain-specific types prevent mixing incompatible values
from typing import NewType

# Macro-related types
MacroId = NewType('MacroId', str)
MacroName = NewType('MacroName', str)
MacroGroupId = NewType('MacroGroupId', str)

# Variable-related types  
VariableName = NewType('VariableName', str)
VariableValue = NewType('VariableValue', str)
VariableScope = NewType('VariableScope', str)

# File-related types
FilePath = NewType('FilePath', str)
FileContent = NewType('FileContent', str)

# Usage prevents accidental mixing
def get_macro_by_id(macro_id: MacroId) -> Optional[Macro]:
    pass

def get_variable_by_name(var_name: VariableName) -> Optional[Variable]:
    pass

# This will cause type checker errors (good!)
# macro = get_macro_by_id(VariableName("wrong_type"))
```

#### Protocol Classes for Structural Typing

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Executable(Protocol):
    """Protocol for executable components."""
    
    def execute(self) -> ExecutionResult:
        """Execute the component."""
        ...
    
    def validate(self) -> bool:
        """Validate component state before execution."""
        ...

@runtime_checkable  
class Serializable(Protocol):
    """Protocol for serializable data structures."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        """Create instance from dictionary."""
        ...
```

### Error Handling Standards

#### Error Hierarchy

```python
# Base exception classes
class KMCPError(Exception):
    """Base exception for all KMCP errors."""
    
    def __init__(self, message: str, error_code: str = None, context: Dict = None):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.timestamp = datetime.now()

class ValidationError(KMCPError):
    """Raised when input validation fails."""
    pass

class MacroExecutionError(KMCPError):
    """Raised when macro execution fails."""
    pass

class PermissionError(KMCPError):
    """Raised when permission checks fail."""
    pass

# Usage with context
try:
    result = execute_macro(macro_id)
except MacroExecutionError as e:
    logger.error(
        f"Macro execution failed: {e.message}",
        extra={
            "error_code": e.error_code,
            "context": e.context,
            "timestamp": e.timestamp
        }
    )
```

#### Defensive Programming Patterns

```python
def secure_file_operation(file_path: FilePath, operation: str) -> FileOperationResult:
    """Secure file operation with comprehensive validation."""
    
    # Input validation at boundaries
    if not file_path:
        raise ValidationError("file_path", None, "cannot be empty")
    
    if operation not in ALLOWED_OPERATIONS:
        raise ValidationError("operation", operation, f"must be one of {ALLOWED_OPERATIONS}")
    
    # Security boundaries
    if not is_path_allowed(file_path):
        raise PermissionError(f"Access denied to path: {file_path}")
    
    # Resource boundaries
    if not has_sufficient_disk_space(file_path):
        raise ResourceError("Insufficient disk space for operation")
    
    # State boundaries
    if not is_system_ready():
        raise SystemError("System not ready for file operations")
    
    try:
        # Protected execution
        result = _perform_file_operation(file_path, operation)
        
        # Post-condition validation
        if not result.is_valid():
            raise ContractViolationError("Invalid operation result")
            
        return result
        
    except Exception as e:
        # Error context preservation
        raise FileOperationError(
            f"File operation failed: {operation}",
            context={"file_path": file_path, "operation": operation}
        ) from e
```

---

## Testing Guidelines

### Testing Philosophy

We follow **property-based testing** principles combined with traditional unit and integration tests:

1. **Property-Based Tests**: Verify invariants and properties across input ranges
2. **Contract Tests**: Verify preconditions, postconditions, and invariants
3. **Integration Tests**: Test complete workflows and system interactions
4. **Performance Tests**: Verify response times and resource usage
5. **Security Tests**: Validate input sanitization and permission checking

### Test Structure

```
tests/
├── properties/           # Property-based tests
│   ├── test_macro_properties.py
│   ├── test_variable_properties.py
│   └── framework.py
├── contracts/           # Contract verification tests
│   ├── test_contract_enforcement.py
│   └── test_boundary_validation.py
├── integration/         # End-to-end integration tests
│   ├── test_km_integration.py
│   └── test_mcp_server.py
├── tools/              # Individual tool tests
│   ├── test_macro_tools.py
│   ├── test_variable_tools.py
│   └── test_system_tools.py
├── boundaries/         # Security and validation tests
│   └── test_input_validation.py
└── types/              # Type system tests
    └── test_domain_types.py
```

### Property-Based Testing Examples

```python
from hypothesis import given, strategies as st, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

# Basic property testing
@given(st.text(min_size=1, max_size=100))
def test_macro_name_validation_properties(macro_name):
    """Test properties of macro name validation."""
    
    # Property: validation should be deterministic
    result1 = validate_macro_name(macro_name)
    result2 = validate_macro_name(macro_name)
    assert result1 == result2
    
    # Property: valid names should remain valid after normalization
    if result1.is_valid:
        normalized = normalize_macro_name(macro_name)
        assert validate_macro_name(normalized).is_valid

@given(st.lists(st.text(min_size=1), min_size=0, max_size=50))
def test_variable_batch_operations(variable_names):
    """Test batch variable operations maintain consistency."""
    
    assume(all(is_valid_variable_name(name) for name in variable_names))
    
    # Property: batch set followed by batch get should be consistent
    test_values = {name: f"value_{i}" for i, name in enumerate(variable_names)}
    
    # Set all variables
    batch_set_variables(test_values)
    
    # Get all variables
    retrieved_values = batch_get_variables(list(variable_names))
    
    # Property: all set values should be retrievable
    for name, expected_value in test_values.items():
        assert retrieved_values[name] == expected_value

# Stateful testing for complex systems
class MacroExecutionStateMachine(RuleBasedStateMachine):
    """Stateful testing for macro execution system."""
    
    def __init__(self):
        super().__init__()
        self.executed_macros = []
        self.system_variables = {}
    
    @rule(macro_name=st.text(min_size=1, max_size=50))
    def execute_macro(self, macro_name):
        assume(is_valid_macro_name(macro_name))
        
        try:
            result = execute_macro(MacroId(macro_name))
            if result.success:
                self.executed_macros.append(macro_name)
        except MacroNotFoundError:
            pass  # Expected for non-existent macros
    
    @rule(var_name=st.text(min_size=1, max_size=50), 
          var_value=st.text(max_size=1000))
    def set_variable(self, var_name, var_value):
        assume(is_valid_variable_name(var_name))
        
        set_variable(VariableName(var_name), VariableValue(var_value))
        self.system_variables[var_name] = var_value
    
    @invariant()
    def variables_remain_consistent(self):
        """Variables should maintain their values."""
        for name, expected_value in self.system_variables.items():
            try:
                actual_value = get_variable(VariableName(name))
                assert actual_value == expected_value
            except VariableNotFoundError:
                pass  # Variable might have been deleted by macro
    
    @invariant()
    def system_remains_stable(self):
        """System should remain responsive after operations."""
        status = get_engine_status()
        assert status.is_responsive
```

### Test Running and Coverage

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/properties/ -v
pytest tests/contracts/ -v  
pytest tests/integration/ -v

# Run tests with property-based testing
pytest tests/properties/ --hypothesis-show-statistics

# Run performance tests
pytest tests/performance/ --benchmark-only

# Generate coverage report
coverage html
open htmlcov/index.html
```

### Test Quality Standards

**Minimum Requirements:**
- **90%+ code coverage** for all new code
- **All public functions** must have property-based tests
- **All contracts** must be verified with specific test cases
- **Integration tests** for all MCP tools
- **Performance baselines** for all operations

**Test Documentation:**
```python
def test_macro_execution_with_timeout():
    """Test macro execution respects timeout limits.
    
    This test verifies that:
    1. Macros complete within specified timeout
    2. Long-running macros are properly terminated
    3. Timeout errors include diagnostic information
    4. System remains stable after timeout
    
    Property tested: execution_time <= timeout_limit
    Boundary tested: timeout enforcement
    Contract tested: post-condition of bounded execution time
    """
    # Test implementation
```

---

## Pull Request Process

### Before Creating a Pull Request

#### 1. Code Quality Checklist

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
pylint src/

# Security checking
bandit -r src/

# Run all tests
pytest --cov=src --cov-fail-under=90
```

#### 2. Documentation Updates

- [ ] Update docstrings for all new/modified functions
- [ ] Add examples to relevant documentation files
- [ ] Update API documentation if tools changed
- [ ] Add troubleshooting entries for new error conditions
- [ ] Update CHANGELOG.md with changes

#### 3. Performance Validation

```bash
# Run performance benchmarks
pytest tests/performance/ --benchmark-compare

# Memory usage testing
python scripts/validation/memory_usage_test.py

# Load testing for new features
python scripts/validation/load_test.py
```

### Pull Request Template

When creating a pull request, use this template:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Security enhancement

## ADDER+ Compliance
- [ ] Design by Contract: Preconditions/postconditions documented
- [ ] Type-Driven Development: Comprehensive type hints added
- [ ] Defensive Programming: Input validation and error handling
- [ ] Property-Based Testing: Relevant properties tested
- [ ] Immutable Functions: Pure functions where applicable
- [ ] Modular Organization: Proper component separation

## Testing
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Property-based tests included where applicable
- [ ] Performance tests added for performance-critical changes
- [ ] Coverage remains above 90%

## Documentation
- [ ] Code documentation updated
- [ ] API documentation updated (if applicable)
- [ ] Examples added/updated
- [ ] Troubleshooting guide updated (if applicable)

## Security Review
- [ ] Input validation added for all user inputs
- [ ] No hardcoded secrets or credentials
- [ ] Permission checks implemented where needed
- [ ] Error messages don't leak sensitive information

## Performance Impact
- [ ] No significant performance degradation
- [ ] Benchmarks run and results acceptable
- [ ] Memory usage profile acceptable
- [ ] New caching/optimization strategies documented

## Breaking Changes
List any breaking changes and migration instructions.

## Additional Notes
Any additional information reviewers should know.
```

### Review Process

#### Code Review Checklist

**Functionality:**
- [ ] Code implements requirements correctly
- [ ] Edge cases are handled appropriately
- [ ] Error handling is comprehensive
- [ ] Performance is acceptable

**ADDER+ Compliance:**
- [ ] Contracts are properly specified
- [ ] Types are comprehensive and correct
- [ ] Defensive programming patterns used
- [ ] Tests verify properties and invariants
- [ ] Functions are pure where possible
- [ ] Module organization is logical

**Code Quality:**
- [ ] Code is readable and well-documented
- [ ] Naming follows conventions
- [ ] No code duplication
- [ ] Complexity is manageable

**Security:**
- [ ] Input validation is present
- [ ] No security vulnerabilities
- [ ] Permissions are checked appropriately
- [ ] Sensitive data is handled correctly

#### Approval Requirements

- **1 approval** for documentation-only changes
- **2 approvals** for feature additions or bug fixes
- **3 approvals** for breaking changes or security-related changes
- **Maintainer approval** required for architectural changes

---

## Project Architecture

### Core Components

#### 1. Type System (`src/types/`)

```python
# Domain types for type safety
from typing import NewType

# Core identifiers
MacroId = NewType('MacroId', str)
VariableName = NewType('VariableName', str)
FilePath = NewType('FilePath', str)

# Value objects
@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    execution_time: float
    output: Optional[str]
    error: Optional[str]
    
    def is_valid(self) -> bool:
        return self.execution_time >= 0 and (self.success or self.error is not None)
```

#### 2. Contract System (`src/contracts/`)

```python
# Design by contract decorators
from functools import wraps

def requires(condition: Callable[[...], bool]):
    """Precondition decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not condition(*args, **kwargs):
                raise ContractViolationError(f"Precondition failed: {condition}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def ensures(condition: Callable[[Any], bool]):
    """Postcondition decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if not condition(result):
                raise ContractViolationError(f"Postcondition failed: {condition}")
            return result
        return wrapper
    return decorator
```

#### 3. Validation System (`src/validators/`)

```python
# Input validation and sanitization
def validate_macro_identifier(identifier: str) -> MacroId:
    """Validate and sanitize macro identifier."""
    if not identifier:
        raise ValidationError("identifier", identifier, "cannot be empty")
    
    if len(identifier) > 255:
        raise ValidationError("identifier", identifier, "exceeds maximum length")
    
    # Sanitize potentially dangerous characters
    sanitized = re.sub(r'[^\w\s\-\.]', '', identifier)
    
    if not sanitized:
        raise ValidationError("identifier", identifier, "contains no valid characters")
    
    return MacroId(sanitized)
```

#### 4. Pure Functions (`src/pure/`)

```python
# Pure functions for data transformation
def normalize_macro_name(name: str) -> str:
    """Normalize macro name to standard format."""
    return ' '.join(name.strip().split())

def calculate_execution_statistics(
    execution_times: List[float]
) -> ExecutionStatistics:
    """Calculate statistics from execution times."""
    if not execution_times:
        return ExecutionStatistics(0, 0, 0, 0)
    
    return ExecutionStatistics(
        count=len(execution_times),
        average=sum(execution_times) / len(execution_times),
        minimum=min(execution_times),
        maximum=max(execution_times)
    )
```

#### 5. Tool Registry (`src/tools/`)

Each MCP tool follows a consistent pattern:

```python
@tool_contract(
    preconditions=["identifier is valid macro ID"],
    postconditions=["returns valid execution result"],
    invariants=["no system state modification on failure"]
)
async def km_execute_macro(
    identifier: str,
    trigger_value: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """Execute a Keyboard Maestro macro with validation."""
    
    # Input validation
    macro_id = validate_macro_identifier(identifier)
    validated_timeout = validate_timeout(timeout)
    
    # Boundary protection
    check_execution_permission(macro_id)
    check_system_resources()
    
    # Core execution
    result = await execute_macro_safely(
        macro_id, 
        trigger_value, 
        validated_timeout
    )
    
    # Result validation
    if not result.is_valid():
        raise ContractViolationError("Invalid execution result")
    
    return result.to_dict()
```

### Adding New Tools

#### 1. Tool Implementation Template

```python
# src/tools/new_tool.py
from src.contracts.decorators import requires, ensures
from src.types.domain_types import *
from src.validators.input_validators import *
from src.boundaries.security_boundaries import *

@requires(lambda param: validate_parameter(param))
@ensures(lambda result: validate_result(result))
async def km_new_tool(
    param: str,
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    """Brief description of what the tool does.
    
    Preconditions:
    - param must be valid according to validation rules
    - optional_param must be positive if provided
    
    Postconditions:
    - Returns valid result dictionary
    - No side effects on error
    
    Invariants:
    - Function is idempotent for read operations
    - Execution time bounded
    
    Args:
        param: Description of parameter
        optional_param: Description of optional parameter
        
    Returns:
        Dictionary containing operation results
        
    Raises:
        ValidationError: If parameters are invalid
        PermissionError: If operation not allowed
        
    Example:
        >>> result = await km_new_tool("test_param")
        >>> assert result["success"] is True
    """
    try:
        # Input validation
        validated_param = validate_parameter(param)
        
        # Permission checking
        check_operation_permission("new_tool")
        
        # Core implementation
        result = perform_new_tool_operation(validated_param, optional_param)
        
        # Result validation
        if not is_valid_result(result):
            raise ContractViolationError("Invalid operation result")
            
        return {
            "success": True,
            "data": result,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "operation": "new_tool"
            }
        }
        
    except Exception as e:
        logger.error(f"New tool operation failed: {e}")
        raise ToolExecutionError(f"Failed to execute new tool") from e
```

#### 2. Tool Registration

```python
# src/core/tool_registry.py
def register_new_tool(mcp_server: FastMCP):
    """Register new tool with MCP server."""
    
    @mcp_server.tool()
    async def km_new_tool(param: str, optional_param: Optional[int] = None):
        """Tool wrapper for MCP integration."""
        from src.tools.new_tool import km_new_tool as tool_impl
        return await tool_impl(param, optional_param)
```

#### 3. Tool Testing

```python
# tests/tools/test_new_tool.py
import pytest
from hypothesis import given, strategies as st
from src.tools.new_tool import km_new_tool

class TestNewTool:
    """Test suite for new tool implementation."""
    
    @pytest.mark.asyncio
    async def test_new_tool_basic_functionality(self):
        """Test basic tool functionality."""
        result = await km_new_tool("valid_param")
        
        assert result["success"] is True
        assert "data" in result
        assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_new_tool_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValidationError):
            await km_new_tool("")  # Invalid empty parameter
    
    @given(st.text(min_size=1, max_size=100))
    @pytest.mark.asyncio
    async def test_new_tool_properties(self, param):
        """Property-based testing for tool."""
        assume(is_valid_parameter(param))
        
        result = await km_new_tool(param)
        
        # Property: successful operations return valid results
        if result["success"]:
            assert validate_result_structure(result)
        
        # Property: operation is deterministic
        result2 = await km_new_tool(param)
        assert result["success"] == result2["success"]
```

---

## Performance Guidelines

### Performance Standards

**Response Time Targets:**
- **Simple operations** (status checks): < 100ms
- **Variable operations**: < 50ms
- **Macro execution**: < 2s average (depends on macro complexity)
- **File operations**: < 500ms for small files
- **Bulk operations**: Linear scaling with batch size

**Resource Usage Limits:**
- **Memory**: < 100MB baseline, < 500MB under load
- **CPU**: < 10% average utilization
- **Disk I/O**: Minimal impact on system performance
- **Network**: Efficient connection reuse

### Performance Optimization Techniques

#### 1. Connection Pooling

```python
class AppleScriptPool:
    """Connection pool for AppleScript execution."""
    
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.connections = asyncio.Queue(maxsize=pool_size)
        self.stats = {"hits": 0, "misses": 0}
    
    async def get_connection(self):
        """Get connection from pool or create new one."""
        try:
            connection = self.connections.get_nowait()
            self.stats["hits"] += 1
            return connection
        except asyncio.QueueEmpty:
            self.stats["misses"] += 1
            return self._create_new_connection()
    
    async def return_connection(self, connection):
        """Return connection to pool."""
        try:
            self.connections.put_nowait(connection)
        except asyncio.QueueFull:
            # Pool is full, discard connection
            await connection.close()
```

#### 2. Intelligent Caching

```python
class ResultCache:
    """LRU cache with TTL for operation results."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.cache = {}
        self.access_order = []
        self.max_size = max_size
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result if valid."""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                # Move to end (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                return entry["value"]
            else:
                # Expired, remove from cache
                del self.cache[key]
                self.access_order.remove(key)
        return None
    
    def put(self, key: str, value: Any):
        """Cache result with timestamp."""
        # Remove oldest entries if at capacity
        while len(self.cache) >= self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
```

#### 3. Batch Operations

```python
async def batch_variable_operations(operations: List[VariableOperation]) -> List[OperationResult]:
    """Efficiently process multiple variable operations."""
    
    # Group operations by type
    get_ops = [op for op in operations if op.type == "get"]
    set_ops = [op for op in operations if op.type == "set"]
    delete_ops = [op for op in operations if op.type == "delete"]
    
    results = []
    
    # Process gets concurrently (read operations are safe)
    if get_ops:
        get_tasks = [get_variable(op.name) for op in get_ops]
        get_results = await asyncio.gather(*get_tasks, return_exceptions=True)
        results.extend(get_results)
    
    # Process sets as batch (more efficient than individual operations)
    if set_ops:
        batch_data = {op.name: op.value for op in set_ops}
        await batch_set_variables(batch_data)
        results.extend([OperationResult("success")] * len(set_ops))
    
    # Process deletes sequentially (safer for consistency)
    for op in delete_ops:
        try:
            await delete_variable(op.name)
            results.append(OperationResult("success"))
        except Exception as e:
            results.append(OperationResult("error", str(e)))
    
    return results
```

### Performance Monitoring

```python
class PerformanceMonitor:
    """Monitor and report performance metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.thresholds = {
            "response_time": 2.0,  # seconds
            "memory_usage": 500,   # MB
            "cpu_usage": 50        # percent
        }
    
    def record_operation(self, operation: str, duration: float, **metadata):
        """Record operation metrics."""
        self.metrics[operation].append({
            "duration": duration,
            "timestamp": time.time(),
            **metadata
        })
        
        # Alert on slow operations
        if duration > self.thresholds["response_time"]:
            logger.warning(f"Slow operation: {operation} took {duration:.2f}s")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        report = {}
        
        for operation, measurements in self.metrics.items():
            if measurements:
                durations = [m["duration"] for m in measurements]
                report[operation] = {
                    "count": len(measurements),
                    "avg_duration": sum(durations) / len(durations),
                    "max_duration": max(durations),
                    "min_duration": min(durations),
                    "recent_measurements": measurements[-10:]  # Last 10
                }
        
        return report
```

---

## Security Guidelines

### Security Standards

1. **Input Validation**: All user inputs must be validated and sanitized
2. **Permission Checking**: Verify permissions before executing operations
3. **Error Information**: Error messages must not leak sensitive information
4. **Audit Logging**: Log all security-relevant operations
5. **Resource Limits**: Enforce limits to prevent resource exhaustion

### Implementation Examples

#### Secure Input Handling

```python
def sanitize_file_path(path: str) -> FilePath:
    """Sanitize file path to prevent directory traversal."""
    
    # Remove null bytes
    clean_path = path.replace('\x00', '')
    
    # Resolve path to absolute form
    abs_path = os.path.abspath(clean_path)
    
    # Check for directory traversal attempts
    if '..' in abs_path or abs_path.startswith('/etc/') or abs_path.startswith('/usr/'):
        raise SecurityError(f"Access denied to path: {path}")
    
    # Verify path is within allowed directories
    allowed_dirs = ['/Users/', '/tmp/', '/var/tmp/']
    if not any(abs_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
        raise SecurityError(f"Path not in allowed directories: {path}")
    
    return FilePath(abs_path)
```

#### Permission Verification

```python
def check_macro_execution_permission(macro_id: MacroId) -> None:
    """Verify permission to execute specific macro."""
    
    # Check if user has general macro execution permission
    if not has_permission("macro_execution"):
        raise PermissionError("Macro execution not permitted")
    
    # Check for restricted macros
    restricted_patterns = [
        "System",
        "Admin",
        "Security",
        "Password"
    ]
    
    macro_name = get_macro_name(macro_id)
    for pattern in restricted_patterns:
        if pattern.lower() in macro_name.lower():
            if not has_permission("restricted_macro_execution"):
                raise PermissionError(f"Access denied to restricted macro: {macro_name}")
    
    # Log permission check
    audit_log("macro_execution_permitted", {
        "macro_id": macro_id,
        "user": get_current_user(),
        "timestamp": datetime.now()
    })
```

---

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

#### Pre-Release

- [ ] All tests pass (unit, integration, property-based)
- [ ] Performance benchmarks within acceptable ranges
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped

#### Release

- [ ] Create release branch: `release/v1.2.3`
- [ ] Final testing on release branch
- [ ] Tag release: `git tag v1.2.3`
- [ ] Build and publish packages
- [ ] Deploy to production (if applicable)
- [ ] Update documentation sites

#### Post-Release

- [ ] Monitor for issues
- [ ] Update dependency managers
- [ ] Announce release
- [ ] Merge release branch to main

---

## Getting Help

### Community Resources

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and community support
- **Wiki**: Extended documentation and tutorials
- **Examples Repository**: Additional code examples

### Development Support

- **Code Review**: All contributors receive thorough code reviews
- **Mentorship**: Experienced contributors mentor newcomers
- **Pair Programming**: Available for complex features
- **Office Hours**: Regular community calls for discussion

### Contact Information

- **Project Maintainer**: [Contact info]
- **Security Issues**: security@project.com
- **General Questions**: discussions on GitHub

---

## License and Legal

This project is licensed under [LICENSE TYPE]. By contributing, you agree that your contributions will be licensed under the same license.

**Contributor Agreement:**
- All contributions must be original work or properly attributed
- Contributors grant permission to use their contributions
- Contributors agree to follow the Code of Conduct

---

## Conclusion

Thank you for contributing to the Keyboard Maestro MCP Server! Your contributions help build a more powerful and reliable automation platform for the entire community.

**Remember:**
- Follow ADDER+ principles in all contributions
- Write comprehensive tests for new functionality
- Document your code thoroughly
- Be responsive to feedback during code review
- Help others learn and contribute

Happy coding! 🚀
