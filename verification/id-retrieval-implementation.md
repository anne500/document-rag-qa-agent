# 🧪 Identifier-Aware Retrieval: Implementation Verification

## 🟩 Offline checks

41 tests passed in development on November 10, 2026:
the 22 existing retrieval-lab tests plus 19 identifier-specific tests.
No embedding or chat model is invoked by these tests.

| Area | Observed offline |
| --- | --- |
| Identifier boundaries | Case normalization, release labels, repeated IDs, prefix collisions, normal hyphenated words, ASCII syntax |
| Ranking | Exact match outside the pool, multiple IDs, unknown IDs, mixed known/unknown IDs |
| Evidence identity | Source/page preservation, duplicate removal, stable lexical tie ordering |
| Semantic fallback | No-ID and unknown-only queries preserve semantic order |
| Adapter | Reads inventory once, caps search pool, checks invalid settings/metadata |
| Paired runner | Saves both methods, LF CSV, charts, per-case deltas, and negative outcomes |
| Failures | Preserves completed pairs and failed/interrupted status |

These controlled checks establish implementation behavior, not local model
quality or performance gains.

## 🟩 First Paired Local Run

The actual five-unit corpus and 14 cases validated, and the paired local
Ollama/Chroma run completed. Its [evidence audit](identifier-run-audit-20261110.md)
reproduces all 56 method rankings, 168 scores, 72 delta rows, 12 CSV rows,
and both charts. The corpus/code snapshot hashes also match.

Maple moved from rank 2 to rank 1 at both chunk sizes. All 12 fallback pairs
retained identical results, and no tested metric regressed in this run.
These are small development-set findings, not answer-quality measurements.

## 🟠 Remaining Checks

- Record the 41-test suite output on the user's Windows environment.
- Check the interactive answer and citations with explicit ID-priority mode.
- Evaluate unknown IDs and larger corpora beyond the offline controlled checks.
- Test generalization using new, held-out questions and artifact revisions.

## 🔗 Reproduction and scope

See the [colored identifier guide](../guides/IDENTIFIER_RETRIEVAL.md).
The existing [semantic baseline audit](retrieval-run-audit-20261110.md)
remains the historical comparison; it is not a measurement of the new rule.
