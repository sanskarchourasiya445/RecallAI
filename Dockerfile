# ==============================================================================
# Jitsly / Gistly — AI Meeting & Video Intelligence Assistant
# Containerized Deployment Dockerfile (Hugging Face Spaces / Cloud Container)
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (ffmpeg required for audio extraction/conversion)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Pre-create runtime directories and set permissions
RUN mkdir -p downloades vector_db && chmod -R 777 downloades vector_db

# Expose Streamlit default web port
EXPOSE 8501

# Streamlit Healthcheck probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Launch application with production flags
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
