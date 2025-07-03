# 🏗️ THE OVERMIND PROTOCOL - Local Development Guide

## 🎯 Overview

This guide implements the **"Local Playground, Global Battlefield"** development workflow for THE OVERMIND PROTOCOL. All development and testing happens locally first, then gets deployed to production only after complete validation.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM available for containers
- OpenAI API key (required for AI functionality)

### 1-Minute Setup

```bash
# Clone and navigate to project
cd /path/to/LastBot

# Start local development environment
./scripts/start-local-dev.sh

# Access Mission Control Dashboard
open http://localhost:8501
```

## 📋 Complete Setup Guide

### Step 1: Environment Configuration

```bash
# Copy environment template
cp .env.local .env

# Edit API keys (REQUIRED)
nano .env  # or your preferred editor
```

**Required Configuration:**
```bash
# Minimum required for AI functionality
OPENAI_API_KEY=your_actual_openai_api_key_here

# Optional but recommended
DEEPSEEK_API_KEY=your_deepseek_api_key_here
HELIUS_API_KEY=your_helius_api_key_here
```

### Step 2: Start Local Environment

```bash
# Automated startup (recommended)
./scripts/start-local-dev.sh

# Manual startup (advanced)
docker-compose -f docker-compose.local.yml up --build -d
```

### Step 3: Verify Services

```bash
# Check all services are running
docker-compose -f docker-compose.local.yml ps

# View logs
docker-compose -f docker-compose.local.yml logs -f
```

## 🌐 Service Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Mission Control Dashboard** | http://localhost:8501 | Main UI for goal management |
| **AI Brain API** | http://localhost:8001 | Python AI components |
| **HFT Executor API** | http://localhost:8080 | Rust trading engine |
| **Vector Database** | http://localhost:8000 | Chroma AI memory |
| **Redis Commander** | http://localhost:8081 | DragonflyDB GUI |
| **pgAdmin** | http://localhost:8082 | PostgreSQL GUI |

## 🔧 Development Workflow

### Hot Reload Development

The local environment supports hot-reload for all components:

```bash
# Python changes (AI Brain, Mission Control)
# Files automatically reload when saved

# Rust changes (HFT Executor)
# Rebuild container: docker-compose -f docker-compose.local.yml up --build overmind-executor-local

# Configuration changes
# Restart affected services: docker-compose -f docker-compose.local.yml restart [service]
```

### Testing Changes

```bash
# 1. Make code changes locally
# 2. Test in local environment
# 3. Run test suite
pixi run test-agent  # Python tests
cargo test           # Rust tests

# 4. Validate Mission Control dashboard
open http://localhost:8501

# 5. Check logs for errors
docker-compose -f docker-compose.local.yml logs -f
```

### Debugging

```bash
# View specific service logs
docker-compose -f docker-compose.local.yml logs -f mission-control-local
docker-compose -f docker-compose.local.yml logs -f overmind-brain-local
docker-compose -f docker-compose.local.yml logs -f overmind-executor-local

# Access container shell
docker exec -it overmind-mission-control-local bash
docker exec -it overmind-brain-local bash

# Check service health
curl http://localhost:8501/_stcore/health  # Mission Control
curl http://localhost:8001/health          # AI Brain
curl http://localhost:8080/health          # HFT Executor
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Mission Control AttributeError
**Problem:** `AttributeError: 'dict' object has no attribute 'target_sol'`
**Solution:** ✅ **FIXED** - Goal data class implemented

#### 2. Services Won't Start
```bash
# Check Docker is running
docker info

# Check ports aren't in use
netstat -tulpn | grep :8501
netstat -tulpn | grep :8080

# Clean up and restart
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up --build
```

#### 3. AI Brain Not Responding
```bash
# Check API key is set
grep OPENAI_API_KEY .env

# Check AI Brain logs
docker-compose -f docker-compose.local.yml logs overmind-brain-local

