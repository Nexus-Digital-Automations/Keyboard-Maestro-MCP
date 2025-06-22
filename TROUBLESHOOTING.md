# Keyboard Maestro MCP Server: Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with the Keyboard Maestro MCP Server. It includes systematic diagnostic procedures, error code references, performance optimization strategies, and detailed solutions for frequently encountered problems.

**🎯 Quick Navigation:**
- **[Common Issues](#common-issues)**: Fast solutions for frequent problems
- **[Diagnostic Procedures](#diagnostic-procedures)**: Step-by-step troubleshooting
- **[Error Code Reference](#error-code-reference)**: Complete error documentation
- **[Performance Debugging](#performance-debugging)**: Optimization strategies
- **[Log Analysis](#log-analysis)**: Understanding server logs
- **[Advanced Troubleshooting](#advanced-troubleshooting)**: Complex issue resolution

---

## Quick Problem Resolution

### 🚨 Emergency Checklist

If the server is completely unresponsive:

1. **Check Keyboard Maestro Engine status**
   ```bash
   ps aux | grep "Keyboard Maestro"
   ```

2. **Restart the MCP Server**
   ```bash
   # Stop server (if running)
   pkill -f "keyboard-maestro-mcp"
   
   # Start server
   python src/main.py
   ```

3. **Verify system permissions**
   - System Preferences → Security & Privacy → Accessibility
   - Ensure "Keyboard Maestro Engine" is checked

4. **Check log files**
   ```bash
   tail -f logs/km_mcp_server.log
   ```

### ⚡ Quick Fixes

| Problem | Quick Solution |
|---------|---------------|
| Server won't start | Check Python dependencies: `pip install -r requirements.txt` |
| Macro not found | Verify macro name/UUID with `km_list_macros` |
| Permission denied | Grant accessibility permissions in System Preferences |
| Timeout errors | Increase timeout values in macro calls |
| Variable not found | Check variable name spelling and scope |
| AppleScript errors | Restart Keyboard Maestro Engine |

---

## Common Issues

### 1. Server Startup Problems

#### Issue: Server fails to start with ImportError

**Symptoms:**
```
ImportError: No module named 'fastmcp'
ModuleNotFoundError: No module named 'src.core.mcp_server'
```

**Diagnosis:**
```bash
# Check Python environment
python --version
pip list | grep fastmcp

# Check project structure
ls -la src/
```

**Solutions:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

2. **Fix Python path:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   python src/main.py
   ```

3. **Use virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python src/main.py
   ```

#### Issue: Server starts but immediately crashes

**Symptoms:**
```
Server starting...
KeyboardInterrupt
Process terminated
```

**Diagnosis:**
```bash
# Run with debug logging
MCP_DEV_MODE=true python src/main.py

# Check system resources
top -l 1 | grep "CPU usage"
df -h
```

**Solutions:**

1. **Check system resources:**
   - Ensure adequate RAM (minimum 1GB free)
   - Check disk space (minimum 100MB free)
   - Close unnecessary applications

2. **Review configuration:**
   ```bash
   # Check config files
   cat config/production.yaml
   
   # Validate configuration
   python scripts/validation/production_validator.py
   ```

3. **Debug mode startup:**
   ```bash
   MCP_DEV_MODE=true MCP_LOG_LEVEL=DEBUG python src/main.py
   ```

### 2. Keyboard Maestro Integration Issues

#### Issue: "Keyboard Maestro Engine not found" error

**Symptoms:**
```json
{
  "error": {
    "code": "APPLESCRIPT_ERROR",
    "message": "Application 'Keyboard Maestro Engine' not found"
  }
}
```

**Diagnosis:**
```bash
# Check if Keyboard Maestro is installed
ls /Applications/Keyboard\ Maestro.app/

# Check if Engine is running
ps aux | grep "Keyboard Maestro Engine"

# Test AppleScript access
osascript -e 'tell application "Keyboard Maestro Engine" to get version'
```

**Solutions:**

1. **Install/reinstall Keyboard Maestro:**
   - Download from [keyboardmaestro.com](https://www.keyboardmaestro.com)
   - Ensure version 10.0+ for full compatibility

2. **Start Keyboard Maestro Engine:**
   ```bash
   open /Applications/Keyboard\ Maestro.app/Contents/MacOS/Keyboard\ Maestro\ Engine.app
   ```

3. **Grant permissions:**
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Add and enable "Keyboard Maestro Engine"
   - Add and enable your Terminal application or IDE

#### Issue: Macro execution fails with timeout

**Symptoms:**
```json
{
  "error": {
    "code": "TIMEOUT_ERROR", 
    "message": "Macro execution exceeded timeout limit"
  }
}
```

**Diagnosis:**
```python
# Test with increased timeout
await client.call_tool("km_execute_macro", {
    "identifier": "Your Macro Name",
    "timeout": 120  # Increase from default 30s
})

# Check macro complexity
await client.call_tool("km_manage_macro_properties", {
    "operation": "get",
    "macro_id": "your-macro-uuid"
})
```

**Solutions:**

1. **Optimize macro performance:**
   - Remove unnecessary pauses in macro
   - Replace slow actions with faster alternatives
   - Break complex macros into smaller parts

2. **Increase timeout strategically:**
   ```python
   # For complex document processing
   timeout = 300  # 5 minutes
   
   # For simple UI automation  
   timeout = 60   # 1 minute
   
   # For file operations
   timeout = 180  # 3 minutes
   ```

3. **Implement async execution:**
   ```python
   # Start macro without waiting
   await client.call_tool("km_execute_macro", {
       "identifier": "Long Running Macro",
       "method": "url",  # Non-blocking method
       "timeout": 10     # Just for trigger confirmation
   })
   
   # Check status separately
   await asyncio.sleep(5)
   # ... check completion via variable or file
   ```

### 3. Permission and Security Issues

#### Issue: "Permission denied" for file operations

**Symptoms:**
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Access denied to file system resource"
  }
}
```

**Diagnosis:**
```bash
# Check file permissions
ls -la /path/to/file

# Check macOS privacy settings
# System Preferences → Security & Privacy → Privacy

# Test file access
echo "test" > /tmp/km_test.txt
cat /tmp/km_test.txt
rm /tmp/km_test.txt
```

**Solutions:**

1. **Grant Full Disk Access:**
   - System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add "Keyboard Maestro Engine"
   - Add your Terminal/IDE application

2. **Update file paths:**
   ```python
   # Use accessible locations
   accessible_paths = [
       "~/Desktop/",
       "~/Documents/", 
       "~/Downloads/",
       "/tmp/",
       "/Users/Shared/"
   ]
   ```

3. **Test permissions programmatically:**
   ```python
   async def test_file_permissions():
       test_paths = [
           "/tmp/km_permission_test.txt",
           "~/Desktop/km_permission_test.txt",
           "~/Documents/km_permission_test.txt"
       ]
       
       for path in test_paths:
           try:
               await client.call_tool("km_file_operations", {
                   "operation": "create_folder",  # Less invasive test
                   "source_path": path + "_folder"
               })
               print(f"✅ {path}: Accessible")
               
               # Cleanup
               await client.call_tool("km_file_operations", {
                   "operation": "delete",
                   "source_path": path + "_folder"
               })
               
           except Exception as e:
               print(f"❌ {path}: {e}")
   ```

### 4. Variable and Data Issues

#### Issue: Variables not persisting between sessions

**Symptoms:**
- Variables set in one session disappear
- Global variables return "not found" errors
- Data loss after server restart

**Diagnosis:**
```python
# Test variable persistence
await client.call_tool("km_variable_manager", {
    "operation": "set",
    "name": "PersistenceTest",
    "value": f"Test_{int(time.time())}",
    "scope": "global"
})

# Wait and check
await asyncio.sleep(2)
result = await client.call_tool("km_variable_manager", {
    "operation": "get", 
    "name": "PersistenceTest",
    "scope": "global"
})
```

**Solutions:**

1. **Verify variable scope:**
   ```python
   # Global variables persist across sessions
   scope = "global"  # ✅ Persistent
   
   # Local variables are session-specific
   scope = "local"   # ❌ Not persistent
   ```

2. **Check Keyboard Maestro storage:**
   ```bash
   # Check KM preferences for variable storage
   defaults read com.stairways.keyboardmaestro.engine Variables
   ```

3. **Implement backup/restore:**
   ```python
   async def backup_critical_variables():
       critical_vars = [
           "ProjectConfig",
           "UserPreferences", 
           "SystemSettings"
       ]
       
       backup_data = {}
       for var_name in critical_vars:
           try:
               result = await client.call_tool("km_variable_manager", {
                   "operation": "get",
                   "name": var_name,
                   "scope": "global"
               })
               backup_data[var_name] = result[0].text
           except Exception as e:
               print(f"Warning: Could not backup {var_name}: {e}")
       
       # Save to file
       with open("variable_backup.json", "w") as f:
           json.dump(backup_data, f, indent=2)
   ```

### 5. Network and Transport Issues

#### Issue: HTTP transport not accessible

**Symptoms:**
```bash
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**Diagnosis:**
```bash
# Check if server is running
netstat -an | grep 8000
lsof -i :8000

# Test server startup
MCP_TRANSPORT=streamable-http MCP_PORT=8000 python src/main.py

# Check firewall settings
sudo pfctl -s all | grep 8000
```

**Solutions:**

1. **Verify server configuration:**
   ```bash
   # Check environment variables
   export MCP_TRANSPORT=streamable-http
   export MCP_HOST=127.0.0.1
   export MCP_PORT=8000
   
   python src/main.py
   ```

2. **Test different ports:**
   ```bash
   # Try alternative ports
   for port in 8000 8080 3000 5000; do
       echo "Testing port $port..."
       MCP_PORT=$port python src/main.py &
       sleep 2
       curl http://localhost:$port/health || echo "Port $port failed"
       pkill -f main.py
   done
   ```

3. **Configure firewall (if needed):**
   ```bash
   # macOS firewall configuration
   sudo pfctl -f /etc/pf.conf
   ```

---

## Diagnostic Procedures

### System Health Check

**Complete diagnostic script:**

```python
async def comprehensive_health_check():
    """Perform comprehensive system health diagnostics."""
    
    print("🏥 Starting comprehensive health check...")
    
    health_report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tests": {},
        "recommendations": [],
        "overall_status": "unknown"
    }
    
    # Test 1: Python Environment
    print("🐍 Checking Python environment...")
    try:
        import fastmcp
        import src.core.mcp_server
        health_report["tests"]["python_environment"] = "✅ PASS"
    except ImportError as e:
        health_report["tests"]["python_environment"] = f"❌ FAIL: {e}"
        health_report["recommendations"].append("Install missing dependencies")
    
    # Test 2: Keyboard Maestro Connectivity
    print("⌨️ Testing Keyboard Maestro connectivity...")
    try:
        async with Client("stdio:keyboard-maestro-mcp") as client:
            await client.call_tool("km_engine_status", {"operation": "status"})
        health_report["tests"]["km_connectivity"] = "✅ PASS"
    except Exception as e:
        health_report["tests"]["km_connectivity"] = f"❌ FAIL: {e}"
        health_report["recommendations"].append("Check Keyboard Maestro installation")
    
    # Test 3: File System Permissions
    print("📁 Testing file system permissions...")
    try:
        test_file = "/tmp/km_mcp_permission_test.txt"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        health_report["tests"]["file_permissions"] = "✅ PASS"
    except Exception as e:
        health_report["tests"]["file_permissions"] = f"❌ FAIL: {e}"
        health_report["recommendations"].append("Grant file system permissions")
    
    # Test 4: Memory and Resources
    print("💾 Checking system resources...")
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        if memory.available > 1024*1024*1024:  # 1GB
            memory_status = "✅ PASS"
        else:
            memory_status = "⚠️ WARN: Low memory"
            health_report["recommendations"].append("Close unnecessary applications")
        
        health_report["tests"]["system_resources"] = memory_status
        health_report["tests"]["disk_space"] = f"{disk.free // (1024**3)}GB free"
        
    except ImportError:
        health_report["tests"]["system_resources"] = "⚠️ SKIP: psutil not available"
    
    # Test 5: Network Connectivity (for HTTP mode)
    print("🌐 Testing network connectivity...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        
        if result == 0:
            health_report["tests"]["network"] = "✅ PASS: Port 8000 accessible"
        else:
            health_report["tests"]["network"] = "⚠️ INFO: Port 8000 not in use (normal for STDIO mode)"
    except Exception as e:
        health_report["tests"]["network"] = f"❌ FAIL: {e}"
    
    # Overall Status
    failed_tests = [k for k, v in health_report["tests"].items() if "❌ FAIL" in v]
    warning_tests = [k for k, v in health_report["tests"].items() if "⚠️" in v]
    
    if not failed_tests:
        if not warning_tests:
            health_report["overall_status"] = "✅ HEALTHY"
        else:
            health_report["overall_status"] = "⚠️ WARNINGS"
    else:
        health_report["overall_status"] = "❌ ISSUES_FOUND"
    
    # Print Report
    print(f"\n📊 Health Check Report:")
    print(f"Overall Status: {health_report['overall_status']}")
    print(f"\nTest Results:")
    for test, result in health_report["tests"].items():
        print(f"  {test}: {result}")
    
    if health_report["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in health_report["recommendations"]:
            print(f"  • {rec}")
    
    return health_report

# Run the health check
asyncio.run(comprehensive_health_check())
```

### Performance Diagnostics

**Performance testing script:**

```python
async def performance_diagnostics():
    """Diagnose performance issues with detailed metrics."""
    
    print("⚡ Starting performance diagnostics...")
    
    async with Client("stdio:keyboard-maestro-mcp") as client:
        
        metrics = {
            "timestamp": datetime.datetime.now().isoformat(),
            "response_times": {},
            "throughput_tests": {},
            "resource_usage": {}
        }
        
        # Test 1: Basic response times
        print("⏱️ Testing basic response times...")
        
        basic_operations = [
            ("km_engine_status", {"operation": "status"}),
            ("km_variable_manager", {"operation": "get", "name": "NonExistent", "scope": "global"}),
            ("km_list_macros", {"include_disabled": False})
        ]
        
        for op_name, params in basic_operations:
            try:
                start_time = time.time()
                await client.call_tool(op_name, params)
                response_time = time.time() - start_time
                metrics["response_times"][op_name] = f"{response_time:.3f}s"
                
                # Flag slow operations
                if response_time > 2.0:
                    metrics["response_times"][f"{op_name}_warning"] = "⚠️ SLOW"
                    
            except Exception as e:
                metrics["response_times"][op_name] = f"ERROR: {str(e)[:50]}"
        
        # Test 2: Throughput testing
        print("📈 Testing throughput...")
        
        throughput_start = time.time()
        concurrent_operations = 5
        
        tasks = []
        for i in range(concurrent_operations):
            task = client.call_tool("km_engine_status", {"operation": "status"})
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        throughput_time = time.time() - throughput_start
        
        successful_ops = len([r for r in results if not isinstance(r, Exception)])
        ops_per_second = successful_ops / throughput_time
        
        metrics["throughput_tests"]["concurrent_operations"] = concurrent_operations
        metrics["throughput_tests"]["successful_operations"] = successful_ops
        metrics["throughput_tests"]["ops_per_second"] = f"{ops_per_second:.2f}"
        
        # Test 3: Memory usage pattern
        print("💾 Testing memory usage...")
        
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform memory-intensive operation
            large_data_operations = []
            for i in range(10):
                task = client.call_tool("km_list_macros", {"include_disabled": True})
                large_data_operations.append(task)
            
            await asyncio.gather(*large_data_operations, return_exceptions=True)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            metrics["resource_usage"]["initial_memory_mb"] = f"{initial_memory:.1f}"
            metrics["resource_usage"]["final_memory_mb"] = f"{final_memory:.1f}"
            metrics["resource_usage"]["memory_increase_mb"] = f"{memory_increase:.1f}"
            
            if memory_increase > 50:  # MB
                metrics["resource_usage"]["memory_warning"] = "⚠️ HIGH_USAGE"
                
        except ImportError:
            metrics["resource_usage"]["memory_tracking"] = "UNAVAILABLE: psutil not installed"
        
        # Performance Analysis
        print(f"\n📊 Performance Diagnostic Report:")
        
        print(f"\n⏱️ Response Times:")
        for op, time_str in metrics["response_times"].items():
            print(f"  {op}: {time_str}")
        
        print(f"\n📈 Throughput:")
        for metric, value in metrics["throughput_tests"].items():
            print(f"  {metric}: {value}")
        
        print(f"\n💾 Resource Usage:")
        for metric, value in metrics["resource_usage"].items():
            print(f"  {metric}: {value}")
        
        # Recommendations based on metrics
        recommendations = []
        
        # Check for slow response times
        slow_ops = [k for k, v in metrics["response_times"].items() if "SLOW" in str(v)]
        if slow_ops:
            recommendations.append("Consider restarting Keyboard Maestro Engine for slow operations")
        
        # Check throughput
        if float(metrics["throughput_tests"]["ops_per_second"]) < 1.0:
            recommendations.append("Low throughput detected - check system resources")
        
        # Check memory usage
        if "memory_increase_mb" in metrics["resource_usage"]:
            increase = float(metrics["resource_usage"]["memory_increase_mb"])
            if increase > 20:
                recommendations.append("High memory usage - consider restarting server periodically")
        
        if recommendations:
            print(f"\n💡 Performance Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        return metrics

# Run performance diagnostics
asyncio.run(performance_diagnostics())
```

---

## Error Code Reference

### Complete Error Code Documentation

| Error Code | Category | Severity | Description | Common Causes | Recovery Actions |
|------------|----------|----------|-------------|---------------|------------------|
| `MACRO_NOT_FOUND` | Validation | Medium | Macro identifier not found | Typo in name, macro deleted, wrong UUID | Use `km_list_macros` to verify, check spelling |
| `INVALID_PARAMETER` | Validation | Low | Parameter format invalid | Wrong data type, missing required field | Check parameter schema, validate inputs |
| `PERMISSION_DENIED` | Security | High | Insufficient permissions | Missing accessibility rights, file access denied | Grant permissions in System Preferences |
| `TIMEOUT_ERROR` | Performance | Medium | Operation timed out | Long-running macro, system overload | Increase timeout, optimize macro |
| `APPLESCRIPT_ERROR` | Integration | High | AppleScript execution failed | KM Engine not running, script syntax error | Restart Engine, check AppleScript |
| `RESOURCE_BUSY` | System | Medium | Resource temporarily unavailable | File locked, application busy | Wait and retry, check resource status |
| `RATE_LIMIT_EXCEEDED` | Performance | Low | Too many requests | Rapid successive calls | Implement delay, use batch operations |
| `SYSTEM_ERROR` | System | Critical | Unexpected system error | Hardware issue, OS problem | Check logs, restart system components |
| `CONNECTION_FAILED` | Network | High | Cannot connect to service | Network issue, service down | Check connectivity, restart services |
| `VALIDATION_ERROR` | Validation | Medium | Data validation failed | Invalid data format, constraint violation | Validate data, check requirements |
| `AUTHENTICATION_ERROR` | Security | High | Authentication failed | Invalid credentials, expired token | Check auth configuration |
| `AUTHORIZATION_ERROR` | Security | High | Insufficient privileges | User lacks required permissions | Grant appropriate permissions |
| `CONFIGURATION_ERROR` | System | High | Configuration invalid | Missing config, wrong format | Check config files, validate settings |
| `DEPENDENCY_ERROR` | System | Critical | Required dependency missing | Missing library, service unavailable | Install dependencies, start services |
| `DATA_CORRUPTION` | Data | Critical | Data integrity compromised | File corruption, incomplete write | Restore from backup, regenerate data |

### Detailed Error Scenarios

#### Macro Execution Errors

```python
# Common macro execution error patterns
async def handle_macro_errors():
    try:
        result = await client.call_tool("km_execute_macro", {
            "identifier": "My Macro",
            "timeout": 30
        })
    except MCPError as e:
        if e.code == "MACRO_NOT_FOUND":
            # Check if macro exists with different name
            macros = await client.call_tool("km_list_macros", {})
            similar_macros = find_similar_names("My Macro", macros)
            print(f"Did you mean: {similar_macros}")
            
        elif e.code == "TIMEOUT_ERROR":
            # Retry with longer timeout
            await client.call_tool("km_execute_macro", {
                "identifier": "My Macro",
                "timeout": 120  # Increased timeout
            })
            
        elif e.code == "APPLESCRIPT_ERROR":
            # Check Engine status and restart if needed
            await client.call_tool("km_engine_status", {
                "operation": "reload"
            })
            # Retry after engine restart
            await asyncio.sleep(3)
            await client.call_tool("km_execute_macro", {
                "identifier": "My Macro",
                "timeout": 30
            })
```

#### Variable Access Errors

```python
async def handle_variable_errors():
    try:
        result = await client.call_tool("km_variable_manager", {
            "operation": "get",
            "name": "MyVariable",
            "scope": "global"
        })
    except MCPError as e:
        if e.code == "INVALID_PARAMETER":
            # Variable name might have invalid characters
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', "MyVariable")
            result = await client.call_tool("km_variable_manager", {
                "operation": "get",
                "name": clean_name,
                "scope": "global"
            })
            
        elif e.code == "PERMISSION_DENIED":
            # Try different scope
            result = await client.call_tool("km_variable_manager", {
                "operation": "get",
                "name": "MyVariable",
                "scope": "local"
            })
```

---

## Performance Debugging

### Performance Monitoring Tools

#### Real-time Performance Monitor

```python
class PerformanceMonitor:
    """Real-time performance monitoring for MCP operations."""
    
    def __init__(self, client):
        self.client = client
        self.metrics = {
            "operation_times": {},
            "error_counts": {},
            "throughput_data": [],
            "resource_usage": []
        }
        self.monitoring = False
    
    async def start_monitoring(self, duration_seconds: int = 300):
        """Start real-time performance monitoring."""
        
        print(f"📊 Starting performance monitoring for {duration_seconds}s...")
        self.monitoring = True
        
        # Start monitoring tasks
        tasks = [
            self.monitor_operations(),
            self.monitor_resources(), 
            self.monitor_errors()
        ]
        
        # Run for specified duration
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=duration_seconds
            )
        except asyncio.TimeoutError:
            print("⏰ Monitoring period completed")
        finally:
            self.monitoring = False
    
    async def monitor_operations(self):
        """Monitor operation response times."""
        
        test_operations = [
            ("km_engine_status", {"operation": "status"}),
            ("km_list_macros", {"include_disabled": False}),
            ("km_variable_manager", {"operation": "get", "name": "TestVar", "scope": "global"})
        ]
        
        while self.monitoring:
            for op_name, params in test_operations:
                try:
                    start_time = time.time()
                    await self.client.call_tool(op_name, params)
                    response_time = time.time() - start_time
                    
                    if op_name not in self.metrics["operation_times"]:
                        self.metrics["operation_times"][op_name] = []
                    
                    self.metrics["operation_times"][op_name].append(response_time)
                    
                    # Alert on slow operations
                    if response_time > 5.0:
                        print(f"🐌 SLOW OPERATION: {op_name} took {response_time:.2f}s")
                
                except Exception as e:
                    self.metrics["error_counts"][op_name] = self.metrics["error_counts"].get(op_name, 0) + 1
                    print(f"❌ ERROR in {op_name}: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def monitor_resources(self):
        """Monitor system resource usage."""
        
        try:
            import psutil
        except ImportError:
            print("⚠️ psutil not available for resource monitoring")
            return
        
        while self.monitoring:
            try:
                # Get current resource usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                resource_data = {
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / 1024 / 1024,
                    "disk_free_gb": disk.free / 1024 / 1024 / 1024
                }
                
                self.metrics["resource_usage"].append(resource_data)
                
                # Alert on high resource usage
                if cpu_percent > 80:
                    print(f"🔥 HIGH CPU: {cpu_percent}%")
                if memory.percent > 80:
                    print(f"💾 HIGH MEMORY: {memory.percent}%")
                
            except Exception as e:
                print(f"❌ Resource monitoring error: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def monitor_errors(self):
        """Monitor for error patterns."""
        
        while self.monitoring:
            # Check error log patterns
            try:
                # This would read actual log files in a real implementation
                error_log_analysis = await self.analyze_error_logs()
                
                if error_log_analysis["new_errors"] > 5:
                    print(f"🚨 ERROR SPIKE: {error_log_analysis['new_errors']} new errors")
                
            except Exception as e:
                print(f"❌ Error monitoring failed: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def analyze_error_logs(self):
        """Analyze error logs for patterns."""
        
        # Simulate error log analysis
        return {
            "new_errors": random.randint(0, 10),
            "error_types": ["TIMEOUT_ERROR", "APPLESCRIPT_ERROR"],
            "error_frequency": "normal"
        }
    
    def generate_performance_report(self):
        """Generate comprehensive performance report."""
        
        report = {
            "monitoring_period": "completed",
            "operation_performance": {},
            "resource_summary": {},
            "error_summary": {},
            "recommendations": []
        }
        
        # Analyze operation performance
        for op_name, times in self.metrics["operation_times"].items():
            if times:
                report["operation_performance"][op_name] = {
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "total_calls": len(times)
                }
                
                # Add recommendations for slow operations
                avg_time = report["operation_performance"][op_name]["avg_time"]
                if avg_time > 2.0:
                    report["recommendations"].append(f"Optimize {op_name} - avg response: {avg_time:.2f}s")
        
        # Analyze resource usage
        if self.metrics["resource_usage"]:
            cpu_values = [r["cpu_percent"] for r in self.metrics["resource_usage"]]
            memory_values = [r["memory_percent"] for r in self.metrics["resource_usage"]]
            
            report["resource_summary"] = {
                "avg_cpu": sum(cpu_values) / len(cpu_values),
                "max_cpu": max(cpu_values),
                "avg_memory": sum(memory_values) / len(memory_values),
                "max_memory": max(memory_values)
            }
            
            if report["resource_summary"]["avg_cpu"] > 50:
                report["recommendations"].append("High CPU usage detected - check for resource-intensive macros")
            
            if report["resource_summary"]["avg_memory"] > 70:
                report["recommendations"].append("High memory usage - consider restarting server")
        
        # Error analysis
        total_errors = sum(self.metrics["error_counts"].values())
        if total_errors > 0:
            report["error_summary"]["total_errors"] = total_errors
            report["error_summary"]["error_by_operation"] = self.metrics["error_counts"]
            
            if total_errors > 10:
                report["recommendations"].append("High error rate - investigate system stability")
        
        return report

# Usage example
async def run_performance_monitoring():
    async with Client("stdio:keyboard-maestro-mcp") as client:
        monitor = PerformanceMonitor(client)
        
        # Monitor for 5 minutes
        await monitor.start_monitoring(300)
        
        # Generate and display report
        report = monitor.generate_performance_report()
        
        print("\n📊 Performance Monitoring Report:")
        print(f"Operation Performance: {json.dumps(report['operation_performance'], indent=2)}")
        print(f"Resource Summary: {json.dumps(report['resource_summary'], indent=2)}")
        print(f"Error Summary: {json.dumps(report['error_summary'], indent=2)}")
        
        if report["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")

# Run monitoring
asyncio.run(run_performance_monitoring())
```

### Performance Optimization Strategies

#### 1. Connection Pooling and Caching

```python
class OptimizedMCPClient:
    """MCP client with built-in performance optimizations."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.cache = {}
        self.cache_ttl = 60  # seconds
        self.connection_pool = []
        self.stats = {"cache_hits": 0, "cache_misses": 0}
    
    async def cached_call_tool(self, tool_name: str, parameters: dict, use_cache: bool = True):
        """Call tool with intelligent caching."""
        
        # Generate cache key
        cache_key = f"{tool_name}:{hash(str(sorted(parameters.items())))}"
        
        # Check cache for read operations
        if use_cache and self.is_read_operation(tool_name, parameters):
            cached_result = self.get_from_cache(cache_key)
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result
        
        self.stats["cache_misses"] += 1
        
        # Execute operation
        async with Client(self.connection_string) as client:
            result = await client.call_tool(tool_name, parameters)
        
        # Cache result for read operations
        if use_cache and self.is_read_operation(tool_name, parameters):
            self.add_to_cache(cache_key, result)
        
        return result
    
    def is_read_operation(self, tool_name: str, parameters: dict) -> bool:
        """Determine if operation is cacheable."""
        
        read_operations = {
            "km_engine_status": True,
            "km_list_macros": True,
            "km_variable_manager": parameters.get("operation") == "get"
        }
        
        return read_operations.get(tool_name, False)
    
    def get_from_cache(self, key: str):
        """Get item from cache if not expired."""
        
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item["timestamp"] < self.cache_ttl:
                return item["data"]
            else:
                del self.cache[key]  # Remove expired item
        
        return None
    
    def add_to_cache(self, key: str, data):
        """Add item to cache with timestamp."""
        
        self.cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
        
        # Limit cache size
        if len(self.cache) > 1000:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
```

#### 2. Batch Operations

```python
class BatchOperationManager:
    """Manage batch operations for improved performance."""
    
    def __init__(self, client):
        self.client = client
        self.batch_queue = []
        self.batch_size = 10
        self.batch_timeout = 2.0  # seconds
    
    async def add_to_batch(self, operation):
        """Add operation to batch queue."""
        
        self.batch_queue.append({
            "operation": operation,
            "timestamp": time.time(),
            "future": asyncio.Future()
        })
        
        # Execute batch if size limit reached
        if len(self.batch_queue) >= self.batch_size:
            await self.execute_batch()
        
        # Return future for this operation
        return self.batch_queue[-1]["future"]
    
    async def execute_batch(self):
        """Execute all operations in current batch."""
        
        if not self.batch_queue:
            return
        
        current_batch = self.batch_queue.copy()
        self.batch_queue.clear()
        
        print(f"🚀 Executing batch of {len(current_batch)} operations")
        
        # Group operations by type for optimization
        grouped_ops = {}
        for item in current_batch:
            op_type = item["operation"]["tool_name"]
            if op_type not in grouped_ops:
                grouped_ops[op_type] = []
            grouped_ops[op_type].append(item)
        
        # Execute groups concurrently
        for op_type, operations in grouped_ops.items():
            try:
                if op_type == "km_variable_manager":
                    await self.batch_variable_operations(operations)
                else:
                    await self.batch_generic_operations(operations)
            except Exception as e:
                # Mark all operations in this group as failed
                for item in operations:
                    item["future"].set_exception(e)
    
    async def batch_variable_operations(self, operations):
        """Optimize variable operations using dictionary bulk operations."""
        
        # Separate get and set operations
        get_ops = [op for op in operations if op["operation"]["parameters"].get("operation") == "get"]
        set_ops = [op for op in operations if op["operation"]["parameters"].get("operation") == "set"]
        
        # Batch variable gets
        if get_ops:
            for op in get_ops:
                try:
                    result = await self.client.call_tool(
                        op["operation"]["tool_name"],
                        op["operation"]["parameters"]
                    )
                    op["future"].set_result(result)
                except Exception as e:
                    op["future"].set_exception(e)
        
        # Batch variable sets using dictionary operation
        if set_ops:
            try:
                # Create bulk data structure
                bulk_data = {}
                for op in set_ops:
                    params = op["operation"]["parameters"]
                    bulk_data[params["name"]] = params["value"]
                
                # Execute bulk set operation (would need custom macro)
                await self.client.call_tool("km_execute_macro", {
                    "identifier": "Bulk Variable Setter",
                    "trigger_value": json.dumps(bulk_data),
                    "timeout": 60
                })
                
                # Mark all set operations as successful
                for op in set_ops:
                    op["future"].set_result({"success": True})
                    
            except Exception as e:
                for op in set_ops:
                    op["future"].set_exception(e)
    
    async def batch_generic_operations(self, operations):
        """Execute generic operations with concurrency control."""
        
        semaphore = asyncio.Semaphore(5)  # Limit concurrency
        
        async def execute_single(item):
            async with semaphore:
                try:
                    result = await self.client.call_tool(
                        item["operation"]["tool_name"],
                        item["operation"]["parameters"]
                    )
                    item["future"].set_result(result)
                except Exception as e:
                    item["future"].set_exception(e)
        
        # Execute all operations concurrently with limit
        await asyncio.gather(*[execute_single(item) for item in operations])
```

---

## Log Analysis

### Understanding MCP Server Logs

#### Log File Locations

```bash
# Main server log
logs/km_mcp_server.log

# Error logs
logs/errors.log

# Performance logs  
logs/performance.log

# Debug logs (development mode)
logs/debug.log

# Keyboard Maestro Engine logs
~/Library/Logs/Keyboard Maestro/Engine.log
```

#### Log Format and Structure

```
2025-06-21 22:15:30,123 [INFO] main:127 - Server starting in STDIO mode
2025-06-21 22:15:30,234 [INFO] mcp_server:89 - Initializing MCP tools registry
2025-06-21 22:15:30,345 [DEBUG] tool_registry:45 - Registered tool: km_execute_macro
2025-06-21 22:15:31,456 [INFO] mcp_server:112 - Server ready, 51 tools available
2025-06-21 22:15:35,567 [INFO] km_interface:78 - Executing macro: Daily Setup
2025-06-21 22:15:36,234 [DEBUG] applescript_pool:23 - AppleScript execution time: 0.667s
2025-06-21 22:15:36,235 [INFO] km_interface:89 - Macro execution completed successfully
```

#### Log Analysis Script

```python
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class LogAnalyzer:
    """Comprehensive log analysis for MCP server troubleshooting."""
    
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.log_entries = []
        self.patterns = {
            "timestamp": r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})",
            "level": r"\[(\w+)\]",
            "module": r"] (\w+):",
            "message": r": (.+)$"
        }
    
    def parse_log_file(self):
        """Parse log file into structured entries."""
        
        print(f"📖 Parsing log file: {self.log_file_path}")
        
        try:
            with open(self.log_file_path, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                entry = self.parse_log_line(line.strip(), line_num)
                if entry:
                    self.log_entries.append(entry)
            
            print(f"📊 Parsed {len(self.log_entries)} log entries")
            
        except FileNotFoundError:
            print(f"❌ Log file not found: {self.log_file_path}")
        except Exception as e:
            print(f"❌ Error parsing log file: {e}")
    
    def parse_log_line(self, line: str, line_num: int) -> dict:
        """Parse individual log line into components."""
        
        entry = {"line_number": line_num, "raw": line}
        
        # Extract timestamp
        timestamp_match = re.search(self.patterns["timestamp"], line)
        if timestamp_match:
            try:
                entry["timestamp"] = datetime.strptime(
                    timestamp_match.group(1), "%Y-%m-%d %H:%M:%S,%f"
                )
            except ValueError:
                entry["timestamp"] = None
        
        # Extract log level
        level_match = re.search(self.patterns["level"], line)
        if level_match:
            entry["level"] = level_match.group(1)
        
        # Extract module
        module_match = re.search(self.patterns["module"], line)
        if module_match:
            entry["module"] = module_match.group(1)
        
        # Extract message
        message_match = re.search(self.patterns["message"], line)
        if message_match:
            entry["message"] = message_match.group(1)
        
        return entry
    
    def analyze_error_patterns(self, time_window_hours: int = 24):
        """Analyze error patterns over specified time window."""
        
        print(f"🔍 Analyzing error patterns (last {time_window_hours} hours)")
        
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_entries = [
            entry for entry in self.log_entries 
            if entry.get("timestamp") and entry["timestamp"] > cutoff_time
        ]
        
        # Count errors by level
        error_levels = Counter(
            entry["level"] for entry in recent_entries 
            if entry.get("level") in ["ERROR", "CRITICAL", "WARNING"]
        )
        
        # Count errors by module
        error_modules = Counter(
            entry["module"] for entry in recent_entries 
            if entry.get("level") == "ERROR" and entry.get("module")
        )
        
        # Identify error message patterns
        error_messages = [
            entry["message"] for entry in recent_entries 
            if entry.get("level") == "ERROR" and entry.get("message")
        ]
        
        # Group similar error messages
        error_patterns = defaultdict(int)
        for message in error_messages:
            # Normalize error messages to identify patterns
            normalized = re.sub(r'\d+', 'X', message)  # Replace numbers
            normalized = re.sub(r"'[^']*'", "'...'", normalized)  # Replace quoted strings
            error_patterns[normalized] += 1
        
        # Performance issues
        slow_operations = []
        for entry in recent_entries:
            if entry.get("message") and "slow" in entry["message"].lower():
                slow_operations.append(entry)
        
        analysis = {
            "time_window": f"{time_window_hours} hours",
            "total_entries": len(recent_entries),
            "error_levels": dict(error_levels),
            "error_modules": dict(error_modules.most_common(10)),
            "error_patterns": dict(error_patterns),
            "slow_operations": len(slow_operations),
            "recommendations": []
        }
        
        # Generate recommendations
        if error_levels["ERROR"] > 50:
            analysis["recommendations"].append("High error rate - investigate system stability")
        
        if "applescript_pool" in error_modules:
            analysis["recommendations"].append("AppleScript errors detected - check Keyboard Maestro Engine")
        
        if error_levels["WARNING"] > 100:
            analysis["recommendations"].append("Many warnings - review configuration")
        
        if slow_operations:
            analysis["recommendations"].append(f"{len(slow_operations)} slow operations - optimize performance")
        
        return analysis
    
    def analyze_performance_trends(self):
        """Analyze performance trends from logs."""
        
        print("📈 Analyzing performance trends")
        
        # Extract timing information
        timing_entries = []
        timing_pattern = r"execution time: ([\d.]+)s"
        
        for entry in self.log_entries:
            if entry.get("message"):
                timing_match = re.search(timing_pattern, entry["message"])
                if timing_match:
                    timing_entries.append({
                        "timestamp": entry["timestamp"],
                        "duration": float(timing_match.group(1)),
                        "operation": entry.get("module", "unknown")
                    })
        
        if not timing_entries:
            return {"message": "No timing data found in logs"}
        
        # Calculate statistics
        durations = [entry["duration"] for entry in timing_entries]
        
        performance_stats = {
            "total_operations": len(timing_entries),
            "avg_duration": sum(durations) / len(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "operations_over_5s": len([d for d in durations if d > 5.0]),
            "operations_over_10s": len([d for d in durations if d > 10.0])
        }
        
        # Trend analysis (simplified)
        if len(timing_entries) > 10:
            recent_avg = sum(durations[-10:]) / 10
            older_avg = sum(durations[:-10]) / (len(durations) - 10)
            
            if recent_avg > older_avg * 1.5:
                performance_stats["trend"] = "degrading"
            elif recent_avg < older_avg * 0.8:
                performance_stats["trend"] = "improving"
            else:
                performance_stats["trend"] = "stable"
        
        return performance_stats
    
    def generate_health_summary(self):
        """Generate overall health summary from log analysis."""
        
        error_analysis = self.analyze_error_patterns()
        performance_analysis = self.analyze_performance_trends()
        
        # Calculate health score
        health_score = 100
        
        # Deduct for errors
        error_count = sum(error_analysis["error_levels"].values())
        health_score -= min(error_count * 2, 40)  # Max 40 point deduction
        
        # Deduct for performance issues
        if isinstance(performance_analysis, dict) and "operations_over_10s" in performance_analysis:
            slow_ops = performance_analysis["operations_over_10s"]
            health_score -= min(slow_ops * 5, 30)  # Max 30 point deduction
        
        # Deduct for trends
        if performance_analysis.get("trend") == "degrading":
            health_score -= 15
        
        health_score = max(0, health_score)  # Ensure non-negative
        
        # Determine status
        if health_score >= 90:
            status = "🟢 EXCELLENT"
        elif health_score >= 70:
            status = "🟡 GOOD"
        elif health_score >= 50:
            status = "🟠 FAIR"
        else:
            status = "🔴 POOR"
        
        summary = {
            "health_score": health_score,
            "status": status,
            "error_analysis": error_analysis,
            "performance_analysis": performance_analysis,
            "recommendations": error_analysis["recommendations"]
        }
        
        return summary

# Usage example
def analyze_server_logs():
    analyzer = LogAnalyzer("logs/km_mcp_server.log")
    analyzer.parse_log_file()
    
    # Generate comprehensive analysis
    health_summary = analyzer.generate_health_summary()
    
    print(f"\n🏥 Server Health Summary:")
    print(f"Health Score: {health_summary['health_score']}/100")
    print(f"Status: {health_summary['status']}")
    
    print(f"\n📊 Error Analysis:")
    error_data = health_summary["error_analysis"]
    print(f"  Total entries: {error_data['total_entries']}")
    print(f"  Error levels: {error_data['error_levels']}")
    print(f"  Top error modules: {list(error_data['error_modules'].keys())[:3]}")
    
    print(f"\n⚡ Performance Analysis:")
    perf_data = health_summary["performance_analysis"]
    if isinstance(perf_data, dict) and "avg_duration" in perf_data:
        print(f"  Average operation time: {perf_data['avg_duration']:.2f}s")
        print(f"  Operations over 5s: {perf_data['operations_over_5s']}")
        print(f"  Performance trend: {perf_data.get('trend', 'unknown')}")
    
    if health_summary["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in health_summary["recommendations"]:
            print(f"  • {rec}")

# Run log analysis
analyze_server_logs()
```

### Common Log Patterns and Solutions

#### Startup Issues

```bash
# Pattern: ImportError during startup
2025-06-21 22:15:30,123 [ERROR] main:45 - ImportError: No module named 'fastmcp'

# Solution: Install dependencies
pip install -r requirements.txt
```

#### Performance Issues

```bash
# Pattern: Slow macro execution
2025-06-21 22:15:35,567 [WARNING] km_interface:78 - Macro execution slow: 15.234s

# Investigation: Check macro complexity
# Solution: Optimize macro or increase timeout
```

#### AppleScript Errors

```bash
# Pattern: AppleScript communication failure
2025-06-21 22:15:40,789 [ERROR] applescript_pool:67 - AppleScript error: Application not found

# Solution: Check Keyboard Maestro Engine status
# Restart Engine if necessary
```

---

## Advanced Troubleshooting

### Custom Diagnostic Tools

#### System Integration Tester

```python
class SystemIntegrationTester:
    """Comprehensive system integration testing and diagnostics."""
    
    def __init__(self):
        self.test_results = {}
        self.client = None
    
    async def run_full_diagnostic(self):
        """Run complete system diagnostic suite."""
        
        print("🔧 Starting comprehensive system integration diagnostic...")
        
        async with Client("stdio:keyboard-maestro-mcp") as client:
            self.client = client
            
            # Test suite
            tests = [
                ("Server Connectivity", self.test_server_connectivity),
                ("Keyboard Maestro Integration", self.test_km_integration),
                ("File System Access", self.test_file_system_access),
                ("Variable Operations", self.test_variable_operations),
                ("Macro Execution", self.test_macro_execution),
                ("Performance Baseline", self.test_performance_baseline),
                ("Error Handling", self.test_error_handling),
                ("Security Permissions", self.test_security_permissions)
            ]
            
            for test_name, test_func in tests:
                print(f"\n🧪 Running: {test_name}")
                try:
                    result = await test_func()
                    self.test_results[test_name] = {"status": "PASS", "details": result}
                    print(f"✅ {test_name}: PASSED")
                except Exception as e:
                    self.test_results[test_name] = {"status": "FAIL", "error": str(e)}
                    print(f"❌ {test_name}: FAILED - {e}")
        
        # Generate diagnostic report
        report = self.generate_diagnostic_report()
        return report
    
    async def test_server_connectivity(self):
        """Test basic server connectivity and responsiveness."""
        
        start_time = time.time()
        
        # Test engine status
        result = await self.client.call_tool("km_engine_status", {
            "operation": "status"
        })
        
        response_time = time.time() - start_time
        
        return {
            "response_time": response_time,
            "engine_responsive": True,
            "result_length": len(result[0].text)
        }
    
    async def test_km_integration(self):
        """Test Keyboard Maestro integration functionality."""
        
        # Test macro listing
        macros_result = await self.client.call_tool("km_list_macros", {
            "include_disabled": False
        })
        
        macro_count = len(eval(macros_result[0].text))  # In production, use json.loads
        
        # Test engine reload
        await self.client.call_tool("km_engine_status", {
            "operation": "reload"
        })
        
        return {
            "macro_count": macro_count,
            "engine_reload": "successful"
        }
    
    async def test_file_system_access(self):
        """Test file system access permissions."""
        
        test_paths = [
            "/tmp/km_test.txt",
            "~/Desktop/km_test.txt",  
            "~/Documents/km_test.txt"
        ]
        
        results = {}
        
        for path in test_paths:
            try:
                # Test file creation
                await self.client.call_tool("km_file_operations", {
                    "operation": "copy",
                    "source_path": "/dev/null",
                    "destination_path": path
                })
                
                # Test file deletion
                await self.client.call_tool("km_file_operations", {
                    "operation": "delete",
                    "source_path": path
                })
                
                results[path] = "accessible"
                
            except Exception as e:
                results[path] = f"denied: {str(e)[:50]}"
        
        return results
    
    async def test_variable_operations(self):
        """Test variable management operations."""
        
        test_var_name = f"DiagnosticTest_{int(time.time())}"
        test_value = "diagnostic_test_value"
        
        # Test variable set
        await self.client.call_tool("km_variable_manager", {
            "operation": "set",
            "name": test_var_name,
            "value": test_value,
            "scope": "global"
        })
        
        # Test variable get
        result = await self.client.call_tool("km_variable_manager", {
            "operation": "get",
            "name": test_var_name,
            "scope": "global"
        })
        
        retrieved_value = result[0].text
        
        # Test variable delete
        await self.client.call_tool("km_variable_manager", {
            "operation": "delete",
            "name": test_var_name,
            "scope": "global"
        })
        
        return {
            "set_operation": "successful",
            "get_operation": "successful",
            "value_match": retrieved_value == test_value,
            "delete_operation": "successful"
        }
    
    async def test_macro_execution(self):
        """Test macro execution capabilities."""
        
        # Try to execute a simple system macro
        try:
            result = await self.client.call_tool("km_execute_macro", {
                "identifier": "System Information",  # Common system macro
                "timeout": 30
            })
            
            return {
                "execution_successful": True,
                "execution_time": "< 30s",
                "result_received": True
            }
            
        except Exception as e:
            if "not found" in str(e).lower():
                return {
                    "execution_successful": False,
                    "reason": "No test macro available",
                    "recommendation": "Create a simple test macro"
                }
            else:
                raise e
    
    async def test_performance_baseline(self):
        """Establish performance baseline."""
        
        operations = [
            ("km_engine_status", {"operation": "status"}),
            ("km_list_macros", {"include_disabled": False}),
            ("km_variable_manager", {"operation": "get", "name": "NonExistent", "scope": "global"})
        ]
        
        timings = {}
        
        for op_name, params in operations:
            times = []
            
            # Run each operation 5 times
            for _ in range(5):
                start_time = time.time()
                try:
                    await self.client.call_tool(op_name, params)
                except Exception:
                    pass  # Ignore errors for timing
                times.append(time.time() - start_time)
            
            timings[op_name] = {
                "avg_time": sum(times) / len(times),
                "max_time": max(times),
                "min_time": min(times)
            }
        
        return timings
    
    async def test_error_handling(self):
        """Test error handling robustness."""
        
        error_tests = [
            ("Invalid macro", "km_execute_macro", {"identifier": "NonExistent__Macro__12345"}),
            ("Invalid variable", "km_variable_manager", {"operation": "get", "name": "NonExistent__Var__12345", "scope": "global"}),
            ("Invalid parameter", "km_engine_status", {"operation": "invalid_operation"})
        ]
        
        error_handling_results = {}
        
        for test_name, tool_name, params in error_tests:
            try:
                await self.client.call_tool(tool_name, params)
                error_handling_results[test_name] = "UNEXPECTED_SUCCESS"
            except Exception as e:
                # Check if error is properly formatted
                error_str = str(e)
                if any(keyword in error_str.lower() for keyword in ["error", "not found", "invalid"]):
                    error_handling_results[test_name] = "PROPER_ERROR"
                else:
                    error_handling_results[test_name] = f"UNCLEAR_ERROR: {error_str[:50]}"
        
        return error_handling_results
    
    async def test_security_permissions(self):
        """Test security and permission configurations."""
        
        # Test accessibility permissions
        try:
            await self.client.call_tool("km_execute_macro", {
                "identifier": "Test Accessibility",
                "timeout": 5
            })
            accessibility_status = "granted"
        except Exception as e:
            if "permission" in str(e).lower():
                accessibility_status = "denied"
            else:
                accessibility_status = "unknown"
        
        # Test file system permissions
        try:
            await self.client.call_tool("km_file_operations", {
                "operation": "copy",
                "source_path": "/dev/null",
                "destination_path": "/tmp/permission_test.txt"
            })
            file_system_status = "granted"
        except Exception as e:
            if "permission" in str(e).lower():
                file_system_status = "denied"
            else:
                file_system_status = "unknown"
        
        return {
            "accessibility_permissions": accessibility_status,
            "file_system_permissions": file_system_status
        }
    
    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report."""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "test_summary": {},
            "detailed_results": self.test_results,
            "recommendations": [],
            "system_readiness": "unknown"
        }
        
        # Analyze test results
        passed_tests = [name for name, result in self.test_results.items() if result["status"] == "PASS"]
        failed_tests = [name for name, result in self.test_results.items() if result["status"] == "FAIL"]
        
        report["test_summary"]["total_tests"] = len(self.test_results)
        report["test_summary"]["passed"] = len(passed_tests)
        report["test_summary"]["failed"] = len(failed_tests)
        report["test_summary"]["pass_rate"] = f"{len(passed_tests)/len(self.test_results)*100:.1f}%"
        
        # Determine overall status
        if len(failed_tests) == 0:
            report["overall_status"] = "🟢 ALL_SYSTEMS_GO"
            report["system_readiness"] = "ready"
        elif len(failed_tests) <= 2:
            report["overall_status"] = "🟡 MINOR_ISSUES"
            report["system_readiness"] = "mostly_ready"
        else:
            report["overall_status"] = "🔴 MAJOR_ISSUES"
            report["system_readiness"] = "not_ready"
        
        # Generate specific recommendations
        for test_name, result in self.test_results.items():
            if result["status"] == "FAIL":
                if "connectivity" in test_name.lower():
                    report["recommendations"].append("Check Keyboard Maestro Engine installation and permissions")
                elif "file system" in test_name.lower():
                    report["recommendations"].append("Grant full disk access permissions")
                elif "security" in test_name.lower():
                    report["recommendations"].append("Review and grant necessary system permissions")
                elif "performance" in test_name.lower():
                    report["recommendations"].append("Investigate performance bottlenecks")
        
        return report

# Usage
async def run_system_diagnostic():
    tester = SystemIntegrationTester()
    report = await tester.run_full_diagnostic()
    
    print(f"\n📋 DIAGNOSTIC REPORT")
    print(f"==================")
    print(f"Overall Status: {report['overall_status']}")
    print(f"System Readiness: {report['system_readiness']}")
    print(f"Tests Passed: {report['test_summary']['passed']}/{report['test_summary']['total_tests']} ({report['test_summary']['pass_rate']})")
    
    if report["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
    
    print(f"\n📊 Detailed Results:")
    for test_name, result in report["detailed_results"].items():
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"  {status_icon} {test_name}: {result['status']}")
        if result["status"] == "FAIL":
            print(f"    Error: {result['error']}")

# Run diagnostic
asyncio.run(run_system_diagnostic())
```

## Conclusion

This troubleshooting guide provides comprehensive diagnostic tools and solutions for the Keyboard Maestro MCP Server. Use these resources systematically to identify and resolve issues efficiently.

**Quick Reference:**
- **Server won't start**: Check dependencies and permissions
- **Macro execution fails**: Verify Keyboard Maestro Engine status
- **Performance issues**: Use monitoring tools and optimization strategies
- **Permission errors**: Grant accessibility and file system permissions
- **Variables not working**: Check scope and persistence settings

**For additional support:**
- Review [EXAMPLES.md](EXAMPLES.md) for usage patterns
- Check [PERFORMANCE.md](PERFORMANCE.md) for optimization strategies
- Consult [SECURITY.md](SECURITY.md) for permission guidance
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development assistance

**Emergency Contacts:**
- GitHub Issues: Report bugs and get community support
- Documentation: Complete guides in project repository
- Logs: Always check logs first for detailed error information
