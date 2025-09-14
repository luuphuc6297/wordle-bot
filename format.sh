#!/bin/bash

# Format code script for Wordle Bot
# Run this before committing to ensure proper formatting with 2 spaces

echo "🎨 Formatting Python code with 2 spaces..."

# Remove unused imports and fix basic issues first
echo "Running autoflake..."
pip install autoflake > /dev/null 2>&1
autoflake --remove-all-unused-imports --remove-unused-variables --remove-duplicate-keys --expand-star-imports --in-place --recursive . --exclude=venv,__pycache__,.pytest_cache

# Format with black (2 spaces from pyproject.toml)
echo "Running black with 2 spaces..."
black .

# Sort imports with isort (2 spaces)
echo "Running isort with 2 spaces..."
isort . --profile black --indent=2

echo "✅ Code formatting complete!"

# Optional: run flake8 to show remaining issues
echo ""
echo "📋 Running flake8 to check for issues..."
flake8 . --max-line-length=88 --max-complexity=10 --indent-size=2 || echo "Some issues found - but main formatting is done!"

echo ""
echo "🚀 Ready to commit!"