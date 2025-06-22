# Keyboard Maestro MCP Server

## Project Overview

A production-ready Model Context Protocol (MCP) server implementation for Keyboard Maestro automation, built with FastMCP Python and advanced programming techniques. This enterprise-grade server provides **50+ MCP tools** enabling AI assistants to create, manage, and execute sophisticated macOS automation workflows through Keyboard Maestro's comprehensive automation capabilities.

**🚀 Production Status**: All core features implemented and tested with comprehensive error handling, security boundaries, and performance optimization.

**🔧 Advanced Implementation**: Built with Design by Contract, Type-Driven Development, Defensive Programming, Property-Based Testing, and Functional Programming patterns for enterprise reliability.

## ADDER+ Workflow Integration

This project is optimized for the ELITE CODE AGENT: ADDER+ (Advanced Development, Documentation & Error Resolution) workflow, implementing advanced programming techniques for enterprise-grade reliability:

### **Advanced Programming Techniques Implemented:**

- **Design by Contract**: Comprehensive precondition/postcondition specifications for all automation operations
- **Type-Driven Development**: Branded types for Keyboard Maestro entities (macros, triggers, actions, variables)
- **Defensive Programming**: Input validation and boundary protection for AppleScript and system operations
- **Property-Based Testing**: Comprehensive testing strategies for complex automation logic
- **Immutability Patterns**: Functional programming approaches for state management
- **Modular Code Organization**: All modules designed to stay under 250 lines for optimal maintainability

### **Core Capabilities** ✅ IMPLEMENTED

The server exposes comprehensive Keyboard Maestro automation through **5 major tool categories** with **51+ production-ready tools**:

1. **🚀 Macro Management Tools** (12 tools): Execute, create, update, delete, import/export macros and groups with full lifecycle management
2. **📊 Variable and Data Tools** (10 tools): Variable CRUD with scope enforcement, dictionary management, clipboard operations, secure token processing
3. **⚙️ System Integration Tools** (17 tools): File operations with permission validation, application control, window management, interface automation with OCR
4. **📧 Communication Tools** (8 tools): Email with attachment support, SMS/iMessage, web requests with auth, system notifications
5. **🔍 Advanced Features** (14 tools): Custom plugin creation, step-through debugging, multi-language OCR, image recognition, secure script execution

**✨ Key Differentiators:**
- **Contract-Driven API**: Every tool includes preconditions, postconditions, and invariants
- **Type-Safe Operations**: Branded types prevent common automation errors
- **Security-First Design**: Comprehensive input validation and permission checking
- **Performance Optimized**: Async operations with connection pooling and caching
- **Error Recovery**: Automatic retry logic with circuit breaker patterns

### **Technology Stack** ✅ PRODUCTION-READY

- **🚀 Core Framework**: FastMCP Python 1.0+ with comprehensive MCP protocol support
- **🔐 Contract Programming**: icontract 2.6+ for Design by Contract implementation
- **📋 Type Safety**: Pydantic 2.5+ with branded types and comprehensive validation
- **⚙️ macOS Integration**: PyObjC frameworks for native system integration
- **📊 Async Processing**: asyncio-pool for high-performance concurrent operations
- **🔍 Testing Framework**: pytest + Hypothesis for property-based testing
- **📜 Structured Logging**: structlog with JSON output for production monitoring
- **🛡️ Security**: Comprehensive input validation, permission checking, audit trails
- **📊 Performance**: Connection pooling, caching, circuit breakers, metrics collection

## Agent Collaboration Protocols

### **ADDER+ Integration Points**

This project structure supports seamless collaboration with the ADDER+ agent:

1. **Contract-Ready Architecture**: All automation functions include contract specifications
2. **Type-Driven Foundation**: Branded types for all Keyboard Maestro entities
3. **Defensive Programming Support**: Comprehensive input validation and boundary protection
4. **Testing Infrastructure**: Property-based testing foundations for complex automation logic
5. **Modular Design**: Script organization maintaining size constraints under 250 lines
6. **Documentation Ecosystem**: Complete technique documentation supporting advanced workflows

### **Development Workflow**

1. **Requirements Analysis**: Review `PRD.md` for business requirements and domain constraints
2. **Architecture Planning**: Consult `ARCHITECTURE.md` for system design and integration patterns
3. **Contract Specification**: Define function contracts in `CONTRACTS.md`
4. **Type System Design**: Implement domain modeling using `TYPES.md`
5. **Implementation**: Follow modular patterns with technique integration checkpoints
6. **Testing**: Apply property-based testing strategies from `TESTING.md`
7. **Validation**: Verify contract compliance and boundary protection

### **Task-Documentation Mapping**

The `TODO.md` file implements intelligent task-documentation mapping where each task includes:

- **Required Reading Lists**: Specific documentation files to consult before implementation
- **Implementation Files**: Exact scripts and modules to modify/create with size targets
- **Reference Dependencies**: Related documentation for context and validation
- **Modularity Strategies**: Guidance on maintaining script size limits and decomposition
- **Technique Integration**: Specific advanced programming techniques to apply
- **Success Criteria**: Measurable completion criteria including modularity verification

## Quick Start

### **Prerequisites** ✅

- **macOS**: 10.14+ (Mojave or later) with Keyboard Maestro 9.0+
- **Python**: 3.10+ with uv package manager (recommended) or pip
- **Permissions**: Accessibility permissions for system automation
- **Hardware**: Intel or Apple Silicon Mac with 4GB+ RAM

### **Production Installation** 🚀

