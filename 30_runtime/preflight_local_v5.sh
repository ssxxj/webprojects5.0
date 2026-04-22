#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
REPORT_PATH="$PROJECT_ROOT/30_runtime/chapter_master_configs/projects5_preflight_report_v5.json"

cd "$PROJECT_ROOT"

set +e
python3 "$PROJECT_ROOT/30_runtime/preflight_projects5_v5.py" "$@" >/dev/null
PREFLIGHT_STATUS=$?
set -e

if [[ -f "$REPORT_PATH" ]]; then
  python3 - "$REPORT_PATH" <<'PY'
import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
report = json.loads(report_path.read_text(encoding="utf-8"))
config = report.get("config_validation", {})
assets = report.get("asset_consistency", {})
lectures = report.get("lecture_governance", {})
status = "READY" if report.get("release_ready") else "BLOCKED"
print(
    f"[preflight] {status} | "
    f"config {config.get('success', 0)}/{config.get('total', 0)} | "
    f"clean {assets.get('clean', 0)}/{assets.get('total', 0)} | "
    f"lecture {lectures.get('clean', 0)}/{lectures.get('total', 0)} | "
    f"drift={assets.get('drift', 0)} error={assets.get('error', 0)} | "
    f"report: {report_path}"
)
PY
else
  echo "[preflight] BLOCKED | report not generated | expected: $REPORT_PATH"
fi

exit "$PREFLIGHT_STATUS"