# Restart AI Brain
docker-compose -f docker-compose.local.yml restart overmind-brain-local
```

#### 4. Database Connection Issues
```bash
# Check PostgreSQL is healthy
docker-compose -f docker-compose.local.yml ps postgres-local

# Access database directly
docker exec -it overmind-postgres-local psql -U overmind -d overmind_local

# Reset database
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up postgres-local
```

### Performance Optimization

```bash
# Allocate more memory to Docker
# Docker Desktop -> Settings -> Resources -> Memory: 8GB+

# Clean up unused containers/images
docker system prune -a

# Monitor resource usage
docker stats
```

## 🔄 Local-to-Production Deployment

### Stage 1: Local Validation ✅

```bash
# 1. All tests pass locally
pixi run test-agent && cargo test

# 2. Mission Control dashboard works
curl -f http://localhost:8501/_stcore/health

# 3. End-to-end functionality verified
# - Goal setting works
# - AI Brain responds
# - HFT Executor connects
# - All services communicate

# 4. No errors in logs
docker-compose -f docker-compose.local.yml logs | grep -i error
```

### Stage 2: Production Deployment

```bash
# 1. Commit changes
git add .
git commit -m "feat: implement local development fixes"
git push origin main

# 2. SSH to production server
ssh marcin@89.117.53.53

# 3. Pull latest changes
cd /path/to/project
git pull origin main

# 4. Deploy to production
docker-compose -f docker-compose.overmind.yml up --build -d

# 5. Verify production deployment
curl -f http://89.117.53.53:8501/_stcore/health
```

## 📊 Monitoring and Metrics

### Local Development Metrics

```bash
# Service health checks
curl http://localhost:8501/_stcore/health  # Mission Control
curl http://localhost:8001/health          # AI Brain  
curl http://localhost:8080/health          # HFT Executor
curl http://localhost:8000/api/v1/heartbeat # Vector DB

# Database connections
docker exec overmind-postgres-local pg_isready -U overmind
redis-cli -h localhost -p 6379 ping

# Resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Development Tools

- **Redis Commander**: http://localhost:8081 - Inspect DragonflyDB data
- **pgAdmin**: http://localhost:8082 - Manage PostgreSQL database
- **Docker Desktop**: Monitor container resources and logs

## 🎯 Best Practices

### Code Changes
1. ✅ Always test locally first
2. ✅ Use hot-reload for rapid iteration
3. ✅ Check logs after changes
4. ✅ Validate Mission Control dashboard
5. ✅ Run test suite before committing

### Environment Management
1. ✅ Keep .env.local as template
2. ✅ Never commit real API keys
3. ✅ Use paper trading mode locally
4. ✅ Use devnet Solana endpoints
5. ✅ Clean up containers regularly

### Deployment Safety
1. ✅ Complete local validation required
2. ✅ No production debugging
3. ✅ Version control all changes
4. ✅ Test production deployment process
5. ✅ Monitor production after deployment

## 🆘 Emergency Procedures

### Stop All Services
```bash
docker-compose -f docker-compose.local.yml down
```

### Reset Everything
```bash
docker-compose -f docker-compose.local.yml down -v
docker system prune -a
./scripts/start-local-dev.sh
```

### Backup Local Data
```bash
# Backup volumes
docker run --rm -v overmind_postgres-local-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .
docker run --rm -v overmind_chroma-local-data:/data -v $(pwd):/backup alpine tar czf /backup/chroma-backup.tar.gz -C /data .
```

---

## ✅ Success Criteria

Your local development environment is working correctly when:

- [ ] Mission Control dashboard loads at http://localhost:8501
- [ ] No AttributeError when accessing goals
- [ ] AI Brain responds to requests
- [ ] HFT Executor starts without errors
- [ ] All services show "healthy" status
- [ ] Hot-reload works for code changes
- [ ] Test suite passes completely

**🎉 Ready for production deployment when all criteria are met!**
