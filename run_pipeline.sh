#!/usr/bin/env bash
set -euo pipefail

# Activate Python virtual environment
source .venv/bin/activate

# Load environment variables from .env if it exists and export them
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
    echo "✅ Loaded environment variables from .env"
    echo "SUHAIL_API_BASE_URL=${SUHAIL_API_BASE_URL:-'not set'}"
fi

# Run the geometric pipeline (Stage 1) without database recreation
meshic-pipeline geometric

# Run the enrichment pipeline (Stage 2)
meshic-pipeline enrich fast-enrich 