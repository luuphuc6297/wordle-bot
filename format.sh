#!/bin/bash

# Format code script for Wordle Bot
# Run this before committing to ensure proper formatting

echo "🎨 Formatting Python code..."

# Run ruff for linting, import sorting, and auto-fixing
echo "Running ruff..."
uv run ruff check . --fix
uv run ruff format .

echo "✅ Code formatting complete!"
echo "🚀 Ready to commit!"