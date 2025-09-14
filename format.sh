#!/bin/bash

# Format code script for Wordle Bot
# Run this before committing to ensure proper formatting

echo "🎨 Formatting Python code with Ruff..."

# Format and fix with ruff
echo "Running ruff format and fix..."
ruff format .
ruff check --fix .

echo "✅ Code formatting complete!"

# Check for remaining issues
echo ""
echo "📋 Running ruff check to show remaining issues..."
ruff check . || echo "Some issues found - but main formatting is done!"

echo ""
echo "🚀 Ready to commit!"