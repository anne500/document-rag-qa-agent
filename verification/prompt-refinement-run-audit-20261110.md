# 🔬 Three-Prompt Refinement: First Run Audit

**🟩 Saved artifacts consistent · 🔴 Refined candidate rejected for adoption · 🟠 Independent human ratings pending**

## 🗂️ Provenance

| Field | Saved value |
| --- | --- |
| Run | 20261111T001306Z-98deeb8f |
| Local capture date | November 10, 2026, America/Los_Angeles |
| Runtime commit | 978eefb7893af6c2d722f4354059b98c952b55d0 |
| Publication commit | 4df805dfd6bb082dcce616f5a105211937ee2e0f |
| Contexts and answers | 13 frozen contexts, 39 answers |
| Model/settings | qwen3.5:4b, temperature 0, reasoning disabled |
| Order | Cyclic baseline/revised/refined; one generation per variant/context |
| Review identity | ChatGPT/Codex AI assistant; independent human review pending |

The UTC run identifier crosses midnight; the local capture date is November 10.
All 13 baseline and 13 revised answer strings match the corresponding earlier
two-prompt run. That is an observation of saved text, not an independent proof
of deterministic service behavior or of whether caching occurred.

## 🧪 Artifact audit and corrected error handling

The audit validates all 39 answer-context hashes and 39 prompt hashes, 38 frozen
excerpt occurrences, three snapshot digests, 13 cyclic orders, and 39 numeric
citation results. Source validation recomputes 65 marker values. Six runtime
code hashes match Git source bytes with Windows CRLF line endings. The saved
chat-model digest matches the source capture. All 39 human-review rows remain null.

The original helper assumed every answer had in-range citations and asserted
that none were invalid. That conflated answer quality with artifact consistency.
The helper now verifies that the recorded citation result matches the answer,
then reports any bad labels as warnings. It still rejects altered context,
hashes, or citation metadata. No raw answer or capture file was changed.

| Refined answer | Available excerpt labels | Invalid label |
| --- | --- | --- |
| three_unit_approvals:k2 | [1], [2] | [7] |
| known_unknown:k4 | [1], [2], [3], [4] | [7] |

The saved report already recorded both errors correctly. The audit should pass
consistency checks while reporting two citation warnings; neither answer thereby
passes citation support. A numbered instruction also uses 7, but the record does
not establish why the model generated [7]. Instruction-number copying is only a
hypothesis, not an audited cause.

```powershell
python .\tools\audit_prompt_run.py .\verification\prompt-runs\20261111T001306Z-98deeb8f
```

Expected: status passed, 39 answers checked, out_of_range_numeric_labels = 2,
and two citation_warning_records. No model calls are made. Run with Python
assertions enabled. All 72 offline tests passed in development, including the
extended regression test: a correctly saved [7] warning is accepted, concealed
warning metadata and a changed context hash are rejected.

[Machine-readable audit](prompt-runs/20261111T001306Z-98deeb8f/artifact-audit.json).

## 📊 Proposed assistant judgments

Counts below cover 12 retrieved-context comparisons and exclude the separate
conflict control. They use the prior four-dimension rubric, with the same
rules for whole-context citations and scoped abstention. Completeness checks
the expected claims; unsupported added claims are counted separately.

| Dimension | Baseline passes | Revised passes | Refined passes |
| --- | ---: | ---: | ---: |
| Expected-answer completeness | 10/12 | 10/12 | 10/12 |
| Attribution | 12/12 | 12/12 | 12/12 |
| Citation support | 9/12 | 11/12 | 6/12 |
| Uncertainty | 11/12 | 12/12 | 10/12 |

Compared with the first revised prompt, the refinement has five citation-support
regressions and two uncertainty regressions, with no gains in those scored
dimensions. Local wording/scope improvements are still recorded below. Both
broader k=2 contexts remain incomplete because the required evidence is absent.
All three variants pass the four dimensions in the separate Larch control.

