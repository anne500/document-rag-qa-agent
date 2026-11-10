# 🧪 Retrieval Lab: Implementation Verification

## 🟩 Verified offline

21 unittest methods passed in the development environment on November 10, 2026.
Tests use controlled ranked passages and mocked runtime dependencies.
No real embedding or chat model is called by these tests.

| Area | Verified behavior |
| --- | --- |
| Evidence identity | Wrong source, wrong PDF page, and missing markers do not count |
| Scoring | Rank-two MRR, partial and complete multi-source coverage, empty retrieval, and actual-return precision |
| Duplicate evidence | Repeated chunks do not inflate distinct-group coverage |
| Controls | No-evidence cases have null metrics and are excluded from averages |
| Dataset | 12 evidence cases, 2 controls, unique IDs, valid pages, nonempty markers |
| Complete mocked run | Produces JSON, CSV, a chart, and a Markdown dashboard |
| Failure and interruption | Preserves completed case evidence; does not report the run complete |
| Corpus guard | Rejects extra sources and missing expected page evidence |
| Chart output | Escapes labels; five-metric table and three-metric chart are generated |

The chart renderer was also visually inspected using clearly labeled illustrative
values. That rendering check is not retrieval-performance evidence.

## 🟩 Local Run and CSV Follow-up

The user recorded 21 passing Windows tests, validated all 14 cases against
five document/page units, and completed the first real embedding run.
See the [published evidence audit](retrieval-run-audit-20261110.md).

All 84 per-setting score records were recomputed, all 84 ranked passages were
checked against their source/page snapshot, and six CSV rows matched the report.

After correcting doubled CSV carriage returns, a regression test was added.
22 offline tests passed in development after that fix. These do not replace
Windows verification of the new formatting change or repeated model runs.

Generalization, answer quality, citation entailment, and no-answer detection
remain outside this retrieval-only evaluation.

## 🚀 Reproduce

```powershell
python -m unittest discover -s tests -v
python .\eval_retrieval.py --validate-only
python .\eval_retrieval.py
```

See the [colored lab guide](../guides/RETRIEVAL_LAB.md) for metric definitions,
case coverage, limitations, and the generated-results layout.
