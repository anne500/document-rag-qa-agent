# 🗺️ Tutorial and Extension Progress Tracker

**Project 5: Local Document RAG Q&A Agent · Updated November 10, 2026, America/Los_Angeles**

![Visual project status](../assets/project-progress.svg)

**🟩 Verified checkpoint · 🟦 Implemented/evidence recorded · 🟠 In progress or review pending · ⬜ Planned · 🔴 Failed/rejected experiment**

Extensions 1–9 have repository deliverables. The seven-case Windows run and assistant source review are recorded. Interactive viewer verification remains open. See the [closeout guide](PROJECT_FINISH.md) for commands and scope.

## 📚 Part A: Base tutorial

Foundation: [Darsh Shah's freeCodeCamp tutorial](https://www.freecodecamp.org/news/build-a-private-rag-qa-ai-agent-for-your-documents-using-langchain/),
published July 2, 2026. The five numbered source steps were checked against the
article. The repository adapts the implementation rather than claiming a verbatim
copy. Its learning architecture is [documented here](../README.md#architecture).

| Source tutorial step | Repository work | Current status | Evidence | Remaining work |
| --- | --- | --- | --- | --- |
| 1. Install Ollama and pull the models | Local Qwen and nomic-embed-text | 🟩 Operating locally | [Saved model identities](../verification/citation-guard-runs/20261111T011524Z-f2bde230/report.json); [initial checks](../verification/initial-results.md) | No blocker for the baseline checkpoint |
| 2. Install Python dependencies | Windows virtual environment and project packages | 🟩 Tested local environment | [Requirements](../requirements.txt); [runtime package records](../verification/multidoc-runs/20261110T222813Z-bc04d7e8/report.json) | Earlier 72 tests passed on Windows. The current suite has 94 tests. |
| 3. Prepare documents | Fictional Markdown notes and text-extractable Atlas PDF | 🟩 Fixture corpus exercised | [Tracked documents](../docs/); [PDF record](../verification/pdf-results.md) | No blocker for the authored fixture checkpoint |
| 4. Q&A agent Python code | Load, chunk, embed, persist, retrieve, supply middleware context, answer and display sources | 🟩 Adapted core implemented and exercised | [Agent code](../qa_agent.py); [initial checks](../verification/initial-results.md); [source audit](../verification/retrieval-run-audit-20261110.md) | Broader answer quality belongs to extension evaluation |
| 5. Run the agent | Interactive questions, answers, source labels, index reuse | 🟩 Baseline demonstrated | [Initial results](../verification/initial-results.md); [interactive Maple](../verification/identifier-interactive-20261110.md); [multi-document examples](../verification/multidoc-manual-20261110.md) | Guarded interactive example remains an Extension 6 check |

**Baseline checkpoint:** the tutorial-derived local pipeline is implemented and
has recorded local operation. The examples use this repository's fictional
fixtures, not the tutorial author's document corpus. Conceptual explanations and
diagrams are references, not an assessment of the learner's understanding.

## 🛠️ Part B: Repository extensions

| # | Extension | Implemented / preserved on GitHub | Verified checkpoint | Remaining work |
| --- | --- | --- | --- | --- |
| **1 📄** | PDF verification and page citations | [Page-preserving loader](../qa_agent.py), [PDF guide](../guides/VISUAL_GUIDE.md) | 🟩 Three recorded PDF smoke checks | Defined initial checkpoint done; broader PDF coverage is outside that claim |
| **2 🔄** | Automatic index updates | [Fingerprint-based startup indexing](../qa_agent.py) | 🟩 [Add/edit/remove/reuse checks](../verification/index-refresh-results.md) | Defined startup-refresh checkpoint done |
| **3 🧪** | Retrieval Evaluation Lab | [Runner](../eval_retrieval.py), [cases](../evaluation/cases.json), [tests](../tests/test_retrieval_lab.py) | 🟩 [Six-setting run](../verification/retrieval-runs/20261110T184155Z-a94eff34/summary.md) and [audit](../verification/retrieval-run-audit-20261110.md) | Authored-fixture checkpoint done; no claim of general retrieval accuracy |
| **4 🔎** | Exact-ID and semantic retrieval | [Retriever](../id_retrieval.py), [paired runner](../eval_id_retrieval.py) | 🟩 [Paired audit](../verification/identifier-run-audit-20261110.md) and [interactive Maple](../verification/identifier-interactive-20261110.md) | Defined ranking/interactive checkpoint done |
| **5 📚** | Multi-document answers | [Answer lab](../eval_multidoc.py), [prompt comparisons](../eval_prompt_comparison.py), raw snapshots, assistant reviews, and negative results | 🟦 Captures/audits recorded; 🔴 second prompt refinement rejected | Independent human ratings remain pending; preserve the rejection, do not equate more instructions with better answers |
| **6 🔗** | Citation and abstention evaluation | [Guard](../citation_guard.py) and [review lab](../eval_answer_evidence.py) | 🟩 Live review recorded 7/7 expected dispositions and 6/7 citation-support passes | Willow evidence-gap citation remains a known issue. Guarded interactive transcript remains open. |
| **7 🛡️** | Document-instruction robustness | [Structured context](../qa_agent.py) and [three attack fixtures](../evaluation/answer-evidence-cases.json) | 🟩 All three live answers retained the supported Cedar policy and rejected the embedded instructions | All three answers quoted the marker. Live baseline comparison remains open. |
| **8 🖥️** | Interactive evidence viewer | [HTML viewer](../viewer/index.html) and [builder](../tools/build_evidence_viewer.py) | 🟩 Historical and lab pages generated with tested source mapping and escaping | 🟠 Confirm the interactions in a browser |
| **9 ⚙️** | Automated tests and CI | [Tests](../tests/) and [Windows/Ubuntu workflow](../.github/workflows/verify.yml) | 🟩 94 tests and both saved audits passed on Windows and Ubuntu | [Passing CI and artifacts](https://github.com/anne500/document-rag-qa-agent/actions/runs/42942803173) |

The extension sequence comes from this learning project. It is separate from
the tutorial author's five steps and from the overall AI-project roadmap where
Project 6 is LangSmith tracing. Tests are added during earlier extensions; the
final CI extension does not postpone testing until the end.

## 🎨 Progress and evidence flow

```mermaid
flowchart TD
    A["Tutorial and Extensions 1–5"] --> B["6 · Review citations and abstention"]
    A --> C["7 · Evaluate document instructions"]
    B --> D["8 · Inspect saved evidence"]
    C --> D
    D --> E["9 · Test and publish viewer artifacts"]
    classDef done fill:#DCFCE7,stroke:#15803D,color:#14532D;
    classDef shipped fill:#DBEAFE,stroke:#2563EB,color:#172554;
    class A done;
    class B,C,D,E shipped;
```

## 📋 Verification still to record

| Check | Evidence |
| --- | --- |
| Live citation and document-instruction cases | Assistant review recorded for all seven cases. [Reviewed report](../verification/answer-evidence-runs/20261111-windows-reviewed.json) |
| Guarded interactive command and evidence viewer | Observed answer or withholding and a browser interaction check |

Use the [closeout guide](PROJECT_FINISH.md) for the local commands.

## 🔬 Verification labels and maintenance

- **Implemented** means code exists; **verified checkpoint** means the linked
  observation passed its stated scope. Neither means universal reliability.
- **Assistant review** is explicitly AI-assisted. Independent human ratings are
  still pending and must never be inferred from a completed capture.
- The user supplied a Windows run of 72 tests, all passing, at c581f3d. The 94-test suite passed locally and in both hosted jobs. [CI evidence](https://github.com/anne500/document-rag-qa-agent/actions/runs/42942803173)
- No completion percentage is invented from rows or file counts. Different tasks
  have different size, and future scope may evolve.
- Update this tracker with each implementation/verification commit. Keep the
  README entry point, roadmap, and verification dashboard consistent with it.

This follows the [shared project documentation standard](../PROJECT_STANDARD.md),
building on [Project 1's versioned baseline/extension layout](https://github.com/anne500/multi-agent-study-guide).

[Detailed verification dashboard](../verification/DASHBOARD.md) ·
[Extension roadmap](EXTENSION_ROADMAP.md) ·
[Tutorial credit](../README.md#tutorial-acknowledgment-and-attribution)
