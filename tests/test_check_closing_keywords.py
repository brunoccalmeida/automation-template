"""Tests for the mission plugin script that rejects stray closing keywords.

The squash merge writes the PR title and body to the main branch as the
commit message, and GitHub closes every issue that a closing keyword
followed by a reference names in it, in plain prose too, negated or not
(issue #94). The script reads that message and fails when a
closing keyword names an issue the message does not declare it closes on a
line of its own (``Closes #N``), the first line of the PR template.

The fixtures are the squash messages of #83 and #93, which closed #82 and
#91 by mistake.

Run: python3 -m unittest discover -s tests -v
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "plugins" / "mission" / "scripts" / "check-closing-keywords.sh"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "closing-keywords"
SH = shutil.which("sh")
TIMEOUT_SECONDS = 30


def setUpModule() -> None:
    """Fail, never skip, when ``sh`` is missing (see the ``test`` contract)."""
    if SH is None:
        raise RuntimeError("not found on PATH: sh; the script runs through it")


class CheckClosingKeywordsTest(unittest.TestCase):
    def setUp(self) -> None:
        # A space in the path proves the script keeps it one argument
        self.directory = Path(tempfile.mkdtemp(prefix="closing keywords "))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)

    def check(self, message: str) -> subprocess.CompletedProcess:
        path = self.directory / "message.txt"
        path.write_text(message, encoding="utf-8", newline="\n")
        return self.run_script(path)

    def run_script(self, path: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [SH, SCRIPT.as_posix(), path.as_posix()],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT_SECONDS,
            check=False,
        )

    def assert_rejected(self, run: subprocess.CompletedProcess, *expected: str) -> None:
        self.assertEqual(run.returncode, 1, f"stdout: {run.stdout}\nstderr: {run.stderr}")
        for text in expected:
            self.assertIn(text, run.stderr)

    def assert_passes(self, run: subprocess.CompletedProcess) -> None:
        self.assertEqual(run.returncode, 0, f"stdout: {run.stdout}\nstderr: {run.stderr}")
        self.assertEqual(run.stderr, "")

    def test_rejects_the_pr_93_message_naming_the_issue_and_line(self) -> None:
        run = self.run_script(FIXTURES / "pr-93-squash.txt")

        # Line 9 says "does not close #91"; line 11 ends in "`Closes" and the
        # reference opens line 12, a form the check rejects too
        self.assert_rejected(run, "line 9: ", "line 11: ", "brunoccalmeida/automation-template#91")

    def test_rejects_the_pr_83_message_on_every_stray_line(self) -> None:
        run = self.run_script(FIXTURES / "pr-83-squash.txt")

        self.assert_rejected(run, "line 5: ", "line 8: ", "line 75: ", "line 77: ", "#82")

    def test_passes_when_every_closing_keyword_names_a_declared_issue(self) -> None:
        run = self.check(
            "fix(x): do the thing (#94) (#95)\n\n"
            "Closes #94\n\n"
            "## Decisions\n\n"
            "This closes #94 and fixes #94 for good; it refers to #91 and #62 only.\n"
        )

        self.assert_passes(run)

    def test_passes_with_several_declared_issues_and_another_repository(self) -> None:
        run = self.check("t\n\nCloses #94, closes owner/repo#7\nFixes #12\n\nThis resolves owner/repo#7 and #12.\n")

        self.assert_passes(run)

    def test_passes_with_no_closing_keyword(self) -> None:
        self.assert_passes(self.check("t\n\nRefs #94\n\nNothing here closes anything.\n"))

    def test_rejects_every_keyword_form_and_reference_form(self) -> None:
        cases = {
            "Close #1": "#1",
            "closed #2": "#2",
            "FIX #3": "#3",
            "fixes: #4": "#4",
            "Fixed owner/repo#5": "owner/repo#5",
            "resolve https://github.com/owner/repo/issues/6": "https://github.com/owner/repo/issues/6",
            "it Resolves #7.": "#7",
            "`Resolved #8`": "#8",
        }
        for text, reference in cases.items():
            with self.subTest(text=text):
                # Inside prose: a line holding only a keyword and a reference
                # is a declaration
                run = self.check(f"t\n\nRefs #99\n\nAs said, {text} later.\n")

                self.assert_rejected(run, "line 5: ", reference)

    def test_rejects_a_keyword_in_the_title(self) -> None:
        run = self.check("fix: closes #3 in the title\n\nCloses #94\n")

        self.assert_rejected(run, "line 1: ", "#3")

    def test_a_declared_issue_does_not_cover_the_same_number_in_another_repository(self) -> None:
        run = self.check("t\n\nCloses #91\n\nThe kit's PR closes other/kit#91.\n")

        self.assert_rejected(run, "line 5: ", "other/kit#91")

    def test_rejects_a_keyword_and_reference_split_across_lines(self) -> None:
        run = self.check("t\n\nRefs #1\n\nthe kit's PR closes it with `Closes\nowner/repo#1`.\n")

        self.assert_rejected(run, "line 5: ", "owner/repo#1")

    def test_ignores_keywords_inside_longer_words(self) -> None:
        self.assert_passes(self.check("t\n\nRefs #1\n\nIt encloses #2 and prefixes #3; disclosed #4.\n"))

    def test_fails_with_the_cause_when_the_file_is_missing(self) -> None:
        run = self.run_script(self.directory / "missing.txt")

        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertIn("missing.txt", run.stderr)


if __name__ == "__main__":
    unittest.main()
