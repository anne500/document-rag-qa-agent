# 🧪 Prompt Comparison Implementation Verification

**🟩 65 offline tests passed in development; first live paired capture audited. 🟠 Windows test output and independent human answer ratings pending.**

November 10, 2026: all 52 existing checks plus 13 new checks passed with
Python 3.12 in development. Validation checked all 13 frozen contexts from
the published source run. The targeted Birch/Willow selection validated
four contexts. Neither validation nor offline testing invoked live models,
embeddings, retrieval, or an index.

| New check | Verified behavior |
| --- | --- |
| Saved source and case selection | All 13 source records accepted; selected case IDs remain explicit |
| Snapshot tampering | Changed corpus text fails digest validation |
| Wrong page or question | Frozen source mismatch is rejected |
| Incomplete or duplicate source records | Rejected before capture |
| Baseline prompt | Saved text preserved verbatim; revision supplies no fixture answers |
| Paired inputs and order | Identical question/context; prompt-first order alternates |
| Failed second variant | First answer, failure status, and context remain checkpointed |
| Interruption | Interrupted status retained |
| Empty model answer | Failed, not accepted as a completed answer |
| Grouped citation regression | [1, 2], [0], [4], and adjacent labels checked; support remains unscored |
| Review worksheet | Both prompt variants start with separate null ratings |
| Agent factory | Default and explicit prompt use the same model settings; no interactive default change |
| Dashboard | Failed capture and unreviewed answer quality remain explicit |

The agent-factory test executes the actual factory body with SDK boundary
fakes, not live LangChain/Ollama integration. The first paired local run is
still required to verify that integration and inspect generated behavior.

The current changes add two helper/runner modules, a prompt override argument
to the existing agent factory, tests, and documentation. They do not replace
the interactive prompt or change retrieval defaults. Previous raw experiment
files and the original singles-only citation parser remain unchanged.

```powershell
python -m unittest discover -s tests -v
python .\eval_prompt_comparison.py --validate-only
python .\eval_prompt_comparison.py
```

The full command captures 26 new answers. No prompt-quality improvement is
claimed from passing implementation tests.

[Workflow and limitations](../guides/PROMPT_COMPARISON.md) ·
[Verification dashboard](DASHBOARD.md) ·
[Tutorial provenance](../README.md#tutorial-acknowledgment-and-attribution)


## 📊 Live Follow-up and Artifact Reproduction

The user captured all 26 paired answers on Windows and published the complete
run. The [audit](prompt-run-audit-20261110.md) rechecks 13 pair contexts,
26 prompt/context hashes each, three snapshot digests, 26 citation results,
and six code digests. All saved-artifact checks passed. The helper also rejected
separately corrupted context and citation results in temporary copies.

The 65-test output from Windows has not been supplied. The live capture does
exercise the model factory's prompt override, but it does not replace that
missing test-suite observation or independent human answer review.

```powershell
python .\tools\audit_prompt_run.py .\verification\prompt-runs\20261110T232200Z-d0f222aa
```

This reproduction command makes no model calls. The separate assistant ratings
are proposals with claim/excerpt notes; original human ratings remain null.