These are AI assistant proposals on authored development examples, not validated
human accuracy. Entity attribution is not failed merely because an extra claim
is unsupported or a source citation is wrong; those defects have their own
dimensions. Scope, layout, and verbosity remain qualitative observations.

## 🔎 Findings by case

| Refined context | Source-grounded finding |
| --- | --- |
| Cedar/Maple k=2 | Required roles/checks are correct, but the final sentence casts the specified approval requirements as potentially recommended or unknown |
| Cedar/Maple k=4 | Core requirements are present; a new limitation wrongly says the comparison cannot be fully determined because unrelated deployment/cloud information is missing; a Maple implication cites Cedar |
| Atlas pages, both settings | Correct approvers, failure cause, and PDF citations retained |
| Cedar/Birch, both settings | Prior Birch improvements retained; no invented intentional omission or rerun prohibition |
| Three approvals k=2 | Recovery digression removed, but missing Cedar statement now cites nonexistent [7] |
| Three approvals k=4 | Correct requested conditions followed by an unrequested all-project missing-information statement supported only by Cedar [3] |
| Four causes, both settings | Correct available causes and bounded abstentions retained; k=2 still incomplete |
| Willow k=2 | Context inventory removed, but Willow's unavailable policy is still cited to unrelated Maple [2] |
| Willow k=4 | Correct abstention acquires nonexistent [7]; a Willow missing-information line also appears under Cedar's heading |
| Larch control | Both competing policies cited; no invented authority or combined approval rule |

The Cedar/Maple k=2 hedge is judged to fail citation support and uncertainty:
both notes explicitly say a release requires approval. Whether enforcement is
implemented technically is a distinct, unasked question; the answer's broader
“enforced or recommended” wording blurs a stated policy requirement. This is
an interpretation for a human reviewer to confirm or revise.

The Cedar/Maple k=4 answer likewise has all expected requirements, so its
completeness rating stays pass. Its added assertion that the requested comparison
is unavailable is scored under unsupported claims and uncertainty instead of
silently changing the completeness rule. The all-project statement in the
three-approval k=4 answer is citation-failed under the same source-scope rule
used for prior Willow inventory statements.

Detailed reasons for all 39 proposed ratings, grouped counts, and directional
changes are saved separately from the human worksheet:

- [Assistant review](prompt-runs/20261111T001306Z-98deeb8f/assistant-review.json)
- [Grouped descriptive counts](prompt-runs/20261111T001306Z-98deeb8f/assistant-review-summary.json)
- [Per-context changes](prompt-runs/20261111T001306Z-98deeb8f/assistant-paired-deltas.json)

## 🧭 Adoption decision and next direction

Do not adopt this refined prompt. It retains one targeted fix but introduces
invalid citations and unhelpful uncertainty, and it does not repair the Willow
source-scope defect. The interactive default remains unchanged. The earlier
revised prompt remains an experimental candidate with its previously documented
limitations; this audit does not promote it to the default either.

Preserve the negative result rather than adding another instruction layer
immediately. A useful next step is to test citation-bound checks at the answer
boundary and use a small set of new questions to evaluate a simpler candidate.
Invalid citations should be flagged or handled by a tested retry/abstention
policy, not silently deleted. Even valid labels still need semantic support
review. Any such application behavior is future work, not implemented here.

Independent human confirmation remains needed. This is a small, fictional,
fixed-order development experiment with no repeats, blinded ratings, statistical
tests, or held-out evidence. Longer instructions did not deliver uniform gains
in this run; no general conclusion about prompt length or model reliability is
established. Timing is not treated as an efficacy metric.

[Raw capture dashboard](prompt-runs/20261111T001306Z-98deeb8f/summary.md) ·
[Three-prompt design](../guides/PROMPT_REFINEMENT.md) ·
[Tutorial provenance](../README.md#tutorial-acknowledgment-and-attribution)
