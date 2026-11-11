"""Build a standalone evidence viewer from a saved guard or answer-evidence run."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from citation_guard import check_citations
from eval_retrieval import fingerprint
from multidoc_lab import format_excerpts

DEMO = ROOT / "verification/citation-guard-runs/20261111T011524Z-f2bde230/report.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def viewer_data(path):
    report = read_json(path)
    experiment = report["experiment"]
    if experiment == "citation_guard_saved_draft_evaluation":
        source = read_json(path.with_name("source-report.snapshot.json"))
        if fingerprint(source) != report["source_sha256"]:
            raise ValueError("The source snapshot does not match this report")
        from eval_citation_guard import validate_capture
        validated = validate_capture(source)
        contexts = {draft["record_id"]: draft for draft in validated}
        excerpts_by_id = {pair["record_id"]: pair["excerpts"] for pair in source["pairs"]}
    elif experiment != "answer_evidence":
        raise ValueError("Select a citation guard or answer-evidence report")

    review_path = path.with_name("assistant-review.json")
    reviews = {}
    if experiment == "citation_guard_saved_draft_evaluation" and review_path.is_file():
        review = read_json(review_path)
        if review["report_canonical_sha256"] != fingerprint(report):
            raise ValueError("The assistant review does not match this report")
        reviews = {row["record_id"]: row for row in review["records"]}

    records = []
    for row in report["records"]:
        if experiment == "answer_evidence":
            case = row["case"]
            question, excerpts = case["question"], case["excerpts"]
            review = row.get("review")
            review_kind = ("Authored example label" if report["mode"] == "authored_examples"
                           else "Recorded review")
        else:
            draft = contexts[row["record_id"]]
            question = draft["question"]
            excerpts = excerpts_by_id[draft["source_record_id"]]
            review = reviews.get(row["record_id"])
            review_kind = "Assistant source review"
        if fingerprint(format_excerpts(excerpts)) != row["context_sha256"]:
            raise ValueError("Excerpt context does not match its saved hash")
        guard = row["guard"]
        answer = guard.get("answer")
        labels = check_citations(answer or "", len(excerpts))["labels"]
        records.append({
            "id": row.get("record_id", row.get("id")), "question": question,
            "status": guard["status"], "reason": guard.get("reason"), "answer": answer,
            "attempts": guard["attempts"], "excerpts": excerpts, "labels": labels,
            "review": review, "review_kind": review_kind,
            "live_calls": row.get("live_calls"),
            "expectation": row.get("case", {}).get("review_notes"),
        })
    return {"run": report.get("run_id", path.stem), "mode": report["mode"],
            "status": report["status"], "records": records}


def render(data):
    template = (ROOT / "viewer/index.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=True).replace("<", r"\u003c")
    return template.replace("__EVIDENCE_JSON__", payload, 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="?", default=DEMO)
    parser.add_argument("--output", type=Path, default=Path("evidence-viewer.html"))
    args = parser.parse_args(argv)
    html = render(viewer_data(args.report))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print("Open in a browser:", args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
