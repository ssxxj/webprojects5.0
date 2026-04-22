#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
python3 -m unittest discover -s tests -p 'test_*.py' -b
bash "$PROJECT_ROOT/30_runtime/preflight_local_v5.sh" "$@"
