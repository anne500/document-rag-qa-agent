"""Evaluate citation support, abstention, and document instruction handling."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from citation_guard import guarded_answer
from eval_retrieval import fingerprint, model_identity, write_json
from multidoc_lab import format_excerpts

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "evaluation/answer-evidence-cases.json"
DISPOSITIONS = {
    "answered", "missing_evidence", "partial_answer", "unresolved_conflict",
    "unnecessary_refusal", "unsupported_answer", "guard_withheld", "generation_failed",
}


def load_cases(path=CASES):
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    ids = {case["id"]: case for case in cases}
    if len(ids) != len(cases) or not cases:
        raise ValueError("Expected unique evaluation cases")
    for case in cases:
        if case["expected_disposition"] not in DISPOSITIONS:
            raise ValueError(f"Invalid disposition in {case['id']}")
        excerpts = case["excerpts"]
        for fact in case["expected_claims"]:
            if not fact["labels"] or any(type(n) is not int or not 1 <= n <= len(excerpts) for n in fact["labels"]):
                raise ValueError(f"Invalid evidence labels in {case['id']}")
        if "control_id" in case:
            control = ids[case["control_id"]]
            if (case["question"] != control["question"] or
                    case["expected_claims"] != control["expected_claims"] or
                    excerpts[:-1] != control["excerpts"][:-1] or
                    excerpts[-1]["source"] != control["excerpts"][-1]["source"] or
                    not excerpts[-1]["text"].startswith(control["excerpts"][-1]["text"]) or
                    case["canary"] not in excerpts[-1]["text"]):
                raise ValueError(f"Attack case must preserve the control evidence in {case['id']}")
    return cases


def evaluate(cases, invoke, checkpoint, *, live=False, compare_baseline=False):
    records = []
    for case in cases:
        context = format_excerpts(case["excerpts"])
        if live:
            modes = ("baseline", "isolated") if compare_baseline else ("isolated",)
            inputs = [(mode, None) for mode in modes]
        else:
            inputs = [("authored_example", example) for example in case["examples"]]
        for number, (mode, example) in enumerate(inputs, 1):
            row = {
                "id": f"{case['id']}::{mode}::{number}",
                "case": case, "mode": mode,
                "context_sha256": fingerprint(context),
                "review": None if live else example["review"],
            }
            records.append(row)

            def generate(question, evidence, feedback):
                if live:
                    return invoke(mode, question, evidence, feedback)
                return example["draft"]

            def update(result):
                row["guard"] = result
                checkpoint(records)

            result = guarded_answer(
                case["question"], context, len(case["excerpts"]),
                generate, on_update=update,
            )
            marker = case.get("canary")
            row["canary_in_displayed_answer"] = bool(marker and marker.casefold() in result["answer"].casefold())
            row["canary_in_any_draft"] = bool(marker and any(
                marker.casefold() in attempt.get("draft", "").casefold()
                for attempt in result["attempts"]
            ))
            checkpoint(records)
    return records


def summarize(report):
    records = report["records"]
    reviews = [row["review"] for row in records if row["review"] is not None]
    return {
        "status": report["status"],
        "mode": report["mode"],
        "cases": len({row["case"]["id"] for row in records}),
        "records": len(records),
        "guard_outcomes": dict(Counter(row["guard"]["status"] for row in records)),
        "reviewed": len(reviews),
        "review_dispositions": dict(Counter(r["disposition"] for r in reviews)),
        "review_citation_support": dict(Counter(r["citation_support"] for r in reviews)),
        "canary_in_any_draft": sum(row.get("canary_in_any_draft", False) for row in records),
        "canary_in_displayed_answer": sum(row.get("canary_in_displayed_answer", False) for row in records),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Generate answers with local Ollama")
    parser.add_argument("--compare-baseline", action="store_true", help="Also run the original prompt format in live mode")
    parser.add_argument("--output", type=Path, help="Save the report as a new JSON file")
    parser.add_argument("--summarize", type=Path, help="Summarize a saved report after filling in review fields")
    args = parser.parse_args(argv)
    if args.summarize:
        print(json.dumps(summarize(json.loads(args.summarize.read_text(encoding="utf-8"))), indent=2))
        return 0
    if args.compare_baseline and not args.live:
        parser.error("--compare-baseline requires --live")
    cases = load_cases()
    output = args.output
    if args.live and output is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = ROOT / f"verification/answer-evidence-runs/{stamp}-{uuid4().hex[:8]}.json"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            handle.write("{}\n")

    report = {"experiment": "answer_evidence", "schema_version": 1, "status": "running",
              "mode": "live_ollama" if args.live else "authored_examples",
              "cases_sha256": fingerprint(cases), "records": []}

    def checkpoint(records):
        report["records"] = records
        if output is not None:
            write_json(output, report)

    invoke = None
    exit_code = 0
    try:
        if args.live:
            from qa_agent import CHAT_MODEL, build_agent
            report["model_identity"] = model_identity("http://localhost:11434", CHAT_MODEL)
            agents = {"isolated": build_agent(harden_documents=True)}
            if args.compare_baseline:
                agents["baseline"] = build_agent()

            def invoke(mode, question, context, feedback):
                reply = agents[mode].invoke(
                    {"messages": [{"role": "user", "content": question}]},
                    context={"excerpts": context, "citation_feedback": feedback},
                )
                return reply["messages"][-1].content

        evaluate(cases, invoke, checkpoint, live=args.live, compare_baseline=args.compare_baseline)
        if args.live:
            after = model_identity("http://localhost:11434", CHAT_MODEL)
            if after["digest"] != report["model_identity"]["digest"]:
                raise RuntimeError("Model identity changed during evaluation")
        report["status"] = "complete"
        if any(row["guard"]["status"] == "generation_failed" for row in report["records"]):
            report["status"] = "completed_with_generation_errors"
            exit_code = 1
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        exit_code = 130
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        print(report["error"])
        exit_code = 1
    finally:
        checkpoint(report["records"])
    print(json.dumps(summarize(report), indent=2))
    if output is not None:
        print("Report:", output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
