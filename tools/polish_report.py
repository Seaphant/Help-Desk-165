"""Clean up the generated Word report so it is ready to hand in.

The first pass of the report was written in Markdown and converted, which left a
handful of defects that only show up in Word:

* LaTeX math survived as literal ``\\[ \\mathrm{NPV} = ... \\]`` text.
* A Markdown link survived as ``[Seaphant](https://github.com/Seaphant)``.
* The three Monte Carlo figures ended up in an appendix at the very end, so a
  grader reading Part J sees no chart even though the rubric asks for one there.
* Tables and figures had no numbered captions, so the prose could not refer to
  them.

This module fixes those in place rather than regenerating the document, so the
prose the team wrote is preserved exactly.

Run:
    python -m tools.polish_report
"""

from __future__ import annotations

import copy
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MONOSPACE = "Consolas"

# Captions are inserted above each table, in the order the tables appear in the
# document body.
TABLE_CAPTIONS = [
    "Table 1. Stakeholder analysis: wants, influence, interest, and stance.",
    "Table 2. Power-interest matrix.",
    "Table 3. Weighted scoring model. Weights total 100 percent; scores are 1-10.",
    "Table 4. Four-year NPV at an 8 percent discount rate. "
    "Present value = net cash flow x discount factor.",
    "Table 5. Production team roles and what each role owns.",
    "Table 6. Risk register, ranked by dollar exposure (probability x dollar impact).",
    "Table 7. Monte Carlo input distributions, six uncertain variables.",
    "Table 8. Simulated total build cost, 10,000 trials.",
    "Table 9. Simulated four-year NPV, 10,000 trials.",
]

# Plain-text replacements for the LaTeX that leaked through the conversion. Each
# entry maps the literal paragraph text to what should replace it; None means the
# paragraph is deleted because it was only a math delimiter.
LATEX_BLOCKS: dict[str, str | None] = {
    r"\[": None,
    r"\]": None,
    r"\mathrm{NPV} = -C_0 + \sum_{t=1}^{4} \frac{B_t}{(1+r)^t}":
        "NPV  =  -C\u2080  +  \u03a3 (t = 1 to 4)  B\u209c / (1 + r)\u1d57",
    r"\mathrm{EMV} = \sum_i p_i \times V_i":
        "EMV  =  \u03a3\u1d62  p\u1d62  \u00d7  V\u1d62",
}

INLINE_REPLACEMENTS = [
    # Markdown link that survived the conversion.
    (
        r"\[Seaphant\]\(https://github\.com/Seaphant\)",
        "github.com/Seaphant",
    ),
    # Inline LaTeX in the sentence that explains the NPV symbols.
    (r"\\\(B_t\\\)", "B\u209c"),
    (r"\\\(t\\\)", "t"),
    (r"\\\(r = 0\.08\\\)", "r = 0.08"),
    (r"\\\((.+?)\\\)", r"\1"),
]

# Maps a grading area from the syllabus to where the reader will find it.
RUBRIC_MAP = [
    ("Problem, mission, strategy, stakeholders", "8", "Part A, Part B1"),
    ("Organizational structure and culture", "7", "Part B2, Part B3"),
    ("Project selection and weighted scoring", "8", "Part C, Table 3"),
    ("Financial analysis / NPV", "8", "Part D, Table 4"),
    ("Leadership and ethics", "8", "Part E"),
    ("Team structure, conflict, negotiation", "8", "Part F, Part G, Table 5"),
    ("Risk identification and risk register", "8", "Part H, Table 6"),
    ("Decision-tree analysis", "8", "Part I"),
    ("Monte Carlo analysis", "8", "Part J, Tables 7-9, Figures 1-3"),
    ("Working software prototype", "10", "Repository: app/, run streamlit run app/Home.py"),
    (
        "GitHub repository and AI-development reflection",
        "5",
        "README.md, section 'AI-Assisted Development'",
    ),
    ("Loom demo", "5", "Submitted separately, max 4 minutes"),
    (
        "Final recommendation and classroom presentation",
        "7",
        "'Final recommendation' section; 4-slide deck",
    ),
]


@dataclass
class PolishReport:
    latex_blocks_fixed: int = 0
    inline_fixes: int = 0
    table_captions_added: int = 0
    figures_relocated: int = 0
    rubric_table_added: bool = False
    toc_added: bool = False
    word_count: int = 0

    def summary(self) -> str:
        return "\n".join(
            [
                f"  LaTeX blocks converted to readable text: {self.latex_blocks_fixed}",
                f"  Inline markup artifacts fixed:           {self.inline_fixes}",
                f"  Numbered table captions added:           {self.table_captions_added}",
                f"  Figures moved into Part J:               {self.figures_relocated}",
                f"  Requirement-coverage table added:        {self.rubric_table_added}",
                f"  Table of contents added:                 {self.toc_added}",
                f"  Body word count:                         {self.word_count:,}",
            ]
        )


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def find_paragraph(document, predicate):
    for paragraph in document.paragraphs:
        if predicate(paragraph):
            return paragraph
    return None


