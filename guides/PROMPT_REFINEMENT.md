# 🧪 Second Prompt Refinement: Scope and Missing Information

**🟩 First live capture audited; 72 development tests passed. 🔴 Refinement rejected for adoption. 🟠 Human review pending.**

The [first prompt audit](../verification/prompt-run-audit-20261110.md) found two
Birch improvements, a persistent Willow citation-scope issue, and supported but
unrequested recovery guidance placed under release checks. This refinement
targets those remaining issues without changing the first two prompt texts.

## 📝 Three prompt variants

| Variant | Instructions | Role |
| --- | --- | --- |
| baseline | Exact original prompt from the source capture | Historical instruction baseline |
| revised | Baseline plus the first evidence-use rules | Previously measured candidate |
| refined | Revised plus the new scope rules | Unmeasured second candidate |

The new rules ask the model to:

- State that requested information cannot be determined from retrieved excerpts,
  without listing other projects as justification or attaching an unrelated citation.
- Continue citing a document that explicitly says its own requirements are unspecified.
- Keep release approval, build-failure causes, and recovery actions distinct;
  include the categories requested by the question.
- Avoid extra deployment/cloud/failure details merely because they are available.

There are no fixture names, expected answers, or prior review ratings in any
prompt. The exact prompts are saved for every new experiment.

## 🔄 Fair inputs and call order

All three variants receive the same question, labeled excerpt text, source/page
order, and model settings. Each answer is generated afresh without conversation
history; old saved answers are provenance, not new experimental outputs.

| Context index | First | Second | Third |
| --- | --- | --- | --- |
| 1 | baseline | revised | refined |
| 2 | revised | refined | baseline |
| 3 | refined | baseline | revised |
| 4 | baseline | revised | refined |

The cycle repeats. Across 13 contexts, first position is not perfectly balanced:
baseline starts five times and the other two start four times each. This is a
fixed cyclic order, not a randomized/repeated experiment or a latency benchmark.
Temperature 0 does not guarantee deterministic output.

The existing two-prompt command and alternating order are retained. The three
variants are selected only with --include-refined. The interactive prompt and
retrieval defaults are unchanged.

## 🚀 Run the full comparison

```powershell
git pull --ff-only origin main
python -m unittest discover -s tests -v
python .\eval_prompt_comparison.py --include-refined --validate-only
```

Expected: **72 passing tests** and **13 frozen contexts, 39 planned chat calls**.
Validation uses the existing source capture and makes no chat, embedding,
retrieval, index, or live-document reads.

```powershell
python .\eval_prompt_comparison.py --include-refined
```

The full run makes 39 sequential local Qwen calls. Allow several minutes;
the previous 26-answer run took roughly ten minutes on the user's machine.
There is no model call from the implementation tests.

For a shorter check restricted to the remaining issues and Birch regressions:

```powershell
python .\eval_prompt_comparison.py --include-refined --case-ids cedar_birch_missing known_unknown three_unit_approvals
```

This selects six contexts and makes 18 calls. It excludes Atlas/failure-cause
and Larch-conflict checks, so label that reduced scope if used.

## 💾 Inspect and reproduce

Results use a unique verification/prompt-runs/ directory, with the same seven
raw artifacts as the earlier experiment. report.json records all three prompt
texts, call order, exact contexts/hashes, new answers, settings, code hashes,
model identity, errors, and numeric citation checks. review.json has separate
initially null ratings for each completed variant. No automatic winner is assigned.

The updated helper accepts the original two-prompt report and the new three-prompt
report. Once a new run exists, substitute its actual directory:

```powershell
$promptRunPath = ".\verification\prompt-runs\REPLACE_WITH_NEW_RUN_ID"
python .\tools\audit_prompt_run.py $promptRunPath
```

The helper checks recorded consistency without a model call. Its historical
output field alternating_call_orders_checked counts validated call orders;
for a three-prompt run those orders are cyclic. Semantic citation support is
still separate from numeric syntax and artifact checks.

## 🟠 Review criteria and decision

Compare all three answers for each frozen context using the established four
dimensions: completeness, attribution, citation support, and uncertainty.
Also preserve the previously noted scope caveats as qualitative observations:

| Question | What to inspect |
| --- | --- |
| Cedar and Willow | Short bounded abstention; no unrelated project inventory citation |
| Cedar and Birch | Cited unspecified-policy statement; no intentional omission or rerun prohibition |
| Three-project approvals | No recovery guidance disguised as approval checks; missing Cedar acknowledged at k=2 |
| Four failure causes | Correct causes when present; missing facts not fabricated at k=2 |
| Atlas PDF pages | Correct page-specific attribution |
| Larch conflict | Both claims cited; no invented authority or combined policy |

Retain improvements and regressions. A shorter answer is not automatically
more complete, and a prompt cannot recover evidence excluded from its context.
No new relevance score is silently added to the earlier four-dimension rubric.
Any assistant-proposed ratings must stay separate from independent human review.

The same development cases motivated this refinement. Favorable results would
therefore remain development findings; new questions and independent human
validation are needed before broader reliability claims or a default change.

[Implementation verification](../verification/prompt-refinement-implementation.md) ·
[Prior prompt comparison](PROMPT_COMPARISON.md) ·
[Tutorial acknowledgment](../README.md#tutorial-acknowledgment-and-attribution)


## 🔴 First Live Result: Refinement Rejected

The [first 39-answer audit](../verification/prompt-refinement-run-audit-20261110.md)
records regressions, including two nonexistent [7] labels, unsupported uncertainty,
and a persistent Willow citation-scope defect. Proposed assistant citation-support
passes are 9/12 baseline, 11/12 revised, and 6/12 refined. The conflict control
remains separate. Human review is pending; the interactive default is unchanged.

The audit helper now accepts correctly recorded citation failures and reports
warning records. It rejects inconsistent metadata or changed context. Thus
status passed establishes artifact consistency even when answer defects exist.
The original capture and its null human-review worksheet are preserved.
