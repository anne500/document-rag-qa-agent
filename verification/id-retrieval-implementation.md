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

## 🟠 Pending local checks

- Run the 41-test suite on the user's Windows environment.
- Validate the actual five-unit corpus and 14 cases.
- Run the paired Ollama/Chroma evaluation.
- Inspect original semantic ranks, exact-ID traces, metrics, and regressions.
- Check the interactive answer and citations with the new mode.
- Publish the selected measured run and update the central dashboard.

## 🔗 Reproduction and scope

See the [colored identifier guide](../guides/IDENTIFIER_RETRIEVAL.md).
The existing [semantic baseline audit](retrieval-run-audit-20261110.md)
remains the historical comparison; it is not a measurement of the new rule.
