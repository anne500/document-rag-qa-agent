import copy
import json
from pathlib import Path
import tempfile
import unittest

from eval_multidoc import run_cases, write_dashboard
from multidoc_lab import inspect_answer, review_template, review_summary, validate_cases


class MultiDocumentTests(unittest.TestCase):
    def setUp(self):
        self.evidence = [
            {"source": f"doc-{i}.md", "page": None, "text": f"fact {i}"}
            for i in range(1, 4)
        ]
        self.case = {"id": "three", "suite": "retrieved", "question": "Compare?",
                     "expected_claims": ["Three facts"], "required_evidence": [
                         {"id": str(i), "source": x["source"], "page": None, "contains": [x["text"]]}
                         for i, x in enumerate(self.evidence)
                     ]}

    def test_two_chunks_cannot_cover_three_units(self):
        result = inspect_answer(self.case, self.evidence[:2], "All facts [1] [2].")
        self.assertEqual(result["retrieval_marker_scores"]["coverage_at_k"], 2/3)
        self.assertEqual(result["retrieval_marker_scores"]["complete_at_k"], 0)
        self.assertNotIn("answer_accuracy", result)

    def test_valid_citation_label_does_not_score_claim_support(self):
        result = inspect_answer(self.case, self.evidence, "Invented fact [1].")
        self.assertEqual(result["citation_syntax_only"]["out_of_range"], [])
        review = review_template([{"record_id": "one", "status": "complete"}])
        summary = review_summary(review, ["one"])
        self.assertIsNone(summary["citation_support"]["pass_rate_reviewed_only"])
        self.assertEqual(summary["citation_support"]["unreviewed"], 1)

    def test_invalid_citation_labels_detected(self):
        result = inspect_answer(self.case, self.evidence, "Claim [0] [4] [2].")
        self.assertEqual(result["citation_syntax_only"]["out_of_range"], [0, 4])

    def test_pdf_page_mismatch_is_not_coverage(self):
        case = copy.deepcopy(self.case)
        case["required_evidence"][0]["page"] = 2
        result = inspect_answer(case, self.evidence, "Fact [1].")
        self.assertNotIn("0", result["retrieval_marker_scores"]["matched_groups"])

    def test_k_settings_share_one_candidate_list(self):
        calls = []
        def retrieve(q, k):
            calls.append(k)
            return self.evidence, {"policy": "fake"}
        records = run_cases([self.case], [2, 4], retrieve, lambda q, e: "Fact [1].", lambda r: None)
        self.assertEqual(calls, [4])
        self.assertEqual([len(r["excerpts"]) for r in records], [2, 3])
        self.assertEqual([r["retrieval_marker_scores"]["complete_at_k"] for r in records], [0, 1])

    def test_context_control_bypasses_retrieval_and_runs_once(self):
        case = {**self.case, "suite": "context_control", "context": self.evidence}
        def forbidden(q, k):
            raise AssertionError("Context controls must not retrieve")
        records = run_cases([case], [2, 4], forbidden, lambda q, e: "Conflicting [1] [2].", lambda r: None)
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0]["k"])
        self.assertFalse(records[0]["trace"]["retrieval_performed"])

    def test_generation_failure_preserves_prior_answer_and_failed_evidence(self):
        saved = []
        def generate(q, e):
            if "[3]" in e:
                raise RuntimeError("model unavailable")
            return "Fact [1]."
        with self.assertRaises(RuntimeError):
            run_cases([self.case], [2, 4], lambda q, k: (self.evidence, {}), generate,
                      lambda r: saved.append(copy.deepcopy(r)))
        self.assertEqual([r["status"] for r in saved[-1]], ["complete", "failed"])
        self.assertEqual(len(saved[-1][1]["excerpts"]), 3)
        self.assertEqual(len(review_template(saved[-1])["records"]), 1)

    def test_interruption_is_checkpointed(self):
        saved = []
        def interrupt(q, e):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            run_cases([self.case], [2], lambda q, k: (self.evidence, {}), interrupt,
                      lambda r: saved.append(copy.deepcopy(r)))
        self.assertEqual(saved[-1][0]["status"], "interrupted")

    def test_review_requires_identity_notes_and_exact_record_ids(self):
        review = review_template([{"record_id": "one", "status": "complete"}])
        review["records"][0]["ratings"]["attribution"] = "pass"
        with self.assertRaises(ValueError):
            review_summary(review, ["one"])
        review["records"][0].update(reviewer="Reviewer", notes="Claim belongs to doc-1, not doc-2.")
        self.assertEqual(review_summary(review, ["one"])["attribution"]["passed"], 1)
        with self.assertRaises(ValueError):
            review_summary(review, ["other"])
        review["records"].append(copy.deepcopy(review["records"][0]))
        with self.assertRaises(ValueError):
            review_summary(review, ["one"])

    def test_validation_rejects_missing_markers_and_duplicate_cases(self):
        validate_cases({"schema_version": 1, "cases": [self.case]}, self.evidence)
        with self.assertRaises(ValueError):
            validate_cases({"schema_version": 1, "cases": [self.case]}, self.evidence[:2])
        with self.assertRaises(ValueError):
            validate_cases({"schema_version": 1, "cases": [self.case, self.case]}, self.evidence)

    def test_dashboard_does_not_label_capture_as_answer_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_dashboard(directory, {"status": "failed", "records": []})
            self.assertIn("**failed**", (directory / "summary.md").read_text())
            self.assertIn("**pending**", (directory / "summary.md").read_text())
            self.assertEqual(json.loads((directory / "report.json").read_text())["status"], "failed")


if __name__ == "__main__":
    unittest.main()
