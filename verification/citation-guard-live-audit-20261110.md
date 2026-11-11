# 🔬 Extension 6: First Live Citation-Guard Checkpoint

**🟩 Numeric guard/withholding verified in the saved run · 🔴 Accepted repair still lacks citation support · 🟠 Broader semantic evaluation and human review pending**

## 🗂️ Capture and provenance

| Field | Saved value |
| --- | --- |
| Run | 20261111T011524Z-f2bde230 |
| Local capture date | November 10, 2026, America/Los_Angeles |
| Runtime commit | 50bf8ba8e4b2cc02db22bf1a21ce2395541538fc |
| Publication commit | 65df395621f9fd700801f2aaaefe6de76b02d48f |
| Mode | Saved drafts plus targeted live repair |
| Inputs | 39 saved drafts from the rejected-refinement comparison |
| New generation calls recorded | Two, one per numerically invalid first draft |
| Model | qwen3.5:4b; saved digest matches source capture |
| Runtime | Python 3.12.10, Windows 11; clean tree reported |

This is replay of existing first drafts plus two new retry drafts, not a fresh
39-answer generation experiment. The other 37 drafts passed the numeric check
without a live model call. The rejected refined prompt supplies the two stress
cases only; it is not adopted as the interactive prompt.

## 🧪 Artifact reconstruction

The audit revalidates the source snapshot digest, 39 record identities and
questions, all frozen context hashes, and each initial draft/check. It then
re-executes the deterministic guard using the recorded draft sequence, without
model calls. It reproduces all 41 attempt checks, exact feedback strings,
statuses, withholding reasons, and final displayed answers. Timing fields are
excluded from deterministic comparison. The three captured code hashes match
the runtime commit after applying Windows CRLF line endings.

Two temporary corruptions were rejected: replacing the withheld visible answer
with a bad draft, and falsely marking its second citation check valid.

```powershell
python .\tools\audit_citation_guard_run.py .\verification\citation-guard-runs\20261111T011524Z-f2bde230
```

Expected: status passed; 39 records; 41 attempt checks; two recorded live calls;
37 accepted without a live call; one accepted after retry; one withheld after
retry. Run with assertions enabled. This checks saved consistency, not live
model-service reproduction or factual accuracy.

[Machine-readable audit](citation-guard-runs/20261111T011524Z-f2bde230/artifact-audit.json).

## 📊 What happened

| Population | Result | Interpretation |
| --- | --- | --- |
| 37 original drafts with valid numeric labels | Accepted unchanged | Replay only; no new factual-support finding |
| Three-project approvals k=2, refined | Retry repeats [7]; entire answer withheld | Correct bounded guard behavior; useful partial facts are also withheld |
| Cedar/Willow k=4, refined | Retry uses existing [1] and [4]; accepted | Numeric repair succeeded, but semantic support still fails |

Final structural statuses are 38 accepted and one guard-induced abstention.
Do not report this as 38 correct answers, or infer a general repair success
rate from two deliberately selected failures. The three conflict-control drafts
are replayed within the 37 numerically valid originals and remain separately
identified by suite in the raw report.

## 🔎 Retry source inspection

### Three-project comparison: failed retry is correctly withheld

The supplied excerpts are Atlas page 1 [1] and Maple [2]. They contain approval
requirements for those two projects but no Cedar policy. The retry correctly
reports the available requirements and bounds Cedar's absence to the excerpts.
It nevertheless attaches nonexistent [7] to Cedar's limitation statement again.
The guard rejects the draft after one retry and displays the fixed withholding
message. It does not silently delete the label or expose the rejected answer.

The retry is incomplete relative to all three requested projects because the
frozen input omits Cedar evidence. Correct abstention about Cedar does not fill
that evidence gap. Numeric withholding is separate from the model's semantic
abstention and from a claim that all retrieved evidence is useless.

### Willow comparison: accepted labels still point to an unrelated source

The retry correctly states Cedar's tests/maintainer policy [1]. It also says
Willow requirements cannot be determined from the provided documents, but
attaches [4]. That excerpt is docs/birch-project.md, about Birch's disk-space
failure and Birch's own unspecified approval requirements. It does not support
a Willow policy or the whole-context absence conclusion.

The correct context-bounded abstention therefore still fails citation support
under the same source-scope rule used in earlier reviews. Numeric validation
worked as designed: [4] exists. It does not establish entailment or relevance.
The visible accepted repair is not marked factually verified.

[Two proposed assistant retry reviews](citation-guard-runs/20261111T011524Z-f2bde230/assistant-review.json)
record completeness, attribution, citation support, and uncertainty separately.
They are explicitly AI-assisted judgments, not independent human ground truth.

## 🧭 Checkpoint and remaining work

Extension 6's first numeric-guard checkpoint is now locally exercised and
audited: initial rejection, one live retry, numeric acceptance, and bounded
withholding have recorded examples. The standalone guarded interactive command
has not yet been recorded in a user transcript. The 89-test suite passed in
development; only the earlier 72-test Windows output has been supplied.

Remaining Extension 6 work is claim-to-source support evaluation and a rubric
that separates correct missing-evidence abstention, unnecessary refusal,
unresolved conflict, and guard-induced withholding. Add new cases and independent
human validation before making broader claims. Extensions 7–9 remain on the
[project tracker](../guides/PROJECT_TRACKER.md); the current checkpoint does not
complete all of Extension 6.

The runtime code, default prompt, rejected candidate status, original source
reports, and raw guard capture are unchanged by this audit. Do not compensate
for semantic citation defects by deleting labels or relabeling a numeric pass
as grounded correctness.

[Guard guide](../guides/CITATION_GUARD.md) ·
[Raw dashboard](citation-guard-runs/20261111T011524Z-f2bde230/summary.md) ·
[Tutorial credit](../README.md#tutorial-acknowledgment-and-attribution)
