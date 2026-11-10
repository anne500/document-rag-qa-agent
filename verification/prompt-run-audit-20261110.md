# 🔬 Frozen-Context Prompt Comparison: First Run Audit

**🟩 Artifact audit passed · 🟩 Assistant source review recorded · 🟠 Independent human validation pending**

## 🗂️ Identity and evidence

| Field | Saved value |
| --- | --- |
| Prompt run | 20261110T232200Z-d0f222aa |
| Runtime commit | 11639b864f567c7e0254ce6f944226aafce38c76 |
| Publication commit | 3c8002adb6f6f308ea9dc1a07d9a4c86cb88588a |
| Source capture | 20261110T222813Z-bc04d7e8 |
| Runtime | Python 3.12.10 on Windows 11; clean tree reported |
| Model | qwen3.5:4b, temperature 0, reasoning disabled |
| Design | 13 frozen contexts, two fresh prompt calls per context; alternating order |
| Review identity | ChatGPT/Codex AI assistant; not an independent human reviewer |

The saved model digest matches the source capture. All 13 new baseline answer
strings exactly match the corresponding older captured answers. This is an
observation about the saved text, not a general determinism guarantee or an
independent verification of model-service execution or caching behavior.

## 🧪 Reproducible artifact audit

The audit checked:

- All 13 pairs and 26 completed answers.
- All 38 frozen-context excerpt occurrences against their source records;
  source validation also checks source/page text against the frozen corpus/control.
- Exact question, excerpt order, labels, context text, and source marker scores.
- All 26 answer-context hashes and 26 answer-prompt hashes.
- The source-report, case, and corpus snapshot digests, plus both exact prompts.
- All 13 recorded alternating call orders and variant insertion orders.
- All 26 numeric citation syntax results, including grouped labels; none is out of range.
- The source capture's 65 marker score values.
- All six code digests against the runtime commit using Windows CRLF line endings.
- The original human worksheet: 26 null-rating records remain untouched.

[Machine-readable audit](prompt-runs/20261110T232200Z-d0f222aa/artifact-audit.json).
Run from a repository checkout with assertions enabled:

```powershell
python .\tools\audit_prompt_run.py .\verification\prompt-runs\20261110T232200Z-d0f222aa
```

Development checks also changed context text and a citation result in separate
temporary report copies; the audit rejected both. It makes no model, embedding,
or retrieval calls. It confirms saved consistency, not live inference reproduction
or semantic answer accuracy. The source code records no retrieval call for this
experiment, and both prompt variants use the same saved context.

## 📊 Proposed assistant judgments

The same four-dimension rubric and context-absence interpretation from the
[source audit](multidoc-run-audit-20261110.md) were retained. The two k settings
are shown separately in the machine-readable review summary; this table gives
descriptive counts across the 12 retrieved-context pairs, excluding the control.

| Dimension | Baseline passes | Revised passes | Improved pairs | Regressed pairs |
| --- | ---: | ---: | ---: | ---: |
| Expected-answer completeness | 10/12 | 10/12 | 0 | 0 |
| Attribution | 12/12 | 12/12 | 0 | 0 |
| Citation support | 9/12 | 11/12 | 2 | 0 |
| Uncertainty | 11/12 | 12/12 | 1 | 0 |

These are proposed AI assistant ratings on authored development cases, not
validated human-scored accuracy or statistically established prompt effects.
The k=2 and k=4 contexts reuse questions and are not independent samples.
The separate conflict control passes all four dimensions for both prompts.

