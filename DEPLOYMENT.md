# Deployment Guide: Keyboard Maestro MCP Server

## Overview

This guide covers production deployment strategies, configuration management, and operational procedures for the Keyboard Maestro MCP Server.

## Deployment Strategies

### 1. Local Production Deployment

**Best for**: Single-user setups, development teams, small organizations

```bash
# Automated production setup
python scripts/setup/production_setup.py \
    --domain yourdomain.com \
    --email admin@yourdomain.com \
    --setup-monitoring \
    --auto-start

# Deploy to production
python scripts/build/deploy.py \
    --environment production \
    --host 0.0.0.0 \
    --port 8080 \
    --verify-health
```

**Characteristics**:
- Runs directly on macOS host
- Full Keyboard Maestro integration
- Lower resource overhead
- Direct system access

### 2. Containerized Deployment

**Best for**: Cloud deployments, scalable architectures, isolated environments

```bash
# Build and deploy container
python scripts/build/deploy.py \
    --environment production \
    --docker \
    --port 8080 \
    --verify-health
```

**Characteristics**:
- Isolated runtime environment
- Consistent deployment across environments
- Easy scaling and management
- Limited macOS integration (requires host passthrough)

### 3. Cloud Deployment

**Best for**: Remote access, team collaboration, high availability

```bash
# Prepare cloud configuration
export CLOUD_PROVIDER=aws  # or gcp, azure
export INSTANCE_TYPE=m5.large
export REGION=us-west-2

# Deploy to cloud (requires additional cloud-specific scripts)
python scripts/cloud/deploy_aws.py \
    --instance-type $INSTANCE_TYPE \
    --region $REGION \
    --domain myserver.example.com
```

**Note**: Cloud deployment requires macOS instances (AWS EC2 Mac, etc.)

## Pre-Deployment Checklist

### System Requirements
- [ ] macOS 10.14+ (required for Keyboard Maestro)
- [ ] Python 3.10+ installed
- [ ] 4GB+ RAM available
- [ ] 2GB+ disk space available
- [ ] Network access for dependencies

### Security Preparation
- [ ] Generate strong JWT secret key
- [ ] Configure firewall rules
- [ ] Set up SSL certificates (if using HTTPS)
- [ ] Review accessibility permissions
- [ ] Audit security configuration

### Keyboard Maestro Setup
- [ ] Keyboard Maestro installed and licensed
- [ ] Keyboard Maestro Engine running
- [ ] Test macros created and functional
- [ ] Accessibility permissions granted

### Dependencies
- [ ] All Python dependencies installed
- [ ] System dependencies available
- [ ] No conflicting services on target ports
- [ ] Network connectivity verified

## Configuration Management

### Environment-Specific Configurations

#### Development
```bash
# .env.development
KM_MCP_DEV_MODE=true
KM_MCP_HOST=127.0.0.1
KM_MCP_PORT=8000
KM_MCP_AUTH_REQUIRED=false
KM_MCP_LOG_LEVEL=DEBUG
```

#### Staging
```bash
# .env.staging
KM_MCP_DEV_MODE=false
KM_MCP_HOST=0.0.0.0
KM_MCP_PORT=8080
KM_MCP_AUTH_REQUIRED=true
KM_MCP_LOG_LEVEL=INFO
KM_MCP_JWT_SECRET_KEY=staging-secret-key
```

#### Production
```bash
# .env.production
KM_MCP_DEV_MODE=false
KM_MCP_HOST=0.0.0.0
KM_MCP_PORT=8080
KM_MCP_AUTH_REQUIRED=true
KM_MCP_LOG_LEVEL=INFO
KM_MCP_JWT_SECRET_KEY=secure-production-secret
KM_MCP_SENTRY_DSN=https://your-sentry-dsn
```

### Configuration Templates

#### Production YAML Configuration
```yaml
# config/production.yaml
server:
  name: "keyboard-maestro-mcp-server"
  version: "1.0.0"
  
  transport:
    type: "streamable-http"
    host: "0.0.0.0"
    port: 8080
    ssl:
      enabled: true
      cert_file: "/path/to/cert.pem"
      key_file: "/path/to/key.pem"
  
  performance:
    max_concurrent_operations: 100
    operation_timeout: 30
    request_timeout: 60

auth:
  required: true
  provider: "bearer"
  jwt:
    secret_key: "${JWT_SECRET_KEY}"
    algorithm: "HS256"
    expiration: 3600

logging:
  level: "INFO"
  format: "json"
  output:
    console: false
    file:
      enabled: true
      path: "logs/km-mcp-server.log"
      rotation:
        enabled: true
        max_size: "10MB"
        backup_count: 5

monitoring:
  metrics:
    enabled: true
    port: 9090
  health_check:
    enabled: true
    path: "/health"
    interval: 30
```