```bash
# Clone repository
git clone <repository-url>
cd Keyboard-Maestro-MCP

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install production dependencies
uv pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your configuration

# Grant accessibility permissions (required)
echo "Grant accessibility permissions in System Preferences > Security & Privacy"

# Test installation
python -m src.main --help
```

### **Development Installation** 🔧

```bash
# After production installation above
uv pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run test suite
pytest tests/ -v

# Run with development configuration
MCP_DEV_MODE=true python -m src.main
```

### **Server Startup Options** ✅

#### **Local Development (STDIO)**
```bash
# Start with debug logging
MCP_DEV_MODE=true MCP_LOG_LEVEL=DEBUG python -m src.main

# Or use FastMCP dev mode with inspector
fastmcp dev src/main.py
```

#### **Remote Access (HTTP)**
```bash
# Production HTTP server
MCP_TRANSPORT=streamable-http MCP_PORT=8080 python -m src.main

# Or with explicit configuration
python -m src.main --transport streamable-http --port 8080
```

#### **Claude Desktop Integration**
```bash
# For Claude Desktop, use STDIO transport (default)
python -m src.main

# Add to Claude Desktop configuration:
# {
#   "keyboard-maestro": {
#     "command": "python",
#     "args": ["-m", "src.main"],
#     "cwd": "/path/to/Keyboard-Maestro-MCP"
#   }
# }
```

### **Testing and Validation** 🧪

```bash
# Run full test suite with property-based tests
pytest tests/ -v --cov=src --cov-report=html

# Run only property-based tests
pytest tests/properties/ -v

# Validate contracts and type safety
mypy src/ --strict

# Run performance tests
pytest tests/properties/test_performance.py -v

# Security validation
bandit -r src/ -f json
```

## Project Structure

```
Keyboard-Maestro-MCP/
├── README.md                      # Project overview + ADDER+ workflow + agent collaboration
├── PRD.md                         # Requirements with contract specifications
├── ARCHITECTURE.md                # System design + security + modularity + libraries
├── CONTRACTS.md                   # Function contract specifications + system invariants
├── TYPES.md                       # Type system and domain modeling
├── TESTING.md                     # Property-based testing strategies
├── TODO.md                        # Task-documentation mapping + current focus + next steps
├── ERRORS.md                      # Advanced error tracking system
├── FASTMCP_PYTHON.md             # FastMCP implementation guidelines
├── KM_MCP.md                     # Keyboard Maestro capabilities analysis
├── src/                           # Source with technique-ready modular structure
│   ├── contracts/                 # Contract specification modules
│   ├── types/                     # Domain type definitions
│   ├── validators/                # Defensive programming modules
│   ├── pure/                      # Pure function implementations
│   ├── boundaries/                # System boundary definitions
│   ├── core/                      # Core business logic modules
│   ├── utils/                     # Utility function modules
│   └── interfaces/                # Interface definitions
├── tests/                         # Enhanced testing framework
│   ├── properties/                # Property-based tests
│   ├── contracts/                 # Contract verification tests
│   ├── boundaries/                # Boundary condition tests
│   └── integration/               # Integration test suites
├── scripts/                       # Implementation-ready modular script structure
│   ├── setup/                     # Setup and initialization scripts
│   ├── build/                     # Build and deployment scripts
│   ├── data/                      # Data processing scripts
│   ├── validation/                # Validation and testing scripts
│   └── maintenance/               # Maintenance and utility scripts
└── logs/                          # Logging directory for stderr and file outputs
```

## Security Framework

### **Permission Management**

- macOS accessibility permissions validation
- Sandboxed script execution for user-provided code
- Input sanitization for all AppleScript interactions
- Audit logging for sensitive automation operations

### **Access Control**

- Read-only vs. write operation classifications
- Privileged operation restrictions (system control, file access)
- Rate limiting for resource-intensive automation tasks
- Authentication support for remote MCP access

## Performance Optimization

### **Efficiency Strategies**

- Batch operation support for multiple macro executions
- Asynchronous execution for long-running automation tasks
- Result caching for frequently accessed Keyboard Maestro data
- AppleScript connection pooling to minimize overhead

### **Modularity Benefits**

- Script size constraints (under 250 lines) improve maintainability
- Clear module separation enables parallel development
- Utility function extraction reduces code duplication
- Import hierarchy optimization minimizes dependencies

## Error Handling

### **Comprehensive Error Management**

- Detailed error codes and messages for automation failures
- Graceful degradation when Keyboard Maestro is unavailable
- Rollback support for reversible automation operations
- Debug information collection for troubleshooting

### **Error Categories**

- Permission errors (accessibility, file access)
- Resource not found errors (macros, variables, files)
- Timeout errors for long-running operations
- Validation errors for malformed inputs
- System errors for macOS integration issues

## Contributing

This project follows ADDER+ development principles:

1. **Contract-First Development**: Define contracts before implementation
2. **Type-Driven Design**: Use branded types for domain modeling
3. **Defensive Programming**: Validate all inputs and boundaries
4. **Property-Based Testing**: Test complex logic with generated inputs
5. **Modular Organization**: Keep scripts under 250 lines
6. **Documentation-Driven**: Maintain comprehensive technique documentation

See `TODO.md` for current implementation priorities and task-documentation mapping.

## License

MIT License - See LICENSE file for details.

## Support

For issues and support:
- Review `ERRORS.md` for common troubleshooting steps
- Check `TODO.md` for known limitations and planned improvements
- Consult `ARCHITECTURE.md` for integration guidance
- Review contract specifications in `CONTRACTS.md` for API usage