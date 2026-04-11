# ===============================
# ResuMatch AI - Dockerfile
# ===============================
FROM python:3.12-slim

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies with uv (leverages layer cache — only reruns when lockfile changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --extra postgres

# Copy application code
COPY . .

# Sync the project itself (installs the `app` package)
RUN uv sync --frozen --extra postgres

# Create necessary directories
RUN mkdir -p uploads chroma_data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run via uv so the venv is used automatically
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
