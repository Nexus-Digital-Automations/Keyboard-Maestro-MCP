# Installation Guide: Keyboard Maestro MCP Server

## Overview

This guide provides comprehensive instructions for installing and configuring the Keyboard Maestro MCP Server for both development and production environments.

## System Requirements

### Minimum Requirements
- **Operating System**: macOS 10.14 (Mojave) or later
- **Python**: 3.10 or later
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 1GB free disk space
- **Network**: Internet connection for dependency installation

### Required Software
- **Keyboard Maestro**: Version 9.0 or later (for full functionality)
- **Xcode Command Line Tools**: For building native dependencies
- **Git**: For source code management (optional)

### macOS Permissions
- **Accessibility**: Required for system automation
- **Full Disk Access**: Required for file operations (optional)
- **AppleScript**: Required for Keyboard Maestro integration

## Quick Start (Development)

### 1. Clone Repository
```bash
git clone https://github.com/your-org/keyboard-maestro-mcp.git
cd keyboard-maestro-mcp
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install uv (fast package installer)
pip install uv

# Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt  # For development
```

### 3. Configure Environment
```bash
# Copy environment template
cp config/.env.template .env

# Edit .env file with your settings
nano .env
```

### 4. Verify Installation
```bash
# Run production readiness validation
python scripts/validation/production_validator.py

# Start development server
python -m src.main
```

## Production Installation

### Automated Setup

The easiest way to set up a production environment is using the automated setup script:

```bash
# Run production setup with all options
python scripts/setup/production_setup.py \
    --domain yourdomain.com \
    --email admin@yourdomain.com \
    --setup-monitoring \
    --configure-firewall \
    --auto-start
```

### Manual Setup

For more control over the installation process:

#### 1. System Preparation
```bash
# Update system (if needed)
sudo softwareupdate -i -a

# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (optional, for additional tools)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Python Environment Setup
```bash
# Clone repository
git clone https://github.com/your-org/keyboard-maestro-mcp.git
cd keyboard-maestro-mcp

# Create production virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install production dependencies
pip install uv
uv pip install -r requirements.txt
```

#### 3. Configuration
```bash
# Copy and customize environment file
cp config/.env.template .env

# Generate secure JWT secret
python -c "import secrets; print(f'KM_MCP_JWT_SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env

# Edit configuration
nano .env
```

Required environment variables:
```bash
# Server Configuration
KM_MCP_TRANSPORT=streamable-http
KM_MCP_HOST=0.0.0.0
KM_MCP_PORT=8080
KM_MCP_DEV_MODE=false

# Security (REQUIRED)
KM_MCP_AUTH_REQUIRED=true
KM_MCP_JWT_SECRET_KEY=your-generated-secret-key-here

# Logging
KM_MCP_LOG_LEVEL=INFO
KM_MCP_LOG_FILE=logs/km-mcp-server.log
```

#### 4. Directory Setup
```bash
# Create required directories
mkdir -p logs
chmod 755 logs

# Set secure permissions
chmod 600 .env
```

#### 5. Validation
```bash
# Run comprehensive validation
python scripts/validation/production_validator.py --comprehensive

# Test deployment (dry run)
python scripts/build/deploy.py --dry-run
```

## macOS Permissions Setup

### Accessibility Permissions
1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Select **Accessibility** in the left panel
3. Click the lock icon and enter your password
4. Click **+** and add:
   - **Terminal** (if running from Terminal)
   - **Python** (your Python interpreter)
   - **Your IDE** (if running from an IDE)
5. Ensure checkboxes are enabled

### Full Disk Access (Optional)
For file operations requiring elevated access:
1. Navigate to **Full Disk Access** in Privacy settings
2. Add the same applications as above
3. Enable checkboxes

### Testing Permissions
```bash
# Test accessibility permissions
osascript -e 'tell application "System Events" to get name of every application process'

# Should return list of running applications if permissions are correct
```

## Keyboard Maestro Setup

### Installation
1. Download Keyboard Maestro from [keyboardmaestro.com](https://www.keyboardmaestro.com)
2. Install and launch the application
3. Ensure Keyboard Maestro Engine is running:
   ```bash
   # Check if engine is running
   ps aux | grep "Keyboard Maestro Engine"
   ```

### Configuration
1. Open Keyboard Maestro
2. Go to **Keyboard Maestro** > **Preferences** > **General**
3. Ensure **Start Keyboard Maestro Engine at login** is checked
4. Configure any specific settings for your use case

## Deployment Options

### Local Deployment (Recommended for Development)

```bash
# Start server locally
python scripts/build/deploy.py --environment development --host 127.0.0.1 --port 8000

# Or run directly
export MCP_DEV_MODE=true
python -m src.main
```

### HTTP Server Deployment

```bash
# Deploy production HTTP server
python scripts/build/deploy.py --environment production --host 0.0.0.0 --port 8080 --verify-health
```

### Docker Deployment

```bash
# Build and deploy with Docker
python scripts/build/deploy.py --environment production --docker --port 8080
```

### systemd Service (Linux/macOS with systemd)

```bash
# Create systemd service
python scripts/setup/production_setup.py --auto-start

# Manual service management
sudo systemctl start keyboard-maestro-mcp
sudo systemctl enable keyboard-maestro-mcp
sudo systemctl status keyboard-maestro-mcp
```

## Configuration Management

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KM_MCP_TRANSPORT` | Transport protocol (stdio/streamable-http) | stdio | Yes |
| `KM_MCP_HOST` | Server host address | 127.0.0.1 | Yes |
| `KM_MCP_PORT` | Server port number | 8080 | Yes |
| `KM_MCP_DEV_MODE` | Development mode flag | false | No |
| `KM_MCP_AUTH_REQUIRED` | Enable authentication | true | Yes |
| `KM_MCP_JWT_SECRET_KEY` | JWT signing secret | - | Yes* |
| `KM_MCP_LOG_LEVEL` | Logging level | INFO | No |
| `KM_MCP_LOG_FILE` | Log file path | logs/server.log | No |

