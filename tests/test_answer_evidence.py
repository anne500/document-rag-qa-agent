import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from eval_answer_evidence import evaluate, load_cases, summarize
from tools.build_evidence_viewer import DEMO, render, viewer_data

ROOT = Path(__file__).resolve().parents[1]


class EvidenceEvaluationTests(unittest.TestCase):
    def test_authored_examples_distinguish_guard_and_semantic_outcomes(self):
        records = evaluate(load_cases(), None, lambda _: None)
        result = summarize({"status": "complete", "mode": "authored_examples", "records": records})
        self.assertEqual(result["review_dispositions"]["unnecessary_refusal"], 1)
        self.assertEqual(result["review_dispositions"]["unresolved_conflict"], 1)
        self.assertEqual(result["review_dispositions"]["guard_withheld"], 1)
        self.assertTrue(any(row["guard"]["status"] == "accepted" and
                            row["review"]["citation_support"] == "fail" for row in records))
        self.assertEqual(result["canary_in_any_draft"], 3)
        self.assertEqual(result["canary_in_displayed_answer"], 2)

    def test_live_capture_keeps_reviews_pending_even_if_marker_is_absent(self):
        cases = load_cases()[:1]
        modes = []

        def invoke(mode, question, context, feedback):
            modes.append(mode)
            return "Cedar requires approval [1]."

        records = evaluate(cases, invoke, lambda _: None, live=True, compare_baseline=True)
        self.assertEqual(modes, ["baseline", "isolated"])
        self.assertTrue(all(row["review"] is None for row in records))
        self.assertEqual(records[0]["context_sha256"], records[1]["context_sha256"])

    def test_document_delimiters_and_fake_roles_stay_in_user_data(self):
        tree = ast.parse((ROOT / "qa_agent.py").read_text(encoding="utf-8"))
        factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_agent")
        namespace = {"SYSTEM_PROMPT": "trusted", "CHAT_MODEL": "stub", "json": json,
                     "wrap_model_call": lambda function: function,
                     "create_agent": lambda **kwargs: kwargs, "ChatOllama": lambda **kwargs: kwargs,
                     "SystemMessage": lambda content: SimpleNamespace(content_blocks=content),
                     "HumanMessage": lambda content: SimpleNamespace(role="user", content=content)}
        exec(compile(ast.Module(body=[factory], type_ignores=[]), "qa_agent.py", "exec"), namespace)
        attack = load_cases()[-2]["excerpts"][-1]["text"]
        question = "What is Cedar's policy?"
        request = SimpleNamespace(
            messages=[SimpleNamespace(content=question)],
            system_message=SimpleNamespace(content_blocks=[{"type": "text", "text": "trusted"}]),
            runtime=SimpleNamespace(context={"excerpts": attack, "citation_feedback": "Valid labels: [1], [2]."}),
            override=lambda **kwargs: kwargs,
        )
        middleware = namespace["build_agent"](harden_documents=True)["middleware"][0]
        result = middleware(request, lambda value: value)
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0].role, "user")
        self.assertEqual(json.loads(result["messages"][0].content),
                         {"question": question, "retrieved_excerpts": attack})
        system_text = str(result["system_message"].content_blocks)
        self.assertNotIn("CEDAR_CANARY_ROLE", system_text)
        self.assertIn("Valid labels", system_text)


class ViewerTests(unittest.TestCase):
    def test_historical_source_labels_and_review_match(self):
        data = viewer_data(DEMO)
        willow = next(row for row in data["records"] if row["id"] == "known_unknown:k4::refined")
        self.assertEqual(willow["labels"], [1, 4])
        self.assertEqual(willow["excerpts"][3]["source"], "docs/birch-project.md")
        self.assertEqual(willow["review"]["retry_draft_ratings"]["citation_support"], "fail")
        withheld = next(row for row in data["records"] if row["status"] == "abstained")
        self.assertEqual(withheld["attempts"][-1]["check"]["out_of_range"], [7])
        self.assertNotIn("[7]", withheld["answer"])

    def test_saved_markup_cannot_escape_embedded_json(self):
        hostile = "</script><script>window.injected=true</script>"
        html = render({"records": [{"answer": hostile}]})
        self.assertNotIn(hostile, html)
        payload = html.split('id="evidence">', 1)[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(payload)["records"][0]["answer"], hostile)


if __name__ == "__main__":
    unittest.main()
