FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY libs/ ./libs/
COPY apps/ ./apps/

# Install dependencies
RUN uv sync --all-extras

# Set environment variables
ENV PYTHONPATH=/app/libs
ENV PATH="/app/.venv/bin:$PATH"

# Default command (can be overridden)
CMD ["/app/.venv/bin/python", "-m", "apps.cli.main", "--help"]