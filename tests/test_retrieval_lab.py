"""Offline scoring and orchestration checks; no real model or Chroma invocation."""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import eval_retrieval as runner
from retrieval_metrics import METRICS, score_case, summarize, validate_dataset


def evidence(group_id="token", source="docs/atlas.pdf", page=2):
    return {"id": group_id, "source": source, "page": page,
            "contains": ["token", "expired"]}


def case(groups=None):
    return {"id": "failure", "kind": "evidence", "question": "Why did it fail?",
            "required_evidence": groups if groups is not None else [evidence()]}


def candidate(source="docs/atlas.pdf", page=2, text="The token expired."):
    return {"source": source, "page": page, "text": text}


class ScoringTests(unittest.TestCase):
    def test_same_words_from_wrong_source_do_not_count(self):
        result = score_case(case(), [candidate(source="docs/birch.md")], 1)
        self.assertEqual(result["hit_at_k"], 0)

    def test_wrong_pdf_page_does_not_count(self):
        self.assertEqual(score_case(case(), [candidate(page=1)], 1)["hit_at_k"], 0)

    def test_correct_filename_without_evidence_does_not_count(self):
        result = score_case(case(), [candidate(text="Release approval policy.")], 1)
        self.assertEqual(result["complete_at_k"], 0)

    def test_case_and_whitespace_are_normalized(self):
        result = score_case(case(), [candidate(text="The TOKEN\n has EXPIRED.")], 1)
        self.assertEqual(result["complete_at_k"], 1)

    def test_partial_multi_source_evidence_is_not_complete(self):
        groups = [evidence(), evidence("other", "docs/maple.md", None)]
        result = score_case(case(groups), [candidate()], 1)
        self.assertEqual(result["coverage_at_k"], 0.5)
        self.assertEqual(result["complete_at_k"], 0)

    def test_duplicate_chunks_do_not_inflate_group_coverage(self):
        groups = [evidence(), evidence("other", "docs/maple.md", None)]
        result = score_case(case(groups), [candidate(), candidate()], 2)
        self.assertEqual(result["matched_groups"], ["token"])
        self.assertEqual(result["coverage_at_k"], 0.5)

    def test_rank_two_has_reciprocal_rank_one_half(self):
        ranked = [candidate(page=1), candidate()]
        self.assertEqual(score_case(case(), ranked, 2)["mrr_at_k"], 0.5)
        self.assertEqual(score_case(case(), ranked, 1)["hit_at_k"], 0)

    def test_precision_uses_actual_returned_chunks(self):
        self.assertEqual(score_case(case(), [candidate()], 3)["precision_at_k"], 1)
        result = score_case(case(), [candidate(), candidate(page=1)], 2)
        self.assertEqual(result["precision_at_k"], 0.5)

    def test_no_evidence_controls_are_unscored_and_excluded(self):
        control = {"kind": "no_evidence", "required_evidence": []}
        unscored = score_case(control, [candidate()], 1)
        self.assertTrue(all(unscored[key] is None for key in METRICS))
        summary = summarize([score_case(case(), [candidate()], 1), unscored])
        self.assertEqual(summary["hit_at_k"], 1)
        self.assertEqual(summary["evidence_cases"], 1)
        self.assertEqual(summary["no_evidence_controls"], 1)

    def test_invalid_k_rejected(self):
        for k in (0, -1, True):
            with self.assertRaises(ValueError):
                score_case(case(), [], k)

    def test_empty_retrieval_is_a_miss(self):
        result = score_case(case(), [], 2)
        self.assertTrue(all(result[key] == 0 for key in METRICS))

    def test_full_multisource_evidence_is_complete(self):
        groups = [evidence(), evidence("other", "docs/maple.md", None)]
        result = score_case(
            case(groups), [candidate(), candidate(source="docs/maple.md", page=None)], 2
        )
        self.assertEqual(result["coverage_at_k"], 1)
        self.assertEqual(result["complete_at_k"], 1)


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(
            (Path(__file__).resolve().parents[1] / "evaluation" / "cases.json")
            .read_text(encoding="utf-8")
        )

    def test_published_dataset_has_twelve_evidence_cases_and_two_controls(self):
        validate_dataset(self.dataset)
        self.assertEqual(sum(c["kind"] == "evidence" for c in self.dataset["cases"]), 12)
        self.assertEqual(sum(c["kind"] == "no_evidence" for c in self.dataset["cases"]), 2)

    def test_duplicate_case_ids_rejected(self):
        self.dataset["cases"].append(copy.deepcopy(self.dataset["cases"][0]))
        with self.assertRaises(ValueError):
            validate_dataset(self.dataset)

    def test_unscored_controls_cannot_claim_required_evidence(self):
        self.dataset["cases"][0]["kind"] = "no_evidence"
        with self.assertRaises(ValueError):
            validate_dataset(self.dataset)

    def test_pdf_pages_and_markers_are_required_to_be_valid(self):
        group = self.dataset["cases"][7]["required_evidence"][0]
        group["page"] = 0
        with self.assertRaises(ValueError):
            validate_dataset(self.dataset)
        group["page"] = 1
        group["contains"] = []
        with self.assertRaises(ValueError):
            validate_dataset(self.dataset)


