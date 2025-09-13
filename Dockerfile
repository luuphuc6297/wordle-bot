# Multi-stage Docker build for Wordle Bot

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-deps -r requirements.txt

# Production stage
FROM base AS production

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from infrastructure.data.word_lexicon import WordLexicon; lexicon = WordLexicon(); print(f'Loaded {len(lexicon.answers)} answers')" || exit 1

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]

# Development stage
FROM base AS development

# Install development dependencies
RUN pip install pytest pytest-cov black isort flake8

# Copy application code
COPY . .

# Keep root for development convenience
USER root

# Default to bash for development
CMD ["/bin/bash"]