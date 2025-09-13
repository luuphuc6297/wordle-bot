#!/bin/bash

# Format code script for Wordle Bot
# Run this before committing to ensure proper formatting

echo "🎨 Formatting Python code..."

# Format with black
echo "Running black..."
black .

# Sort imports with isort
echo "Running isort..."
isort . --profile black

# Remove unused imports and fix basic issues
echo "Running autoflake..."
pip install autoflake > /dev/null 2>&1
autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive .

echo "✅ Code formatting complete!"

# Optional: run flake8 to show remaining issues
echo ""
echo "📋 Running flake8 to check for issues..."
flake8 . || echo "Some issues found - but main formatting is done!"

echo ""
echo "🚀 Ready to commit!"