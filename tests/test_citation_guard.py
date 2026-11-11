import argparse
import ast
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from citation_guard import check_citations, guarded_answer, WITHHELD
from eval_citation_guard import replay, validate_capture

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "verification/prompt-runs/20261111T001306Z-98deeb8f/report.json"


class CitationGuardTests(unittest.TestCase):
    def test_numeric_singles_groups_and_bounds(self):
        result = check_citations("A [1, 2]. B [2][7]. C [0].", 2)
        self.assertFalse(result["valid"])
        self.assertEqual(result["out_of_range"], [0, 7])
        self.assertTrue(check_citations("A [ 1 , 2 ].", 2)["valid"])

    def test_malformed_and_unfinished_numeric_spans(self):
        for span in ["[1-2]", "[1;2]", "[1,]", "[-1]", "[1a]", "[7", "[7\nnext", "[" + "9" * 5000 + "]"]:
            with self.subTest(span=span[:30]):
                self.assertFalse(check_citations(span, 2)["valid"])

    def test_valid_labels_and_no_labels_do_not_establish_support(self):
        self.assertTrue(check_citations("Invented fact [1].", 2)["valid"])
        self.assertTrue(check_citations("Unsupported answer with no references.", 2)["valid"])
        self.assertNotIn("factual_support", check_citations("Fact [1].", 2))

    def test_valid_first_draft_is_returned_unchanged_once(self):
        calls = []
        def generate(*args):
            calls.append(args)
            return "Exact answer [1]."
        result = guarded_answer("Q", "context", 2, generate)
        self.assertEqual(result["answer"], "Exact answer [1].")
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(calls, [("Q", "context", None)])

    def test_repair_uses_identical_question_context_and_bounded_feedback(self):
        calls = []
        def generate(q, context, feedback):
            calls.append((q, context, feedback))
            return "Invalid [7]." if feedback is None else "Fresh answer [1]."
        result = guarded_answer("Q", "frozen", 2, generate)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][:2], calls[1][:2])
        self.assertIn("[1], [2]", calls[1][2])
        self.assertNotIn("Invalid [7]", calls[1][2])
        self.assertEqual(result["answer"], "Fresh answer [1].")
        self.assertEqual(result["attempts"][0]["draft"], "Invalid [7].")

    def test_repeated_invalid_answer_is_withheld_without_editing_drafts(self):
        result = guarded_answer("Q", "C", 2, lambda *a: "Bad [7].")
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["answer"], WITHHELD)
        self.assertEqual([a["draft"] for a in result["attempts"]], ["Bad [7].", "Bad [7]."])

    def test_empty_context_does_not_call_model(self):
        result = guarded_answer("Q", "", 0, lambda *a: self.fail("No model call expected"))
        self.assertEqual(result["reason"], "no_excerpts")
        self.assertEqual(result["attempts"], [])

    def test_generation_error_is_distinct_and_checkpointed(self):
        saved = []
        def fail(*args):
            raise RuntimeError("offline")
        result = guarded_answer("Q", "C", 2, fail, on_update=lambda r: saved.append(copy.deepcopy(r)))
        self.assertEqual(result["status"], "generation_failed")
        self.assertEqual(len(result["attempts"]), 1)
        self.assertEqual(saved[-1]["status"], "generation_failed")

    def test_interruption_preserves_rejected_draft_and_retry_status(self):
        saved = []
        def generate(q, c, feedback):
            if feedback:
                raise KeyboardInterrupt()
            return "Bad [7]."
        with self.assertRaises(KeyboardInterrupt):
            guarded_answer("Q", "C", 2, generate, on_update=lambda r: saved.append(copy.deepcopy(r)))
        self.assertEqual(saved[-1]["status"], "interrupted")
        self.assertEqual(saved[-1]["attempts"][0]["draft"], "Bad [7].")

    def test_retry_bounds_and_empty_answer(self):
        for retries in [-1, 2, True]:
            with self.assertRaises(ValueError):
                guarded_answer("Q", "C", 2, lambda *a: "A [1]", max_retries=retries)
        result = guarded_answer("Q", "C", 2, lambda *a: "", max_retries=0)
        self.assertEqual(len(result["attempts"]), 1)
        self.assertEqual(result["status"], "abstained")

    def test_published_39_drafts_replay_preserves_two_failures(self):
        drafts = validate_capture(json.loads(CAPTURE.read_text(encoding="utf-8")))
        self.assertEqual(len(drafts), 39)
        self.assertEqual(sum(not d["initial_check"]["valid"] for d in drafts), 2)
        with redirect_stdout(io.StringIO()):
            records = replay(drafts, None, lambda r: None)
        self.assertEqual(sum(r["guard"]["status"] == "abstained" for r in records), 2)
        self.assertEqual(sum(r["live_calls"] for r in records), 0)

    def test_only_invalid_saved_drafts_invoke_repair(self):
        drafts = validate_capture(json.loads(CAPTURE.read_text(encoding="utf-8")))
        calls = []
        def repair(*args):
            calls.append(args)
            return "Stub repaired answer [1]."
        with redirect_stdout(io.StringIO()):
            records = replay(drafts, repair, lambda r: None)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(r["guard"]["status"] == "accepted" for r in records))
        self.assertEqual(sum(r["live_calls"] for r in records), 2)

    def test_capture_validation_rejects_missing_variant_and_changed_context(self):
        source = json.loads(CAPTURE.read_text(encoding="utf-8"))
        changed = copy.deepcopy(source)
        changed["pairs"][0]["context_text"] += " altered"
        with self.assertRaises(ValueError):
            validate_capture(changed)
        del source["pairs"][0]["variants"]["refined"]
        with self.assertRaises(ValueError):
            validate_capture(source)

    def execute_cli(self, answers, guard):
        tree = ast.parse((ROOT / "qa_agent.py").read_text(encoding="utf-8"))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        calls = []
        answers = iter(answers)
        def invoke(payload, context):
            calls.append((copy.deepcopy(payload), copy.deepcopy(context)))
            return {"messages": [SimpleNamespace(content=next(answers))]}
        documents = [SimpleNamespace(metadata={"source": "one.md"}, page_content="evidence")]
        namespace = {"argparse": argparse, "json": json, "perf_counter": lambda: 0,
                     "get_vectorstore": lambda: SimpleNamespace(similarity_search=lambda *a, **k: documents),
                     "build_agent": lambda: SimpleNamespace(invoke=invoke), "RETRIEVAL_K": 2,
                     "source_label": lambda d: d.metadata["source"], "guarded_answer": guarded_answer}
        exec(compile(ast.Module(body=[main], type_ignores=[]), "qa_agent.py", "exec"), namespace)
        output = io.StringIO()
        with patch("builtins.input", side_effect=["Question", "exit"]), redirect_stdout(output):
            namespace["main"](["--citation-guard"] if guard else [])
        return output.getvalue(), calls

    def test_interactive_guard_suppresses_bad_draft_and_displays_repair(self):
        output, calls = self.execute_cli(["REJECTED_DRAFT [7].", "Supported [1]."], True)
        self.assertNotIn("REJECTED_DRAFT", output)
        self.assertIn("Answer: Supported [1].", output)
        self.assertEqual(calls[0][0], calls[1][0])
        self.assertEqual(calls[0][1]["excerpts"], calls[1][1]["excerpts"])
        self.assertIsNone(calls[0][1]["citation_feedback"])
        self.assertTrue(calls[1][1]["citation_feedback"])

    def test_interactive_guard_withholds_after_one_retry(self):
        output, calls = self.execute_cli(["REJECTED_DRAFT [7].", "REJECTED_DRAFT [7]."], True)
        self.assertNotIn("REJECTED_DRAFT", output)
        self.assertIn(WITHHELD, output)
        self.assertEqual(len(calls), 2)

    def test_default_interactive_mode_is_preserved(self):
        output, calls = self.execute_cli(["Original behavior [7]."], False)
        self.assertIn("Original behavior [7].", output)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("citation_feedback", calls[0][1])

    def test_retry_feedback_is_separate_from_unchanged_excerpts(self):
        tree = ast.parse((ROOT / "qa_agent.py").read_text(encoding="utf-8"))
        factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_agent")
        namespace = {"SYSTEM_PROMPT": "baseline", "CHAT_MODEL": "stub",
                     "wrap_model_call": lambda function: function,
                     "create_agent": lambda **kwargs: kwargs, "ChatOllama": lambda **kwargs: kwargs,
                     "SystemMessage": lambda content: SimpleNamespace(content_blocks=content)}
        exec(compile(ast.Module(body=[factory], type_ignores=[]), "qa_agent.py", "exec"), namespace)
        middleware = namespace["build_agent"]()["middleware"][0]
        original_blocks = [{"type": "text", "text": "baseline"}]
        context = {"excerpts": "frozen evidence"}
        request = SimpleNamespace(messages=[SimpleNamespace(content="Original question")],
                                  runtime=SimpleNamespace(context=context),
                                  system_message=SimpleNamespace(content_blocks=original_blocks),
                                  override=lambda **kwargs: kwargs)
        initial = middleware(request, lambda value: value)["system_message"].content_blocks
        context["citation_feedback"] = "Trusted retry instruction"
        retried = middleware(request, lambda value: value)["system_message"].content_blocks
        self.assertEqual(initial, retried[:-1])
        self.assertEqual(retried[-1]["text"], "Trusted retry instruction")
        self.assertIn("frozen evidence", retried[1]["text"])
        self.assertEqual(original_blocks, [{"type": "text", "text": "baseline"}])


if __name__ == "__main__":
    unittest.main()
