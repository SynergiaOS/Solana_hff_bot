# 🚀 THE OVERMIND PROTOCOL - Production Deployment Guide

## 📋 Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Pre-deployment Checklist](#pre-deployment-checklist)
3. [Mission Control Deployment](#mission-control-deployment)
4. [Integration Validation](#integration-validation)
5. [Production Monitoring](#production-monitoring)
6. [Rollback Procedures](#rollback-procedures)
7. [Maintenance & Updates](#maintenance--updates)

---

## 🎯 Deployment Overview

THE OVERMIND PROTOCOL Mission Control deployment includes:

- **Streamlit Dashboard**: Web interface for goal management and monitoring
- **API Integration**: Real-time connection to AI Brain components
- **Docker Containerization**: Scalable and isolated deployment
- **Nginx Reverse Proxy**: Load balancing and SSL termination
- **Comprehensive Monitoring**: Health checks and performance validation

### 🏗️ Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                Production Deployment Stack                  │
├─────────────────────────────────────────────────────────────┤
│ Nginx Reverse Proxy (Port 8090)                            │
│ ├── /mission-control/ → Mission Control Dashboard          │
│ ├── /api/ → AI Brain API Endpoints                         │
│ ├── /grafana/ → Monitoring Dashboard                       │
│ └── /health → System Health Check                          │
├─────────────────────────────────────────────────────────────┤
│ Mission Control Container (Port 8501)                      │
│ ├── Streamlit Application                                  │
│ ├── Goal Management Interface                              │
│ ├── Portfolio Tracking Dashboard                           │
│ ├── Trading Activity Monitor                               │
│ └── System Health Overview                                 │
├─────────────────────────────────────────────────────────────┤
│ AI Brain Integration                                        │
│ ├── DragonflyDB (Port 6379)                               │
│ ├── TensorZero Gateway (Port 3003)                        │
│ ├── Goal Manager API                                       │
│ ├── Portfolio Monitor                                      │
│ └── Strategy Mapper                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Pre-deployment Checklist

### 🔧 System Requirements

- **Operating System**: Ubuntu 20.04+ or compatible Linux distribution
- **Docker**: Version 20.10+ with Docker Compose
- **Python**: Version 3.11+ with pip
- **Nginx**: Version 1.18+ for reverse proxy
- **Memory**: Minimum 4GB RAM, recommended 8GB+
- **Storage**: Minimum 20GB free space
- **Network**: Stable internet connection with open ports 8501, 8080, 8090

### 📦 Dependencies Verification

```bash
# Check Docker installation
docker --version
docker-compose --version

# Check Python installation
python3 --version
pip3 --version

# Check Nginx installation
nginx -v

# Check available ports
sudo netstat -tlnp | grep -E ':(8501|8080|8090|6379|3003)'
```

### 🔐 Security Configuration

```bash
# Ensure firewall is configured
sudo ufw status

# Allow required ports
sudo ufw allow 8090/tcp  # Nginx proxy
sudo ufw allow 22/tcp    # SSH access

# Verify SSL certificates (if using HTTPS)
sudo certbot certificates
```

### 📁 File Structure Verification

```bash
# Verify required files exist
ls -la mission_control/
ls -la infrastructure/compose/
ls -la scripts/
ls -la docs/

# Check configuration files
cat infrastructure/compose/docker-compose.overmind.yml | grep mission-control
cat infrastructure/nginx/overmind.conf | grep mission-control
```

---

## 🚀 Mission Control Deployment

### 🔄 Automated Deployment

Use the provided deployment script for automated deployment:

```bash
# Make script executable
chmod +x scripts/deploy_mission_control.sh

# Run full deployment
./scripts/deploy_mission_control.sh deploy

# Available commands:
# deploy   - Full deployment (default)
# rollback - Rollback to previous version
# validate - Validate current deployment
# test     - Run integration tests only
```

### 📋 Manual Deployment Steps

#### Step 1: Prepare Environment

```bash
# Navigate to project directory
cd /path/to/Solana_hff_bot

# Create backup directory
mkdir -p backups/mission_control

# Set environment variables
export PRODUCTION_SERVER="marcin@89.117.53.53"
export PRODUCTION_PATH="/home/marcin/Solana_hff_bot"
```

#### Step 2: Deploy Files

```bash
# Copy Mission Control files
scp -r mission_control/ $PRODUCTION_SERVER:$PRODUCTION_PATH/

# Copy Docker Compose configuration
scp infrastructure/compose/docker-compose.overmind.yml \
    $PRODUCTION_SERVER:$PRODUCTION_PATH/infrastructure/compose/

# Copy Nginx configuration
scp infrastructure/nginx/overmind.conf \
    $PRODUCTION_SERVER:/tmp/overmind.conf
```

#### Step 3: Configure Nginx

```bash
# SSH to production server
ssh $PRODUCTION_SERVER

# Update Nginx configuration
sudo cp /tmp/overmind.conf /etc/nginx/sites-available/overmind
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 4: Install Dependencies

```bash
# On production server
cd $PRODUCTION_PATH/mission_control

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Deploy Container

```bash
# Build and start Mission Control container
cd $PRODUCTION_PATH
docker-compose -f infrastructure/compose/docker-compose.overmind.yml build mission-control
docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d mission-control
```

### 🔍 Deployment Verification

```bash
# Check container status
docker-compose -f infrastructure/compose/docker-compose.overmind.yml ps mission-control

# Check container logs
docker logs overmind-mission-control

# Test health endpoint
curl -f http://localhost:8501/health

# Test nginx proxy
curl -f http://localhost:8090/mission-control/
```

---

## 🧪 Integration Validation

### 🔄 Automated Validation

Use the integration validation script:

```bash
# Make script executable
chmod +x scripts/validate_integration.py

# Run validation tests
python3 scripts/validate_integration.py \
    --mission-control-url http://localhost:8501 \
    --api-url http://localhost:8080 \
    --output /tmp/integration_results.json

# Check results
cat /tmp/integration_results.json | jq '.status'
```

### 📋 Manual Validation Steps

#### Test 1: Mission Control Access

```bash
# Test direct access
curl -I http://localhost:8501/

# Test proxy access
curl -I http://localhost:8090/mission-control/

# Test health endpoint
curl http://localhost:8501/health
```

#### Test 2: API Integration

```bash
# Test goal management API
curl http://localhost:8080/api/v1/control/health

# Test portfolio monitoring
curl http://localhost:8080/api/v1/portfolio/state

# Test strategy mapping
curl http://localhost:8080/api/v1/strategy/active-profile
```

#### Test 3: Performance Validation

```bash
# Test response times (should be <50ms)
for i in {1..10}; do
    curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8080/api/v1/control/health
done
```

#### Test 4: Goal Management Workflow

```bash
# Set a test goal
curl -X POST http://localhost:8080/api/v1/control/set-goal \
    -H "Content-Type: application/json" \
    -d '{
        "goal_type": "REACH_BALANCE",
        "target_sol": 2.0,
        "reason": "Deployment validation test",
        "changed_by": "deployment_validator"
    }'

# Retrieve current goal
curl http://localhost:8080/api/v1/control/current-goal

# Check goal history
curl http://localhost:8080/api/v1/control/goal-history?limit=5
```

### 📊 Validation Criteria

**Mission Control Dashboard:**
- ✅ Web interface accessible via browser
- ✅ All dashboard sections loading correctly
- ✅ Real-time data updates functioning
- ✅ Goal management interface operational

**API Integration:**
- ✅ All API endpoints responding
- ✅ Goal setting and retrieval working
- ✅ Portfolio data available
- ✅ Strategy mapping functional

**Performance Requirements:**
- ✅ Response times <50ms for API calls
- ✅ Dashboard loading <5 seconds
- ✅ Real-time updates <5 second latency
- ✅ Zero-downtime goal transitions

**Error Handling:**
- ✅ Invalid requests properly rejected
- ✅ Graceful degradation on API failures
- ✅ Comprehensive error messages
- ✅ Automatic retry mechanisms

---

## 📊 Production Monitoring

### 🔍 Health Monitoring

**System Health Checks:**
```bash
# Container health
docker-compose -f infrastructure/compose/docker-compose.overmind.yml ps

# Service health
curl http://localhost:8501/health
curl http://localhost:8080/api/v1/control/health

# Resource utilization
docker stats overmind-mission-control
```

**Log Monitoring:**
```bash
# Mission Control logs
docker logs overmind-mission-control --tail 100 -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log | grep mission-control

# System logs
journalctl -u docker -f
```

### 📈 Performance Monitoring

**Key Metrics to Monitor:**
- Response time for API calls (<50ms target)
- Dashboard loading time (<5s target)
- Memory usage (<2GB per container)
- CPU utilization (<80% sustained)
- Network I/O and connection counts

**Monitoring Commands:**
```bash
# Performance metrics
curl http://localhost:8080/metrics | grep mission_control

# Resource usage
docker exec overmind-mission-control top -bn1

# Network connections
netstat -an | grep :8501
```

### 🚨 Alert Configuration

**Critical Alerts:**
- Mission Control container down
- API response time >100ms
- Memory usage >90%
- Disk space <10% free

**Warning Alerts:**
- API response time >50ms
- Memory usage >80%
- High error rate (>5%)
- Goal change failures

---

## 🔄 Rollback Procedures

### 🚨 Emergency Rollback

```bash
# Quick rollback using deployment script
./scripts/deploy_mission_control.sh rollback

# Manual rollback steps
docker-compose -f infrastructure/compose/docker-compose.overmind.yml stop mission-control
docker-compose -f infrastructure/compose/docker-compose.overmind.yml rm mission-control

# Restore from backup
LATEST_BACKUP=$(ls -t backups/mission_control/ | head -1)
cp -r backups/mission_control/$LATEST_BACKUP/mission_control ./

# Restart with previous version
docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d mission-control
```

### 📋 Rollback Validation

```bash
# Verify rollback success
curl http://localhost:8501/health
curl http://localhost:8080/api/v1/control/health

# Check functionality
python3 scripts/validate_integration.py --mission-control-url http://localhost:8501
```

---

## 🔧 Maintenance & Updates

### 📅 Regular Maintenance

**Daily Tasks:**
- Check system health indicators
- Review error logs
- Monitor resource utilization
- Verify backup integrity

**Weekly Tasks:**
- Update dependencies
- Review performance metrics
- Clean up old logs
- Test rollback procedures

**Monthly Tasks:**
- Security updates
- Performance optimization
- Capacity planning review
- Documentation updates

### 🔄 Update Procedures

```bash
# Update Mission Control
git pull origin main
./scripts/deploy_mission_control.sh deploy

# Update dependencies
pip install --upgrade -r mission_control/requirements.txt

# Update Docker images
docker-compose -f infrastructure/compose/docker-compose.overmind.yml pull
docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d
```

---

## 📞 Support & Troubleshooting

### 🔧 Common Issues

**Issue: Mission Control not accessible**
- Check container status: `docker ps | grep mission-control`
- Check port binding: `netstat -tlnp | grep 8501`
- Review logs: `docker logs overmind-mission-control`

**Issue: API integration failures**
- Verify AI Brain services running
- Check DragonflyDB connectivity
- Review API endpoint configuration

**Issue: Performance degradation**
- Monitor resource usage
- Check for memory leaks
- Review database performance
- Optimize query patterns

### 📚 Additional Resources

- **[Mission Control User Guide](./MISSION_CONTROL_USER_GUIDE.md)**: Complete user manual
- **[Adaptive Cortex Guide](./ADAPTIVE_CORTEX_GUIDE.md)**: Technical documentation
- **[API Documentation](./ADAPTIVE_CORTEX_GUIDE.md#api-endpoints-documentation)**: API reference
- **[Troubleshooting Guide](./MISSION_CONTROL_USER_GUIDE.md#troubleshooting)**: Common solutions

For critical issues or emergency support, contact the development team immediately.
