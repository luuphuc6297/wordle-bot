FROM python:3.11-slim

WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project metadata and lockfile first for better Docker layer caching
# Include LICENSE/README because build backend validates these during editable build
COPY pyproject.toml uv.lock LICENSE README.md ./

# Sync dependencies exactly as locked, without dev extras
RUN uv sync --frozen --no-dev

# Ensure the synced virtual environment is on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the source code
COPY . .

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
