# THE OVERMIND PROTOCOL - Consolidated Project Structure

## 📁 Project Layout

```
LastBot/                           # Main project root
├── src/                          # Rust HFT Executor
│   ├── main.rs                   # Main entry point
│   └── modules/                  # Trading modules
├── brain/                        # Python AI Brain
│   ├── src/                      # AI analysis code
│   └── Dockerfile               # Brain container
├── infrastructure/               # Deployment configs
│   ├── compose/                  # Docker Compose files
│   └── kubernetes/              # K8s configs (if any)
├── monitoring/                   # Monitoring setup
│   ├── grafana/                 # Dashboards
│   └── prometheus/              # Metrics
├── docs/                        # Documentation
│   ├── overmind/               # OVERMIND-specific docs
│   └── *.md                    # General docs
├── scripts/                     # Utility scripts
│   └── overmind/               # OVERMIND-specific scripts
├── library/                     # Knowledge base
├── tests/                       # Test suites
├── .env                         # Environment config
├── Cargo.toml                   # Rust dependencies
├── pixi.toml                    # Python environment
└── docker-compose.overmind.yml # Main compose file
```

## 🎯 Key Changes

1. **Eliminated Duplication**: Merged overmind-protocol/ into main structure
2. **Centralized Configuration**: Single .env and Cargo.toml
3. **Organized Components**: Clear separation of Rust/Python/Infrastructure
4. **Simplified Deployment**: Single docker-compose file
5. **Unified Documentation**: All docs in docs/ directory

## 🚀 Usage

```bash
# Development
cargo run                        # Run Rust HFT Executor
pixi run brain                   # Run Python AI Brain

# Testing
cargo test                       # Rust tests
./test-overmind-complete.sh     # Complete test suite

# Deployment
docker-compose -f docker-compose.overmind.yml up -d
```

## 📋 Migration Notes

- Original structure backed up in backup-YYYYMMDD-HHMMSS/
- Configuration files merged where possible
- Duplicate files preserved with .overmind suffix
- Manual review needed for Cargo.toml dependencies
