#!/bin/bash
# Script to help set up best practices for SNIPERCOR

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up best practices for SNIPERCOR...${NC}"

# Create directories if they don't exist
mkdir -p docs

# Check if Clippy is installed
if ! rustup component list --installed | grep -q clippy; then
    echo -e "${YELLOW}Installing Clippy...${NC}"
    rustup component add clippy
fi

# Check if rustfmt is installed
if ! rustup component list --installed | grep -q rustfmt; then
    echo -e "${YELLOW}Installing rustfmt...${NC}"
    rustup component add rustfmt
fi

# Create a pre-commit hook for Clippy and rustfmt
echo -e "${GREEN}Setting up Git pre-commit hook...${NC}"
mkdir -p .git/hooks

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo "Running Clippy..."
cargo clippy --all-targets --all-features -- -D warnings

if [ $? -ne 0 ]; then
    echo "Clippy found issues. Please fix them before committing."
    exit 1
fi

echo "Running rustfmt..."
cargo fmt -- --check

if [ $? -ne 0 ]; then
    echo "Code formatting issues found. Please run 'cargo fmt' before committing."
    exit 1
fi

echo "Pre-commit checks passed!"
EOF

chmod +x .git/hooks/pre-commit

# Create a basic prometheus.yml file
cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'snipercor'
    static_configs:
      - targets: ['sniper-core:8080']
EOF

echo -e "${GREEN}Created prometheus.yml for monitoring${NC}"

# Create a basic docker-compose.yml if it doesn't exist
if [ ! -f docker-compose.yml ]; then
    echo -e "${YELLOW}Creating basic docker-compose.yml...${NC}"
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  sniper-core:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - SNIPER_TRADING_MODE=paper
      - RUST_LOG=info
    restart: unless-stopped
    
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  grafana_data:
EOF
fi

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run 'cargo clippy --all-targets --all-features' to check code quality"
echo "2. Run 'cargo fmt' to format code"
echo "3. Run 'docker-compose up -d' to start monitoring stack"
echo "4. Access Grafana at http://localhost:3000 (admin/admin)"