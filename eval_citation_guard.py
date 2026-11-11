"""Replay saved drafts through the guard; optionally repair only invalid drafts live."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from uuid import uuid4

from citation_guard import check_citations, guarded_answer
import eval_retrieval as lab
from multidoc_lab import format_excerpts

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "verification/prompt-runs/20261111T001306Z-98deeb8f"


def validate_capture(source):
    if source.get("status") != "complete" or not source.get("pairs"):
        raise ValueError("Use a complete prompt capture")
    seen = set()
    drafts = []
    if [p["record_id"] for p in source["pairs"]] != source["settings"]["selected_record_ids"]:
        raise ValueError("Selected context inventory mismatch")
    for pair in source["pairs"]:
        if pair["record_id"] in seen or pair["status"] != "complete":
            raise ValueError("Duplicate or incomplete context")
        seen.add(pair["record_id"])
        if set(pair["variants"]) != set(source["prompts"]):
            raise ValueError("Missing or unexpected prompt variant")
        context = format_excerpts(pair["excerpts"])
        if context != pair["context_text"] or lab.fingerprint(context) != pair["context_sha256"]:
            raise ValueError("Context text/hash mismatch")
        for variant, item in pair["variants"].items():
            if (item["status"] != "complete" or item["context_sha256"] != pair["context_sha256"]
                    or lab.fingerprint(source["prompts"][variant]) != item["prompt_sha256"]):
                raise ValueError("Incomplete variant or prompt/context mismatch")
            check = check_citations(item["answer"], len(pair["excerpts"]))
            drafts.append({"record_id": pair["record_id"] + "::" + variant,
                           "source_record_id": pair["record_id"], "variant": variant,
                           "suite": pair["suite"], "question": pair["question"],
                           "context": context, "excerpt_count": len(pair["excerpts"]),
                           "draft": item["answer"], "initial_check": check})
    return drafts


def replay(drafts, repair, checkpoint):
    records = []
    for draft in drafts:
        record = {"record_id": draft["record_id"], "suite": draft["suite"],
                  "initial_check": draft["initial_check"], "live_calls": 0,
                  "context_sha256": lab.fingerprint(draft["context"]), "question": draft["question"]}
        records.append(record)
        calls = 0

        def generate(question, context, feedback):
            nonlocal calls
            calls += 1
            if calls == 1 or repair is None:
                return draft["draft"]
            record["live_calls"] += 1
            return repair(draft["variant"], question, context, feedback)

        def update(result):
            record["guard"] = result
            checkpoint(records)

        guarded_answer(draft["question"], draft["context"], draft["excerpt_count"], generate, on_update=update)
        print(draft["record_id"], "=>", record["guard"]["status"], flush=True)
    return records


def save(directory, report):
    lab.write_json(directory / "report.json", report)
    lines = ["# 🔗 Citation Guard Evaluation", "", f"Run status: **{report['status']}**.", "",
             f"Mode: **{report['mode']}**. Numeric validation does not establish factual support.", "",
             "| Saved answer | Initial numeric check | Final guard status | Live calls |",
             "| --- | --- | --- | --- |"]
    for row in report["records"]:
        lines.append(f"| {row['record_id']} | {'pass' if row['initial_check']['valid'] else 'fail'} | "
                     f"{row['guard']['status']} | {row['live_calls']} |")
    lines += ["", "First drafts are replayed from the frozen capture. In offline mode the same invalid draft "
              "is replayed on retry to test withholding, not model repair. In live-repair mode only rejected "
              "drafts receive a new model call. Review repaired claims separately. No general answer-accuracy "
              "or semantic-abstention score is computed.", ""]
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, default=SOURCE)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--repair-invalid", action="store_true", help="One live repair call for each invalid saved draft")
    args = parser.parse_args(argv)
    source = json.loads((args.source_run / "report.json").read_text(encoding="utf-8"))
    drafts = validate_capture(source)
    invalid = sum(not row["initial_check"]["valid"] for row in drafts)
    print(f"Validated {len(drafts)} saved drafts; {invalid} fail numeric-citation validation.")
    if args.validate_only:
        print("Validation only: no model, retrieval, embedding, or index calls.")
        return 0
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = ROOT / "verification/citation-guard-runs" / run_id
    report = {"schema_version": 1, "experiment": "citation_guard_saved_draft_evaluation",
              "run_id": run_id, "status": "running", "records": [],
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "platform": platform.platform(),
              "mode": "saved_draft_plus_live_repair" if args.repair_invalid else "offline_repeat_draft_replay",
              "source_run_id": source["run_id"], "source_sha256": lab.fingerprint(source),
              "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ["citation_guard.py", "eval_citation_guard.py", "qa_agent.py"]}}
    try:
        report["git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        report["git_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip())
    except (OSError, subprocess.CalledProcessError):
        report["git_commit"] = None
        report["git_dirty"] = None
    directory.mkdir(parents=True, exist_ok=False)
    lab.write_json(directory / "source-report.snapshot.json", source)
    save(directory, report)
    print("Run directory:", directory, flush=True)

    def checkpoint(records):
        report["records"] = records
        save(directory, report)

    exit_code = 0
    try:
        repair = None
        if args.repair_invalid and invalid:
            import qa_agent as qa
            from importlib.metadata import version
            if qa.CHAT_MODEL != source["settings"]["model"]:
                raise ValueError("Use the source capture's chat model")
            report["model_identity"] = lab.model_identity("http://localhost:11434", qa.CHAT_MODEL)
            report["model_digest_matches_source_capture"] = report["model_identity"]["digest"] == source["model_identity"]["digest"]
            report["packages"] = {name: version(name) for name in ["langchain", "langchain-core", "langchain-ollama"]}
            agents = {v: qa.build_agent(system_prompt=source["prompts"][v])
                      for v in {d["variant"] for d in drafts if not d["initial_check"]["valid"]}}

            def repair(variant, question, context, feedback):
                response = agents[variant].invoke(
                    {"messages": [{"role": "user", "content": question}]},
                    context={"excerpts": context, "citation_feedback": feedback},
                )
                return response["messages"][-1].content

        replay(drafts, repair, checkpoint)
        if "model_identity" in report:
            if lab.model_identity("http://localhost:11434", source["settings"]["model"])["digest"] != report["model_identity"]["digest"]:
                raise RuntimeError("Model identity changed during repair")
        report["status"] = ("completed_with_generation_errors" if any(
            row["guard"]["status"] == "generation_failed" for row in report["records"]
        ) else "complete")
        exit_code = int(report["status"] != "complete")
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        exit_code = 130
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        exit_code = 1
    finally:
        report["ended_utc"] = datetime.now(timezone.utc).isoformat()
        save(directory, report)
    print("Evaluation status:", report["status"])
    if "error" in report:
        print(report["error"])
    print("Dashboard:", directory / "summary.md")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
