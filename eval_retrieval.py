"""Compare retrieval settings on the fictional corpus; never invoke chat."""

import argparse
import csv
import hashlib
import io
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from html import escape
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from urllib.request import urlopen
from uuid import uuid4

from retrieval_metrics import METRICS, matches, score_case, summarize, validate_dataset

ROOT = Path(__file__).resolve().parent


def fingerprint(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def validate_corpus(dataset, documents):
    actual = {doc.metadata["source"] for doc in documents}
    if actual != set(dataset["expected_sources"]):
        raise ValueError(
            "This evaluation requires only the four published fixture files. "
            f"Missing: {sorted(set(dataset['expected_sources']) - actual)}; "
            f"extra: {sorted(actual - set(dataset['expected_sources']))}"
        )
    if len(documents) != dataset["expected_document_units"]:
        raise ValueError("Expected three Markdown documents and two PDF pages")
    candidates = [{
        "source": doc.metadata["source"], "page": doc.metadata.get("page"),
        "text": doc.page_content,
    } for doc in documents]
    for case in dataset["cases"]:
        for group in case["required_evidence"]:
            if not any(matches(group, candidate) for candidate in candidates):
                raise ValueError(
                    f"Ground-truth evidence absent: {case['id']} / {group['id']}"
                )
    return candidates


def model_identity(base_url, name):
    with urlopen(base_url.rstrip("/") + "/api/tags", timeout=15) as response:
        models = json.load(response)["models"]
    canonical = name if ":" in name else name + ":latest"
    for model in models:
        names = {model.get("name"), model.get("model")}
        if canonical in names or name in names:
            if not model.get("digest"):
                raise ValueError("Ollama did not return an embedding model digest")
            return {
                "requested_name": name, "resolved_name": model.get("name"),
                "digest": model["digest"], "details": model.get("details", {}),
            }
    raise ValueError(f"Embedding model not installed: {name}")


def summary_rows(report):
    rows = []
    for config in report["configurations"]:
        if config["status"] != "complete":
            continue
        for k in report["settings"]["ks"]:
            summary = summarize([
                case["scores_by_k"][str(k)] for case in config["cases"]
            ])
            rows.append({
                "chunk_size": config["chunk_size"],
                "overlap": config["overlap"], "k": k, **summary,
            })
    return rows


def render_svg(rows, status, label="Observed retrieval metrics"):
    """Standalone exact SVG chart; no plotting dependency required."""
    height = 185 + max(1, len(rows)) * 85
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" '
        f'viewBox="0 0 1100 {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(label)}</title>',
        '<desc id="desc">Authored evidence marker coverage, complete evidence '
        'rate, and mean reciprocal rank. No answer generation is evaluated.</desc>',
        f'<rect width="1100" height="{height}" fill="#F8FAFC"/>',
        '<g font-family="DejaVu Sans,Arial,sans-serif">',
        f'<text x="28" y="35" font-size="23" font-weight="700" fill="#0F172A">'
        f'{escape(label)}</text>',
        f'<text x="28" y="63" font-size="14" fill="#475569">'
        f'Status: {escape(status)} / fictional corpus / retrieval only</text>',
    ]
    columns = [
        ("coverage_at_k", "Evidence coverage", "#2563EB"),
        ("complete_at_k", "Complete evidence", "#15803D"),
        ("mrr_at_k", "MRR", "#7C3AED"),
    ]
    for index, (_, title, color) in enumerate(columns):
        x = 230 + index * 280
        parts.append(f'<text x="{x}" y="99" font-size="16" font-weight="700" '
                     f'fill="{color}">{title} (0 to 1)</text>')
    if not rows:
        parts.append('<text x="28" y="145" font-size="17" fill="#B45309">'
                     'No completed configurations. Inspect report.json.</text>')
    for row_index, row in enumerate(rows):
        y = 138 + row_index * 85
        parts.append(f'<text x="28" y="{y + 19}" font-size="16" fill="#0F172A">'
                     f'Chunk {row["chunk_size"]} / k={row["k"]}</text>')
        for index, (key, _, color) in enumerate(columns):
            x = 230 + index * 280
            value = row[key]
            parts.extend([
                f'<rect x="{x}" y="{y}" width="190" height="25" rx="4" fill="#E2E8F0"/>',
                f'<rect x="{x}" y="{y}" width="{190 * value:.2f}" height="25" '
                f'rx="4" fill="{color}"/>',
                f'<text x="{x + 198}" y="{y + 19}" font-size="15" fill="#0F172A">'
                f'{value:.3f}</text>',
            ])
        parts.append(f'<text x="230" y="{y + 48}" font-size="12" fill="#475569">'
                     f'{row["evidence_cases"]} evidence cases; '
                     f'{row["no_evidence_controls"]} unscored controls</text>')
    parts.append(f'<text x="28" y="{height - 22}" font-size="13" fill="#475569">'
                 'Markers are an authored retrieval proxy, not semantic answer quality or thesis results.'
                 '</text></g></svg>')
    return "\n".join(parts) + "\n"


