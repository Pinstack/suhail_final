#!/bin/bash
# Run vulture and save output to vulture_report.txt (tool via uvx)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="${REPORT_DIR:-/tmp}"
REPORT_PATH="$REPORT_DIR/vulture_report.txt"

mkdir -p "$REPORT_DIR"

cd "$PROJECT_ROOT" || exit 1
uvx vulture src tests > "$REPORT_PATH"

echo "Vulture report saved to $REPORT_PATH"
