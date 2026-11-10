"""Frozen-context prompt experiment helpers; no model or retrieval dependencies."""

import re
from time import perf_counter

from eval_retrieval import fingerprint
from multidoc_lab import format_excerpts, inspect_answer, validate_cases

REVISION = (
    "\n\nEvidence-use rules:\n"
    "1. Address each requested entity separately. Include each requested condition "
    "that the excerpts support, and keep facts attached to the correct entity.\n"
    "2. Make only claims supported by the supplied excerpts. Do not add inferred "
    "operational restrictions, approval gates, or reasons why documentation lacks information. "
    "Distinguish a recommended action from an enforced requirement.\n"
    "3. When information is missing, say it cannot be determined from the retrieved "
    "excerpts. This does not establish absence from the full corpus or the real world. "
    "Do not infer that an omission was intentional.\n"
    "4. Cite each factual claim to the excerpt or excerpts that support it. "
    "Do not present an unrelated source as evidence about an entity with missing information. "
    "A statement about unavailable context is a limitation of this answer, not a fact "
    "established by an unrelated document.\n"
    "5. If excerpts disagree, describe and cite the competing claims. "
    "Do not choose an authoritative claim or combine conflicting requirements "
    "unless the supplied evidence resolves the conflict.\n"
    "6. Keep the answer focused on the question; omit unrequested facts."
)
VARIANTS = ("baseline", "revised")


def prompts_for(baseline):
    if not isinstance(baseline, str) or not baseline.strip():
        raise ValueError("The saved baseline prompt must be nonempty text")
    return {"baseline": baseline, "revised": baseline + REVISION}


def validate_frozen(report, dataset, corpus):
    if report.get("schema_version") != 1 or report.get("status") != "complete":
        raise ValueError("Use a complete schema-1 multi-document capture")
    if fingerprint(dataset) != report["dataset_sha256"] or fingerprint(corpus) != report["corpus_sha256"]:
        raise ValueError("Frozen case/corpus digest mismatch")
    validate_cases(dataset, corpus)
    prompts_for(report["settings"]["system_prompt"])
    cases = {c["id"]: c for c in dataset["cases"]}
    expected = {
        c["id"] + (f":k{k}" if k is not None else ":control")
        for c in dataset["cases"]
        if report["settings"]["suite"] == "all" or c["suite"] == report["settings"]["suite"]
        for k in (report["settings"]["ks"] if c["suite"] == "retrieved" else [None])
    }
    records = report["records"]
    if len(records) != len(expected) or {r["record_id"] for r in records} != expected:
        raise ValueError("Source record IDs are missing or duplicated")
    for record in records:
        case = cases[record["case_id"]]
        expected_id = case["id"] + (f":k{record['k']}" if record["k"] is not None else ":control")
        if (record["status"] != "complete" or record["suite"] != case["suite"]
                or record["question"] != case["question"] or record["record_id"] != expected_id):
            raise ValueError("Source record does not match its case")
        available = corpus if case["suite"] == "retrieved" else case["context"]
        if not record["excerpts"] or any(
            not any(item["source"] == doc["source"] and item.get("page") == doc.get("page")
                    and item["text"].strip() == doc["text"].strip() for doc in available)
            for item in record["excerpts"]
        ):
            raise ValueError("Frozen excerpt missing from its source/page snapshot")
        scores = inspect_answer(case, record["excerpts"], record["answer"])["retrieval_marker_scores"]
        if scores != record["retrieval_marker_scores"]:
            raise ValueError("Source evidence score mismatch")
    return records


def select_records(records, case_ids=None):
    if case_ids is None:
        return records
    unknown = set(case_ids) - {r["case_id"] for r in records}
    if unknown:
        raise ValueError("Unknown or uncaptured case IDs: " + ", ".join(sorted(unknown)))
    return [r for r in records if r["case_id"] in case_ids]


def citation_check(answer, excerpt_count):
    """Check numeric singles/groups, not factual support or all citation syntaxes."""
    spans = re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", answer)
    labels = sorted({int(n) for span in spans for n in re.findall(r"\d+", span)})
    return {"schema_version": 2, "labels": labels,
            "out_of_range": [n for n in labels if not 1 <= n <= excerpt_count],
            "has_numeric_citation": bool(labels),
            "scope": "Numeric [1] and [1, 2] forms only; syntax does not establish claim support"}


def run_pairs(records, prompts, generate, checkpoint):
    pairs = []
    for number, source in enumerate(records):
        context = format_excerpts(source["excerpts"])
        order = list(VARIANTS if number % 2 == 0 else reversed(VARIANTS))
        pair = {"record_id": source["record_id"], "case_id": source["case_id"],
                "suite": source["suite"], "k": source["k"], "question": source["question"],
                "excerpts": source["excerpts"], "context_text": context,
                "context_sha256": fingerprint(context),
                "retrieval_marker_scores": source["retrieval_marker_scores"],
                "call_order": order, "status": "running", "variants": {}}
        pairs.append(pair)
        checkpoint(pairs)
        for variant in order:
            result = {"status": "running", "prompt_sha256": fingerprint(prompts[variant]),
                      "context_sha256": pair["context_sha256"]}
            pair["variants"][variant] = result
            checkpoint(pairs)
            started = perf_counter()
            try:
                answer = generate(variant, source["question"], context)
                if not isinstance(answer, str) or not answer.strip():
                    raise ValueError("Expected a nonempty text answer")
                result.update(status="complete", answer=answer,
                              citation_syntax_only=citation_check(answer, len(source["excerpts"])))
            except BaseException as exc:
                result["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
                pair["status"] = result["status"]
                result["error"] = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                result["elapsed_seconds"] = perf_counter() - started
                checkpoint(pairs)
            print(f"{source['record_id']} :: {variant} captured; review pending", flush=True)
        pair["status"] = "complete"
        checkpoint(pairs)
    return pairs


def completed_review_records(pairs):
    return [{"record_id": pair["record_id"] + "::" + variant, "status": "complete"}
            for pair in pairs for variant, result in pair["variants"].items()
            if result["status"] == "complete"]
