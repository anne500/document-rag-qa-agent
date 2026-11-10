# 🔬 First Multi-Document Capture: Evidence Audit and Assistant Review

**🟩 Saved artifacts audited · 🟩 Assistant source review recorded · 🟠 Independent human review pending**

## 🗂️ Run and provenance

| Field | Saved value |
| --- | --- |
| Run | 20261110T222813Z-bc04d7e8 |
| Runtime commit | 1114b9d1bb551cf8167b9a54e56d60fc054257fd |
| Publication commit | 4d2e8e1c8d1f1b4e386c9b1646ec9a0721cd30d4 |
| Runtime | Python 3.12.10, Windows 11; clean tree reported |
| Retrieval | ID priority; 1000-character chunks; overlap 200; k=2 and k=4 |
| Models | qwen3.5:4b and nomic-embed-text; identities/digests saved in report |
| Capture | 12 retrieved-context answers and one direct-context conflict answer |
| Review identity | ChatGPT/Codex AI assistant, not an independent human reviewer |

The audit rechecks saved data without rerunning Ollama. Saved model identities
are provenance records, not an independent verification of the user's model service.
The captured prompt and ranking behavior remain the baseline.

## 🧪 Artifact checks

- Recomputed all 65 metric values across 13 saved records, plus matched groups
  and returned-chunk counts. The control's marker score describes supplied context,
  not retrieval success.
- Checked 38 excerpt occurrences against frozen source/page text; the 36 retrieved
  excerpt occurrences also match the saved five-chunk inventory.
- Confirmed k=2 excerpts are identical prefixes of k=4 for all six paired questions;
  paired traces agree. This verifies the saved pairing, not the embedding rankings
  by independently repeating semantic search.
- Recomputed the case and corpus snapshot digests.
- Matched all six captured code hashes to the recorded runtime commit after
  applying Windows CRLF line endings to Git's LF source bytes.
- Recomputed the saved singles-only citation checks. A supplemental grouped-label
  inspection also found no out-of-range numeric labels.
- Confirmed the original review.json still has null ratings for all 13 answers.

[Machine-readable artifact audit](multidoc-runs/20261110T222813Z-bc04d7e8/artifact-audit.json).
Reproduce from a repository checkout with assertions enabled:

```powershell
python .\tools\audit_multidoc_run.py .\verification\multidoc-runs\20261110T222813Z-bc04d7e8
```

The audit script was also checked against a temporary report with a deliberately
corrupted coverage value; it rejected the mismatch. No live models were invoked.

## 📊 Evidence and answer completeness

| On six retrieved cases | k=2 | k=4 |
| --- | ---: | ---: |
| Complete authored evidence groups | 4/6 | 6/6 |
| Mean evidence-group coverage | 86.1% | 100% |
| Assistant-reviewed expected-answer completeness | 4/6 | 6/6 |
| Assistant-reviewed attribution | 6/6 | 6/6 |
| Assistant-reviewed citation support | 4/6 | 5/6 |
| Assistant-reviewed uncertainty | 5/6 | 6/6 |

Automatic marker scores and assistant judgments are separate layers. These are
descriptive counts on six authored development questions, not validated human-scored
accuracy, statistical evidence, or a general superiority claim. The conflict
control is excluded from this table.

## 🟠 Per-answer assistant judgments

**P = pass; F = fail.** All ratings are AI-assisted source inspection and remain
subject to independent human confirmation. Completeness checks expected claims;
unsupported extra claims are separately counted under citation support.

| Record | Completeness | Attribution | Citation support | Uncertainty |
| --- | --- | --- | --- | --- |
| cedar_maple:k2 | P | P | P | P |
| cedar_maple:k4 | P | P | P | P |
| atlas_pages:k2 | P | P | P | P |
| atlas_pages:k4 | P | P | P | P |
| cedar_birch_missing:k2 | P | P | F | F |
| cedar_birch_missing:k4 | P | P | F | P |
| three_unit_approvals:k2 | F | P | P | P |
| three_unit_approvals:k4 | P | P | P | P |
| four_unit_failures:k2 | F | P | P | P |
| four_unit_failures:k4 | P | P | P | P |
| known_unknown:k2 | P | P | F | P |
| known_unknown:k4 | P | P | P | P |
| conflicting_approvals:control | P | P | P | P |

