# THE OVERMIND PROTOCOL - Mission Control Dashboard
# Streamlit-based web interface for real-time system management

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY mission_control/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mission_control/ /app/mission_control/
COPY brain/ /app/brain/

# Set Python path
ENV PYTHONPATH=/app/brain/src

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# Run Streamlit application
CMD ["streamlit", "run", "mission_control/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