class RunnerTests(unittest.TestCase):
    def run_fixture(self, failure=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        doc = SimpleNamespace(page_content="The token expired.",
                              metadata={"source": "docs/atlas.pdf", "page": 2})
        sample = {"schema_version": 1, "expected_sources": ["docs/atlas.pdf"],
                  "expected_document_units": 1, "cases": [
                      case(), {"id": "absent", "kind": "no_evidence",
                               "question": "Missing fact?", "required_evidence": []}
                  ]}
        cases_path = root / "cases.json"
        cases_path.write_text(json.dumps(sample), encoding="utf-8")
        for name in ("qa_agent.py", "eval_retrieval.py", "retrieval_metrics.py"):
            (root / name).write_text("# offline fixture", encoding="utf-8")

        class Splitter:
            def __init__(self, **kwargs):
                pass

            def split_documents(self, documents):
                return documents

        class Store:
            deleted = 0

            @classmethod
            def from_documents(cls, **kwargs):
                return cls()

            def similarity_search_with_score(self, question, k):
                if failure and question == "Missing fact?":
                    raise failure
                return [(doc, 0.1)]

            def delete_collection(self):
                Store.deleted += 1

        modules = {
            "qa_agent": SimpleNamespace(load_documents=lambda: [doc]),
            "langchain_chroma": SimpleNamespace(Chroma=Store),
            "langchain_ollama": SimpleNamespace(OllamaEmbeddings=lambda **kwargs: object()),
            "langchain_text_splitters": SimpleNamespace(RecursiveCharacterTextSplitter=Splitter),
        }
        with patch.object(runner, "ROOT", root), patch.dict("sys.modules", modules), \
             patch.object(runner, "model_identity", return_value={"digest": "offline-fixture"}), \
             patch.object(runner, "version", return_value="offline-fixture"), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = runner.main(["--cases", str(cases_path), "--chunk-sizes", "500",
                                "--ks", "1", "2"])
        directory = next((root / "verification" / "retrieval-runs").iterdir())
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        return code, directory, report, Store.deleted

    def test_complete_run_writes_dashboard_and_excludes_controls(self):
        code, directory, report, deleted = self.run_fixture()
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(deleted, 1)
        self.assertTrue((directory / "metrics.csv").is_file())
        self.assertTrue((directory / "retrieval-results.svg").is_file())
        rows = runner.summary_rows(report)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["evidence_cases"], 1)
        self.assertEqual(rows[0]["no_evidence_controls"], 1)

    def test_failed_search_preserves_partial_case_evidence(self):
        code, directory, report, deleted = self.run_fixture(RuntimeError("offline search failure"))
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(len(report["configurations"][0]["cases"]), 1)
        self.assertEqual(runner.summary_rows(report), [])
        self.assertEqual(deleted, 1)
        self.assertIn("failed", (directory / "summary.md").read_text())

    def test_csv_output_uses_lf_without_carriage_returns(self):
        _, directory, _, _ = self.run_fixture()
        raw = (directory / "metrics.csv").read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.endswith(b"\n"))

    def test_interruption_is_not_reported_as_a_complete_run(self):
        code, _, report, deleted = self.run_fixture(KeyboardInterrupt())
        self.assertEqual(code, 130)
        self.assertEqual(report["status"], "interrupted")
        self.assertEqual(len(report["configurations"][0]["cases"]), 1)
        self.assertEqual(deleted, 1)

    def test_corpus_rejects_extra_documents_and_wrong_page_content(self):
        dataset = {"expected_sources": ["docs/atlas.pdf"], "expected_document_units": 1,
                   "cases": [case()]}
        wrong = SimpleNamespace(page_content="The token expired.",
                                metadata={"source": "docs/atlas.pdf", "page": 1})
        with self.assertRaises(ValueError):
            runner.validate_corpus(dataset, [wrong])
        extra = SimpleNamespace(page_content="Other text",
                                metadata={"source": "docs/private.md"})
        with self.assertRaises(ValueError):
            runner.validate_corpus(dataset, [wrong, extra])

    def test_svg_escapes_labels(self):
        svg = runner.render_svg([], "failed", "<Offline & renderer test>")
        self.assertIn("&lt;Offline &amp; renderer test&gt;", svg)
        self.assertIn("No completed configurations", svg)


if __name__ == "__main__":
    unittest.main()
