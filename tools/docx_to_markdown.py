"""Convert the polished Word report into the Markdown copy kept in docs/.

The Word file is the submitted artifact and the Markdown is what renders on
GitHub. Generating one from the other means they cannot say different things,
which matters because the report quotes about forty numbers.

Run:
    python -m tools.docx_to_markdown docs/deliverables/CMPE165_Project1_Report.docx \\
        docs/PROJECT_REPORT.md
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

# Figures are stored in the repository, so the Markdown links to them there
# rather than re-extracting the embedded copies.
FIGURE_FILES = [
    "../analysis/outputs/monte_carlo_cost_histogram.png",
    "../analysis/outputs/monte_carlo_npv_distribution.png",
    "../analysis/outputs/monte_carlo_sensitivity.png",
]

LIST_STYLES = {"List Bullet", "List Bullet 2", "List Bullet 3"}
NUMBER_STYLES = {"List Number", "List Number 2", "List Number 3"}

HEADING_PREFIX = {
    "Title": "# ",
    "Heading 1": "## ",
    "Heading 2": "### ",
    "Heading 3": "#### ",
}


def escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_runs(paragraph: Paragraph) -> str:
    """Preserve bold and italic as Markdown emphasis.

    Emphasis markers cannot sit next to whitespace in Markdown, so surrounding
    whitespace is moved outside the markers rather than stripped. Dropping it
    would run words together, as in ``**Team:**W. Nguyen``.
    """
    parts: list[str] = []
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue

        stripped = text.strip()
        if not stripped:
            parts.append(text)
            continue

        if run.bold and run.italic:
            marker = "***"
        elif run.bold:
            marker = "**"
        elif run.italic:
            marker = "*"
        else:
            parts.append(text)
            continue

        leading = text[: len(text) - len(text.lstrip())]
        trailing = text[len(text.rstrip()) :]
        parts.append(f"{leading}{marker}{stripped}{marker}{trailing}")

    rendered = "".join(parts)
    # Collapse the artifacts that emphasis-splitting creates.
    rendered = re.sub(r"\*\*\s*\*\*", " ", rendered)
    return re.sub(r"[ \t]+", " ", rendered).strip()


def slugify(heading: str) -> str:
    """GitHub's anchor rules: lowercase, drop punctuation, spaces to hyphens."""
    slug = heading.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"\s+", "-", slug).strip("-")


def render_table(table: Table) -> list[str]:
    rows = [
        [escape_cell(cell.text) for cell in row.cells] for row in table.rows
    ]
    if not rows:
        return []

    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]

    lines = ["| " + " | ".join(rows[0]) + " |"]
    lines.append("|" + "|".join([" --- "] * width) + "|")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def is_monospace(paragraph: Paragraph) -> bool:
    return any(
        run.font.name in {"Consolas", "Courier New"} for run in paragraph.runs
    )


def convert(source: Path, destination: Path) -> dict[str, int]:
    document = Document(str(source))
    body = document.element.body

    lines: list[str] = []
    stats = {"headings": 0, "tables": 0, "figures": 0, "paragraphs": 0}
    figure_index = 0
    in_code_block = False
    # Placeholder index for the generated table of contents, and the top-level
    # headings collected as the document is walked.
    toc_slot: int | None = None
    toc_entries: list[str] = []

    def close_code_block() -> None:
        nonlocal in_code_block
        if in_code_block:
            lines.append("```")
            lines.append("")
            in_code_block = False

    for child in body.iterchildren():
        if child.tag == qn("w:tbl"):
            close_code_block()
            lines.extend(render_table(Table(child, document)))
            lines.append("")
            stats["tables"] += 1
            continue

        if child.tag != qn("w:p"):
            continue

        paragraph = Paragraph(child, document)
        text = paragraph.text.strip()
        style = paragraph.style.name

        # An image paragraph carries a drawing and no text.
        if not text and "blip" in child.xml:
            close_code_block()
            if figure_index < len(FIGURE_FILES):
                lines.append(
                    f"![Monte Carlo figure {figure_index + 1}]"
                    f"({FIGURE_FILES[figure_index]})"
                )
                lines.append("")
                figure_index += 1
                stats["figures"] += 1
            continue

        if not text:
            continue

        # Word's TOC is a field that Markdown has no equivalent for, so the
        # heading becomes an anchor for a generated list instead.
        if style == "Heading 1" and text.lower() == "contents":
            close_code_block()
            lines.append("")
            lines.append("## Contents")
            lines.append("")
            toc_slot = len(lines)
            lines.append("")
            continue
        if text.startswith("Right-click here and choose Update Field"):
            continue

        # The decision tree is drawn with box characters; it only survives
        # inside a fenced block.
        if is_monospace(paragraph) and ("\u2500" in text or "\u250c" in text):
            if not in_code_block:
                lines.append("```text")
                in_code_block = True
            lines.append(paragraph.text.rstrip())
            continue

        close_code_block()

        if style in HEADING_PREFIX:
            lines.append("")
            lines.append(HEADING_PREFIX[style] + text)
            lines.append("")
            if style == "Heading 1":
                toc_entries.append(text)
            stats["headings"] += 1
            continue

        rendered = render_runs(paragraph) or text

        if style in LIST_STYLES:
            lines.append(f"- {rendered}")
        elif style in NUMBER_STYLES:
            lines.append(f"1. {rendered}")
        elif re.match(r"^(Table|Figure) \d+\.", text) or style == "Caption":
            lines.append(f"*{rendered}*")
            lines.append("")
        else:
            lines.append(rendered)
            lines.append("")
        stats["paragraphs"] += 1

    close_code_block()

    if toc_slot is not None:
        lines[toc_slot] = "\n".join(
            f"- [{heading}](#{slugify(heading)})" for heading in toc_entries
        )

    # Collapse runs of blank lines and blank lines inside lists.
    output: list[str] = []
    for line in lines:
        if line == "" and output and output[-1] == "":
            continue
        output.append(line)

    text = "\n".join(output).strip() + "\n"
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(\n- .+)\n\n(?=- )", r"\1\n", text)
    text = re.sub(r"(\n1\. .+)\n\n(?=1\. )", r"\1\n", text)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return stats


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()

    stats = convert(arguments.source, arguments.destination)
    print(f"Wrote {arguments.destination}")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
