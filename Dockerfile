# Step-3.5-Flash – Hugging Face Space Optimised Dockerfile
# Single-stage, non‑root, port 7860, Debian slim base
# -------------------------------------------------------------------
FROM python:3.13-slim AS production

LABEL maintainer="Nordeim" \
      description="Flash Chatbot – NVIDIA API, Streamlit, Clean Architecture" \
      version="1.0.0"

# -------------------------------------------------------------------
# Environment – robust defaults, no .env dependency
# -------------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# -------------------------------------------------------------------
# System dependencies – only what is strictly necessary
# -------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------------
# Create non‑root user and set working directory
# -------------------------------------------------------------------
RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g appuser -s /bin/bash appuser && \
    mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app

# -------------------------------------------------------------------
# Python dependencies – leverage Docker cache
# -------------------------------------------------------------------
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------------
# Application code – baked in, no runtime mounts
# -------------------------------------------------------------------
COPY --chown=appuser:appuser src/ ./src/
# Provide a default .env file (will be overridden by env vars)
COPY --chown=appuser:appuser .env.example .env

# -------------------------------------------------------------------
# Switch to non‑root user for security
# -------------------------------------------------------------------
USER appuser

# -------------------------------------------------------------------
# Port declaration – HF Space expects 7860
# -------------------------------------------------------------------
EXPOSE 7860

# -------------------------------------------------------------------
# Health check – ensures Space orchestrator knows container is ready
# -------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

# -------------------------------------------------------------------
# Start Streamlit – port and address already set via ENV
# -------------------------------------------------------------------
ENTRYPOINT ["streamlit", "run", "src/main.py"]
