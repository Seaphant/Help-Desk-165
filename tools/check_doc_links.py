"""Confirm every local path the documentation points at actually exists.

The README, the submission checklist, and the report cross-reference about a
hundred files between them. A link that rots is invisible on disk and obvious to
a grader, so this checks them all.

Markdown links have to resolve relative to the document containing them, because
that is how GitHub renders them. A path merely mentioned in backticks is prose
and may be written relative to either the repository root or the document, so
both are accepted.

Run:
    python -m tools.check_doc_links
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK = re.compile(r"`([^`\n]+)`")
PATHLIKE = re.compile(r"^[\w./-]+$")

SKIP_SCHEMES = ("http://", "https://", "mailto:", "#")

# A backticked token is only treated as a path when it looks like one of ours,
# otherwise every shell flag and variable name would be checked.
PATH_PREFIXES = ("app/", "analysis/", "docs/", "tests/", "tools/", "data/")
ROOT_FILES = frozenset(
    {"README.md", "requirements.txt", "conftest.py", ".gitignore"}
)

# Created at run time and deliberately not committed.
GENERATED = frozenset({"data/", "data/helpdesk.db", "data/helpdesk.db-journal"})


def documents() -> list[Path]:
    found = sorted((PROJECT_ROOT / "docs").rglob("*.md"))
    readme = PROJECT_ROOT / "README.md"
    if readme.exists():
        found.insert(0, readme)
    return found


def check(document: Path) -> tuple[int, int, list[str]]:
    text = document.read_text(encoding="utf-8")
    failures: list[str] = []
    label = document.relative_to(PROJECT_ROOT)

    links = {
        target
        for target in MD_LINK.findall(text)
        if not target.startswith(SKIP_SCHEMES)
    }
    for target in sorted(links):
        if not (document.parent / target.split("#")[0]).exists():
            failures.append(f"{label}: link -> {target}")

    mentions = set()
    for snippet in BACKTICK.findall(text):
        snippet = snippet.strip()
        if not PATHLIKE.match(snippet) or snippet in GENERATED:
            continue
        if snippet.startswith(PATH_PREFIXES) or snippet in ROOT_FILES:
            mentions.add(snippet)
    mentions -= links

    for target in sorted(mentions):
        if not (
            (PROJECT_ROOT / target).exists() or (document.parent / target).exists()
        ):
            failures.append(f"{label}: mentions {target}")

    return len(links), len(mentions), failures


def main() -> int:
    total_links = total_mentions = 0
    failures: list[str] = []

    for document in documents():
        links, mentions, document_failures = check(document)
        total_links += links
        total_mentions += mentions
        failures.extend(document_failures)
        status = "FAIL" if document_failures else "ok"
        print(
            f"  {status:<4} {document.relative_to(PROJECT_ROOT)} "
            f"({links} links, {mentions} mentions)"
        )

    print(
        f"\n{total_links} markdown links and {total_mentions} prose mentions checked."
    )
    if failures:
        print(f"\n{len(failures)} unresolved reference(s):")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("Every referenced path resolves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
