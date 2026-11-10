"""Recompute saved multi-document evidence checks without Ollama or Chroma."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval_retrieval import fingerprint
from multidoc_lab import inspect_answer, validate_cases


def audit(directory, source_dir=None):
    def read(name):
        return json.loads((directory / name).read_text(encoding="utf-8"))
    report, dataset, corpus = map(read, ["report.json", "cases.snapshot.json", "corpus.snapshot.json"])
    assert report["status"] == "complete", "Capture was not complete"
    assert fingerprint(dataset) == report["dataset_sha256"], "Case snapshot digest mismatch"
    assert fingerprint(corpus) == report["corpus_sha256"], "Corpus snapshot digest mismatch"
    validate_cases(dataset, corpus)
    cases = {c["id"]: c for c in dataset["cases"]}
    expected = {c["id"] + (f":k{k}" if k else ":control")
                for c in dataset["cases"]
                for k in (report["settings"]["ks"] if c["suite"] == "retrieved" else [None])}
    records = report["records"]
    assert len(records) == len(expected) and {r["record_id"] for r in records} == expected
    assert len(report["indexed_chunks"]) == len(corpus) == 5
    excerpt_count = 0
    grouped = []
    for record in records:
        case = cases[record["case_id"]]
        assert record["status"] == "complete"
        assert record["question"] == case["question"] and record["suite"] == case["suite"]
        assert isinstance(record["answer"], str) and record["answer"].strip()
        available = corpus if case["suite"] == "retrieved" else case["context"]
        for item in record["excerpts"]:
            assert any(item["source"] == x["source"] and item.get("page") == x.get("page")
                       and item["text"].strip() == x["text"].strip() for x in available), record["record_id"]
            if case["suite"] == "retrieved":
                assert any(item["source"] == x["source"] and item.get("page") == x.get("page")
                           and item["text"] == x["text"] for x in report["indexed_chunks"])
        if case["suite"] == "context_control":
            assert record["excerpts"] == case["context"] and record["k"] is None
            assert record["trace"]["retrieval_performed"] is False
        else:
            assert len(record["excerpts"]) == record["k"]
        recomputed = inspect_answer(case, record["excerpts"], record["answer"])
        for key, value in recomputed.items():
            assert value == record[key], (record["record_id"], key)
        # Supplement the original singles-only parser; do not rewrite its saved output.
        labels = [int(n) for body in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", record["answer"])
                  for n in re.findall(r"\d+", body)]
        assert all(1 <= n <= len(record["excerpts"]) for n in labels)
        if re.search(r"\[\d+\s*,", record["answer"]):
            grouped.append(record["record_id"])
        excerpt_count += len(record["excerpts"])
    prefixes = 0
    for case in dataset["cases"]:
        if case["suite"] != "retrieved":
            continue
        pair = sorted([r for r in records if r["case_id"] == case["id"]], key=lambda r:r["k"])
        assert pair[0]["excerpts"] == pair[-1]["excerpts"][:pair[0]["k"]]
        assert pair[0]["trace"] == pair[-1]["trace"]
        prefixes += 1
    code = {}
    for name, digest in report["code_sha256"].items():
        raw = (source_dir / name).read_bytes() if source_dir else subprocess.check_output(
            ["git", "show", report["git_commit"] + ":" + name], cwd=ROOT)
        lf = raw.replace(b"\r\n", b"\n")
        variants = {"LF": lf, "CRLF": lf.replace(b"\n", b"\r\n")}
        matched = [kind for kind, data in variants.items() if hashlib.sha256(data).hexdigest() == digest]
        assert matched, "Code digest mismatch: " + name
        code[name] = matched[0]
    raw_review = read("review.json")
    assert {x["record_id"] for x in raw_review["records"]} == expected
    assert all(all(v is None for v in x["ratings"].values()) for x in raw_review["records"])
    return {"status": "passed", "scope": "Saved artifact consistency, not live inference reproduction or answer accuracy",
            "records_checked": len(records), "metric_values_recomputed": 5*len(records),
            "excerpt_occurrences_checked": excerpt_count, "shared_prefix_pairs_checked": prefixes,
            "snapshot_digests_checked": 2, "code_digest_line_endings": code,
            "grouped_citation_records_checked_separately": grouped,
            "out_of_range_numeric_labels_in_supplemental_check": 0,
            "original_human_review": "13 records remain unreviewed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--source-dir", type=Path, help="Optional frozen source directory; otherwise use git show of recorded commit")
    args = parser.parse_args()
    print(json.dumps(audit(args.run_directory, args.source_dir), indent=2))