def write_artifacts(run_dir, report):
    write_json(run_dir / "report.json", report)
    rows = summary_rows(report)
    fields = ["chunk_size", "overlap", "k", "evidence_cases",
              "no_evidence_controls", *METRICS]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (run_dir / "metrics.csv").write_text(
        stream.getvalue(), encoding="utf-8", newline="\n"
    )
    (run_dir / "retrieval-results.svg").write_text(
        render_svg(rows, report["status"]), encoding="utf-8"
    )
    lines = [
        "# Retrieval Evaluation Dashboard", "",
        f"Run status: **{report['status']}**", "",
        "![Retrieval metrics](retrieval-results.svg)", "",
        "| Chunk | k | Hit | Complete | Coverage | MRR | Precision |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        values = " | ".join(f"{row[key]:.3f}" for key in METRICS)
        lines.append(f"| {row['chunk_size']} | {row['k']} | {values} |")
    lines.extend([
        "", "Metrics average only evidence cases. No-evidence controls are "
        "unscored and cannot establish abstention quality.",
        "", "Per-case ranks, full retrieved text, PDF pages, distances, marker "
        "matches, settings, hashes, and model identity are in report.json.",
        "", "One search at the largest k supplies shared ranking prefixes. "
        "Query timings therefore do not measure separate k configurations.",
        "", "These are small, authored, development-set results. They are not "
        "a held-out benchmark, general accuracy claim, or thesis experiment.",
    ])
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "evaluation" / "cases.json")
    parser.add_argument("--chunk-sizes", type=int, nargs="+", default=[500, 1000])
    parser.add_argument("--ks", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--model", default="nomic-embed-text")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    args.chunk_sizes = sorted(set(args.chunk_sizes))
    args.ks = sorted(set(args.ks))
    if min(args.ks) < 1 or args.overlap < 0 or min(args.chunk_sizes) <= args.overlap:
        parser.error("k must be positive; chunk size must exceed nonnegative overlap")
    return args


def main(argv=None):
    args = parse_args(argv)
    dataset = json.loads(args.cases.read_text(encoding="utf-8-sig"))
    validate_dataset(dataset)
    # Use the application's actual loader without changing its index or settings.
    import qa_agent
    documents = qa_agent.load_documents()
    corpus = validate_corpus(dataset, documents)
    print(f"Validated {len(dataset['cases'])} cases and {len(documents)} document/page units.")
    if args.validate_only:
        print("Validation only: no Ollama calls, embeddings, or index writes.")
        return 0

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    run_dir = ROOT / "verification" / "retrieval-runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    settings = {
        "chunk_sizes": args.chunk_sizes, "ks": args.ks, "overlap": args.overlap,
        "embedding_model": args.model, "ollama_url": args.ollama_url,
    }
    report = {
        "schema_version": 1, "run_id": run_id, "status": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(), "settings": settings,
        "dataset_sha256": fingerprint(dataset), "corpus_sha256": fingerprint(corpus),
        "python": platform.python_version(), "platform": platform.platform(),
        "configurations": [],
        "code_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ["eval_retrieval.py", "retrieval_metrics.py", "qa_agent.py"]
        },
    }
    try:
        report["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
        ).decode("ascii").strip()
    except (OSError, subprocess.CalledProcessError):
        report["git_commit"] = None
    write_json(run_dir / "cases.snapshot.json", dataset)
    write_json(run_dir / "corpus.snapshot.json", corpus)
    write_artifacts(run_dir, report)
    print("Run directory:", run_dir, flush=True)
    exit_code = 0
    try:
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        report["packages"] = {
            name: version(name) for name in [
                "langchain", "langchain-core", "langchain-chroma",
                "chromadb", "langchain-ollama", "langchain-text-splitters", "pypdf"
            ]
        }
        report["embedding_identity"] = model_identity(args.ollama_url, args.model)
        embeddings = OllamaEmbeddings(model=args.model, base_url=args.ollama_url)
        for size in args.chunk_sizes:
            config = {"chunk_size": size, "overlap": args.overlap,
                      "status": "running", "cases": []}
            report["configurations"].append(config)
            write_artifacts(run_dir, report)
            chunks = RecursiveCharacterTextSplitter(
                chunk_size=size, chunk_overlap=args.overlap
            ).split_documents(documents)
            config["chunks"] = len(chunks)
            for index, chunk in enumerate(chunks):
                chunk.metadata = {**chunk.metadata, "eval_chunk": index}
            print(f"Building chunk size {size}: {len(chunks)} chunks", flush=True)
            started = perf_counter()
            store = Chroma.from_documents(
                documents=chunks, embedding=embeddings,
                collection_name="retrieval_eval_" + uuid4().hex,
                ids=[str(index) for index in range(len(chunks))],
            )
            config["index_seconds"] = perf_counter() - started
            try:
                for case in dataset["cases"]:
                    started = perf_counter()
                    retrieved = store.similarity_search_with_score(
                        case["question"], k=min(max(args.ks), len(chunks))
                    )
                    seconds = perf_counter() - started
                    ranked = [{
                        "source": doc.metadata["source"],
                        "page": doc.metadata.get("page"),
                        "text": doc.page_content,
                        "chunk_id": doc.metadata["eval_chunk"],
                        "distance": float(distance),
                        "matched_groups": [
                            group["id"] for group in case["required_evidence"]
                            if matches(group, {
                                "source": doc.metadata["source"],
                                "page": doc.metadata.get("page"), "text": doc.page_content
                            })
                        ],
                    } for doc, distance in retrieved]
                    config["cases"].append({
                        "id": case["id"], "kind": case["kind"],
                        "question": case["question"], "retrieved_max_k": ranked,
                        "retrieval_seconds_at_max_k": seconds,
                        "scores_by_k": {
                            str(k): score_case(case, ranked, k) for k in args.ks
                        },
                    })
                    write_artifacts(run_dir, report)
                    print(f"  {case['id']}: recorded", flush=True)
                config["status"] = "complete"
            finally:
                store.delete_collection()
            write_artifacts(run_dir, report)
        final_identity = model_identity(args.ollama_url, args.model)
        if final_identity["digest"] != report["embedding_identity"]["digest"]:
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
        write_artifacts(run_dir, report)
    print(f"Evaluation status: {report['status']}")
    if "error" in report:
        print(report["error"], file=sys.stderr)
    print("Dashboard:", run_dir / "summary.md")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
