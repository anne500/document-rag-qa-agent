# 🎨 Standard for Tutorial-Based AI Learning Projects

**Base tutorial → documented extensions → verification evidence → remaining work**

This is our shared documentation format for AI learning projects intended for
learning, GitHub portfolios, and carefully bounded research use. It records the
user's standing preference for clear tables, color, diagrams, visuals, and emojis.
Apply the format when creating a project and when updating an existing project.

## 📚 Baseline and extension provenance

Every project must identify the source tutorial, author, publisher, and source
link. Map the tutorial's actual parts to the implemented baseline. Then separate
repository-specific adaptations and extensions. Preserve working baselines and
negative experiments so later versions can be compared.

Project 1 provides the established example:
[Multi-Agent AI in Python](https://github.com/anne500/multi-agent-study-guide)
documents V1–V2 as the tutorial baseline and V3–V17 as repository extensions and
delivery work, with a version roadmap and architecture/status references.
Use its evidence-first pattern without forcing every project to use V numbers.
The Document RAG project instead uses the tutorial's five steps and Extensions 1–9.

## 🗂️ Required GitHub documentation

| Item | What it must show |
| --- | --- |
| 📚 Tutorial table | Original steps/parts, repository mapping, status, evidence, and remaining work |
| 🛠️ Extension table | Stable IDs, purpose, code links, verified scope, pending work, and observed failures |
| 🎨 Visual overview | Readable colored status graphic and a meaningful diagram where branching/progression helps |
| 🧩 Architecture | Actual implemented components and routing, including failure/retry paths where relevant |
| 🧪 Verification index | Tests, local observations, CI runs if present, raw logs/reports, and reproduction commands |
| 🔬 Limitations | What was measured, what was not, fictional/development data scope, and human versus assistant review |
| 📋 Next actions | Concrete remaining work and the evidence needed to change its status |
| 📚 Attribution | Original author/publisher credit near the introduction and in a dedicated acknowledgment |

The README is the entry point. It links to one canonical tracker; supporting
roadmap and verification pages link back to that tracker. Repositories may use
guides/PROJECT_TRACKER.md, docs/PROJECT_STATUS.md, or an established equivalent.
Preserve existing version numbering and working links instead of renaming a
mature project solely to match a new filename.

## 🟩 Status vocabulary

| Marker | Meaning | Evidence needed |
| --- | --- | --- |
| ⬜ Planned | Work is listed; implementation is not claimed | Defined goal and acceptance check |
| 🟦 Implemented | Code or deliverable exists | Link to the actual file/version |
| 🟠 In progress / pending review | Part of the implementation or validation is incomplete | Explicit remaining task |
| 🟩 Verified checkpoint | A stated check passed | Test output, saved run, CI result, or clearly sourced manual observation |
| 🔴 Failed / rejected | An experiment or check did not meet its criteria | Preserved failure and explanation; do not erase it to make a roadmap look complete |

Use text as well as color. Keep implementation and verification separate.
Recorded assistant ratings do not count as independent human validation.
Passing citation syntax does not establish factual support. A local test does
not automatically establish CI, deployment, or broad research effectiveness.
Do not invent a completion percentage from unequal tasks.

## 🎨 Visual conventions

Use professional Markdown tables, consistent section emojis, and the project's
[architecture palette](VISUAL_STYLE.md) when present: blue processing, purple
model calls, teal storage, amber uncertainty/decisions, orange human review,
green observed passes, red failures, and slate planned/neutral states.
Every color must have a label. Keep diagrams compact and match real behavior.
Use exact charts only when measured data supports them. Do not generate
decorative “results” or count a diagram as proof of functionality.

## 🔄 Update checklist

- [ ] Tutorial baseline remains distinguishable from extensions.
- [ ] Every implemented extension has code/document links; future work stays planned.
- [ ] Tracker rows identify what is verified and what remains.
- [ ] Tests and relevant observed checks are recorded at their actual scope.
- [ ] Negative results and original evidence remain accessible.
- [ ] Visual overview and diagrams match the status tables.
- [ ] README, tracker, roadmap, and verification index agree.
- [ ] Tutorial credit is intact; repository adaptations are credited separately.
- [ ] Research claims remain bounded by the actual data and review method.

Current application: [Document RAG tracker](guides/PROJECT_TRACKER.md).
This file establishes the reusable standard; it does not claim that uninspected
projects have already been retroactively audited or reformatted.
