#!/bin/bash
set -euo pipefail

echo "Setting up data-quality-checker..."

if ! command -v uv &> /dev/null; then
    echo "uv not found. Install from https://github.com/astral-sh/uv"
    exit 1
fi

echo "Installing dependencies..."
uv sync --all-extras

echo "Running tests..."
uv run pytest tests/ -v

echo "Setup complete."
