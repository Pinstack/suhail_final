#!/bin/bash
# Run flake8 and save output to flake8_report.txt (tool via uvx; not a project dependency)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="${REPORT_DIR:-/tmp}"
REPORT_PATH="$REPORT_DIR/flake8_report.txt"

mkdir -p "$REPORT_DIR"

cd "$PROJECT_ROOT" || exit 1
uvx flake8 src tests > "$REPORT_PATH"

echo "Flake8 report saved to $REPORT_PATH"
