"""Bounded numeric-citation validation. This does not verify factual support."""

import re
from time import perf_counter

WITHHELD = "Answer withheld because its citation labels could not be validated. Please review the retrieved sources or rephrase the question."
GENERATION_FAILED = "I could not complete answer generation. Please try again."


def check_citations(answer, excerpt_count):
    if type(excerpt_count) is not int or excerpt_count < 0:
        raise ValueError("excerpt_count must be a nonnegative integer")
    if not isinstance(answer, str):
        raise ValueError("Expected a text answer")
    labels = set()
    malformed = []
    # Only numeric-looking square brackets are interpreted as citations.
    # Also flag unfinished spans, signs, ranges, and unsupported separators.
    for match in re.finditer(r"\[(?=\s*[+-]?[0-9])([^\]\n]*)(\]|(?=\n|$))", answer):
        body, closing = match.groups()
        if not closing or not re.fullmatch(r"\s*[0-9]+(?:\s*,\s*[0-9]+)*\s*", body):
            malformed.append(match.group(0))
            continue
        tokens = re.findall(r"[0-9]+", body)
        if any(len(token) > 9 for token in tokens):
            malformed.append(match.group(0))
            continue
        labels.update(int(token) for token in tokens)
    invalid = sorted(n for n in labels if not 1 <= n <= excerpt_count)
    return {"schema_version": 1, "valid": bool(answer.strip()) and not invalid and not malformed,
            "labels": sorted(labels), "out_of_range": invalid, "malformed_numeric_spans": malformed,
            "empty_answer": not bool(answer.strip()), "has_numeric_citation": bool(labels),
            "scope": "Numeric citation syntax/range only; no factual-support, completeness, or semantic-abstention guarantee"}


def retry_instruction(excerpt_count):
    allowed = ", ".join(f"[{n}]" for n in range(1, excerpt_count + 1))
    return (
        "The previous draft failed numeric-citation validation. Generate a fresh answer "
        "to the same question using the same excerpts. Available source labels are " + allowed + ". "
        "Use only those source labels in [n] or [n, m] form. Do not cite numbered "
        "instructions as sources. Do not merely remove labels from unsupported claims; "
        "answer only from supplied evidence and state when information is unavailable."
    )


def guarded_answer(question, context, excerpt_count, generate, max_retries=1, on_update=None):
    """generate(question, context, feedback) returns a draft; never edits a draft."""
    if type(max_retries) is not int or max_retries not in (0, 1):
        raise ValueError("max_retries must be 0 or 1")
    check_citations("", excerpt_count)
    result = {"status": "running", "answer": None, "attempts": [],
              "validation_scope": "numeric citation syntax/range only"}
    checkpoint = on_update or (lambda value: None)
    checkpoint(result)
    if excerpt_count == 0:
        result.update(status="abstained", reason="no_excerpts",
                      answer="No retrieved excerpts are available for an evidence-based answer.")
        checkpoint(result)
        return result
    for number in range(max_retries + 1):
        attempt = {"attempt": number + 1, "status": "running",
                   "feedback": None if number == 0 else retry_instruction(excerpt_count)}
        result["attempts"].append(attempt)
        checkpoint(result)
        started = perf_counter()
        try:
            draft = generate(question, context, attempt["feedback"])
            check = check_citations(draft, excerpt_count)
            attempt.update(status="accepted" if check["valid"] else "rejected", draft=draft, check=check)
        except Exception as exc:
            attempt.update(status="generation_failed", error=f"{type(exc).__name__}: {exc}")
            result.update(status="generation_failed", answer=GENERATION_FAILED)
            return result
        except KeyboardInterrupt:
            attempt["status"] = "interrupted"
            result["status"] = "interrupted"
            raise
        finally:
            attempt["elapsed_seconds"] = perf_counter() - started
            checkpoint(result)
        if check["valid"]:
            result.update(status="accepted", answer=draft)
            checkpoint(result)
            return result
    result.update(status="abstained", reason="invalid_citations", answer=WITHHELD)
    checkpoint(result)
    return result
