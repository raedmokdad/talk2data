# Talk2Data Agent - Linux Docker Setup for Railway
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY data/ ./data/
COPY api_service.py .
COPY .env.example .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Railway sets PORT automatically, fallback to 8000
ENV PORT=8000
EXPOSE $PORT

# Start the API service
CMD ["python", "-m", "uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]