### Secrets Management

#### Environment Variables
```bash
# Required secrets
export KM_MCP_JWT_SECRET_KEY="$(openssl rand -base64 32)"
export KM_MCP_SENTRY_DSN="https://your-sentry-dsn"
export KM_MCP_DATABASE_URL="postgresql://user:pass@host:5432/db"
```

#### Using External Secret Managers
```bash
# AWS Secrets Manager
export KM_MCP_JWT_SECRET_KEY="$(aws secretsmanager get-secret-value --secret-id prod/km-mcp/jwt-key --query SecretString --output text)"

# HashiCorp Vault
export KM_MCP_JWT_SECRET_KEY="$(vault kv get -field=secret_key secret/km-mcp/production)"

# macOS Keychain
export KM_MCP_JWT_SECRET_KEY="$(security find-generic-password -s km-mcp-jwt -w)"
```

## Deployment Procedures

### Automated Deployment

#### Full Production Setup
```bash
#!/bin/bash
# deploy-production.sh

set -e

echo "🚀 Starting production deployment..."

# 1. Environment preparation
python scripts/setup/production_setup.py \
    --domain ${DOMAIN} \
    --email ${ADMIN_EMAIL} \
    --setup-monitoring \
    --configure-firewall \
    --auto-start

# 2. Pre-deployment validation
python scripts/validation/production_validator.py \
    --comprehensive \
    --output validation-report.json

# 3. Backup current deployment (if exists)
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# 4. Deploy application
python scripts/build/deploy.py \
    --environment production \
    --host ${SERVER_HOST:-0.0.0.0} \
    --port ${SERVER_PORT:-8080} \
    --verify-health \
    --timeout 60

# 5. Post-deployment verification
python scripts/validation/production_validator.py \
    --skip-integration \
    --output post-deploy-validation.json

echo "✅ Deployment completed successfully!"
```

#### Docker Deployment
```bash
#!/bin/bash
# deploy-docker.sh

set -e

echo "🐳 Starting Docker deployment..."

# 1. Build image
docker build \
    -f docker/Dockerfile \
    -t keyboard-maestro-mcp:${VERSION:-latest} \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VERSION=${VERSION:-1.0.0} \
    --build-arg VCS_REF=$(git rev-parse --short HEAD) \
    .

# 2. Stop existing container
docker stop km-mcp-production 2>/dev/null || true
docker rm km-mcp-production 2>/dev/null || true

# 3. Start new container
docker run -d \
    --name km-mcp-production \
    --restart unless-stopped \
    -p ${SERVER_PORT:-8080}:8080 \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/config:/app/config:ro \
    --env-file .env \
    keyboard-maestro-mcp:${VERSION:-latest}

# 4. Health check
sleep 10
docker exec km-mcp-production curl -f http://localhost:8080/health

echo "✅ Docker deployment completed successfully!"
```

### Manual Deployment Steps

#### 1. Environment Preparation
```bash
# Create deployment directory
sudo mkdir -p /opt/keyboard-maestro-mcp
sudo chown $(whoami):$(whoami) /opt/keyboard-maestro-mcp
cd /opt/keyboard-maestro-mcp

# Clone repository
git clone https://github.com/your-org/keyboard-maestro-mcp.git .
git checkout v1.0.0  # Use specific version for production
```

#### 2. Python Environment
```bash
# Create production virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip uv
uv pip install -r requirements.txt
```

#### 3. Configuration
```bash
# Copy and customize configuration
cp config/.env.template .env
nano .env  # Edit configuration

# Set secure permissions
chmod 600 .env
chmod 755 logs/
```

#### 4. Validation
```bash
# Run comprehensive validation
python scripts/validation/production_validator.py --comprehensive

# Fix any issues found
# Re-run validation until all checks pass
```

#### 5. Service Setup
```bash
# Create systemd service (Linux)
sudo cp scripts/systemd/keyboard-maestro-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable keyboard-maestro-mcp

# Or create launchd service (macOS)
sudo cp scripts/launchd/com.example.keyboard-maestro-mcp.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.example.keyboard-maestro-mcp.plist
```

