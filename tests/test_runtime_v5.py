import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = PROJECT_ROOT / "30_runtime"
sys.path.insert(0, str(RUNTIME_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "40_evaluation" / "runtime"))
sys.path.insert(0, str(PROJECT_ROOT / "50_assets" / "课堂实施方案" / "runtime"))

import build_all_chapter_assets_v5 as build_all  # noqa: E402
import build_chapter_assets_v5 as build_single  # noqa: E402
import check_all_chapter_asset_drift_v5 as drift_check  # noqa: E402
import course_assignment_eval_v5 as eval_runtime  # noqa: E402
import generate_lesson_script_v5 as lesson_gen  # noqa: E402
import preflight_projects5_v5 as preflight  # noqa: E402


FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "chapter99_demo.yaml"


class Projects5RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name) / "projects5.0"
        (self.temp_root / "30_runtime" / "chapter_master_configs").mkdir(parents=True, exist_ok=True)
        (self.temp_root / "40_evaluation" / "runtime" / "chapter_profiles").mkdir(parents=True, exist_ok=True)
        (self.temp_root / "50_assets" / "assignment_packs").mkdir(parents=True, exist_ok=True)
        (self.temp_root / "50_assets" / "课堂实施方案").mkdir(parents=True, exist_ok=True)
        (self.temp_root / "50_assets" / "章节讲义").mkdir(parents=True, exist_ok=True)
        self.config_path = self.temp_root / "30_runtime" / "chapter_master_configs" / "chapter99_demo.yaml"
        shutil.copyfile(FIXTURE, self.config_path)
        self.config_data = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        self.chapter_id = self.config_data["chapter_id"]
        self.chapter_title = self.config_data["chapter_title"]
        self._write_minimal_lecture_assets()

        self.patchers = [
            patch.object(build_single, "PROJECT_ROOT", self.temp_root),
            patch.object(build_all, "PROJECT_ROOT", self.temp_root),
            patch.object(drift_check, "PROJECT_ROOT", self.temp_root),
            patch.object(lesson_gen, "PROJECT_ROOT", self.temp_root),
            patch.object(preflight, "PROJECT_ROOT", self.temp_root),
            patch.object(preflight, "LECTURE_ROOT", self.temp_root / "50_assets" / "章节讲义"),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.temp_dir.cleanup()

    def _run_main_quiet(self, module, argv: list[str]) -> int:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return module.main()

    def _run_build_single(self) -> int:
        return self._run_main_quiet(
            build_single,
            ["build_chapter_assets_v5.py", "--input", str(self.config_path)],
        )

    def _write_minimal_lecture_assets(self) -> None:
        lecture_dir = self.temp_root / "50_assets" / "章节讲义" / self.chapter_id
        lecture_dir.mkdir(parents=True, exist_ok=True)

        teacher_path = lecture_dir / f"{self.chapter_title}_教师版讲义_v5.0.md"
        student_path = lecture_dir / f"{self.chapter_title}_学生预习版讲义_v5.0.md"
        checklist_path = lecture_dir / f"{self.chapter_title}_讲义迁移清单_v5.0.json"
        mapping_path = lecture_dir / f"{self.chapter_title}_4.0讲义到5.0讲义到5.0作业包对照表.md"

        teacher_path.write_text(f"# {self.chapter_title} 教师版讲义 v5.0\n", encoding="utf-8")
        student_path.write_text(f"# {self.chapter_title} 学生预习版讲义 v5.0\n", encoding="utf-8")
        mapping_path.write_text(f"# {self.chapter_title} 4.0讲义到5.0讲义到5.0作业包对照表\n", encoding="utf-8")
        checklist_path.write_text(
            json.dumps(
                {
                    "chapter_id": self.chapter_id,
                    "chapter_name": self.chapter_title,
                    "upstream_5_0": {
                        "profile": str(self.temp_root / "40_evaluation" / "runtime" / "chapter_profiles" / f"{self.chapter_id}.json"),
                        "assignment_pack": str(
                            self.temp_root
                            / "50_assets"
                            / "assignment_packs"
                            / self.chapter_id
                            / f"{self.chapter_title}_教师端作业包_v5.0.md"
                        ),
                    },
                    "generated_assets": [
                        str(teacher_path),
                        str(student_path),
                        str(mapping_path),
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_build_single_generates_expected_assets(self) -> None:
        code = self._run_build_single()
        self.assertEqual(code, 0)

        profile_path = self.temp_root / "40_evaluation" / "runtime" / "chapter_profiles" / "chapter99_demo.json"
        teacher_pack = self.temp_root / "50_assets" / "assignment_packs" / "chapter99_demo" / "第九十九章 Demo章节_教师端作业包_v5.0.md"
        lesson_input = self.temp_root / "50_assets" / "课堂实施方案" / "chapter99_demo" / "lesson_script_input_v5.yaml"
        lesson_script = self.temp_root / "50_assets" / "课堂实施方案" / "chapter99_demo" / "第九十九章 Demo章节_课堂实施方案_v5.0.md"

        self.assertTrue(profile_path.exists())
        self.assertTrue(teacher_pack.exists())
        self.assertTrue(lesson_input.exists())
        self.assertTrue(lesson_script.exists())
        self.assertIn("教师端作业包", teacher_pack.read_text(encoding="utf-8"))

    def test_build_all_validate_only_passes(self) -> None:
        code = self._run_main_quiet(
            build_all,
            ["build_all_chapter_assets_v5.py", "--root", str(self.config_path.parent), "--validate-only"],
        )
        self.assertEqual(code, 0)
        summary_path = self.config_path.parent / "all_chapters_build_manifest_v5.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["success"], 1)

    def test_drift_check_detects_modified_teacher_pack(self) -> None:
        self.assertEqual(self._run_build_single(), 0)
        teacher_pack = self.temp_root / "50_assets" / "assignment_packs" / "chapter99_demo" / "第九十九章 Demo章节_教师端作业包_v5.0.md"
        teacher_pack.write_text("BROKEN\n", encoding="utf-8")

        result = drift_check.process_config(self.config_path, diff_lines=4)
        self.assertEqual(result["status"], "drift")
        self.assertIn("teacher_pack", result["drifted_files"])

    def test_preflight_reports_release_ready_on_clean_project(self) -> None:
        self.assertEqual(self._run_build_single(), 0)
        root = self.config_path.parent
        code = self._run_main_quiet(
            preflight,
            ["preflight_projects5_v5.py", "--root", str(root)],
        )
        self.assertEqual(code, 0)
        report_path = root / "projects5_preflight_report_v5.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertTrue(report["release_ready"])
        self.assertEqual(report["asset_consistency"]["drift"], 0)
        self.assertEqual(report["lecture_governance"]["issue"], 0)

    def test_preflight_fails_when_assets_drift(self) -> None:
        self.assertEqual(self._run_build_single(), 0)
        teacher_pack = self.temp_root / "50_assets" / "assignment_packs" / "chapter99_demo" / "第九十九章 Demo章节_教师端作业包_v5.0.md"
        teacher_pack.write_text("BROKEN\n", encoding="utf-8")
        root = self.config_path.parent
        code = self._run_main_quiet(
            preflight,
            ["preflight_projects5_v5.py", "--root", str(root)],
        )
        self.assertEqual(code, 1)
        report_path = root / "projects5_preflight_report_v5.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertFalse(report["release_ready"])
        self.assertEqual(report["asset_consistency"]["drift"], 1)

    def test_preflight_fails_when_lecture_assets_missing(self) -> None:
        self.assertEqual(self._run_build_single(), 0)
        teacher_lecture = (
            self.temp_root
            / "50_assets"
            / "章节讲义"
            / self.chapter_id
            / f"{self.chapter_title}_教师版讲义_v5.0.md"
        )
        teacher_lecture.unlink()
        root = self.config_path.parent
        code = self._run_main_quiet(
            preflight,
            ["preflight_projects5_v5.py", "--root", str(root)],
        )
        self.assertEqual(code, 1)
        report_path = root / "projects5_preflight_report_v5.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertFalse(report["release_ready"])
        self.assertEqual(report["lecture_governance"]["issue"], 1)

    def test_detect_public_targets_ignores_reference_links_and_ocr_noise(self) -> None:
        text = """
        实验页面：DVWA SQL Injection Low
        参考资料：https://en.wikipedia.org/wiki/SQL_injection
        参考链接：https://www.netsparker.com/web-vulnerability-scanner/sql-injection/
        OCR 噪声：3.low / 2.blind / sqlisourcelow.php / 6bb25e10266328ead3e1f12c49d0f.aa
        """
        self.assertEqual(eval_runtime.detect_public_targets(text), [])

    def test_detect_public_targets_keeps_real_live_target(self) -> None:
        text = """
        实验目标：www.example.com
        请求 URL：http://www.example.com/vuln.php?id=1
        对目标站点进行 SQL 注入验证，并记录返回差异。
        """
        self.assertEqual(eval_runtime.detect_public_targets(text), ["www.example.com"])

    def test_detect_self_eval_trace_accepts_qna_style_answers(self) -> None:
        text = """
        收口项2：学生自评表
        1. 我本章最清楚的一点是什么：
        2. 我最容易混淆的一点是什么：
        3. 我本次作业中哪一段最需要教师复核：
        4. 如果重做一次，我最想改进哪一部分：
        """
        trace = eval_runtime.detect_self_eval_trace(text)
        self.assertTrue(trace["present"])
        self.assertTrue(trace["structured"])

    def test_detect_self_eval_trace_accepts_heading_variants(self) -> None:
        samples = [
            "任务6：自评\n我本章最清楚的一点是什么：……\n如果重做一次，我会优先改哪一部分：……",
            "收口项 2 学生自评\n本次实验最清晰的内容：……\n需要教师复核的内容：……",
            "六、学生自评\n通过本次实验，我理解了 SQL 注入的产生原理。",
        ]
        for text in samples:
            trace = eval_runtime.detect_self_eval_trace(text)
            self.assertTrue(trace["present"])

    def test_locate_sections_generic_finds_self_eval_heading_variants(self) -> None:
        profile = eval_runtime.ChapterProfile(
            course_name="demo",
            chapter_name="demo",
            chapter_mainline="demo",
            capability_goals=[],
            tasks=[],
            relation_item_name="关系图",
            relation_item_score=0.0,
            self_eval_score=0.0,
            redlines=[],
            professional_checks=[],
            default_tags=[],
        )
        text = """
        收口项 1 因果链关系图
        输入点 -> 查询构造 -> 数据库执行
        收口项 2 学生自评
        本次实验最清晰的内容：理解了结构污染是根因。
        需要教师复核的内容：盲注与普通注入的差异。
        收口项 3 AI 输出审核记录
        """
        sections = eval_runtime.locate_sections_generic(text, profile)
        self.assertIn("self_eval", sections)
        self.assertIn("学生自评", sections["self_eval"])

    def test_locate_sections_generic_finds_ai_review_heading_variants(self) -> None:
        profile = eval_runtime.ChapterProfile(
            course_name="demo",
            chapter_name="demo",
            chapter_mainline="demo",
            capability_goals=[],
            tasks=[],
            relation_item_name="关系图",
            relation_item_score=0.0,
            self_eval_score=0.0,
            redlines=[],
            professional_checks=[],
            default_tags=[],
        )
        text = """
        收口项 2 学生自评
        本次实验最清晰的内容：理解了结构污染是根因。
        收口项 3 AI 输出审核记录
        AI 使用情况：本次作业借助 AI 完成框架整理。
        人工复核与修改：结合 DVWA 现象修正逻辑表述。
        """
        sections = eval_runtime.locate_sections_generic(text, profile)
        self.assertIn("ai_review", sections)
        self.assertIn("AI 输出审核记录", sections["ai_review"])

    def test_locate_sections_chapter2_accepts_heading_variants(self) -> None:
        text = """
        任务一 Google 公开页面线索记录
        示例内容
        收口项 2 学生自评
        本次实验最清晰的内容：学会区分线索与证据。
        收口项 3 AI 输出审核记录
        AI 使用情况：借助 AI 整理框架。
        人工复核与修改：结合实际截图修正表述。
        """
        sections = eval_runtime.locate_sections_chapter2(text)
        self.assertIn("self_eval", sections)
        self.assertIn("ai_review", sections)
        self.assertIn("学生自评", sections["self_eval"])
        self.assertIn("AI 输出审核记录", sections["ai_review"])

    def test_detect_ai_review_trace_accepts_semantic_variants(self) -> None:
        text = """
        AI 输出审核与人工复核记录
        1. 本作业哪些内容使用过 AI 辅助：
        2. 哪些判断是我自己复核后保留的：
        3. 哪些内容我发现 AI 原始输出不够准确，并做了修正：
        4. 本作业中我自行核实过的 3 个专业判断：
        5. 我认为最容易误判的一处边界问题：
        """
        trace = eval_runtime.detect_ai_review_trace(text)
        self.assertTrue(trace["present"])
        self.assertTrue(trace["complete"])

    def test_detect_ai_review_trace_accepts_spaced_heading_variant(self) -> None:
        text = """
        AI 输出审核记录
        AI 使用情况：本次作业借助 AI 完成框架整理。
        人工复核与修改：结合 DVWA 实验现象修正逻辑表述。
        """
        trace = eval_runtime.detect_ai_review_trace(text)
        self.assertTrue(trace["present"])


if __name__ == "__main__":
    unittest.main()
