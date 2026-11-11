# 🧪 Second Prompt Refinement: Implementation Verification

**🟩 72 offline tests passed in development. 🟠 Windows tests and live three-prompt effects pending.**

On November 10, 2026, all 65 prior checks and seven additional checks passed
with Python 3.12 in development. The full three-prompt selection validated 13
frozen contexts and 39 planned calls without loading a model or index.

| Additional check | Verified behavior |
| --- | --- |
| Historical prompt preservation | Baseline/revised text is identical; refined appends generic rules |
| Three-variant inputs and ordering | Identical contexts; first position rotates over three contexts |
| Third-call failure | Both completed answers and the failed refined state remain checkpointed |
| Three-variant dashboard | All variant columns appear; answer quality remains unreviewed |
| Targeted validation | Birch/Willow selection validates four contexts and 12 calls without models |
| Unknown prompt set | Rejected before any generation |
| Audit integration | Three variants and their human-review IDs pass with stubbed answers/source bytes; corrupted refined-context hash is rejected |

The updated audit helper also rechecked the original published two-prompt run:
13 pairs, 26 answers, six runtime source hashes and unchanged human worksheet
all passed. A separate synthetic nine-answer capture exercised cyclic orders
and refined hashes; it contained stub answers, not measured model output, and
was not published as empirical evidence.

The first two prompt strings, interactive agent default, original experiment
files, and original human worksheets are preserved. The existing command still
runs two prompts; --include-refined opts into all three. Failures/interruption
continue to preserve prior answers and leave incomplete calls unreviewed.

```powershell
python -m unittest discover -s tests -v
python .\eval_prompt_comparison.py --include-refined --validate-only
python .\eval_prompt_comparison.py --include-refined
```

The last command requires local Ollama and captures 39 new answers. Offline
checks establish implementation behavior, not prompt improvement or live SDK
integration for the new variant. Independent human review remains pending.

[Design and limitations](../guides/PROMPT_REFINEMENT.md) ·
[Previous measured results](prompt-run-audit-20261110.md) ·
[Tutorial provenance](../README.md#tutorial-acknowledgment-and-attribution)