| Source context | Baseline issue | Revised result |
| --- | --- | --- |
| Cedar/Maple, both k settings | None identified | Expected conditions and source attribution retained |
| Atlas pages, both k settings | None identified | Correct approval roles and failure cause retained |
| Cedar/Birch k=2 | Unsupported editorial omission and overbroad summary | Both claims removed; correct scoped missing-information statement |
| Cedar/Birch k=4 | Unsupported claim that build failures prevent rerunning | Rerun restriction removed; unspecified approval policy retained |
| Three approvals k=2 | Cedar evidence unavailable; answer incomplete | Still incomplete; clearer abstention, with a new scope caveat below |
| Three approvals k=4 | All conditions supported; extra Birch note | Complete and supported; Birch digression removed |
| Four causes k=2 | Birch/Atlas evidence unavailable | Still incomplete; explicitly scoped abstentions retained |
| Four causes k=4 | All four causes supported | All four causes and citations retained |
| Cedar/Willow k=2 | Maple citation used for whole-context statement | Partial presentation improvement; citation-scope defect remains |
| Cedar/Willow k=4 | Correctly scoped abstention | Correctly scoped abstention retained |
| Larch control | Conflict accurately disclosed | Conflict accurately disclosed; no invented policy resolution |

Detailed proposed ratings and reasons:

- [Assistant review](prompt-runs/20261110T232200Z-d0f222aa/assistant-review.json)
- [Grouped descriptive counts](prompt-runs/20261110T232200Z-d0f222aa/assistant-review-summary.json)
- [Per-context, per-dimension changes](prompt-runs/20261110T232200Z-d0f222aa/assistant-paired-deltas.json)

The original review.json is still available for a human to confirm, reject,
or revise these judgments. The assistant files do not complete human review.

## 🔎 Remaining defects and qualitative trade-offs

### Willow k=2: partial improvement, persistent citation scope

The revision removes the separate “Lack of Willow information” evidence bullet.
However, it still says the supplied documents contain Cedar and Maple notes
and attaches only Maple's [2] citation to that combined-context statement.
Maple alone does not establish the Cedar portion or the full context inventory.
Under the unchanged all-claims citation rule, citation support remains failed.
The model correctly abstains from inventing Willow policy in both versions.

### Three-project k=2: a new scope concern without a four-dimension regression

The revised answer places Maple certificate-recovery guidance under “Required
Checks” while answering a release-approval question. Its sentence explicitly
limits the action to “before rerunning the build,” which the Maple excerpt
supports. For that reason, no additional hard citation/attribution failure is
assigned. Its placement nevertheless risks suggesting a new release prerequisite.
This is a new qualitative scope concern and should be corrected before adoption.
Mixed-script approver headings are also present in that answer; they are cosmetic.

The revised Birch answers add Cedar deployment-date/cloud-provider omissions,
and the k=2 answer adds Birch disk-space details. Those facts are supported,
but unrequested. The revision's instruction to stay focused is therefore not
uniformly followed. The existing rubric has no dedicated brevity/relevance
dimension; these concerns remain explicit notes instead of silently adding a
new scoring dimension after seeing the outputs.

### Frozen evidence still limits completeness

Both prompts fail expected-answer completeness for the two broader k=2 contexts.
The missing Cedar policy and Birch/Atlas failure facts were never supplied.
Improved missing-information wording is valuable but cannot replace retrieval
coverage. Complete answers at k=4 do not establish a prompt-caused recovery of
missing evidence because the prompt comparison holds each context fixed.

## 🧭 Adoption recommendation

Keep the revised prompt experimental. It is a useful candidate: both targeted
Birch defects were removed in this run without a pass/fail regression under
the existing four dimensions. Willow's citation-scope defect and unrequested
recovery-policy material still need attention. Independent human validation
is pending. The interactive prompt and retrieval defaults remain unchanged.

Next, test a narrow instruction refinement that removes unnecessary context
inventory statements and separates build recovery from release requirements.
Preserve this comparison as the baseline for that next iteration. Then include
new questions and independent human review before making a default change.

## ⚠️ Limits

This is one generation per prompt/context, on a small fictional dataset already
used to motivate the prompt revision. Order alternates but is not randomized;
there are no repeats, blinded ratings, held-out evidence, or statistical tests.
Model/service state and caching effects are not independently characterized.
No latency improvement, general superiority, or thesis-effectiveness claim is
supported. Assistant review is a transparent proposal, not human ground truth.

[Raw capture dashboard](prompt-runs/20261110T232200Z-d0f222aa/summary.md) ·
[Experiment guide](../guides/PROMPT_COMPARISON.md) ·
[Tutorial acknowledgment](../README.md#tutorial-acknowledgment-and-attribution)