*Required for production

### Configuration Files

- **`.env`**: Environment variables (create from template)
- **`config/production.yaml`**: Production settings
- **`config/.env.template`**: Environment template

### Security Configuration

```bash
# Generate secure configurations
python -c "import secrets; print(f'JWT_SECRET={secrets.token_urlsafe(32)}')"

# Set file permissions
chmod 600 .env
chmod 644 config/production.yaml
```

## Health Checks and Monitoring

### Health Check Endpoint
```bash
# Check server health
curl http://localhost:8080/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-06-21T12:00:00Z",
  "checks": {
    "keyboard_maestro": "available",
    "permissions": "granted",
    "resources": "sufficient"
  }
}
```

### Monitoring Setup
```bash
# Enable monitoring during setup
python scripts/setup/production_setup.py --setup-monitoring

# Manual health check script
bash scripts/health_check.sh
```

### Log Management
```bash
# View logs
tail -f logs/km-mcp-server.log

# Rotate logs (automatically handled)
# Logs rotate at 10MB with 5 backup files
```

## Troubleshooting

### Common Issues

#### Permission Denied Errors
```bash
# Check accessibility permissions
osascript -e 'tell application "System Events" to get name of every application process'

# Re-grant permissions if needed
sudo tccutil reset Accessibility
```

#### Port Already in Use
```bash
# Find process using port
lsof -i :8080

# Kill process if needed
kill -9 <PID>

# Or use different port
export KM_MCP_PORT=8081
```

#### Keyboard Maestro Not Found
```bash
# Check installation
ls -la "/Applications/Keyboard Maestro.app"

# Check engine status
ps aux | grep "Keyboard Maestro Engine"

# Start engine if needed
open "/Applications/Keyboard Maestro.app"
```

#### Module Import Errors
```bash
# Verify virtual environment
which python
pip list | grep fastmcp

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Debug Mode

Enable debug logging for troubleshooting:
```bash
# Set debug environment
export KM_MCP_LOG_LEVEL=DEBUG
export KM_MCP_DEV_MODE=true

# Run with debug output
python -m src.main
```

### Validation Tools

```bash
# Comprehensive system validation
python scripts/validation/production_validator.py --comprehensive

# Quick configuration check
python scripts/validation/production_validator.py

# Network connectivity test
curl -v http://localhost:8080/health
```

## Performance Tuning

### System Optimization
```bash
# Increase file descriptor limits
ulimit -n 4096

# Optimize Python
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

### Configuration Tuning
```yaml
# config/production.yaml
server:
  performance:
    max_concurrent_operations: 100  # Adjust based on system capacity
    operation_timeout: 30           # Increase for slow operations
    request_timeout: 60             # HTTP request timeout
```

### Monitoring Performance
```bash
# Monitor resource usage
top -pid $(pgrep -f "src.main")

# Check memory usage
ps -o pid,vsz,rss,comm -p $(pgrep -f "src.main")
```

## Security Hardening

### Production Security Checklist
- [ ] Generated strong JWT secret key
- [ ] Enabled authentication (`KM_MCP_AUTH_REQUIRED=true`)
- [ ] Set secure file permissions (`.env` = 600)
- [ ] Configured firewall rules
- [ ] Enabled audit logging
- [ ] Reviewed accessibility permissions
- [ ] Updated all dependencies
- [ ] Configured HTTPS (if applicable)

### Security Validation
```bash
# Run security checks
python scripts/validation/production_validator.py --comprehensive

# Check for vulnerabilities
safety check --json
```

## Backup and Recovery

### Configuration Backup
```bash
# Backup configuration
cp .env config/backup/.env.$(date +%Y%m%d)
cp config/production.yaml config/backup/production.yaml.$(date +%Y%m%d)
```

### Data Backup
```bash
# Backup logs
tar -czf backup/logs-$(date +%Y%m%d).tar.gz logs/

# Backup entire installation
tar -czf backup/km-mcp-$(date +%Y%m%d).tar.gz \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .
```

## Support and Documentation

### Additional Resources
- **API Documentation**: `docs/API_REFERENCE.md`
- **Architecture Guide**: `ARCHITECTURE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Contributing**: `CONTRIBUTING.md`

### Getting Help
1. Check the troubleshooting section above
2. Review logs in `logs/km-mcp-server.log`
3. Run validation: `python scripts/validation/production_validator.py`
4. Check GitHub Issues for known problems
5. Create a new issue with:
   - System information (`uname -a`)
   - Python version (`python --version`)
   - Error messages and logs
   - Steps to reproduce

## Next Steps

After successful installation:

1. **Test Basic Functionality**:
   ```bash
   # Test server response
   curl http://localhost:8080/health
   ```

2. **Create First Macro** (if using Keyboard Maestro):
   - Open Keyboard Maestro
   - Create a simple test macro
   - Test execution via MCP server

3. **Configure Client Integration**:
   - Set up Claude Desktop or other MCP client
   - Configure server connection
   - Test tool execution

4. **Production Deployment**:
   - Review security settings
   - Set up monitoring
   - Configure backup procedures
   - Document operational procedures

Congratulations! Your Keyboard Maestro MCP Server is now installed and ready for use.
