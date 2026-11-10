# 🎨 Document RAG: Visual Guide

🟦 Learning · 🟩 Verified behavior · 🟪 Research connection · 🟠 Pending work

## 🗺️ How PDF evidence reaches an answer

```mermaid
flowchart TD
    A["Atlas PDF"] --> B["Page 1: Release approval"]
    A --> C["Page 2: Failure and recovery"]
    B --> D["Chunks with filename and page metadata"]
    C --> D
    D --> E["Local embeddings and Chroma index"]
    E --> F["Retrieve evidence for each question"]
    F --> G["Qwen answer with excerpt labels"]
    F --> H["Source list with PDF page numbers"]

    %% Shared architecture palette: see VISUAL_STYLE.md
    classDef default fill:#F8FAFC,stroke:#475569,color:#0F172A,stroke-width:2px;
    classDef process fill:#DBEAFE,stroke:#2563EB,color:#172554,stroke-width:2px;
    classDef model fill:#EDE9FE,stroke:#7C3AED,color:#3B0764,stroke-width:2px;
    classDef store fill:#CCFBF1,stroke:#0F766E,color:#134E4A,stroke-width:2px;
    classDef decision fill:#FEF3C7,stroke:#B45309,color:#78350F,stroke-width:2px;
    classDef human fill:#FFEDD5,stroke:#C2410C,color:#7C2D12,stroke-width:2px;
    classDef output fill:#DCFCE7,stroke:#15803D,color:#14532D,stroke-width:2px;
    classDef failure fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D,stroke-width:2px;
    class A,B,C,D,F process;
    class G model;
    class E store;
    class H output;
```

## 🔎 Reading a citation

| Display | Meaning |
| --- | --- |
| Answer includes [1] | The model points to retrieved excerpt 1 |
| Source [1] names Atlas PDF, page 2 | That excerpt came from PDF page 2 |
| Reviewer checks page 2 | Confirms whether it supports the answer |

Excerpt labels are assigned separately for each question.
[1] is not a permanent document or page identifier.

## 🧪 Verification dashboard

| Capability | Status | Evidence |
| --- | --- | --- |
| Local embeddings | 🟩 Observed | 768-dimensional vector |
| Saved-index reuse | 🟩 Observed | Index reopened successfully |
| Direct project retrieval | 🟩 Observed | Cedar, Maple, and Birch |
| Missing-information handling | 🟩 Observed | Selected Markdown and PDF questions |
| PDF page citations | 🟩 Observed | Three Atlas smoke checks |
| Retrieval Evaluation Lab | 🟩 First local run audited; 22 development tests | [Measured results](../verification/retrieval-runs/20261110T184155Z-a94eff34/summary.md) |
| Automatic index updates | 🟠 Pending | Manual rebuild currently required |
| Scanned PDFs and OCR | 🟠 Pending | Not implemented |
| Document-instruction robustness | 🟠 Pending | Not evaluated |

## 🔬 Retrieval experiment

| Setting | Evidence | Outcome |
| --- | --- | --- |
| k=1 | Birch | Missing Maple evidence; agent abstained |
| k=2 | Birch and Maple | Corrected the misleading Maple premise |

This is one observed improvement, not a general performance claim.

## 🟪 Research connection

Evaluate these separately:

1. Did retrieval find the necessary evidence?
2. Did the answer faithfully use that evidence?
3. Does each citation support its associated claim?

See the [initial results](../verification/initial-results.md) and
[PDF results](../verification/pdf-results.md).

## ?? Automatic Startup Refresh

```mermaid
flowchart TD
    A["Start agent: read document text"] --> B["Fingerprint corpus and settings"]
    B --> C{"Matching completed index?"}
    C -->|Yes| D["Reuse that index"]
    C -->|No| E["Build a versioned index"]
    E --> F["Write completion marker"]
    D --> G["Answer using the selected index"]
    F --> G

    classDef default fill:#F8FAFC,stroke:#475569,color:#0F172A,stroke-width:2px;
    classDef process fill:#DBEAFE,stroke:#2563EB,color:#172554,stroke-width:2px;
    classDef model fill:#EDE9FE,stroke:#7C3AED,color:#3B0764,stroke-width:2px;
    classDef store fill:#CCFBF1,stroke:#0F766E,color:#134E4A,stroke-width:2px;
    classDef decision fill:#FEF3C7,stroke:#B45309,color:#78350F,stroke-width:2px;
    classDef human fill:#FFEDD5,stroke:#C2410C,color:#7C2D12,stroke-width:2px;
    classDef output fill:#DCFCE7,stroke:#15803D,color:#14532D,stroke-width:2px;
    classDef failure fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D,stroke-width:2px;
    class A,B,E process;
    class C decision;
    class D store;
    class F output;
    class G model;
```

?? Observed: unchanged restart, document addition, edit, and removal.

?? Scope: startup checks, complete-corpus rebuilds, historical index retention.
This does not implement live watching, incremental embedding, or secure erasure.

See the [refresh results](../verification/index-refresh-results.md).

## 📋 Complete Verification Dashboard

See the [repository verification dashboard](../verification/DASHBOARD.md) for
the tutorial baseline, extensions, preserved failures, and pending local checks.
The [colored evaluation guide](RETRIEVAL_LAB.md) explains the experiment flow
and the generated results dashboard.

## 📊 Measured Retrieval Results

![First local retrieval run](../verification/retrieval-runs/20261110T184155Z-a94eff34/retrieval-results.svg)

See the [evidence audit](../verification/retrieval-run-audit-20261110.md) for
the Maple retrieval miss, Atlas page coverage, and the limits of these scores.
