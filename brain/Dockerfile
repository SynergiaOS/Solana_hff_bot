FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY uv.lock .
COPY src/ ./src/

# Install dependencies with uv (without --frozen for flexibility)
RUN uv sync

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uv", "run", "python", "src/overmind_brain/main.py"]
