# 🗺️ Document RAG Extension Roadmap

This records the previously proposed project-specific extension sequence.
Use the [central tracker](PROJECT_TRACKER.md) for tutorial steps, implementation,
verified evidence, and remaining work; this page preserves the numbering.
The sequence is separate from the overall AI tutorial/project numbering;
LangSmith tracing is the next tutorial project, not Document RAG Extension 6.
The extensions are repository adaptations, not claims about the tutorial author's
own numbered roadmap.

| Extension | Work | Current checkpoint |
| --- | --- | --- |
| 1 📄 | PDF verification and page citations | Three initial manual smoke checks recorded |
| 2 🔄 | Automatic index updates | Startup add/edit/remove/reuse checks recorded |
| 3 🧪 | Retrieval Evaluation Lab | First saved run and metric audit recorded |
| 4 🔎 | Exact-ID and semantic retrieval | Paired ranking audit and interactive Maple example recorded |
| 5 📚 | Multi-document answers | Captures and assistant reviews recorded; second refinement rejected; independent human ratings pending |
| **6 🔗** | **Citation and abstention evaluation** | **Current: numeric guard and two live retry outcomes audited; claim support and broader semantic evaluation pending** |
| 7 🛡️ | Document-instruction robustness | Planned adversarial document tests; prompt instruction alone is not verification |
| 8 🖥️ | Interactive evidence viewer | Planned source/page/excerpt inspection |
| 9 ⚙️ | Automated tests and CI | Tests already developed incrementally; CI and final integrated checks remain planned |

Checkpoint completion describes observed work, not universal reliability or
completed thesis evidence. Human validation remains separate from assistant
source review. Preserve earlier raw runs and negative results as work advances.

We now move through Extension 6 rather than adding more prompt layers to
Extension 5. [The first Extension 6 guide](CITATION_GUARD.md) specifies the exact
numeric-guard scope, replay/live distinction, and remaining evaluation tasks.

[Central tracker](PROJECT_TRACKER.md) ·
[Verification dashboard](../verification/DASHBOARD.md) ·
[Tutorial credit](../README.md#tutorial-acknowledgment-and-attribution)

