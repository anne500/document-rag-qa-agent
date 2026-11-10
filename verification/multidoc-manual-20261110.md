# 💬 Multi-Document Answers: Three User-Recorded Examples

**🟩 Two examples without an identified issue; 🟡 one wording caveat.**

Source: the user's Windows PowerShell transcript shared November 10, 2026.
This is manual inspection of the supplied transcript, not an independent rerun.
Command: python .\qa_agent.py --retrieval-mode id_priority.
The unchanged index 8a06fad96141 was reused. Runtime commit, model digests,
and the full retrieved excerpt text were not printed in this transcript.
Published Markdown fixtures were inspected; Atlas facts agree with the existing
page-specific labels and previously verified PDF fixture. No formal aggregate
answer accuracy is derived from these three examples.

## 🌲🍁 Cedar and Maple

Question: Compare the release approval requirements for Cedar and Maple.
Cite each project's source.

Observed answer:

> Based on the provided documents, here is the comparison of release approval requirements:
>
> * **Maple**: A release requires passing security checks and approval from the release manager [1].
> * **Cedar**: A release requires all required tests to pass and approval from a maintainer [2].

Sources: [1] docs/maple-project.md; [2] docs/cedar-project.md.
Trace: no query/matched/unknown IDs; semantic_fallback; five semantic
candidates; zero exact candidates. Elapsed: 24.90 seconds, one observation.
Inspection: both conditions per project are present and attributed correctly.

## 📄 Atlas across two PDF pages

Question: Who must approve ATLAS-R12, and why did ATLAS-418 fail?
Cite the supporting pages.

Observed answer:

> ATLAS-R12 requires approval from both the quality lead and the operations lead [1]. ATLAS-418 failed because the artifact registry access token had expired [2].

Sources: [1] docs/atlas-release-report.pdf, page 1;
[2] docs/atlas-release-report.pdf, page 2.
Trace: ATLAS-R12 and ATLAS-418 both matched; no unknown IDs;
id_priority; five semantic candidates; two exact candidates.
Elapsed: 8.86 seconds, one observation.
Inspection: both approvers and the failure cause are included, with the expected pages.

## 🔎 Cedar and unspecified Birch requirements

Question: Compare the release approval requirements for Cedar and Birch.
Cite the evidence and identify any missing information.

Observed answer:

> Based on the provided documents, here is the comparison of release approval requirements:
>
> * **Project Cedar:** A release requires all required tests to pass and explicit approval from a maintainer. Additionally, a failed required test blocks the release workflow until the issue is reviewed [1].
> * **Project Birch:** The document does not specify any release approval requirements; it only notes that the project uses a nightly build schedule [2].
>
> **Missing Information:**
> The provided documents do not contain information regarding specific release approval requirements for Project Birch, as this section is explicitly omitted from its documentation [2].

Sources: [1] docs/cedar-project.md; [2] docs/birch-project.md.
Trace: no query/matched/unknown IDs; semantic_fallback; five semantic
candidates; zero exact candidates. Elapsed: 19.85 seconds, one observation.

Inspection: Cedar's conditions and Birch's unspecified requirements are correct.
However, “explicitly omitted” suggests an editorial act that the note does not
establish. The phrase “it only notes” is also too broad if read as a summary of
the entire note: Birch also includes a disk-space failure and recovery guidance.
Use: “The retrieved Birch document does not specify release approval requirements.”
This preserves the missing-information finding while bounding it to the source.

## 🧪 Consequence for Extension 5

These observations justify repeatable evaluation before behavioral changes.
The new lab adds three/four-unit cases, absent-project questions, and a separate
conflict control. It separates marker coverage, citation syntax, and human
assessment of all answer claims. The baseline prompt has not been changed.

[Evaluation guide](../guides/MULTIDOC_EVALUATION.md) ·
[Verification dashboard](DASHBOARD.md)
