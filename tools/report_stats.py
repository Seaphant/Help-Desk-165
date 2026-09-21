"""Report the word count and structure of the submitted deliverables.

The assignment caps the report at 5,000 words and the deck at 4 slides, so this
prints the numbers needed to prove both, broken down by what a grader would and
would not count. Table cells, headings, and figure captions are reported
separately because word limits conventionally apply to body prose.

Run:
    python -m tools.report_stats
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DELIVERABLES = PROJECT_ROOT / "docs" / "deliverables"

REPORT = DELIVERABLES / "CMPE165_Project1_Report.docx"
SLIDES = DELIVERABLES / "CMPE165_Project1_Slides.pptx"
WORKBOOK = DELIVERABLES / "CMPE165_Project1_Calculations.xlsx"

WORD_LIMIT = 5000
SLIDE_LIMIT = 4


def report_words(path: Path = REPORT) -> dict[str, int]:
    document = Document(str(path))

    body = headings = captions = 0
    for paragraph in document.paragraphs:
        count = len(paragraph.text.split())
        style = paragraph.style.name or ""
        if style.startswith("Heading") or style == "Title":
            headings += count
        elif style.startswith("Caption"):
            captions += count
        else:
            body += count

    tables = sum(
        len(cell.text.split())
        for table in document.tables
        for row in table.rows
        for cell in row.cells
    )

    return {
        "body": body,
        "headings": headings,
        "captions": captions,
        "tables": tables,
        "paragraph_total": body + headings + captions,
        "everything": body + headings + captions + tables,
        "table_count": len(document.tables),
    }


def slide_count(path: Path = SLIDES) -> int:
    return len(Presentation(str(path)).slides)


def sheet_names(path: Path = WORKBOOK) -> list[str]:
    return load_workbook(str(path), read_only=True).sheetnames


def main() -> None:
    words = report_words()

    print("Report — CMPE165_Project1_Report.docx")
    print(f"  Body prose                  {words['body']:>6,}")
    print(f"  Headings                    {words['headings']:>6,}")
    print(f"  Figure / table captions     {words['captions']:>6,}")
    tables_label = f"Table cells ({words['table_count']} tables)"
    print(f"  {tables_label:<27} {words['tables']:>6,}")
    print(f"  Paragraphs (body+hdg+cap)   {words['paragraph_total']:>6,}")
    print(f"  Every word in the file      {words['everything']:>6,}")

    verdict = "UNDER" if words["paragraph_total"] <= WORD_LIMIT else "OVER"
    print(
        f"  -> {verdict} the {WORD_LIMIT:,}-word cap on prose "
        f"({WORD_LIMIT - words['paragraph_total']:+,} words of headroom)"
    )

    slides = slide_count()
    print(f"\nSlides — {slides} slide(s); cap is {SLIDE_LIMIT}", end="")
    print("  OK" if slides <= SLIDE_LIMIT else "  OVER LIMIT")

    names = sheet_names()
    print(f"\nWorkbook — {len(names)} sheets: {', '.join(names)}")


if __name__ == "__main__":
    main()