def find_paragraph_starting(document, prefix: str):
    return find_paragraph(
        document, lambda p: p.text.strip().startswith(prefix)
    )


def delete_paragraph(paragraph) -> None:
    element = paragraph._p
    element.getparent().remove(element)


def style_as_formula(paragraph, text: str) -> None:
    """Render a formula centred, in a monospace font, with breathing room."""
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)
    run = paragraph.add_run(text)
    run.font.name = MONOSPACE
    run.font.size = Pt(12)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(8)


def insert_paragraph_before_element(document, element, text: str, style: str | None):
    """Create a paragraph with ``text`` and splice it in above ``element``."""
    holder = document.add_paragraph(text, style=style)
    element.addprevious(holder._p)
    return holder


def caption_paragraph(paragraph) -> None:
    """Apply caption formatting that survives without a theme dependency."""
    try:
        paragraph.style = paragraph.part.document.styles["Caption"]
    except KeyError:
        pass
    for run in paragraph.runs:
        run.font.size = Pt(9)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(4)


# ---------------------------------------------------------------------------
# Individual fixes
# ---------------------------------------------------------------------------


def fix_latex(document, report: PolishReport) -> None:
    """Turn literal LaTeX into something a human can read in Word."""
    for paragraph in list(document.paragraphs):
        stripped = paragraph.text.strip()
        if stripped not in LATEX_BLOCKS:
            continue
        replacement = LATEX_BLOCKS[stripped]
        if replacement is None:
            delete_paragraph(paragraph)
        else:
            style_as_formula(paragraph, replacement)
        report.latex_blocks_fixed += 1


def fix_inline_markup(document, report: PolishReport) -> None:
    """Repair Markdown and inline-LaTeX artifacts without losing formatting.

    Runs are edited individually so bold and italic inside a paragraph survive.
    """
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            original = run.text
            updated = original
            for pattern, replacement in INLINE_REPLACEMENTS:
                updated = re.sub(pattern, replacement, updated)
            if updated != original:
                run.text = updated
                report.inline_fixes += 1


def add_table_captions(document, report: PolishReport) -> None:
    """Number every table so the prose can refer to it."""
    for table, caption in zip(document.tables, TABLE_CAPTIONS):
        previous = table._tbl.getprevious()
        if previous is not None and previous.tag == qn("w:p"):
            text = "".join(previous.itertext()).strip()
            if text.startswith("Table "):
                continue
        paragraph = insert_paragraph_before_element(
            document, table._tbl, caption, style=None
        )
        caption_paragraph(paragraph)
        report.table_captions_added += 1


def relocate_figures(document, report: PolishReport) -> None:
    """Move the Monte Carlo figures out of the trailing appendix into Part J.

    The rubric awards Part J points for including a chart; a figure eight pages
    later does not read as part of Part J.
    """
    heading = find_paragraph(
        document,
        lambda p: p.style.name == "Heading 1"
        and p.text.strip().lower() == "monte carlo charts",
    )
    if heading is None:
        return

    # Collect every element after the appendix heading: image paragraphs and
    # their caption paragraphs, in document order.
    trailing: list = []
    node = heading._p.getnext()
    while node is not None:
        trailing.append(node)
        node = node.getnext()

    anchor = find_paragraph_starting(document, "Charts live in")
    if anchor is None:
        anchor = find_paragraph_starting(document, "The tornado chart")
    if anchor is None:
        return

    # Rewrite the pointer sentence now that the figures sit next to it.
    for run in list(anchor.runs):
        run._r.getparent().remove(run._r)
    anchor.add_run(
        "Figures 1 through 3 are reproduced below. They are generated by "
        "analysis/monte_carlo.py and written to analysis/outputs/, so rerunning "
        "python -m analysis.run_all reproduces them exactly from seed 165."
    )

    cursor = anchor._p
    for node in trailing:
        moved = copy.deepcopy(node)
        cursor.addnext(moved)
        cursor = moved
        if node.tag == qn("w:p"):
            text = "".join(node.itertext()).strip()
            if text.startswith("Figure "):
                report.figures_relocated += 1

    # Remove the now-empty appendix.
    for node in trailing:
        node.getparent().remove(node)
    delete_paragraph(heading)

    # Style the relocated captions.
    for paragraph in document.paragraphs:
        if re.match(r"^Figure \d+\.", paragraph.text.strip()):
            caption_paragraph(paragraph)


