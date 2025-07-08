#!/bin/bash
# Run vulture and save output to vulture_report.txt

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$PROJECT_ROOT/.venv/bin/activate"
cd "$PROJECT_ROOT"
vulture src tests > vulture_report.txt

echo "Vulture report saved to $PROJECT_ROOT/vulture_report.txt" 