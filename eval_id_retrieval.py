"""Paired semantic vs whole-ID-priority retrieval; no chat-model invocation."""

import argparse
import csv
import hashlib
import io
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import eval_retrieval as lab
from id_retrieval import IdentifierIndex, candidate
from retrieval_metrics import METRICS, matches, score_case, summarize, validate_dataset

ROOT = Path(__file__).resolve().parent
STRATEGIES = ("semantic", "id_priority")


def summary_rows(report):
    rows = []
    for config in report["configurations"]:
        if config["status"] != "complete":
            continue
        for k in report["settings"]["ks"]:
            for strategy in STRATEGIES:
                rows.append({
                    "chunk_size": config["chunk_size"], "overlap": config["overlap"],
                    "k": k, "strategy": strategy,
                    **summarize([
                        case["strategies"][strategy]["scores_by_k"][str(k)]
                        for case in config["cases"]
                    ]),
                })
    return rows


def paired_rows(report):
    rows = []
    for config in report["configurations"]:
        if config["status"] != "complete":
            continue
        for case in config["cases"]:
            if case["kind"] != "evidence":
                continue
            for k in report["settings"]["ks"]:
                before = case["strategies"]["semantic"]["scores_by_k"][str(k)]
                after = case["strategies"]["id_priority"]["scores_by_k"][str(k)]
                rows.append({
                    "chunk_size": config["chunk_size"], "case": case["id"], "k": k,
                    **{key + "_delta": after[key] - before[key] for key in METRICS},
                })
    return rows


