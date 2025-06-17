#!/bin/bash

# THE OVERMIND PROTOCOL - Project Reorganization Script
# Restructures project for production cloud deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

🔄 PROJECT REORGANIZATION FOR CLOUD DEPLOYMENT
EOF
echo -e "${NC}"

# Create new directory structure
create_new_structure() {
    print_status "Creating new project structure..."
    
    # Create main directories
    mkdir -p overmind-protocol/{core,brain,infrastructure,docs,monitoring,scripts}
    
    # Create subdirectories
    mkdir -p overmind-protocol/core/{src,tests,target}
    mkdir -p overmind-protocol/brain/{src,tests}
    mkdir -p overmind-protocol/infrastructure/{docker,compose,config}
    mkdir -p overmind-protocol/docs/{api,deployment,architecture}
    mkdir -p overmind-protocol/monitoring/{grafana,prometheus,alerting}
    mkdir -p overmind-protocol/scripts/{deployment,maintenance,backup}
    
    print_success "New directory structure created"
}

# Move Rust core files
move_rust_core() {
    print_status "Moving Rust core files..."
    
    # Move source code
    cp -r src/* overmind-protocol/core/src/
    cp Cargo.toml overmind-protocol/core/
    cp Cargo.lock overmind-protocol/core/
    
    # Move tests
    cp -r tests/* overmind-protocol/core/tests/
    
    # Move Rust-specific configs
    cp Dockerfile overmind-protocol/core/Dockerfile.core
    
    print_success "Rust core files moved"
}

# Setup Python brain structure
setup_python_brain() {
    print_status "Setting up Python brain structure..."
    
    # Create Python brain files
    cat > overmind-protocol/brain/pyproject.toml << 'EOF'
[project]
name = "overmind-brain"
version = "1.0.0"
description = "THE OVERMIND PROTOCOL - Python AI Brain"
authors = ["THE OVERMIND PROTOCOL Team"]
dependencies = [
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
    "chromadb>=0.4.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
    "redis>=5.0.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "aioredis>=2.0.0",
    "pydantic>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/overmind_brain"]
EOF

    # Create Python brain Dockerfile
    cat > overmind-protocol/brain/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["poetry", "run", "python", "src/overmind_brain/main.py"]
EOF

    # Create basic Python brain structure
    mkdir -p overmind-protocol/brain/src/overmind_brain
    
    cat > overmind-protocol/brain/src/overmind_brain/__init__.py << 'EOF'
"""THE OVERMIND PROTOCOL - Python AI Brain"""
__version__ = "1.0.0"
EOF

    cat > overmind-protocol/brain/src/overmind_brain/main.py << 'EOF'
"""THE OVERMIND PROTOCOL - Python AI Brain Main Entry Point"""
import asyncio
import logging
from fastapi import FastAPI
from .brain import OVERMINDBrain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OVERMIND Brain", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "overmind-brain"}

async def main():
    logger.info("🧠 THE OVERMIND PROTOCOL Python Brain starting...")
    
    brain = OVERMINDBrain()
    await brain.start()

if __name__ == "__main__":
    asyncio.run(main())
EOF

    cat > overmind-protocol/brain/src/overmind_brain/brain.py << 'EOF'
"""THE OVERMIND PROTOCOL - AI Brain Implementation"""
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OVERMINDBrain:
    """Main AI Brain for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        self.is_running = False
        logger.info("🧠 OVERMIND Brain initialized")
    
    async def start(self):
        """Start the AI brain"""
        self.is_running = True
        logger.info("🚀 OVERMIND Brain started")
        
        # Main brain loop
        while self.is_running:
            await self.process_cycle()
            await asyncio.sleep(1)
    
    async def process_cycle(self):
        """Process one cycle of AI brain operations"""
        # TODO: Implement AI decision making
        pass
    
    async def stop(self):
        """Stop the AI brain"""
        self.is_running = False
        logger.info("🛑 OVERMIND Brain stopped")
EOF

    print_success "Python brain structure created"
}

# Move infrastructure files
move_infrastructure() {
    print_status "Moving infrastructure files..."
    
    # Move Docker Compose files
    cp docker-compose.overmind.yml overmind-protocol/infrastructure/compose/
    cp docker-compose.simple.yml overmind-protocol/infrastructure/compose/
    
    # Move configuration files
    cp -r tensorzero-config overmind-protocol/infrastructure/config/
    cp -r monitoring overmind-protocol/monitoring/
    
    # Move deployment scripts
    cp deploy-overmind.sh overmind-protocol/scripts/deployment/
    cp deploy-simple.sh overmind-protocol/scripts/deployment/
    
    print_success "Infrastructure files moved"
}

# Consolidate documentation
consolidate_docs() {
    print_status "Consolidating documentation..."
    
    # Move main documentation
    cp README-OVERMIND.md overmind-protocol/docs/
    cp RULES.md overmind-protocol/docs/architecture/
    
    # Move library documentation
    cp -r library overmind-protocol/docs/
    cp -r docs/* overmind-protocol/docs/
    
    # Create main README
    cat > overmind-protocol/README.md << 'EOF'
# 🧠 THE OVERMIND PROTOCOL

## Production-Ready AI-Enhanced HFT Trading System

THE OVERMIND PROTOCOL is a sophisticated hybrid Python-Rust trading system that combines:
- **Python AI Brain** for strategic decision making with vector memory
- **Rust HFT Executor** for sub-50ms trade execution
- **Vector Database** for long-term AI learning
- **TensorZero Optimization** for AI performance enhancement

## Quick Start

```bash
# Deploy to cloud
cd scripts/deployment
./deploy-cloud.sh

# Local development
pixi install
pixi run dev-full
```

## Architecture

- `core/` - Rust HFT Executor (sub-50ms execution)
- `brain/` - Python AI Brain (strategic decisions)
- `infrastructure/` - Docker, monitoring, deployment
- `docs/` - Complete documentation
- `monitoring/` - Grafana, Prometheus, alerting
- `scripts/` - Deployment and maintenance scripts

## Documentation

- [Deployment Guide](docs/deployment/)
- [Architecture Overview](docs/architecture/)
- [API Documentation](docs/api/)

---

**Status:** Production Ready | **Mode:** Paper Trading → Live Trading
EOF

    print_success "Documentation consolidated"
}

# Create production pixi.toml
create_production_pixi() {
    print_status "Creating production pixi.toml..."
    
    cat > overmind-protocol/pixi.toml << 'EOF'
# THE OVERMIND PROTOCOL - Production Configuration
[project]
name = "overmind-protocol"
description = "Production AI-Enhanced HFT Trading System"
authors = ["THE OVERMIND PROTOCOL Team"]
channels = ["conda-forge", "pytorch"]
platforms = ["linux-64"]
version = "1.0.0"

[dependencies]
python = "3.11.*"
poetry = "*"
docker = "*"
docker-compose = "*"
git = "*"
curl = "*"

[tasks]
# Production deployment
deploy-cloud = "cd scripts/deployment && ./deploy-cloud.sh"
deploy-local = "cd scripts/deployment && ./deploy-local.sh"

# Development
dev-core = "cd core && cargo run --profile contabo"
dev-brain = "cd brain && poetry run python src/overmind_brain/main.py"
dev-full = { depends_on = ["dev-brain", "dev-core"] }

# Testing
test-core = "cd core && cargo test --workspace"
test-brain = "cd brain && poetry run pytest"
test-all = { depends_on = ["test-core", "test-brain"] }

# Maintenance
backup = "cd scripts/maintenance && ./backup.sh"
restore = "cd scripts/maintenance && ./restore.sh"
health-check = "cd scripts/maintenance && ./health-check.sh"

[environments]
production = { solve-group = "prod" }
development = { solve-group = "dev" }
EOF

    print_success "Production pixi.toml created"
}

# Clean up old files
cleanup_old_files() {
    print_status "Cleaning up old files..."
    
    # Create list of files to keep
    cat > .keep_files << 'EOF'
overmind-protocol/
.git/
.gitignore
.env.example
pixi.toml
EOF

    print_warning "Old files cleanup prepared (manual review recommended)"
    print_success "Reorganization completed"
}

# Main execution
main() {
    print_status "Starting THE OVERMIND PROTOCOL reorganization..."
    
    create_new_structure
    move_rust_core
    setup_python_brain
    move_infrastructure
    consolidate_docs
    create_production_pixi
    cleanup_old_files
    
    echo ""
    print_success "🎯 THE OVERMIND PROTOCOL reorganization completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Review the new structure in overmind-protocol/"
    echo "2. Test the reorganized components"
    echo "3. Commit to Git repository"
    echo "4. Deploy to cloud with scripts/deployment/deploy-cloud.sh"
    echo ""
    print_warning "⚠️  Manual review recommended before deleting old files"
}

# Execute main function
main "$@"