#### 6. Start Service
```bash
# Start service
sudo systemctl start keyboard-maestro-mcp  # Linux
# OR
sudo launchctl start com.example.keyboard-maestro-mcp  # macOS

# Verify service status
sudo systemctl status keyboard-maestro-mcp
```

## Load Balancing and High Availability

### Multiple Instance Deployment

#### Load Balancer Configuration (nginx)
```nginx
# /etc/nginx/sites-available/km-mcp
upstream km_mcp_backend {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://km_mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://km_mcp_backend/health;
        access_log off;
    }
}
```

#### Multi-Instance Startup
```bash
# Start multiple instances
for port in 8080 8081 8082; do
    export KM_MCP_PORT=$port
    python scripts/build/deploy.py \
        --environment production \
        --host 127.0.0.1 \
        --port $port \
        --no-health-check &
done

# Wait for all to start
sleep 10

# Verify all instances
for port in 8080 8081 8082; do
    curl -f http://127.0.0.1:$port/health
done
```

### Health Monitoring

#### Monitoring Script
```bash
#!/bin/bash
# scripts/monitoring/health_monitor.sh

INSTANCES=(8080 8081 8082)
ALERT_EMAIL="admin@yourdomain.com"
LOG_FILE="/var/log/km-mcp-health.log"

for port in "${INSTANCES[@]}"; do
    if ! curl -sf http://127.0.0.1:$port/health > /dev/null; then
        echo "$(date): Instance on port $port is DOWN" >> $LOG_FILE
        
        # Send alert
        echo "KM-MCP instance on port $port is not responding" | \
            mail -s "KM-MCP Health Alert" $ALERT_EMAIL
        
        # Attempt restart
        systemctl restart keyboard-maestro-mcp@$port
    else
        echo "$(date): Instance on port $port is healthy" >> $LOG_FILE
    fi
done
```

#### Prometheus Monitoring
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'km-mcp'
    static_configs:
      - targets: ['localhost:9090', 'localhost:9091', 'localhost:9092']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

## Blue-Green Deployment

### Setup
```bash
# Blue environment (current production)
export KM_MCP_ENV=blue
export KM_MCP_PORT=8080

# Green environment (new version)
export KM_MCP_ENV=green  
export KM_MCP_PORT=8081
```

### Deployment Process
```bash
#!/bin/bash
# blue-green-deploy.sh

set -e

BLUE_PORT=8080
GREEN_PORT=8081
HEALTH_CHECK_URL="http://127.0.0.1"

echo "🔵 Starting blue-green deployment..."

# 1. Deploy to green environment
echo "Deploying to green environment (port $GREEN_PORT)..."
export KM_MCP_PORT=$GREEN_PORT
python scripts/build/deploy.py \
    --environment production \
    --host 127.0.0.1 \
    --port $GREEN_PORT \
    --verify-health

# 2. Smoke tests on green
echo "Running smoke tests on green environment..."
python scripts/tests/smoke_tests.py --port $GREEN_PORT

# 3. Switch load balancer to green
echo "Switching traffic to green environment..."
nginx -s reload  # Assuming nginx config is updated

# 4. Verify green is receiving traffic
sleep 30
curl -f $HEALTH_CHECK_URL:$GREEN_PORT/health

# 5. Stop blue environment
echo "Stopping blue environment..."
# Stop blue service

echo "✅ Blue-green deployment completed!"
```

## Rollback Procedures

### Automatic Rollback
```bash
#!/bin/bash
# rollback.sh

set -e

PREVIOUS_VERSION=${1:-"previous"}
BACKUP_DIR="backup"

echo "🔄 Starting rollback to $PREVIOUS_VERSION..."

# 1. Stop current service
systemctl stop keyboard-maestro-mcp

# 2. Backup current configuration
cp .env $BACKUP_DIR/.env.rollback.$(date +%Y%m%d_%H%M%S)

# 3. Restore previous version
if [ -f "$BACKUP_DIR/.env.$PREVIOUS_VERSION" ]; then
    cp $BACKUP_DIR/.env.$PREVIOUS_VERSION .env
else
    echo "❌ Backup not found: $BACKUP_DIR/.env.$PREVIOUS_VERSION"
    exit 1
fi

# 4. Restore previous code
git checkout $PREVIOUS_VERSION

# 5. Install dependencies (in case they changed)
source .venv/bin/activate
uv pip install -r requirements.txt

# 6. Start service
systemctl start keyboard-maestro-mcp

# 7. Verify rollback
sleep 10
curl -f http://localhost:8080/health

echo "✅ Rollback completed successfully!"
```

