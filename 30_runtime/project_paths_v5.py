#!/usr/bin/env python3
"""projects5.0 path helpers.

Project-owned manifests should be portable. Store paths inside the current
project as POSIX-style paths relative to the project root; keep external
historical paths unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def project_relative(path: Path | str, project_root: Path) -> str:
    raw = str(path)
    candidate = Path(raw)
    if not candidate.is_absolute():
        return raw.replace("\\", "/")

    try:
        return candidate.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return raw


def resolve_project_path(path: Path | str, project_root: Path) -> Path:
    candidate = Path(str(path))
    if candidate.is_absolute():
        return candidate
    return project_root / candidate


def relativize_mapping(value: Any, project_root: Path) -> Any:
    if isinstance(value, dict):
        return {key: relativize_mapping(item, project_root) for key, item in value.items()}
    if isinstance(value, list):
        return [relativize_mapping(item, project_root) for item in value]
    if isinstance(value, str):
        return project_relative(value, project_root)
    return value
