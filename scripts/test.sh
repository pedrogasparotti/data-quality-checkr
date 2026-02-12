#!/bin/bash
set -euo pipefail

echo "Running tests with coverage..."
uv run pytest tests/ -v --cov=src/data_quality_checker --cov-report=term-missing