### Manual Rollback Steps
1. **Stop current service**
2. **Backup current state**
3. **Restore previous configuration**
4. **Checkout previous code version**
5. **Install dependencies**
6. **Start service**
7. **Verify functionality**
8. **Update monitoring/alerting**

## Security Considerations

### Network Security
```bash
# Firewall configuration
ufw allow 22/tcp      # SSH
ufw allow 8080/tcp    # MCP Server
ufw allow 443/tcp     # HTTPS (if applicable)
ufw enable
```

### Application Security
- **Authentication**: Always enable in production
- **JWT Secrets**: Use strong, unique secrets
- **HTTPS**: Enable for remote access
- **Input Validation**: All inputs validated
- **Rate Limiting**: Prevent abuse
- **Audit Logging**: Track all operations

### Access Control
```bash
# Create dedicated user
sudo useradd -r -s /bin/false km-mcp
sudo chown -R km-mcp:km-mcp /opt/keyboard-maestro-mcp

# Set file permissions
chmod 600 /opt/keyboard-maestro-mcp/.env
chmod 755 /opt/keyboard-maestro-mcp/logs
chmod 644 /opt/keyboard-maestro-mcp/config/*.yaml
```

## Monitoring and Alerting

### Key Metrics to Monitor
- **Service Health**: HTTP health check endpoint
- **Response Times**: API response latencies
- **Error Rates**: Failed requests per minute
- **Resource Usage**: CPU, memory, disk usage
- **Keyboard Maestro**: Engine status and connectivity
- **Authentication**: Failed login attempts

### Alerting Rules
```yaml
# alerts.yml
groups:
  - name: km-mcp
    rules:
      - alert: ServiceDown
        expr: up{job="km-mcp"} == 0
        for: 1m
        annotations:
          summary: "KM-MCP service is down"
          
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 512
        for: 10m
        annotations:
          summary: "High memory usage"
```

## Performance Optimization

### Configuration Tuning
```yaml
# config/production.yaml - Performance section
server:
  performance:
    max_concurrent_operations: 200    # Increase for high-traffic
    operation_timeout: 45             # Longer for complex operations
    request_timeout: 120              # Longer for large requests
    keepalive_timeout: 75             # HTTP keepalive
    max_request_size: 20971520        # 20MB for large payloads
```

### System Optimization
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize Python
export PYTHONOPTIMIZE=2
export PYTHONDONTWRITEBYTECODE=1
export PYTHONIOENCODING=utf-8
```

### Database Optimization (if applicable)
```bash
# Connection pooling
export KM_MCP_DB_POOL_SIZE=20
export KM_MCP_DB_MAX_OVERFLOW=30
export KM_MCP_DB_POOL_TIMEOUT=30
```

## Troubleshooting

### Common Deployment Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :8080
kill -9 <PID>

# Or use different port
export KM_MCP_PORT=8081
```

#### Permission Errors
```bash
# Fix accessibility permissions
sudo tccutil reset Accessibility
# Re-grant permissions in System Preferences

# Fix file permissions
chmod 600 .env
chmod -R 755 logs/
```

#### Service Won't Start
```bash
# Check service logs
journalctl -u keyboard-maestro-mcp -f

# Check application logs
tail -f logs/km-mcp-server.log

# Validate configuration
python scripts/validation/production_validator.py
```

### Health Check Failures
```bash
# Manual health check
curl -v http://localhost:8080/health

# Check server logs for errors
grep ERROR logs/km-mcp-server.log

# Verify Keyboard Maestro connectivity
osascript -e 'tell application "Keyboard Maestro Engine" to version'
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Weekly
- Review application logs
- Check disk usage
- Monitor performance metrics
- Verify backup integrity

#### Monthly
- Update dependencies (after testing)
- Review security audit logs
- Performance optimization review
- Disaster recovery testing

#### Quarterly
- Security vulnerability assessment
- Configuration review
- Capacity planning review
- Documentation updates

### Backup Procedures
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/km-mcp/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration
cp .env $BACKUP_DIR/
cp -r config/ $BACKUP_DIR/

# Backup logs
tar -czf $BACKUP_DIR/logs.tar.gz logs/

# Backup application code
git archive --format=tar.gz --output=$BACKUP_DIR/source.tar.gz HEAD

echo "Backup completed: $BACKUP_DIR"
```

This deployment guide provides comprehensive procedures for successfully deploying and maintaining the Keyboard Maestro MCP Server in production environments.
