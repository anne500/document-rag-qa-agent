# 🧪 Extension 6 Citation Guard: Implementation Verification

**🟩 89 offline tests passed in development; two live retries audited. 🟠 New Windows test output, guarded interactive example, and broader semantic evaluation pending.**

On November 10, 2026, all 72 existing checks plus 17 guard checks passed in
development Python 3.12. The user's preceding 72-test output already verified
that earlier suite on Windows. No new model output was generated in development.

The offline replay exercised all 39 published drafts: 37 passed the numeric
check; the two saved [7] failures were withheld after the deliberately repeated
invalid draft. The evaluator made zero live calls. This verifies detection and
bounded withholding, not automatic factual correctness or live retry success.

| New check | Verified behavior |
| --- | --- |
| Numeric singles/groups/bounds | Existing labels accepted; 0 and unavailable labels rejected |
| Malformed numeric spans | Ranges, signs, separators, incomplete spans, excessive digits rejected |
| Semantic limit | Unsupported claims with valid/no labels can still pass numeric validation |
| Valid first answer | Returned unchanged after one generation call |
| Successful stub repair | Same question/context; allowed-label feedback; two calls |
| Repeated bad citation | Both drafts retained; fixed withholding message; no label deletion |
| No excerpts | No model call |
| Generation failure | Distinct status and checkpoint preserved |
| Retry interruption | Rejected first draft and interrupted second attempt checkpointed |
| Retry limits/empty answer | Only zero or one retry; blank answer is not accepted |
| Actual saved replay | 39 drafts checked, two numeric failures withheld |
| Targeted repair stub | Exactly two invalid drafts invoke repair |
| Corrupt source context/variant inventory | Rejected before replay |
| Real CLI body with SDK boundary fakes | Invalid draft hidden; valid repair displayed |
| Repeated-invalid CLI path | Fixed withholding after two attempts |
| Default CLI path | Existing unguarded one-call behavior preserved |
| Middleware | Retry feedback separated from unchanged evidence; baseline blocks preserved |

The CLI/factory tests execute the actual function bodies with SDK boundary
fakes, not a live LangChain/Ollama service. Run the live-repair command on the
user's machine to test that integration. The rejected refined prompt is used
only as the source of the two stress-test drafts, not as an adopted default.

```powershell
python -m unittest discover -s tests -v
python .\eval_citation_guard.py --validate-only
python .\eval_citation_guard.py --repair-invalid
```

The last command replays all saved first drafts but makes only two live repair
calls. Inspect successful repairs for semantic support and proper abstention;
valid labels do not prove either. Guard withholding, missing-evidence abstention,
and generation errors are recorded separately.

[Guide](../guides/CITATION_GUARD.md) ·
[Remaining extensions](../guides/EXTENSION_ROADMAP.md) ·
[Prior negative result](prompt-refinement-run-audit-20261110.md)


## 💬 Live Retry Checkpoint

The user's Windows run recorded two live repair attempts. The
[audit](citation-guard-live-audit-20261110.md) reproduced all 41 attempt checks,
context/feedback matching, final decisions, and source/runtime hashes. One
retry was withheld; one passed the numeric check but retained an unsupported
Willow-to-Birch citation. These are guard-scope observations, not factual success.

The new offline helper audit_citation_guard_run.py replays the saved attempt
sequence without models. Temporary changes to the withheld displayed answer
and a citation-check result were both rejected. No guard/runtime code changed
in that audit follow-up. Full Extension 6 and independent human review remain
pending, as listed in the [tracker](../guides/PROJECT_TRACKER.md).
