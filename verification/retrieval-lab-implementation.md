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

## 🟠 Pending local verification

- Validate the actual installed loader against the full fixture corpus.
- Run real Ollama embeddings and in-memory Chroma retrieval.
- Inspect report status, embedding identity, ranks, and per-case evidence.
- Publish a selected observed results directory and link it from the dashboard.

No real retrieval score, best configuration, or speed improvement is claimed yet.

## 🚀 Reproduce

```powershell
python -m unittest discover -s tests -v
python .\eval_retrieval.py --validate-only
python .\eval_retrieval.py
```

See the [colored lab guide](../guides/RETRIEVAL_LAB.md) for metric definitions,
case coverage, limitations, and the generated-results layout.
