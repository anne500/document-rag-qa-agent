"""Offline helpers for evidence coverage and human-reviewed answer evaluation."""

import re
from retrieval_metrics import matches, score_case

DIMENSIONS = ("completeness", "attribution", "citation_support", "uncertainty")


def validate_cases(dataset, corpus):
    if dataset.get("schema_version") != 1 or not dataset.get("cases"):
        raise ValueError("Invalid multi-document dataset")
    if "expected_sources" in dataset and (
        {item["source"] for item in corpus} != set(dataset["expected_sources"])
        or len(corpus) != dataset["expected_document_units"]
    ):
        raise ValueError("Use the four published fixture files and five document/page units")
    ids = set()
    for case in dataset["cases"]:
        if not case.get("id") or case["id"] in ids:
            raise ValueError("Missing or duplicate case ID")
        ids.add(case["id"])
        if case.get("suite") not in {"retrieved", "context_control"}:
            raise ValueError("Invalid suite")
        if not case.get("question") or not case.get("expected_claims"):
            raise ValueError("Question and expected claims are required")
        evidence = case.get("required_evidence", [])
        available = corpus if case["suite"] == "retrieved" else case["context"]
        if not evidence or any(
            not group.get("contains") or not all(isinstance(t, str) and t.strip() for t in group["contains"])
            or not any(matches(group, item) for item in available)
            for group in evidence
        ):
            raise ValueError("Missing ground-truth evidence: " + case["id"])
        if len({g["id"] for g in evidence}) != len(evidence):
            raise ValueError("Duplicate evidence group")


def format_excerpts(ranked):
    return "\n\n".join(
        f"[{i}] {item['source']}" +
        (f", page {item['page']}" if item.get("page") else "") +
        "\n" + item["text"]
        for i, item in enumerate(ranked, 1)
    )


def inspect_answer(case, ranked, answer):
    labels = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer)})
    return {
        "retrieval_marker_scores": score_case({**case, "kind": "evidence"}, ranked, max(1, len(ranked))),
        "citation_syntax_only": {
            "labels": labels,
            "out_of_range": [n for n in labels if not 1 <= n <= len(ranked)],
            "has_numeric_citation": bool(labels),
            "warning": "A valid label does not establish claim support. Human review required.",
        },
    }


def review_template(records):
    return {
        "instructions": "Use the frozen case/corpus snapshots and report. Rate each dimension pass or fail; leave null if unreviewed. Supply notes quoting the answer claim and its source/page. Check all substantive claims, including unexpected additions. Do not infer support from citation syntax or marker coverage.",
        "records": [{
            "record_id": item["record_id"],
            "ratings": {key: None for key in DIMENSIONS},
            "reviewer": "", "notes": "",
        } for item in records if item["status"] == "complete"],
    }


def review_summary(review, expected_ids):
    records = review["records"]
    ids = [item["record_id"] for item in records]
    if len(ids) != len(set(ids)) or set(ids) != set(expected_ids):
        raise ValueError("Review IDs must match completed report records exactly")
    result = {}
    for key in DIMENSIONS:
        values = []
        for item in records:
            value = item["ratings"][key]
            if value is not None and value not in ("pass", "fail"):
                raise ValueError("Ratings must be pass, fail, or null")
            if value is not None and (not item["reviewer"].strip() or not item["notes"].strip()):
                raise ValueError("Reviewed ratings need a reviewer and evidence notes")
            values.append(value)
        reviewed = sum(v is not None for v in values)
        passed = values.count("pass")
        result[key] = {"reviewed": reviewed, "unreviewed": len(values) - reviewed,
                       "passed": passed, "failed": values.count("fail"),
                       "pass_rate_reviewed_only": passed / reviewed if reviewed else None}
    return result
