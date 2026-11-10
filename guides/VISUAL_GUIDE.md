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
    style A fill:#dbeafe,stroke:#2563eb,color:#172554
    style B fill:#dbeafe,stroke:#2563eb,color:#172554
    style C fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    style D fill:#dbeafe,stroke:#2563eb,color:#172554
    style E fill:#dbeafe,stroke:#2563eb,color:#172554
    style F fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    style G fill:#dcfce7,stroke:#16a34a,color:#14532d
    style H fill:#dcfce7,stroke:#16a34a,color:#14532d
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