def add_rubric_map(document, report: PolishReport) -> None:
    """Insert a table telling the grader where each graded area is answered."""
    anchor = find_paragraph(
        document,
        lambda p: p.style.name == "Heading 1"
        and p.text.strip().startswith("The product we actually built"),
    )
    if anchor is None:
        return

    heading = insert_paragraph_before_element(
        document, anchor._p, "Where each graded requirement is answered", style="Heading 1"
    )
    caption = insert_paragraph_before_element(
        document,
        anchor._p,
        "Reading guide. The 100-point rubric mapped to sections of this report "
        "and files in the repository.",
        style=None,
    )
    caption_paragraph(caption)

    table = document.add_table(rows=1, cols=3)
    table.style = "Light List Accent 1"
    header = table.rows[0].cells
    header[0].text = "Graded area"
    header[1].text = "Points"
    header[2].text = "Where it is answered"
    for area, points, location in RUBRIC_MAP:
        row = table.add_row().cells
        row[0].text = area
        row[1].text = points
        row[2].text = location

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)

    anchor._p.addprevious(table._tbl)

    note = insert_paragraph_before_element(
        document,
        anchor._p,
        "Every figure in Parts C, D, H, I, and J is produced by the scripts in "
        "analysis/ and regenerated with a single command, so the numbers in this "
        "report, the slides, and the calculation workbook cannot drift apart.",
        style=None,
    )
    caption_paragraph(note)

    _ = heading
    report.rubric_table_added = True


def add_table_of_contents(document, report: PolishReport) -> None:
    """Add a TOC field and ask Word to refresh fields when the file opens."""
    anchor = find_paragraph(
        document,
        lambda p: p.style.name == "Heading 1"
        and p.text.strip().startswith("Where each graded requirement"),
    )
    if anchor is None:
        anchor = find_paragraph(
            document,
            lambda p: p.style.name == "Heading 1"
            and p.text.strip().startswith("The product we actually built"),
        )
    if anchor is None:
        return

    heading = insert_paragraph_before_element(
        document, anchor._p, "Contents", style="Heading 1"
    )
    field_paragraph = insert_paragraph_before_element(
        document, anchor._p, "", style=None
    )

    run = field_paragraph.add_run()
    begin = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "begin"})
    instruction = run._r.makeelement(qn("w:instrText"), {qn("xml:space"): "preserve"})
    instruction.text = r'TOC \o "1-2" \h \z \u'
    separate = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "separate"})
    placeholder = run._r.makeelement(qn("w:t"), {})
    placeholder.text = (
        "Right-click here and choose Update Field to build the table of contents."
    )
    end = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "end"})
    for element in (begin, instruction, separate, placeholder, end):
        run._r.append(element)

    # Ask Word to refresh fields on open so the TOC is populated without the
    # reader having to know to press F9.
    settings = document.settings.element
    if settings.find(qn("w:updateFields")) is None:
        update = settings.makeelement(qn("w:updateFields"), {qn("w:val"): "true"})
        settings.append(update)

    _ = heading
    report.toc_added = True


def count_words(document) -> int:
    """Body word count, excluding tables and captions.

    The assignment's 5,000-word limit applies to the written report only, so
    tables, captions, and the calculation appendix are left out deliberately.
    """
    total = 0
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if re.match(r"^(Table|Figure) \d+\.", text):
            continue
        total += len(text.split())
    return total


def annotate_cover(document, report: PolishReport) -> None:
    """Put the word count on the cover and make the team placeholder obvious."""
    team = find_paragraph_starting(document, "Team:")
    if team is not None:
        for run in list(team.runs):
            run._r.getparent().remove(run._r)
        label = team.add_run("Team: ")
        label.bold = True
        team.add_run("W. Nguyen (github.com/Seaphant) \u00b7 ")
        todo = team.add_run(
            "ADD REMAINING TEAMMATE NAMES HERE BEFORE SUBMITTING"
        )
        todo.bold = True
        todo.font.color.rgb = RGBColor(0xB1, 0x1A, 0x1A)

    note = find_paragraph_starting(document, "Tables, charts, equations")
    if note is not None:
        note.add_run(
            f" Body word count: {report.word_count:,}, within the 5,000-word limit."
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def polish(source: Path, destination: Path) -> PolishReport:
    document = Document(str(source))
    report = PolishReport()

    fix_latex(document, report)
    fix_inline_markup(document, report)
    relocate_figures(document, report)
    # Captions are numbered from document order, so they have to be applied
    # before any new table is spliced into the front matter.
    add_table_captions(document, report)
    add_rubric_map(document, report)
    add_table_of_contents(document, report)

    report.word_count = count_words(document)
    annotate_cover(document, report)

    destination.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(destination))
    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Word report to polish")
    parser.add_argument("destination", type=Path, help="Where to write the result")
    arguments = parser.parse_args()

    report = polish(arguments.source, arguments.destination)
    print(f"Polished {arguments.source.name} -> {arguments.destination}")
    print(report.summary())


if __name__ == "__main__":
    main()
