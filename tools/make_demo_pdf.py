from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak
)
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "atlas-release-report.pdf"


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(54, 45, 558, 45)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(54, 31, "Project Atlas | Fictional RAG test fixture")
    canvas.drawRightString(558, 31, f"Page {document.page}")
    canvas.restoreState()


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#1D4ED8")
    styles["Heading1"].textColor = colors.HexColor("#7C3AED")
    styles["BodyText"].fontSize = 11
    styles["BodyText"].leading = 17

    story = []

    def paragraph(text, style="BodyText"):
        story.append(Paragraph(text, styles[style]))
        story.append(Spacer(1, 12))

    paragraph("Project Atlas", "Title")
    paragraph("Release Approval", "Heading1")
    paragraph(
        "This fictional report is a test fixture for checking PDF "
        "retrieval and page citations. It describes no real release."
    )
    paragraph(
        "<b>Release ATLAS-R12 requires approval from both the "
        "quality lead and the operations lead.</b>"
    )
    paragraph(
        "All required integration tests must pass before approval. "
        "A passing test run alone does not authorize the release."
    )

    story.append(PageBreak())

    paragraph("Project Atlas", "Title")
    paragraph("Build Failure and Recovery", "Heading1")
    paragraph(
        "<b>Build ATLAS-418 failed because the artifact registry "
        "access token had expired.</b>"
    )
    paragraph(
        "Before rerunning ATLAS-418, rotate the registry access token "
        "and verify that the build runner can authenticate to the "
        "artifact registry."
    )
    paragraph(
        "This report does not specify a production deployment date."
    )

    SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=65,
    ).build(story, onFirstPage=footer, onLaterPages=footer)

    reader = PdfReader(OUTPUT)
    expected = {
        1: ["ATLAS-R12", "quality lead", "operations lead"],
        2: ["ATLAS-418", "access token", "expired"],
    }

    if len(reader.pages) != 2:
        raise RuntimeError("Expected exactly two PDF pages.")

    for number, terms in expected.items():
        text = reader.pages[number - 1].extract_text() or ""
        missing = [term for term in terms if term not in text]
        if missing:
            raise RuntimeError(f"Page {number}: missing {missing}")
        print(f"Page {number}: text extraction OK")

    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    main()
