FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project metadata and lockfile first for better Docker layer caching
COPY pyproject.toml uv.lock LICENSE README.md ./


FROM base AS development

# Install dev dependencies
RUN uv sync --frozen

# Ensure the synced virtual environment is on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy source
COPY . .

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]


FROM base AS production

# Install only runtime deps
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY . .

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
