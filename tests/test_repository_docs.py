"""Mechanical guards for this repository's own Markdown (#62).

Each test guards an author error the reviewer caught in a merged mission:
a relative link left pointing at a moved path (#83) and a table row split
by a stray line break (#73). template/ is left out: its links resolve only
after rendering, and test_template.py checks them in the generated project.
"""

import re
import subprocess
import unittest
from pathlib import Path

from test_template import _relative_links

ROOT = Path(__file__).resolve().parent.parent

# An unescaped pipe separates cells, inside code spans too (GFM spec 0.29,
# section 4.10, example 200).
PIPE = re.compile(r"(?<!\\)\|")
DELIMITER_ROW = re.compile(r"\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*")
FENCE = re.compile(r"\s*(```|~~~)")


def _documents() -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [ROOT / name for name in listed if not name.startswith("template/")]


def _broken_links(document: Path) -> list[str]:
    return [
        target
        for target in _relative_links(document.read_text(encoding="utf-8"))
        if not (document.parent / target.split("#")[0]).exists()
    ]


def _malformed_table_rows(markdown: str) -> list[str]:
    """Body rows that do not start with a pipe or whose cell count differs from the header's.

    GFM renders both without a warning: a line with no pipe after a table
    becomes a row of empty cells, and extra cells are dropped (examples 202
    and 204). Requiring a leading pipe and the header's count is this
    repository's convention, stricter than the spec.
    """
    lines = markdown.splitlines()
    found = []
    in_fence = False
    index = 0
    while index < len(lines) - 1:
        line = lines[index]
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and line.lstrip().startswith("|") and DELIMITER_ROW.fullmatch(lines[index + 1]):
            cells = len(PIPE.findall(line))
            index += 2
            while index < len(lines) and lines[index].strip():
                row = lines[index]
                if not row.lstrip().startswith("|") or len(PIPE.findall(row)) != cells:
                    found.append(f"{index + 1}: {row[:60]}")
                index += 1
            continue
        index += 1
    return found


class RepositoryDocsTest(unittest.TestCase):
    def test_relative_links_resolve(self) -> None:
        broken = [
            f"{document.relative_to(ROOT).as_posix()} -> {target}"
            for document in _documents()
            for target in _broken_links(document)
        ]
        self.assertEqual(broken, [], "links to files that do not exist")

    def test_table_rows_match_their_header(self) -> None:
        malformed = [
            f"{document.relative_to(ROOT).as_posix()}:{row}"
            for document in _documents()
            for row in _malformed_table_rows(document.read_text(encoding="utf-8"))
        ]
        self.assertEqual(malformed, [], "table rows that render wrong (split row or wrong cell count)")


if __name__ == "__main__":
    unittest.main()
