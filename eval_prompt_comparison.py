"""Compare two prompts on frozen multi-document excerpts without retrieval calls."""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
from uuid import uuid4

import eval_retrieval as lab
from multidoc_lab import review_template
from prompt_lab import completed_review_records, prompts_for, run_pairs, select_records, validate_frozen

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "verification/multidoc-runs/20261110T222813Z-bc04d7e8"


def write_artifacts(directory, report):
    lab.write_json(directory / "report.json", report)
    variants = list(report.get("prompts", {"baseline": "", "revised": ""}))
    lines = ["# 🧪 Frozen-Context Prompt Comparison", "",
             f"Capture status: **{report['status']}**. Answer quality: **unreviewed**.", "",
             "All variant answers are freshly generated from the same frozen excerpts. No retrieval is performed.", "",
             "| Source record | Order | " + " | ".join(v.title() for v in variants) + " |",
             "| --- | --- | " + " | ".join("---" for _ in variants) + " |"]
    for pair in report["pairs"]:
        lines.append("| " + " | ".join([
            pair["record_id"], ", ".join(pair["call_order"]),
            *(pair["variants"].get(v, {}).get("status", "not started") for v in variants),
        ]) + " |")
    lines.extend(["", "Inspect report.json and review.json for completeness, attribution, citation support, and uncertainty. "
                  "Syntax checks and capture completion are not answer-quality scores. "
                  "Do not pool the direct-context conflict control into retrieved-context results.", ""])
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, default=SOURCE)
    parser.add_argument("--case-ids", nargs="+", help="Optional case IDs, not record IDs with :k suffixes")
    parser.add_argument("--include-refined", action="store_true", help="Compare baseline, revised, and the second refinement")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    source = args.source_run.resolve()
    def read(name):
        return json.loads((source / name).read_text(encoding="utf-8"))
    original, dataset, corpus = map(read, ["report.json", "cases.snapshot.json", "corpus.snapshot.json"])
    try:
        records = select_records(validate_frozen(original, dataset, corpus), args.case_ids)
    except ValueError as exc:
        parser.error(str(exc))
    prompts = prompts_for(original["settings"]["system_prompt"], include_refined=args.include_refined)
    label = "three-prompt contexts" if args.include_refined else "pairs"
    print(f"Validated {len(original['records'])} frozen source records; selected {len(records)} {label} ({len(prompts)*len(records)} new chat calls).")
    if args.validate_only:
        print("Validation only: no chat, embedding, retrieval, or index calls.")
        return 0
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = ROOT / "verification/prompt-runs" / run_id
    report = {
        "schema_version": 1, "experiment": "frozen_context_prompt_comparison",
        "run_id": run_id, "status": "running", "pairs": [],
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_id": original["run_id"], "source_report_sha256": lab.fingerprint(original),
        "dataset_sha256": lab.fingerprint(dataset), "corpus_sha256": lab.fingerprint(corpus),
        "python": platform.python_version(), "platform": platform.platform(),
        "settings": {"selected_record_ids": [r["record_id"] for r in records],
                     "model": original["settings"]["chat_model"], "temperature": 0, "reasoning": False,
                     "ollama_url": "http://localhost:11434", "repeats": 1,
                     "variants": list(prompts), "include_refined": args.include_refined,
                     "order": ("cyclic baseline/revised/refined by selected record" if args.include_refined
                               else "alternating baseline-first and revised-first by selected record"),
                     "retrieval_performed": False},
        "prompts": prompts,
        "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                        for name in ["eval_prompt_comparison.py", "prompt_lab.py", "qa_agent.py",
                                     "multidoc_lab.py", "retrieval_metrics.py", "eval_retrieval.py"]},
    }
    try:
        report["git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        report["git_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip())
    except (OSError, subprocess.CalledProcessError):
        report["git_commit"] = None
        report["git_dirty"] = None
    directory.mkdir(parents=True, exist_ok=False)
    for name, value in [("source-report.snapshot.json", original), ("cases.snapshot.json", dataset),
                        ("corpus.snapshot.json", corpus), ("prompts.json", prompts)]:
        lab.write_json(directory / name, value)

    def checkpoint(pairs):
        report["pairs"] = pairs
        write_artifacts(directory, report)

    checkpoint([])
    print("Run directory:", directory, flush=True)
    exit_code = 0
    try:
        import qa_agent as qa
        if qa.CHAT_MODEL != report["settings"]["model"]:
            raise ValueError("Use the saved chat model name for this comparison")
        report["model_identity"] = lab.model_identity(report["settings"]["ollama_url"], qa.CHAT_MODEL)
        saved_identity = original.get("model_identities", {}).get(qa.CHAT_MODEL, {})
        report["model_digest_matches_source_capture"] = saved_identity.get("digest") == report["model_identity"]["digest"]
        report["packages"] = {name: version(name) for name in ["langchain", "langchain-core", "langchain-ollama"]}
        agents = {name: qa.build_agent(system_prompt=prompt) for name, prompt in prompts.items()}

        def generate(variant, question, context):
            result = agents[variant].invoke({"messages": [{"role": "user", "content": question}]},
                                            context={"excerpts": context})
            return result["messages"][-1].content

        run_pairs(records, prompts, generate, checkpoint)
        final_identity = lab.model_identity(report["settings"]["ollama_url"], qa.CHAT_MODEL)
        if final_identity["digest"] != report["model_identity"]["digest"]:
            raise RuntimeError("Chat model identity changed during comparison")
        report["status"] = "complete"
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        exit_code = 130
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        exit_code = 1
    finally:
        report["ended_utc"] = datetime.now(timezone.utc).isoformat()
        write_artifacts(directory, report)
        review = review_template(completed_review_records(report["pairs"]))
        review["review_type"] = "human_review_pending"
        lab.write_json(directory / "review.json", review)
    print("Capture status:", report["status"])
    if "error" in report:
        print(report["error"])
    print("Dashboard:", directory / "summary.md")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

