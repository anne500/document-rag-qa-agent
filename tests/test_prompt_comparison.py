import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest

from eval_prompt_comparison import write_artifacts
from multidoc_lab import review_template
from prompt_lab import (citation_check, completed_review_records, prompts_for,
                        run_pairs, select_records, validate_frozen)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "verification/multidoc-runs/20261110T222813Z-bc04d7e8"


class PromptComparisonTests(unittest.TestCase):
    def setUp(self):
        def read(name):
            return json.loads((SOURCE / name).read_text(encoding="utf-8"))
        self.report = read("report.json")
        self.dataset = read("cases.snapshot.json")
        self.corpus = read("corpus.snapshot.json")
        self.records = self.report["records"][:2]
        self.prompts = prompts_for(self.report["settings"]["system_prompt"])

    def test_saved_source_validation_and_selection(self):
        records = validate_frozen(self.report, self.dataset, self.corpus)
        self.assertEqual(len(records), 13)
        self.assertEqual(len(select_records(records, ["cedar_birch_missing", "known_unknown"])), 4)
        with self.assertRaises(ValueError):
            select_records(records, ["not_a_case"])

    def test_changed_snapshot_rejected(self):
        corpus = copy.deepcopy(self.corpus)
        corpus[0]["text"] += " changed"
        with self.assertRaises(ValueError):
            validate_frozen(self.report, self.dataset, corpus)

    def test_wrong_source_page_and_changed_question_rejected(self):
        report = copy.deepcopy(self.report)
        report["records"][0]["excerpts"][0]["page"] = 99
        with self.assertRaises(ValueError):
            validate_frozen(report, self.dataset, self.corpus)
        report = copy.deepcopy(self.report)
        report["records"][0]["question"] = "Changed question"
        with self.assertRaises(ValueError):
            validate_frozen(report, self.dataset, self.corpus)

    def test_incomplete_and_duplicate_source_records_rejected(self):
        report = copy.deepcopy(self.report)
        report["status"] = "interrupted"
        with self.assertRaises(ValueError):
            validate_frozen(report, self.dataset, self.corpus)
        report = copy.deepcopy(self.report)
        report["records"][1] = report["records"][0]
        with self.assertRaises(ValueError):
            validate_frozen(report, self.dataset, self.corpus)

    def test_baseline_text_is_preserved_and_revision_contains_no_fixture_answers(self):
        self.assertEqual(self.prompts["baseline"], self.report["settings"]["system_prompt"])
        self.assertTrue(self.prompts["revised"].startswith(self.prompts["baseline"]))
        self.assertNotIn("Birch", self.prompts["revised"])
        self.assertNotIn("maintainer", self.prompts["revised"])
        with self.assertRaises(ValueError):
            prompts_for("")

    def test_both_variants_receive_identical_context_and_order_alternates(self):
        calls = []
        def generate(variant, question, context):
            calls.append((variant, question, context))
            return "Supported [1]."
        pairs = run_pairs(self.records, self.prompts, generate, lambda r: None)
        self.assertEqual([x[0] for x in calls], ["baseline", "revised", "revised", "baseline"])
        for index, pair in enumerate(pairs):
            a, b = calls[2*index:2*index+2]
            self.assertEqual(a[1:], b[1:])
            self.assertEqual(pair["variants"]["baseline"]["context_sha256"],
                             pair["variants"]["revised"]["context_sha256"])
        self.assertEqual(self.records, self.report["records"][:2])

    def test_failed_second_variant_preserves_first_answer_and_context(self):
        saved = []
        def generate(variant, question, context):
            if variant == "revised":
                raise RuntimeError("chat unavailable")
            return "Baseline [1]."
        with self.assertRaises(RuntimeError):
            run_pairs(self.records[:1], self.prompts, generate,
                      lambda r: saved.append(copy.deepcopy(r)))
        pair = saved[-1][0]
        self.assertEqual(pair["status"], "failed")
        self.assertEqual(pair["variants"]["baseline"]["answer"], "Baseline [1].")
        self.assertEqual(pair["variants"]["revised"]["status"], "failed")
        self.assertEqual(pair["excerpts"], self.records[0]["excerpts"])

    def test_interruption_is_checkpointed(self):
        saved = []
        def interrupt(*args):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            run_pairs(self.records[:1], self.prompts, interrupt,
                      lambda r: saved.append(copy.deepcopy(r)))
        self.assertEqual(saved[-1][0]["status"], "interrupted")

    def test_empty_answer_is_failed_not_complete(self):
        saved = []
        with self.assertRaises(ValueError):
            run_pairs(self.records[:1], self.prompts, lambda *a: " ",
                      lambda r: saved.append(copy.deepcopy(r)))
        self.assertEqual(saved[-1][0]["variants"]["baseline"]["status"], "failed")

    def test_grouped_and_single_citations_have_separate_syntax_check(self):
        check = citation_check("A [1, 2]. B [2][4]. C [0].", 2)
        self.assertEqual(check["labels"], [0, 1, 2, 4])
        self.assertEqual(check["out_of_range"], [0, 4])
        self.assertEqual(citation_check("Invented claim [1, 2].", 2)["out_of_range"], [])
        self.assertNotIn("citation_support", check)

    def test_review_starts_unreviewed_and_keeps_variants_separate(self):
        pairs = run_pairs(self.records[:1], self.prompts, lambda *a: "Claim [1].", lambda r: None)
        review = review_template(completed_review_records(pairs))
        self.assertEqual({r["record_id"] for r in review["records"]}, {"cedar_maple:k2::baseline", "cedar_maple:k2::revised"})
        self.assertTrue(all(v is None for r in review["records"] for v in r["ratings"].values()))

    def test_agent_default_and_explicit_prompt_use_same_model_settings(self):
        # Exercise the real factory body with SDK boundary fakes; no model calls.
        tree = ast.parse((ROOT / "qa_agent.py").read_text(encoding="utf-8"))
        factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_agent")
        namespace = {"SYSTEM_PROMPT": "interactive default", "CHAT_MODEL": "test-model",
                     "wrap_model_call": lambda function: function,
                     "ChatOllama": lambda **kwargs: kwargs,
                     "create_agent": lambda **kwargs: kwargs}
        exec(compile(ast.Module(body=[factory], type_ignores=[]), "qa_agent.py", "exec"), namespace)
        default = namespace["build_agent"]()
        revised = namespace["build_agent"](system_prompt="explicit variant")
        self.assertEqual(default["system_prompt"], "interactive default")
        self.assertEqual(revised["system_prompt"], "explicit variant")
        self.assertEqual(default["model"], revised["model"])
        self.assertEqual(default["model"], {"model": "test-model", "temperature": 0, "reasoning": False})

    def test_dashboard_keeps_quality_unreviewed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            write_artifacts(path, {"status": "failed", "pairs": []})
            summary = (path / "summary.md").read_text(encoding="utf-8")
            self.assertIn("**failed**", summary)
            self.assertIn("**unreviewed**", summary)


if __name__ == "__main__":
    unittest.main()