def write_artifacts(directory, report):
    lab.write_json(directory / "report.json", report)
    rows = summary_rows(report)
    fields = ["chunk_size", "overlap", "k", "strategy", "evidence_cases",
              "no_evidence_controls", *METRICS]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (directory / "metrics.csv").write_text(
        stream.getvalue(), encoding="utf-8", newline="\n"
    )
    deltas = paired_rows(report)
    lab.write_json(directory / "paired-deltas.json", deltas)
    for strategy in STRATEGIES:
        svg = lab.render_svg(
            [row for row in rows if row["strategy"] == strategy],
            report["status"],
            "Semantic baseline" if strategy == "semantic" else "Whole-ID priority + semantic fallback",
        )
        (directory / (strategy + "-results.svg")).write_text(svg, encoding="utf-8")
    lines = [
        "# Identifier-Aware Retrieval Dashboard", "",
        f"Run status: **{report['status']}**", "",
        "## Paired aggregate comparison", "",
        "| Chunk | k | Method | Hit | Complete | Coverage | MRR | Precision |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        values = " | ".join(f"{row[key]:.3f}" for key in METRICS)
        lines.append(
            f"| {row['chunk_size']} | {row['k']} | {row['strategy']} | {values} |"
        )
    lines.extend([
        "", "## Complete-evidence changes by question", "",
        "| Chunk | k | Improved | Regressed | Unchanged |",
        "| --- | --- | --- | --- | --- |",
    ])
    for size in report["settings"]["chunk_sizes"]:
        for k in report["settings"]["ks"]:
            group = [row for row in deltas if row["chunk_size"] == size and row["k"] == k]
            if not group:
                continue
            improved = sum(row["complete_at_k_delta"] > 0 for row in group)
            regressed = sum(row["complete_at_k_delta"] < 0 for row in group)
            lines.append(
                f"| {size} | {k} | {improved} | {regressed} | "
                f"{len(group) - improved - regressed} |"
            )
    lines.extend([
        "", "## Semantic baseline", "", "![Semantic metrics](semantic-results.svg)", "",
        "## Whole-ID priority", "", "![ID-priority metrics](id_priority-results.svg)", "",
        "The two methods use the same semantic candidate list for each question. "
        "The priority method can also select exact-ID chunks outside that pool.",
        "", "Source IDs, page numbers, full text, original semantic ranks, "
        "selection reasons, unknown IDs, and per-case scores are in report.json. "
        "All metric deltas, including regressions, are in paired-deltas.json.",
        "", "Only authored evidence-marker retrieval is evaluated. "
        "No answer generation, abstention accuracy, held-out generalization, "
        "or general superiority is established. No-evidence controls are unscored.",
    ])
    (directory / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evaluation" / "cases.json")
    parser.add_argument("--chunk-sizes", type=int, nargs="+", default=[500, 1000])
    parser.add_argument("--ks", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--candidate-pool", type=int, default=20)
    parser.add_argument("--model", default="nomic-embed-text")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    args.chunk_sizes = sorted(set(args.chunk_sizes))
    args.ks = sorted(set(args.ks))
    if min(args.ks) < 1 or args.overlap < 0 or min(args.chunk_sizes) <= args.overlap:
        parser.error("k must be positive; chunk size must exceed nonnegative overlap")
    if args.candidate_pool < max(args.ks):
        parser.error("candidate-pool must be at least the largest k")
    return args


def main(argv=None):
    args = parse_args(argv)
    dataset = json.loads(args.cases.read_text(encoding="utf-8-sig"))
    validate_dataset(dataset)
    import qa_agent
    documents = qa_agent.load_documents()
    corpus = lab.validate_corpus(dataset, documents)
    print(f"Validated {len(dataset['cases'])} cases and {len(documents)} document/page units.")
    if args.validate_only:
        print("Validation only: no embedding, chat, or index calls.")
        return 0
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = ROOT / "verification" / "identifier-runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    report = {
        "schema_version": 1, "experiment": "paired_identifier_priority",
        "run_id": run_id, "status": "running", "configurations": [],
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": lab.fingerprint(dataset), "corpus_sha256": lab.fingerprint(corpus),
        "python": platform.python_version(), "platform": platform.platform(),
        "settings": {
            "chunk_sizes": args.chunk_sizes, "ks": args.ks, "overlap": args.overlap,
            "candidate_pool": args.candidate_pool, "strategies": list(STRATEGIES),
            "embedding_model": args.model, "ollama_url": args.ollama_url,
        },
        "code_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ["eval_id_retrieval.py", "id_retrieval.py", "eval_retrieval.py",
                         "retrieval_metrics.py", "qa_agent.py"]
        },
    }
    try:
        report["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
        ).decode("ascii").strip()
    except (OSError, subprocess.CalledProcessError):
        report["git_commit"] = None
    lab.write_json(directory / "cases.snapshot.json", dataset)
    lab.write_json(directory / "corpus.snapshot.json", corpus)
    write_artifacts(directory, report)
    print("Run directory:", directory, flush=True)
    exit_code = 0
    try:
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        report["packages"] = {
            name: version(name) for name in [
                "langchain", "langchain-core", "langchain-chroma", "chromadb",
                "langchain-ollama", "langchain-text-splitters", "pypdf"
            ]
        }
        report["embedding_identity"] = lab.model_identity(args.ollama_url, args.model)
        embeddings = OllamaEmbeddings(model=args.model, base_url=args.ollama_url)
        for size in args.chunk_sizes:
            config = {"chunk_size": size, "overlap": args.overlap,
                      "status": "running", "cases": []}
            report["configurations"].append(config)
            write_artifacts(directory, report)
            chunks = RecursiveCharacterTextSplitter(
                chunk_size=size, chunk_overlap=args.overlap
            ).split_documents(documents)
            inventory = [candidate(doc.page_content, doc.metadata) for doc in chunks]
            config["indexed_chunks"] = inventory
            config["chunks"] = len(chunks)
            index = IdentifierIndex(inventory)
            print(f"Building chunk size {size}: {len(chunks)} chunks", flush=True)
            started = perf_counter()
            store = Chroma.from_documents(
                documents=chunks, embedding=embeddings,
                collection_name="identifier_eval_" + uuid4().hex,
                ids=[str(number) for number in range(len(chunks))],
            )
            config["index_seconds"] = perf_counter() - started
            try:
                for case in dataset["cases"]:
                    started = perf_counter()
                    results = store.similarity_search_with_score(
                        case["question"], k=min(args.candidate_pool, len(chunks))
                    )
                    semantic_seconds = perf_counter() - started
                    semantic = [
                        {**candidate(doc.page_content, doc.metadata, float(distance)),
                         "semantic_rank": rank, "selection": "semantic"}
                        for rank, (doc, distance) in enumerate(results, start=1)
                    ]
                    started = perf_counter()
                    priority, trace = index.rerank(case["question"], semantic)
                    rerank_seconds = perf_counter() - started
                    rankings = {"semantic": semantic, "id_priority": priority}
                    record = {
                        "id": case["id"], "kind": case["kind"], "question": case["question"],
                        "semantic_candidate_pool": semantic,
                        "semantic_search_seconds": semantic_seconds,
                        "id_rerank_seconds": rerank_seconds, "identifier_trace": trace,
                        "strategies": {},
                    }
                    for strategy, ranked in rankings.items():
                        selected = ranked[:max(args.ks)]
                        selected = [
                            {**item, "matched_evidence_groups": [
                                group["id"] for group in case["required_evidence"]
                                if matches(group, item)
                            ]} for item in selected
                        ]
                        record["strategies"][strategy] = {
                            "ranked_max_k": selected,
                            "scores_by_k": {
                                str(k): score_case(case, selected, k) for k in args.ks
                            },
                        }
                    config["cases"].append(record)
                    write_artifacts(directory, report)
                    print(f"  {case['id']}: both methods recorded", flush=True)
                config["status"] = "complete"
            finally:
                store.delete_collection()
            write_artifacts(directory, report)
        final = lab.model_identity(args.ollama_url, args.model)
        if final["digest"] != report["embedding_identity"]["digest"]:
            raise RuntimeError("Embedding model identity changed during evaluation")
        report["status"] = "complete"
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        report["error"] = "KeyboardInterrupt"
        exit_code = 130
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        exit_code = 1
    finally:
        report["ended_utc"] = datetime.now(timezone.utc).isoformat()
        write_artifacts(directory, report)
    print("Evaluation status:", report["status"])
    if "error" in report:
        print(report["error"], file=sys.stderr)
    print("Dashboard:", directory / "summary.md")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
