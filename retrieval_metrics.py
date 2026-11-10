"""Dependency-free scoring for authored retrieval evidence, not answer quality."""

METRICS = ("hit_at_k", "complete_at_k", "coverage_at_k", "mrr_at_k", "precision_at_k")


def normalized(text):
    return " ".join(text.casefold().split())


def matches(group, candidate):
    """Require the source, optional PDF page, and every authored text marker."""
    return (
        candidate["source"] == group["source"]
        and candidate.get("page") == group.get("page")
        and all(normalized(term) in normalized(candidate["text"])
                for term in group["contains"])
    )


def validate_dataset(dataset):
    if dataset.get("schema_version") != 1:
        raise ValueError("Unsupported case schema")
    sources = dataset.get("expected_sources", [])
    if not sources or len(sources) != len(set(sources)):
        raise ValueError("Expected sources must be nonempty and unique")
    cases = dataset.get("cases", [])
    if not cases:
        raise ValueError("No evaluation cases")
    ids = set()
    for case in cases:
        if not isinstance(case.get("id"), str) or not case["id"].strip():
            raise ValueError("Each case needs an ID")
        if case["id"] in ids:
            raise ValueError("Duplicate case ID: " + case["id"])
        ids.add(case["id"])
        if not isinstance(case.get("question"), str) or not case["question"].strip():
            raise ValueError("Each case needs a question")
        groups = case.get("required_evidence")
        kind = case.get("kind")
        if not isinstance(groups, list) or kind not in {"evidence", "no_evidence"}:
            raise ValueError("Invalid case kind or evidence list")
        if (kind == "evidence") != bool(groups):
            raise ValueError("Only evidence cases must have required evidence")
        group_ids = set()
        for group in groups:
            if not isinstance(group.get("id"), str) or not group["id"].strip():
                raise ValueError("Each evidence group needs an ID")
            if group["id"] in group_ids:
                raise ValueError("Duplicate evidence group ID within case")
            group_ids.add(group["id"])
            if group.get("source") not in sources:
                raise ValueError("Evidence source outside the fixture corpus")
            page = group.get("page")
            if page is not None and (type(page) is not int or page < 1):
                raise ValueError("PDF pages must be positive integers")
            terms = group.get("contains")
            if not isinstance(terms, list) or not terms or any(
                not isinstance(term, str) or not term.strip() for term in terms
            ):
                raise ValueError("Evidence groups need nonempty text markers")
    if not any(case["kind"] == "evidence" for case in cases):
        raise ValueError("At least one evidence case is required")


def score_case(case, ranked, k):
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    selected = ranked[:k]
    if case["kind"] == "no_evidence":
        return {**{key: None for key in METRICS}, "matched_groups": [],
                "returned_chunks": len(selected)}
    groups = case["required_evidence"]
    matched = set()
    relevant_ranks = []
    for rank, candidate in enumerate(selected, start=1):
        hits = {group["id"] for group in groups if matches(group, candidate)}
        if hits:
            relevant_ranks.append(rank)
            matched.update(hits)
    return {
        "hit_at_k": int(bool(matched)),
        "complete_at_k": int(len(matched) == len(groups)),
        "coverage_at_k": len(matched) / len(groups),
        "mrr_at_k": 1 / relevant_ranks[0] if relevant_ranks else 0.0,
        "precision_at_k": len(relevant_ranks) / len(selected) if selected else 0.0,
        "matched_groups": sorted(matched),
        "returned_chunks": len(selected),
    }


def summarize(scores):
    eligible = [score for score in scores if score["hit_at_k"] is not None]
    if not eligible:
        raise ValueError("No evidence cases available to summarize")
    return {
        "evidence_cases": len(eligible),
        "no_evidence_controls": len(scores) - len(eligible),
        **{key: sum(score[key] for score in eligible) / len(eligible)
           for key in METRICS},
    }
