#!/bin/bash

# THE OVERMIND PROTOCOL - Project Consolidation
# Merge overmind-protocol/ back into main LastBot project

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

🔧 PROJECT CONSOLIDATION
EOF
echo -e "${NC}"

echo "THE OVERMIND PROTOCOL - Project Consolidation"
echo "============================================="
echo ""
echo "Merging overmind-protocol/ back into main LastBot project structure"
echo ""

# Check if we're in the right directory
if [[ ! -f "Cargo.toml" ]] || [[ ! -d "overmind-protocol" ]]; then
    echo "❌ Error: Must be run from LastBot root directory"
    echo "Current directory: $(pwd)"
    echo "Expected: /home/marcin/windsurf/Projects/LastBot"
    exit 1
fi

print_step "1. Backing up current structure"

# Create backup
BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup key files
cp -r overmind-protocol "$BACKUP_DIR/"
cp Cargo.toml "$BACKUP_DIR/Cargo.toml.original"
cp -r src "$BACKUP_DIR/src.original" 2>/dev/null || true

print_success "Backup created: $BACKUP_DIR"

print_step "2. Consolidating configuration files"

# Move .env to root if it doesn't exist
if [[ -f "overmind-protocol/.env" ]] && [[ ! -f ".env" ]]; then
    cp "overmind-protocol/.env" ".env"
    print_success "Moved .env to project root"
elif [[ -f "overmind-protocol/.env" ]] && [[ -f ".env" ]]; then
    print_warning ".env already exists in root, keeping overmind-protocol/.env as .env.overmind"
    cp "overmind-protocol/.env" ".env.overmind"
fi

# Move pixi.toml if better
if [[ -f "overmind-protocol/pixi.toml" ]]; then
    if [[ ! -f "pixi.toml" ]]; then
        cp "overmind-protocol/pixi.toml" "pixi.toml"
        print_success "Moved pixi.toml to project root"
    else
        print_warning "pixi.toml already exists, keeping overmind version as pixi.toml.overmind"
        cp "overmind-protocol/pixi.toml" "pixi.toml.overmind"
    fi
fi

print_step "3. Consolidating Python Brain"

# Create brain directory in root if it doesn't exist
if [[ ! -d "brain" ]] && [[ -d "overmind-protocol/brain" ]]; then
    cp -r "overmind-protocol/brain" "brain"
    print_success "Moved Python Brain to project root"
elif [[ -d "overmind-protocol/brain" ]]; then
    print_warning "brain/ directory already exists, merging content"
    rsync -av "overmind-protocol/brain/" "brain/"
fi

print_step "4. Consolidating infrastructure"

# Merge infrastructure
if [[ -d "overmind-protocol/infrastructure" ]]; then
    if [[ ! -d "infrastructure" ]]; then
        cp -r "overmind-protocol/infrastructure" "infrastructure"
        print_success "Moved infrastructure to project root"
    else
        print_warning "infrastructure/ directory exists, merging content"
        rsync -av "overmind-protocol/infrastructure/" "infrastructure/"
    fi
fi

print_step "5. Consolidating Docker configurations"

# Move Docker files
DOCKER_FILES=(
    "docker-compose.overmind.yml"
    "Dockerfile.overmind"
)

for file in "${DOCKER_FILES[@]}"; do
    if [[ -f "overmind-protocol/$file" ]] && [[ ! -f "$file" ]]; then
        cp "overmind-protocol/$file" "$file"
        print_success "Moved $file to project root"
    elif [[ -f "overmind-protocol/$file" ]]; then
        print_warning "$file already exists in root"
    fi
done

print_step "6. Consolidating documentation"

# Merge docs
if [[ -d "overmind-protocol/docs" ]]; then
    if [[ ! -d "docs/overmind" ]]; then
        mkdir -p "docs/overmind"
        cp -r "overmind-protocol/docs/"* "docs/overmind/"
        print_success "Moved OVERMIND docs to docs/overmind/"
    else
        print_warning "docs/overmind/ exists, merging content"
        rsync -av "overmind-protocol/docs/" "docs/overmind/"
    fi
fi

print_step "7. Consolidating scripts"

# Merge scripts
if [[ -d "overmind-protocol/scripts" ]]; then
    if [[ ! -d "scripts/overmind" ]]; then
        mkdir -p "scripts/overmind"
        cp -r "overmind-protocol/scripts/"* "scripts/overmind/"
        print_success "Moved OVERMIND scripts to scripts/overmind/"
    else
        print_warning "scripts/overmind/ exists, merging content"
        rsync -av "overmind-protocol/scripts/" "scripts/overmind/"
    fi
fi

print_step "8. Updating main Cargo.toml"

# Check if Cargo.toml needs updates
if [[ -f "overmind-protocol/core/Cargo.toml" ]]; then
    print_warning "Found overmind-protocol/core/Cargo.toml"
    echo "You may need to manually merge dependencies from:"
    echo "  overmind-protocol/core/Cargo.toml -> Cargo.toml"
    echo ""
    echo "Key dependencies to check:"
    grep -E "^(tokio|serde|reqwest|redis|solana)" "overmind-protocol/core/Cargo.toml" 2>/dev/null || echo "  (none found)"
fi

print_step "9. Creating consolidated structure summary"

# Create structure summary
cat > CONSOLIDATED_STRUCTURE.md << 'EOF'
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
EOF

print_success "Created CONSOLIDATED_STRUCTURE.md"

print_step "10. Cleaning up duplicate structure"

# Ask user before removing overmind-protocol/
echo ""
echo "🗑️  Ready to remove duplicate overmind-protocol/ directory?"
echo "   (Backup created in $BACKUP_DIR)"
echo ""
read -p "Remove overmind-protocol/ directory? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf overmind-protocol/
    print_success "Removed duplicate overmind-protocol/ directory"
else
    print_warning "Kept overmind-protocol/ directory (you can remove it manually later)"
fi

print_step "11. Final verification"

echo ""
echo "📊 Consolidated Project Structure:"
echo "=================================="
echo ""

# Show new structure
echo "📁 Root files:"
ls -la | grep -E "\.(toml|yml|env|md)$" | head -10

echo ""
echo "📁 Key directories:"
for dir in src brain infrastructure monitoring docs scripts library tests; do
    if [[ -d "$dir" ]]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ (missing)"
    fi
done

echo ""
echo "🎯 Consolidation Summary:"
echo "========================"
echo "✅ Configuration files consolidated"
echo "✅ Python Brain moved to brain/"
echo "✅ Infrastructure configs organized"
echo "✅ Documentation merged"
echo "✅ Scripts organized"
echo "✅ Backup created: $BACKUP_DIR"

if [[ ! -d "overmind-protocol" ]]; then
    echo "✅ Duplicate directory removed"
else
    echo "⚠️  Duplicate directory preserved (remove manually if desired)"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Review and test the consolidated structure"
echo "2. Update any scripts that reference overmind-protocol/"
echo "3. Test compilation: cargo check"
echo "4. Test Python Brain: pixi run brain (if pixi installed)"
echo "5. Run integration tests: ./test-overmind-complete.sh"
echo ""
echo "🧠 THE OVERMIND PROTOCOL structure is now consolidated!"