Detailed claim/excerpt reasoning is in
[assistant-review.json](multidoc-runs/20261110T222813Z-bc04d7e8/assistant-review.json).
[Grouped review counts](multidoc-runs/20261110T222813Z-bc04d7e8/assistant-review-summary.json)
keep the two k settings and direct-context control separate. No human identity
or human judgment is inferred from these files. The original human worksheet
is preserved for a person to complete or disagree with these proposed ratings.

## 🔎 Findings that determine the next changes

### Evidence depth: two paired improvements

For three-project approvals, k=2 supplied Atlas and Maple (2/3 groups) but omitted
Cedar. k=4 supplied Cedar too, and the answer included all required conditions.
Its extra Birch note was supported but unrequested.

For four failure causes, k=2 supplied only Cedar and Maple (2/4 groups), and the
answer acknowledged the missing Birch/Atlas context. k=4 supplied all four causes;
the answer correctly assigned and cited them, including Atlas PDF page 2.
The ability to abstain correctly does not make an incomplete answer complete.

### Birch: evidence is present, but generation adds unsupported wording

At k=2, “this section is explicitly omitted” [2] implies an editorial omission.
The Birch note only states that it does not specify approval requirements.
“It only notes” the nightly schedule also overlooks its failure/recovery content.
Both points affect citation support; intentional omission also fails uncertainty.

At k=4, the model replaces that wording but adds “Build failures ... prevent
rerunning the build” [2]. Birch instead gives recovery guidance before rerunning
BIRCH-309; it establishes no general prohibition or enforced release gate.
This is an unsupported added claim, not a retrieval miss.

### Willow: distinguish a context limit from evidence about an absent project

At k=2, the correct abstention is accompanied by “Lack of Willow information”
assigned to Maple [2]. The answer also cites only [2] for a combined Cedar/Maple
context description. Under the all-claims citation rule, one source does not
establish that whole-context finding. This is a citation-scope failure, not an
invented Willow policy or a failed abstention.

At k=4, the answer explicitly bounds the missing information to the retrieved
excerpts and labels the complete supplied set. That is accepted as a context
description, not proof that Willow is absent from the full corpus. The citations
could be simplified by stating the context limitation without presenting an
unrelated note as factual evidence of Willow's requirements.

### Scope and conflict interpretation

The three-project k=2 answer opens with “Based on the provided documents,” so
its “no mention” statement is interpreted within that frame and passes uncertainty.
More explicit “in the retrieved excerpts” wording would reduce ambiguity. This
interpretation is recorded so a human can review the rating rather than silently
turning a wording concern into a measured failure.

The Larch control correctly states both conflicting policies, notes the absence
of revision/authority information, and calls the conflict unresolved. The two
cited notes jointly support its final provenance sentence. It neither chooses
one policy nor invents a combined both-leads rule. This is one direct-context
generation example; retrieval did not run for it.

## 🔗 Citation-checker limitation

The original regex recognizes [1] and [2] separately, but not the grouped form
[1, 2] used twice by four_unit_failures:k2. Its saved labels therefore do not
describe every citation span. The supplemental audit parses those groups and
checks both labels; neither is out of range. The raw report and parser are
unchanged. Valid numeric labels still cannot establish factual support.

## 🧭 Next work and limits

1. Evaluate an explicit evidence-depth setting for broader multi-project questions;
   retain k=2 as the current application baseline until a behavior change is tested.
2. Test a prompt variant that bounds absence statements to retrieved excerpts,
   avoids inferring intentional omissions, and discourages unsupported extra rules.
3. Extend citation syntax checking to grouped labels with a regression check,
   keeping that check separate from semantic citation support.
4. Obtain independent human review of the saved claims and proposed ratings.

The run is small, fictional, authored, and fixed-order, with one answer per
question/setting. There is no held-out generalization, latency comparison,
blinded review, or inference of thesis-level effectiveness. This audit does not
change the interactive prompt, default k, or raw capture files.

[Capture dashboard](multidoc-runs/20261110T222813Z-bc04d7e8/summary.md) ·
[Lab workflow and rubric](../guides/MULTIDOC_EVALUATION.md) ·
[Tutorial acknowledgment](../README.md#tutorial-acknowledgment-and-attribution)
