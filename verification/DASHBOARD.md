# 📋 Verification Dashboard

**🟩 Observed or checked · 🟠 Pending · 🔴 Preserved failure**

This is the repository's verification index. Status describes the cited checks,
not universal reliability or completion of a thesis experiment.

## 🧱 Tutorial foundation and extensions

| Stage | Status | Evidence |
| --- | --- | --- |
| 📚 Tutorial-based local RAG baseline | 🟩 Manual checks recorded | [Initial results](initial-results.md); [first implementation](https://github.com/anne500/document-rag-qa-agent/tree/32a4847) |
| 🔎 Multiple-document selection | 🟩 Three direct examples passed | [Initial results](initial-results.md) |
| 🧪 Misleading Maple question at k=1 | 🔴 Supporting Maple evidence was missed | [Preserved comparison](initial-results.md) |
| 🧪 Same Maple question at k=2 | 🟩 Evidence retrieved and answer corrected in one run | [Preserved comparison](initial-results.md) |
| 📄 Extension 1: PDF pages and citations | 🟩 Three manual smoke checks passed | [PDF results](pdf-results.md) |
| 🔄 Extension 2: startup index refresh | 🟩 Add, edit, remove, and reuse checks passed | [Index-refresh results](index-refresh-results.md) |
| 🧪 Extension 3: evaluation implementation | 🟩 21 Windows tests; 22 development tests after CSV fix | [Implementation verification](retrieval-lab-implementation.md) |
| 📊 Extension 3: local embedding evaluation | 🟩 Completed; all saved scores recomputed | [Measured dashboard](retrieval-runs/20261110T184155Z-a94eff34/summary.md); [audit](retrieval-run-audit-20261110.md) |
| 🔌 Live Chroma/Ollama integration for the lab | 🟩 One Windows run inspected | 28 query records; six aggregate settings; [report](retrieval-runs/20261110T184155Z-a94eff34/report.json) |
| 🛡️ Retrieved-document instruction robustness | 🟠 Not evaluated | Future extension |

## 🎨 Where the measured-results dashboard appears

The runner creates a unique directory under verification/retrieval-runs/.
Open its summary.md to see the metric table and colored chart.
The same directory contains JSON, CSV, case snapshots, and corpus snapshots.

First inspected local run: [20261110T184155Z-a94eff34](retrieval-runs/20261110T184155Z-a94eff34/summary.md).

![Measured retrieval metrics](retrieval-runs/20261110T184155Z-a94eff34/retrieval-results.svg)

Both chunk sizes reached complete marker coverage at k=2 on the 12 evidence
cases. Increasing to k=3 added no coverage. See the [audit](retrieval-run-audit-20261110.md)
for diagnostic failures at k=1, provenance checks, and interpretation limits.
Failed or interrupted future runs must retain their actual status.

## 🗺️ Reading paths

| Goal | Start here |
| --- | --- |
| Understand the architecture | [Visual guide](../guides/VISUAL_GUIDE.md) |
| Reproduce baseline examples | [README](../README.md) |
| Inspect authored evaluation cases | [Case dataset](../evaluation/cases.json) |
| Understand scoring and limits | [Retrieval lab guide](../guides/RETRIEVAL_LAB.md) |
| Trace original tutorial credit | [Tutorial acknowledgment](../README.md#tutorial-acknowledgment-and-attribution) |

## 🟪 Research interpretation

The evidence comes from fictional fixtures, manual checks, and offline software
tests. Retrieval marker scores, generated-answer correctness, citation support,
and abstention quality are separate evaluation questions.
No real-build BRI effectiveness claim or general model ranking is made.
