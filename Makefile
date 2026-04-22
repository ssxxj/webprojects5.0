PYTHON ?= python3

.PHONY: help test validate rebuild check maintain preflight ci-local reports

help:
	@echo "projects5.0 maintenance commands"
	@echo "  make validate   # 只校验主配置，不写产物"
	@echo "  make rebuild    # 批量重建全课程资产"
	@echo "  make check      # 只做 drift check"
	@echo "  make maintain   # 先重建再检查"
	@echo "  make test       # 运行回归测试"
	@echo "  make preflight  # 轻量发布前检查"
	@echo "  make ci-local   # 本地 CI 入口（先测试，再 preflight）"
	@echo "  make reports    # 显示报告路径"

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -b

validate:
	$(PYTHON) 30_runtime/maintain_projects5_v5.py --mode validate

rebuild:
	$(PYTHON) 30_runtime/maintain_projects5_v5.py --mode rebuild

check:
	$(PYTHON) 30_runtime/maintain_projects5_v5.py --mode check

maintain:
	$(PYTHON) 30_runtime/maintain_projects5_v5.py

preflight:
	bash 30_runtime/preflight_local_v5.sh

ci-local:
	bash 30_runtime/local_ci_v5.sh

reports:
	@echo "build summary:     30_runtime/chapter_master_configs/all_chapters_build_manifest_v5.json"
	@echo "drift summary:     30_runtime/chapter_master_configs/all_chapters_drift_report_v5.json"
	@echo "maintenance report:30_runtime/chapter_master_configs/projects5_maintenance_report_v5.json"
	@echo "preflight report:  30_runtime/chapter_master_configs/projects5_preflight_report_v5.json"
