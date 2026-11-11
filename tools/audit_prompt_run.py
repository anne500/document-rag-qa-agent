"""Recheck a saved frozen-context prompt capture without invoking any model."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval_retrieval import fingerprint
from multidoc_lab import format_excerpts
from prompt_lab import citation_check, prompts_for, validate_frozen


def audit(directory, source_dir=None):
    def read(name):
        return json.loads((directory / name).read_text(encoding="utf-8"))
    report = read("report.json")
    source = read("source-report.snapshot.json")
    dataset, corpus, prompts = map(read, ["cases.snapshot.json", "corpus.snapshot.json", "prompts.json"])
    assert report["status"] == "complete" and report["experiment"] == "frozen_context_prompt_comparison"
    assert fingerprint(source) == report["source_report_sha256"]
    assert fingerprint(dataset) == report["dataset_sha256"]
    assert fingerprint(corpus) == report["corpus_sha256"]
    source_records = {r["record_id"]: r for r in validate_frozen(source, dataset, corpus)}
    refined = report["settings"].get("include_refined", False)
    assert report["prompts"] == prompts == prompts_for(source["settings"]["system_prompt"], include_refined=refined)
    prompt_variants = list(prompts)
    expected = report["settings"]["selected_record_ids"]
    pairs = report["pairs"]
    assert len(expected) == len(set(expected))
    assert [p["record_id"] for p in pairs] == expected
    baseline_matches = []
    total_excerpts = 0
    syntax_checks = 0
    for i, pair in enumerate(pairs):
        original = source_records[pair["record_id"]]
        assert pair["status"] == "complete"
        for key in ("case_id", "suite", "k", "question", "excerpts", "retrieval_marker_scores"):
            assert pair[key] == original[key], (pair["record_id"], key)
        context = format_excerpts(original["excerpts"])
        assert pair["context_text"] == context
        assert pair["context_sha256"] == fingerprint(context)
        offset = i % len(prompt_variants)
        order = prompt_variants[offset:] + prompt_variants[:offset]
        assert pair["call_order"] == order
        assert list(pair["variants"]) == order
        for variant in order:
            result = pair["variants"][variant]
            assert result["status"] == "complete" and result["answer"].strip()
            assert result["prompt_sha256"] == fingerprint(prompts[variant])
            assert result["context_sha256"] == pair["context_sha256"]
            assert result["citation_syntax_only"] == citation_check(result["answer"], len(pair["excerpts"]))
            assert not result["citation_syntax_only"]["out_of_range"]
            syntax_checks += 1
        if pair["variants"]["baseline"]["answer"] == original["answer"]:
            baseline_matches.append(pair["record_id"])
        total_excerpts += len(pair["excerpts"])
    assert report["source_run_id"] == source["run_id"]
    assert report["settings"]["retrieval_performed"] is False
    model = report["settings"]["model"]
    assert model == source["settings"]["chat_model"]
    same_digest = report["model_identity"]["digest"] == source["model_identities"][model]["digest"]
    assert report["model_digest_matches_source_capture"] == same_digest
    code = {}
    for name, digest in report["code_sha256"].items():
        raw = (source_dir / name).read_bytes() if source_dir else subprocess.check_output(
            ["git", "show", report["git_commit"] + ":" + name], cwd=ROOT)
        lf = raw.replace(b"\r\n", b"\n")
        variants = {"LF": lf, "CRLF": lf.replace(b"\n", b"\r\n")}
        matches = [label for label, data in variants.items() if hashlib.sha256(data).hexdigest() == digest]
        assert matches, "Code hash mismatch: " + name
        code[name] = matches[0]
    review = read("review.json")
    expected_reviews = {p["record_id"] + "::" + v for p in pairs for v in prompt_variants}
    assert len(review["records"]) == len(expected_reviews)
    assert {r["record_id"] for r in review["records"]} == expected_reviews
    assert all(all(v is None for v in r["ratings"].values()) for r in review["records"])
    return {"status": "passed", "scope": "Saved artifact consistency, not live inference reproduction or answer accuracy",
            "pairs_checked": len(pairs), "answers_checked": syntax_checks,
            "frozen_context_excerpt_occurrences_checked": total_excerpts,
            "answer_context_hashes_checked": syntax_checks, "answer_prompt_hashes_checked": syntax_checks,
            "snapshot_digests_checked": 3, "alternating_call_orders_checked": len(pairs),
            "citation_syntax_checks_recomputed": syntax_checks,
            "source_marker_score_values_recomputed": 5*len(source_records),
            "out_of_range_numeric_labels": 0, "code_digest_line_endings": code,
            "saved_model_digest_matches_source_capture": same_digest,
            "baseline_answers_identical_to_original_capture": len(baseline_matches),
            "original_human_review": f"{len(expected_reviews)} records remain unreviewed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--source-dir", type=Path, help="Optional frozen sources; defaults to git show of the recorded runtime commit")
    args = parser.parse_args()
    print(json.dumps(audit(args.run_directory, args.source_dir), indent=2))

