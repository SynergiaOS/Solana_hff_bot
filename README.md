# 🚀 THE OVERMIND PROTOCOL - Clean Architecture

## 📁 Project Structure

```
├── brain/                     # 🧠 AI Brain (Python) - Layer 3: Intelligence
│   ├── src/                   # Core AI components
│   ├── Dockerfile             # Container definition
│   └── pyproject.toml         # Python dependencies (uv managed)
├── src/                       # ⚡ Rust HFT Executor - Layer 4: Execution
│   ├── modules/               # Trading modules
│   ├── config/                # Rust configuration
│   └── main.rs                # Main entry point
├── mission_control/           # 🎛️ Mission Control Dashboard
│   ├── app.py                 # Streamlit dashboard (FIXED AttributeError)
│   ├── Dockerfile             # Container definition
│   └── pyproject.toml         # Dependencies (uv managed)
├── deployment/                # 🚀 Deployment & Infrastructure
│   ├── docker-compose/        # Production compose files
│   └── scripts/               # Deployment automation
├── docs/                      # 📚 Documentation
│   ├── LOCAL_DEVELOPMENT_GUIDE.md  # Local dev workflow
│   └── architecture/          # System architecture docs
├── scripts/                   # 🛠️ Utility Scripts
│   ├── start-local-dev.sh     # Local development startup
│   └── deployment/            # Production deployment scripts
├── monitoring/                # 📊 Observability
│   ├── prometheus.yml         # Metrics collection
│   └── grafana/               # Dashboards
├── wallets/                   # 🔐 Wallet Management
├── logs/                      # 📋 System Logs
├── tests/                     # 🧪 Test Suite
├── docker-compose.local.yml   # 🏗️ Local Development Environment
├── .env.local                 # 🔧 Local Environment Template
└── pixi.toml                  # 📦 Unified Dependency Management
```

## 🚀 Quick Start

### 🏗️ Local Development (NEW!)

```bash
# Professional local development environment
./scripts/start-local-dev.sh

# Access Mission Control Dashboard
open http://localhost:8501
```

### 🚀 Production Deployment

```bash
# Deploy to production server
docker-compose -f deployment/docker-compose/docker-compose.overmind.yml up --build -d
```

### 🧪 Testing

```bash
# Run complete test suite
pixi run test-agent  # Python tests
cargo test           # Rust tests
```

## 📊 Test Results

All FRONT tests completed successfully:
- ✅ FRONT 1: AI Brain Intelligence (GENIUS level)
- ✅ FRONT 2: Communication Excellence (EXCELLENT)
- ✅ FRONT 3: Performance & Scalability (ULTRA-HIGH)

System ready for production deployment.
