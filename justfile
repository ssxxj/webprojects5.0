default:
  @just --list

validate:
  python3 30_runtime/maintain_projects5_v5.py --mode validate

test:
  python3 -m unittest discover -s tests -p 'test_*.py' -b

rebuild:
  python3 30_runtime/maintain_projects5_v5.py --mode rebuild

check:
  python3 30_runtime/maintain_projects5_v5.py --mode check

maintain:
  python3 30_runtime/maintain_projects5_v5.py

preflight:
  python3 30_runtime/preflight_projects5_v5.py

ci-local:
  bash 30_runtime/local_ci_v5.sh

reports:
  @echo "build summary:      30_runtime/chapter_master_configs/all_chapters_build_manifest_v5.json"
  @echo "drift summary:      30_runtime/chapter_master_configs/all_chapters_drift_report_v5.json"
  @echo "maintenance report: 30_runtime/chapter_master_configs/projects5_maintenance_report_v5.json"
  @echo "preflight report:   30_runtime/chapter_master_configs/projects5_preflight_report_v5.json"
