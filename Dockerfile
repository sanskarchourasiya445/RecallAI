# ==============================================================================
# RecallAI — Production FastAPI Backend Container
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (ffmpeg is required for audio extraction/transcription)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure storage directories exist with appropriate permissions
RUN mkdir -p downloades vector_db && chmod -R 777 downloades vector_db

# Expose FastAPI backend default port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production server entrypoint
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
