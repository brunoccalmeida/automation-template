"""Tests for the Copier template: generate a project and check the result.

The template does not run on its own, so it is tested by rendering it
(ADR 0001, consequences). setUpClass runs ``copier copy`` once, from this
checkout, into a temporary directory, with every answer given on the command
line, and each test checks one file of the generated project.

``--vcs-ref=HEAD`` makes Copier render the checked-out revision, including
uncommitted changes; without it, Copier renders the latest Git tag (Copier
docs, "Generating a project"), and the tests would check a release instead of
the change under test.

Run: python3 -m unittest discover -s tests -v
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
COPIER = shutil.which("copier")
TIMEOUT_SECONDS = 120
PROJECT_NAME = "Demo Project"
CORE_RULES = Path(".claude/rules/core.md")
ALWAYS_LOADED_LINE_LIMIT = 200
# Each document the core ships, by path in the generated project, with the
# title it must open with
DOCUMENTS = {
    "docs/PROJECT_SESSION_SUMMARY.md": "Session summary",
    "docs/KNOWN_ISSUES.md": "Known issues",
    "docs/FLAKY_TESTS.md": "Flaky test policy",
    "docs/adr/README.md": "Architecture Decision Records",
    "docs/adr/template.md": "N. Title of the decision",
    "docs/spikes/template.md": "Spike: the question it answers",
    "docs/ai-workflow/README.md": "AI workflow",
    "docs/ai-workflow/AGENT_TOKEN_SPEND.md": "Agent token spend",
}
# Files the generated project fills in and owns after the first copy
PROJECT_OWNED = (
    "README.md",
    "CLAUDE.md",
    "docs/PROJECT_SESSION_SUMMARY.md",
    "docs/KNOWN_ISSUES.md",
    "docs/adr/README.md",
)
PROJECT_TEXT = "# Written by the project\n"


def _copier_copy(destination: Path, *extra: str) -> None:
    """Render this checkout into destination, with every answer given."""
    result = subprocess.run(
        [
            COPIER,
            "copy",
            "--vcs-ref=HEAD",
            "--defaults",
            *extra,
            "--data",
            f"project_name={PROJECT_NAME}",
            str(TEMPLATE_ROOT),
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise RuntimeError(f"copier copy failed ({result.returncode}):\n{result.stderr}")


def _scoped_paths(rule: Path) -> bool:
    """Whether a rules file opens with a frontmatter that declares paths:."""
    lines = rule.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return False
    try:
        end = lines.index("---", 1)
    except ValueError:
        return False
    return any(line.startswith("paths:") for line in lines[1:end])


def _table_rows(markdown: str) -> list[list[str]]:
    """The body rows of every Markdown table, as lists of stripped cells."""
    rows = []
    for line in markdown.splitlines():
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def _first_column(rows: list[list[str]]) -> set[str]:
    """The backticked names in the first column (the contract roles)."""
    return {row[0].strip("`") for row in rows if row[0].startswith("`") and row[0].endswith("`")}


def setUpModule() -> None:
    """Fail, never skip, when Copier is missing.

    The ``test`` contract lists Copier as a precondition; skipping would
    print OK without rendering the template, an error passing in silence.
    """
    if COPIER is None:
        raise RuntimeError(
            "copier not found on PATH; install it in a virtual environment with "
            "pip install --require-hashes --only-binary :all: -r .github/tools/copier/requirements.txt"
        )


class GeneratedProjectTest(unittest.TestCase):
    project: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.project = Path(cls._tmp.name) / "project"
        try:
            _copier_copy(cls.project)
        except RuntimeError:
            cls._tmp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_readme_is_titled_with_the_project_name(self) -> None:
        readme = self.project / "README.md"
        self.assertTrue(readme.is_file(), f"README.md not rendered; generated: {sorted(p.name for p in self.project.iterdir())}")
        self.assertEqual(readme.read_text(encoding="utf-8").splitlines()[0], f"# {PROJECT_NAME}")

    def test_answers_file_records_the_answers_for_copier_update(self) -> None:
        # copier update needs a valid .copier-answers.yml in the project
        # (Copier docs, "Updating a project")
        answers = self.project / ".copier-answers.yml"
        self.assertTrue(answers.is_file(), f".copier-answers.yml not rendered; generated: {sorted(p.name for p in self.project.iterdir())}")
        lines = answers.read_text(encoding="utf-8").splitlines()
        self.assertIn(f"project_name: {PROJECT_NAME}", lines)
        self.assertTrue(any(line.startswith("_src_path: ") for line in lines), f"no _src_path in:\n{lines}")

    def test_core_rules_are_the_ones_this_repository_follows(self) -> None:
        # core.md is identical in every project (its own header says so); the
        # template ships the same file this repository loads, so the two
        # copies cannot drift apart
        generated = self.project / CORE_RULES
        self.assertTrue(generated.is_file(), f"{CORE_RULES} not rendered")
        self.assertEqual(
            generated.read_text(encoding="utf-8"),
            (TEMPLATE_ROOT / CORE_RULES).read_text(encoding="utf-8"),
            f"the generated {CORE_RULES} differs from this repository's",
        )

    def test_always_loaded_rules_stay_under_the_line_limit(self) -> None:
        # Claude Code loads CLAUDE.md and every .claude/rules file without a
        # paths: frontmatter at the start of each session; the core keeps
        # them under 200 lines (core.md, "Context and tokens")
        always_loaded = [self.project / "CLAUDE.md"] + [
            rule for rule in sorted((self.project / ".claude" / "rules").glob("*.md")) if not _scoped_paths(rule)
        ]
        lines = {path.relative_to(self.project).as_posix(): len(path.read_text(encoding="utf-8").splitlines()) for path in always_loaded}
        self.assertLess(sum(lines.values()), ALWAYS_LOADED_LINE_LIMIT, f"always-loaded lines: {lines}")

    def test_only_core_rules_are_always_loaded(self) -> None:
        # Any other rule is for one part of the code, so it declares the
        # paths it applies to and loads only when Claude reads them
        rules = sorted((self.project / ".claude" / "rules").glob("*.md"))
        scoped = [rule.name for rule in rules if rule.name != CORE_RULES.name]
        self.assertTrue(scoped, "no path-scoped rule rendered")
        for name in scoped:
            self.assertTrue(_scoped_paths(self.project / ".claude" / "rules" / name), f"{name} has no paths: frontmatter, so it is always loaded")

    def test_claude_md_maps_every_contract_role(self) -> None:
        # core.md refers to commands by role and expects the project's
        # CLAUDE.md to map each one (core.md, "Contracts")
        roles = _first_column(_table_rows((TEMPLATE_ROOT / CORE_RULES).read_text(encoding="utf-8")))
        claude_md = self.project / "CLAUDE.md"
        self.assertTrue(claude_md.is_file(), "CLAUDE.md not rendered")
        mapped = _first_column(_table_rows(claude_md.read_text(encoding="utf-8")))
        self.assertTrue(roles, "no contract roles found in core.md")
        self.assertEqual(sorted(mapped & roles), sorted(roles), "contract roles missing from CLAUDE.md")

    def test_document_templates_are_rendered(self) -> None:
        for path, title in DOCUMENTS.items():
            with self.subTest(path=path):
                document = self.project / path
                self.assertTrue(document.is_file(), f"{path} not rendered")
                self.assertEqual(document.read_text(encoding="utf-8").splitlines()[0], f"# {title}")

    def test_git_stores_and_checks_out_text_with_lf(self) -> None:
        gitattributes = self.project / ".gitattributes"
        self.assertTrue(gitattributes.is_file(), ".gitattributes not rendered")
        self.assertIn("* text=auto eol=lf", gitattributes.read_text(encoding="utf-8").splitlines())

    def test_copier_never_overwrites_files_the_project_owns(self) -> None:
        # The project fills these in; _skip_if_exists renders them once and
        # skips them when they already exist (Copier docs, "Configuring a
        # template"), so copier update keeps the project's text
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(self.project, project)
            for path in PROJECT_OWNED:
                with self.subTest(path=path):
                    self.assertTrue((project / path).is_file(), f"{path} not rendered")
                    (project / path).write_text(PROJECT_TEXT, encoding="utf-8")
            _copier_copy(project, "--overwrite")
            for path in PROJECT_OWNED:
                with self.subTest(path=path):
                    self.assertEqual((project / path).read_text(encoding="utf-8"), PROJECT_TEXT, f"Copier overwrote {path}")

    def test_template_files_stay_out_of_the_project(self) -> None:
        # _subdirectory keeps the template repository's own files (plugin,
        # docs, CI) out of every generated project
        for name in ("copier.yml", "plugins", "docs/INVENTORY.md", "docs/adr/0001-use-copier.md", ".github"):
            self.assertFalse((self.project / name).exists(), f"{name} leaked into the generated project")


if __name__ == "__main__":
    unittest.main()
