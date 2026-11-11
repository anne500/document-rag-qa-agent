"""Reconstruct saved numeric-guard decisions from recorded drafts, without models."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from citation_guard import guarded_answer
from eval_citation_guard import validate_capture
from eval_retrieval import fingerprint


def without_timing(result):
    copied = json.loads(json.dumps(result))
    for attempt in copied["attempts"]:
        attempt.pop("elapsed_seconds", None)
    return copied


def audit(directory, source_dir=None):
    def read(name):
        return json.loads((directory / name).read_text(encoding="utf-8"))
    report, source = map(read, ["report.json", "source-report.snapshot.json"])
    assert report["status"] == "complete"
    assert report["mode"] in {"saved_draft_plus_live_repair", "offline_repeat_draft_replay"}
    assert fingerprint(source) == report["source_sha256"]
    assert source["run_id"] == report["source_run_id"]
    drafts = validate_capture(source)
    assert [r["record_id"] for r in report["records"]] == [d["record_id"] for d in drafts]
    counters = {"records_checked": 0, "attempt_checks_recomputed": 0,
                "replayed_initial_drafts": len(drafts), "initial_invalid_drafts": 0,
                "live_calls_recorded": 0, "accepted_without_live_call": 0,
                "accepted_after_live_retry": 0, "withheld_after_live_retry": 0,
                "accepted": 0, "abstained": 0}
    for row, draft in zip(report["records"], drafts):
        assert row["suite"] == draft["suite"]
        assert row["initial_check"] == draft["initial_check"]
        assert row["question"] == draft["question"]
        assert row["context_sha256"] == fingerprint(draft["context"])
        attempts = row["guard"]["attempts"]
        assert attempts and attempts[0]["draft"] == draft["draft"]
        supplied = iter(attempts)

        def generate(question, context, feedback):
            saved = next(supplied)
            assert question == draft["question"] and context == draft["context"]
            assert saved["feedback"] == feedback
            return saved["draft"]

        replayed = guarded_answer(draft["question"], draft["context"], draft["excerpt_count"], generate)
        assert without_timing(replayed) == without_timing(row["guard"]), row["record_id"]
        assert next(supplied, None) is None
        invalid = not draft["initial_check"]["valid"]
        expected_live = int(invalid and report["mode"] == "saved_draft_plus_live_repair")
        assert row["live_calls"] == expected_live
        if report["mode"] == "offline_repeat_draft_replay":
            assert all(a["draft"] == draft["draft"] for a in attempts)
        counters["records_checked"] += 1
        counters["attempt_checks_recomputed"] += len(attempts)
        counters["initial_invalid_drafts"] += int(invalid)
        counters["live_calls_recorded"] += row["live_calls"]
        counters[row["guard"]["status"]] += 1
        counters["accepted_without_live_call"] += int(row["live_calls"] == 0 and row["guard"]["status"] == "accepted")
        counters["accepted_after_live_retry"] += int(row["live_calls"] > 0 and row["guard"]["status"] == "accepted")
        counters["withheld_after_live_retry"] += int(row["live_calls"] > 0 and row["guard"]["status"] == "abstained")
    code = {}
    for name, digest in report["code_sha256"].items():
        raw = (source_dir / name).read_bytes() if source_dir else subprocess.check_output(
            ["git", "show", report["git_commit"] + ":" + name], cwd=ROOT)
        lf = raw.replace(b"\r\n", b"\n")
        variants = {"LF": lf, "CRLF": lf.replace(b"\n", b"\r\n")}
        matched = [key for key, data in variants.items() if hashlib.sha256(data).hexdigest() == digest]
        assert matched, "Code digest mismatch: " + name
        code[name] = matched[0]
    if counters["live_calls_recorded"]:
        same = report["model_identity"]["digest"] == source["model_identity"]["digest"]
        assert same == report["model_digest_matches_source_capture"]
    return {"status": "passed", "scope": "Saved artifact consistency and deterministic numeric decisions; not live model reproduction or factual accuracy",
            **counters, "source_snapshot_digest_checked": True, "code_digest_line_endings": code}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--source-dir", type=Path, help="Optional frozen source bytes; otherwise git show of runtime commit")
    args = parser.parse_args()
    print(json.dumps(audit(args.run_directory, args.source_dir), indent=2))
