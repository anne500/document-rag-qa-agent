# 💬 Identifier-Priority Mode: Interactive Maple Check

**🟩 One manually reviewed example passed · 🟠 Broader answer evaluation remains open**

## 🗂️ Evidence source and setup

Recorded from the user's PowerShell transcript shared on November 10, 2026.
This record preserves that observation; it is not an independent rerun.

| Field | Observed value |
| --- | --- |
| Command | python .\qa_agent.py --retrieval-mode id_priority |
| Index | Reused unchanged index 8a06fad96141 |
| Mode | id_priority |
| Semantic candidates | 5 |
| Exact-ID candidates | 1 |
| Query ID | MAPLE-207 |
| Matched ID | MAPLE-207 |
| Unknown IDs | None |
| Elapsed time | 30.23 seconds, one observation |
| Runtime commit and chat-model digest | Not printed in this transcript |

## ❓ Question

> Did MAPLE-207 fail because the runner ran out of disk space?

## 🔎 Retrieval trace

```json
{
  "query_ids": ["MAPLE-207"],
  "matched_ids": ["MAPLE-207"],
  "unknown_ids": [],
  "policy": "id_priority",
  "semantic_candidates": 5,
  "exact_candidate_count": 1
}
```

## 💬 Observed answer

> No, MAPLE-207 did not fail because the runner ran out of disk space. According to the provided documents, it failed because the signing certificate had expired [1]. The document mentions that BIRCH-309 failed due to a lack of disk space, but this is unrelated to MAPLE-207 [2].

## 📚 Citation inspection

| Citation | Retrieved source | Claim supported by that source |
| --- | --- | --- |
| [1] | [Maple project note](../docs/maple-project.md) | MAPLE-207 failed because its signing certificate expired |
| [2] | [Birch project note](../docs/birch-project.md) | BIRCH-309 failed because the runner ran out of disk space |

Both claims match the published fictional fixtures.
Maple was source [1], and the answer kept the two projects' failure causes separate.

## 🟩 What this verifies

- The identifier-priority adapter works in the interactive application.
- The selected index can be reused with the optional ranking mode.
- The trace identifies the known query ID and the applied policy.
- The model produced a correct answer to this misleading question.
- Both answer citations point to supporting fixture documents in this example.

## ⚠️ Interpretation limits

This is one manual example, not a general answer-accuracy or citation benchmark.
The earlier semantic k=2 example also answered this question correctly, so this
check does not establish improved answer accuracy over semantic k=2.
The paired retrieval experiment separately established the observed rank change.

The single elapsed-time observation does not establish a latency improvement.
Unknown identifiers, conflicting evidence, stale artifacts, and broader
multi-document answer quality still require evaluation.
The default application mode remains semantic; ID priority is explicitly selected.

## 🔗 Related work and credit

- [Paired retrieval audit](identifier-run-audit-20261110.md)
- [Identifier architecture and method](../guides/IDENTIFIER_RETRIEVAL.md)
- [Central verification dashboard](DASHBOARD.md)
- [Darsh Shah/freeCodeCamp tutorial acknowledgment](../README.md#tutorial-acknowledgment-and-attribution)
