#!/bin/bash
# Run flake8 and save output to flake8_report.txt

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$PROJECT_ROOT/.venv/bin/activate"
cd "$PROJECT_ROOT"
flake8 src tests > flake8_report.txt

echo "Flake8 report saved to $PROJECT_ROOT/flake8_report.txt" 