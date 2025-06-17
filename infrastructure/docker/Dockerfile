# Multi-stage Dockerfile for SNIPERCOR
# Optimized for production deployment with minimal attack surface

# Build stage
FROM rust:1.75-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1001 sniper

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY Cargo.toml Cargo.lock ./

# Create dummy main.rs to build dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs

# Build dependencies (this layer will be cached)
RUN cargo build --profile contabo

# Remove dummy source
RUN rm -rf src

# Copy actual source code
COPY src ./src

# Build the application
RUN cargo build --profile contabo

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN useradd -m -u 1001 sniper

# Create necessary directories
RUN mkdir -p /app/logs && chown -R sniper:sniper /app

# Copy binary from builder stage
COPY --from=builder /app/target/contabo/snipercor /app/snipercor

# Copy configuration files
COPY .env.example /app/.env.example

# Set ownership
RUN chown -R sniper:sniper /app

# Switch to non-root user
USER sniper

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set environment variables
ENV RUST_LOG=info
ENV SNIPER_TRADING_MODE=paper

# Run the application
CMD ["./snipercor"]
