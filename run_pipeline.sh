#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ -f .env ]; then
    set -o allexport
    # shellcheck source=/dev/null
    source .env
    set +o allexport
    echo "✅ Loaded environment variables from .env"
    echo "SUHAIL_API_BASE_URL=${SUHAIL_API_BASE_URL:-'not set'}"
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL not set" >&2
  exit 1
fi

echo "Seeding pilot tiles for two provinces (riyadh, eastern)..."
uv run suhail-pipeline seed-tiles --provinces riyadh --provinces eastern --limit 200 --stride 20

echo "Running DB-driven geometric pilot..."
uv run suhail-pipeline db-geometric --batch-size 200 --concurrency 20 --request-delay 0.05

echo "Pilot complete. To proceed countrywide:"
echo "  1) uv run suhail-pipeline seed-tiles"
echo "  2) uv run suhail-pipeline db-geometric --batch-size 1000 --concurrency 20 --request-delay 0.05"
