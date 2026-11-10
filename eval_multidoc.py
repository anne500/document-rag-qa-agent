"""Capture multi-document answers, evidence, and a separate human-review worksheet."""

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import eval_retrieval as lab
from multidoc_lab import format_excerpts, inspect_answer, review_template, review_summary, validate_cases

ROOT = Path(__file__).resolve().parent


def load_corpus():
    from pypdf import PdfReader
    corpus = []
    for path in sorted((ROOT / "docs").rglob("*")):
        if not path.is_file():
            continue
        source = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8-sig")
            if text.strip():
                corpus.append({"source": source, "page": None, "text": text})
        elif path.suffix.lower() == ".pdf":
            for page, item in enumerate(PdfReader(path).pages, 1):
                text = item.extract_text() or ""
                if text.strip():
                    corpus.append({"source": source, "page": page, "text": text})
    return corpus


def run_cases(cases, ks, retrieve, generate, checkpoint):
    """Inject backends for offline failure/coverage tests; checkpoint every answer."""
    records = []
    for case in cases:
        settings = ks if case["suite"] == "retrieved" else [None]
        ranked = trace = None
        for k in settings:
            record = {"record_id": case["id"] + (f":k{k}" if k else ":control"),
                      "case_id": case["id"], "suite": case["suite"], "k": k,
                      "question": case["question"], "status": "running"}
            records.append(record)
            checkpoint(records)
            started = perf_counter()
            try:
                if case["suite"] == "context_control":
                    selected = case["context"]
                    trace = {"policy": "direct_context_control", "retrieval_performed": False}
                else:
                    if ranked is None:
                        ranked, trace = retrieve(case["question"], max(ks))
                    selected = ranked[:k]
                record.update({"excerpts": selected, "trace": trace})
                record["answer"] = generate(case["question"], format_excerpts(selected))
                record.update(inspect_answer(case, selected, record["answer"]))
                record["status"] = "complete"
            except BaseException as exc:
                record["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
                record["error"] = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                record["elapsed_seconds"] = perf_counter() - started
                checkpoint(records)
            print(record["record_id"], "captured; human review pending", flush=True)
    return records


def write_dashboard(directory, report):
    lab.write_json(directory / "report.json", report)
    lines = ["# 📚 Multi-Document Answer Capture", "",
             f"Capture status: **{report['status']}**. Answer-quality review: **pending**.", "",
             "| Case | Suite | k | Status | Marker coverage | Citation labels outside excerpts |",
             "| --- | --- | --- | --- | --- | --- |"]
    for record in report["records"]:
        coverage = record.get("retrieval_marker_scores", {}).get("coverage_at_k", "unscored")
        invalid = record.get("citation_syntax_only", {}).get("out_of_range", "unscored")
        lines.append(f"| {record['case_id']} | {record['suite']} | {record['k']} | {record['status']} | {coverage} | {invalid} |")
    lines.extend(["", "Marker coverage and citation syntax do not score answer quality.", "",
                  "Review report.json against cases.snapshot.json and corpus.snapshot.json. "
                  "Fill review.json with pass/fail ratings, reviewer, and claim/source evidence notes. "
                  "Null ratings remain unreviewed. Context-control evidence is supplied directly, not retrieved.", ""])
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ks", type=int, nargs="+", default=[2, 4])
    parser.add_argument("--suite", choices=["retrieved", "context_control", "all"], default="retrieved")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--summarize-review", type=Path, metavar="RUN_DIRECTORY")
    args = parser.parse_args(argv)
    args.ks = sorted(set(args.ks))
    if min(args.ks) < 1:
        parser.error("k must be positive")
    if args.summarize_review:
        directory = args.summarize_review
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        review = json.loads((directory / "review.json").read_text(encoding="utf-8"))
        result = review_summary(review, [r["record_id"] for r in report["records"] if r["status"] == "complete"])
        lab.write_json(directory / "review-summary.json", {"capture_status": report["status"], "dimensions": result})
        print(json.dumps(result, indent=2))
        return 0
    dataset = json.loads((ROOT / "evaluation/multidoc-cases.json").read_text(encoding="utf-8"))
    corpus = load_corpus()
    validate_cases(dataset, corpus)
    cases = [c for c in dataset["cases"] if args.suite == "all" or c["suite"] == args.suite]
    print(f"Validated {len(dataset['cases'])} cases; selected {len(cases)}. Corpus: {len(corpus)} document/page units.")
    if args.validate_only:
        print("Validation only: no embedding, chat, or index calls.")
        return 0
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = ROOT / "verification/multidoc-runs" / run_id
    report = {"schema_version": 1, "run_id": run_id, "status": "running", "records": [],
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "platform": platform.platform(),
              "dataset_sha256": lab.fingerprint(dataset), "corpus_sha256": lab.fingerprint(corpus),
              "settings": {"ks": args.ks, "suite": args.suite, "retrieval_mode": "id_priority", "candidate_pool": 20},
              "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ["eval_multidoc.py", "multidoc_lab.py", "qa_agent.py", "id_retrieval.py", "retrieval_metrics.py", "eval_retrieval.py"]}}
    try:
        report["git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        report["git_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip())
    except (OSError, subprocess.CalledProcessError):
        report["git_commit"] = None
        report["git_dirty"] = None
    directory.mkdir(parents=True, exist_ok=False)
    lab.write_json(directory / "cases.snapshot.json", dataset)
    lab.write_json(directory / "corpus.snapshot.json", corpus)

    def checkpoint(records):
        report["records"] = records
        write_dashboard(directory, report)

    checkpoint([])
    print("Run directory:", directory, flush=True)
    exit_code = 0
    try:
        import qa_agent as qa
        from id_retrieval import IdentifierAwareRetriever
        report["settings"].update({"chat_model": qa.CHAT_MODEL, "embedding_model": qa.EMBED_MODEL,
                                  "chunk_size": qa.CHUNK_SIZE, "overlap": qa.CHUNK_OVERLAP,
                                  "system_prompt": qa.SYSTEM_PROMPT})
        report["packages"] = {name: version(name) for name in ["langchain", "langchain-core", "langchain-chroma", "chromadb", "langchain-ollama", "langchain-text-splitters", "pypdf"]}
        report["model_identities"] = {name: lab.model_identity("http://localhost:11434", name)
                                      for name in [qa.CHAT_MODEL, qa.EMBED_MODEL]}
        agent = qa.build_agent()
        retriever = None
        if any(c["suite"] == "retrieved" for c in cases):
            retriever = IdentifierAwareRetriever(qa.get_vectorstore(), 20)
            report["indexed_chunks"] = retriever.inventory

        def retrieve(question, k):
            result = retriever.retrieve(question, k)
            return result["ranked"], result["trace"]

        def generate(question, excerpts):
            result = agent.invoke({"messages": [{"role": "user", "content": question}]}, context={"excerpts": excerpts})
            answer = result["messages"][-1].content
            if not isinstance(answer, str):
                raise ValueError("Expected a text answer")
            return answer

        run_cases(cases, args.ks, retrieve, generate, checkpoint)
        for name, identity in report["model_identities"].items():
            if lab.model_identity("http://localhost:11434", name)["digest"] != identity["digest"]:
                raise RuntimeError("Model identity changed during capture")
        if lab.fingerprint(load_corpus()) != report["corpus_sha256"]:
            raise RuntimeError("Corpus changed during capture")
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
        write_dashboard(directory, report)
        lab.write_json(directory / "review.json", review_template(report["records"]))
    print("Capture status:", report["status"])
    if "error" in report:
        print(report["error"])
    print("Dashboard:", directory / "summary.md")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
