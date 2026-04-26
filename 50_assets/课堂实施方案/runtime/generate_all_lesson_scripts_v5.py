#!/usr/bin/env python3
"""
projects5.0 Step8 全章课堂实施方案批量生成器

输入：
1. `50_assets/课堂实施方案/chapter*/lesson_script_input_v5.yaml`

输出：
1. 每章 `课堂实施方案_v5.0.md`
2. 每章 `课堂实施方案_生成清单_v5.0.json`
3. 批量生成摘要 `批量生成清单_v5.0.json`
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import generate_lesson_script_v5 as single


ASSET_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "30_runtime"))

from project_paths_v5 import project_relative  # type: ignore  # noqa: E402


def discover_inputs(root: Path, chapter_filters: list[str] | None) -> list[Path]:
    inputs = sorted(root.glob("chapter*/lesson_script_input_v5.yaml"))
    if not chapter_filters:
        return inputs
    wanted = {item.strip() for item in chapter_filters if item.strip()}
    return [path for path in inputs if path.parent.name in wanted]


def build_output_paths(data: dict[str, Any], chapter_dir: Path) -> tuple[Path, Path]:
    safe_title = single.normalize_filename(single.ensure_str(data["chapter_title"]))
    output_path = chapter_dir / f"{safe_title}_课堂实施方案_v5.0.md"
    manifest_path = chapter_dir / f"{safe_title}_课堂实施方案_生成清单_v5.0.json"
    return output_path, manifest_path


def build_batch_summary(
    root: Path,
    results: list[dict[str, Any]],
    chapter_filters: list[str] | None,
    validate_only: bool,
) -> dict[str, Any]:
    return {
        "schema_version": "v5.0",
        "generator": "generate_all_lesson_scripts_v5.py",
        "generated_at": str(date.today()),
        "root": project_relative(root, PROJECT_ROOT),
        "chapter_filters": chapter_filters or [],
        "validate_only": validate_only,
        "total": len(results),
        "success": sum(1 for item in results if item.get("status") == "ok"),
        "failed": sum(1 for item in results if item.get("status") != "ok"),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="projects5.0 Step8 全章课堂实施方案批量生成器")
    parser.add_argument(
        "--root",
        default=str(ASSET_ROOT),
        help="课堂实施方案资产根目录，默认指向 50_assets/课堂实施方案",
    )
    parser.add_argument(
        "--chapters",
        nargs="*",
        help="可选，按 chapter_dir 过滤，例如 chapter02_web_info_collection",
    )
    parser.add_argument("--validate-only", action="store_true", help="仅校验输入，不写出 Markdown")
    parser.add_argument(
        "--summary",
        help="批量生成摘要 JSON 路径；默认写到 root/批量生成清单_v5.0.json",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    inputs = discover_inputs(root, args.chapters)
    if not inputs:
        print(
            json.dumps(
                {
                    "schema_version": "v5.0",
                    "generator": "generate_all_lesson_scripts_v5.py",
                    "root": project_relative(root, PROJECT_ROOT),
                    "message": "未找到任何 lesson_script_input_v5.yaml",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    results: list[dict[str, Any]] = []
    exit_code = 0

    for input_path in inputs:
        chapter_dir = input_path.parent
        try:
            data = single.load_input(input_path)
            errors = single.validate_input(data)
            output_path, manifest_path = build_output_paths(data, chapter_dir)

            if errors:
                exit_code = 1
                results.append(
                    {
                        "chapter_dir": chapter_dir.name,
                        "input_file": project_relative(input_path, PROJECT_ROOT),
                        "status": "error",
                        "validation_errors": errors,
                    }
                )
                continue

            if not args.validate_only:
                markdown = single.render_markdown(data)
                output_path.write_text(markdown, encoding="utf-8")
                manifest_path.write_text(
                    json.dumps(
                        single.build_manifest(
                            input_path,
                            output_path,
                            single.ensure_str(data["chapter_id"]),
                            single.ensure_str(data["chapter_title"]),
                            [],
                        ),
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

            results.append(
                {
                    "chapter_dir": chapter_dir.name,
                    "input_file": project_relative(input_path, PROJECT_ROOT),
                    "output_file": project_relative(output_path, PROJECT_ROOT),
                    "manifest_file": project_relative(manifest_path, PROJECT_ROOT),
                    "status": "ok",
                    "validation_errors": [],
                }
            )
        except Exception as exc:  # noqa: BLE001
            exit_code = 1
            results.append(
                {
                    "chapter_dir": chapter_dir.name,
                    "input_file": project_relative(input_path, PROJECT_ROOT),
                    "status": "error",
                    "validation_errors": [str(exc)],
                }
            )

    summary = build_batch_summary(root, results, args.chapters, args.validate_only)
    summary_path = Path(args.summary).expanduser().resolve() if args.summary else root / "批量生成清单_v5.0.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
