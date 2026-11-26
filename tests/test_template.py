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

import json
import re
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
# Answers to the contract questions, and the value each one renders in the
# CLAUDE.md contracts table, by role. The commands name no tool, so the
# stack-term test can scan the whole generated project
CONTRACT_ANSWERS = {
    "cmd_check": ("check", "./scripts/check"),
    "cmd_test": ("test", "./scripts/test"),
    "cmd_smoke": ("smoke", "./scripts/smoke"),
    "main_branch": ("main-branch", "trunk"),
    "gate": ("gate", "all-checks-passed"),
}
# Tools, languages and stack-specific settings the core must not name (ADR
# 0003: "The core never names a stack, a tool or a target type"). Whole
# words, any case. Words that are also plain English (Behave) stay out, or
# the test would fail on prose
STACK_TERMS = (
    "npm", "npx", "node", "nodejs", "yarn", "pnpm", "typescript", "javascript", "prettier", "eslint",
    "playwright", "cypress", "jest", "vitest", "selenium", "python", "pip", "poetry", "pytest",
    "java", "maven", "gradle", "dotnet", "BASE_URL",
)
# Links the core ships unresolved on purpose: placeholders the project fills
# in when it copies a template, as (file, target)
PLACEHOLDER_LINKS = {("docs/adr/template.md", "NNNN-title.md")}
MARKETPLACE = TEMPLATE_ROOT / ".claude-plugin" / "marketplace.json"
# Template-owned files this repository uses too (#4)
ADOPTED = (
    ".claude/rules/core.md",
    ".claude/rules/agent-rules.md",
    ".claude/settings.json",
    ".gitattributes",
    "docs/ai-workflow/AGENT_TOKEN_SPEND.md",
)


# Commits in throwaway repositories need an identity, and must not depend on
# the machine's signing setup
GIT = ("git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false")
TEMPLATE_CHANGE = "\nA line added by a new template version.\n"


def _run(*args: str, cwd: Path | None = None) -> None:
    result = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed ({result.returncode}):\n{result.stderr}")


def _copier_copy(destination: Path, answers: dict[str, str] | None = None) -> None:
    """Render this checkout into destination; unanswered questions take their default."""
    data = [arg for name, value in {"project_name": PROJECT_NAME, **(answers or {})}.items() for arg in ("--data", f"{name}={value}")]
    _run(COPIER, "copy", "--vcs-ref=HEAD", "--defaults", *data, str(TEMPLATE_ROOT), str(destination))


def _commit(repository: Path, message: str) -> None:
    _run(*GIT, "add", "-A", cwd=repository)
    _run(*GIT, "commit", "-q", "-m", message, cwd=repository)


def _template_source(path: str) -> Path:
    """The file in template/ that renders path in the project."""
    source = Path("template") / path
    rendered = source.with_name(source.name + ".jinja")
    return rendered if (TEMPLATE_ROOT / rendered).is_file() else source


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


def _contract_values(claude_md: Path) -> dict[str, str]:
    """The contracts table of a CLAUDE.md, as role -> value."""
    rows = _table_rows(claude_md.read_text(encoding="utf-8"))
    return {row[0].strip("`"): row[1] for row in rows if len(row) == 2 and row[0].startswith("`")}


def _relative_links(markdown: str) -> list[str]:
    """Inline and reference link targets that point into the repository."""
    targets = re.findall(r"\]\(([^)\s]+)\)", markdown) + re.findall(r"^\[[^\]]+\]:\s*(\S+)", markdown, re.MULTILINE)
    return [target for target in targets if not re.match(r"[a-z][a-z0-9+.-]*:|#", target)]


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
            _copier_copy(cls.project, {question: value for question, (_, value) in CONTRACT_ANSWERS.items()})
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

    def test_this_repository_uses_the_template_owned_files_it_shares(self) -> None:
        # This repository follows its own core (#4): each template-owned file
        # it also has is the same file, so changing one copy without the
        # other fails here. Copier does not generate this repository: it is
        # the template's source, and its README and CLAUDE.md are its own
        source = TEMPLATE_ROOT / "template"
        shared = sorted(
            name
            for name in (path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file())
            if not name.endswith(".jinja") and name not in PROJECT_OWNED and (TEMPLATE_ROOT / name).is_file()
        )
        self.assertEqual([name for name in ADOPTED if name not in shared], [], "template-owned files this repository no longer uses")
        for name in shared:
            with self.subTest(path=name):
                self.assertEqual(
                    (self.project / name).read_text(encoding="utf-8"),
                    (TEMPLATE_ROOT / name).read_text(encoding="utf-8"),
                    f"the generated {name} differs from this repository's",
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

    def test_claude_md_renders_the_contract_answers(self) -> None:
        values = _contract_values(self.project / "CLAUDE.md")
        for role, value in CONTRACT_ANSWERS.values():
            with self.subTest(role=role):
                self.assertEqual(values.get(role), f"`{value}`")

    def test_unanswered_contracts_read_not_set(self) -> None:
        # A project generated from the core alone has no stack, so no command
        # to fill in; "Not set" makes the plugin stop and ask, not guess
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            _copier_copy(project)
            values = _contract_values(project / "CLAUDE.md")
        for role, _ in CONTRACT_ANSWERS.values():
            with self.subTest(role=role):
                self.assertEqual(values.get(role), "Not set")

    def test_core_names_no_stack(self) -> None:
        pattern = re.compile(r"\b(" + "|".join(map(re.escape, STACK_TERMS)) + r")\b", re.IGNORECASE)
        found = []
        # The answers file is Copier's, not the core's, and its _src_path
        # holds this checkout's absolute path, which may contain any word
        for path in sorted(self.project.rglob("*")):
            if path.is_file() and path.name != ".copier-answers.yml":
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    found += [f"{path.relative_to(self.project).as_posix()}:{number}: {term}" for term in pattern.findall(line)]
        self.assertEqual(found, [], "stack terms in the core")

    def test_relative_links_resolve(self) -> None:
        broken = []
        for document in sorted(self.project.rglob("*.md")):
            name = document.relative_to(self.project).as_posix()
            for target in _relative_links(document.read_text(encoding="utf-8")):
                if (name, target) not in PLACEHOLDER_LINKS and not (document.parent / target.split("#")[0]).exists():
                    broken.append(f"{name} -> {target}")
        self.assertEqual(broken, [], "links to files that do not exist")

    def test_settings_register_the_mission_marketplace(self) -> None:
        # The marketplace in extraKnownMarketplaces with auto-update off, and
        # each of its plugins enabled (plugins/mission/README.md)
        settings_file = self.project / ".claude" / "settings.json"
        self.assertTrue(settings_file.is_file(), ".claude/settings.json not rendered")
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        entry = settings.get("extraKnownMarketplaces", {}).get(marketplace["name"])
        self.assertIsNotNone(entry, f"marketplace {marketplace['name']} not registered: {settings}")
        self.assertEqual(entry["source"], {"source": "github", "repo": "brunoccalmeida/automation-template"})
        self.assertIs(entry["autoUpdate"], False)
        for plugin in marketplace["plugins"]:
            with self.subTest(plugin=plugin["name"]):
                self.assertIs(settings.get("enabledPlugins", {}).get(f"{plugin['name']}@{marketplace['name']}"), True)

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

    def test_copier_update_keeps_the_files_the_project_owns(self) -> None:
        # The project fills these in; _skip_if_exists renders them once and
        # skips them when they already exist (Copier docs, "Configuring a
        # template"). This runs the real copier update between two tagged
        # template versions that both change those files, from a copy of this
        # checkout, so it covers uncommitted changes too
        with tempfile.TemporaryDirectory() as tmp:
            template, project = Path(tmp) / "template", Path(tmp) / "project"
            template.mkdir()
            shutil.copy2(TEMPLATE_ROOT / "copier.yml", template)
            shutil.copytree(TEMPLATE_ROOT / "template", template / "template")
            _run(*GIT, "init", "-q", cwd=template)
            _commit(template, "v1")
            _run(*GIT, "tag", "v1.0.0", cwd=template)
            _run(COPIER, "copy", "--defaults", "--data", f"project_name={PROJECT_NAME}", str(template), str(project))
            _run(*GIT, "init", "-q", cwd=project)
            _commit(project, "generated")
            for path in PROJECT_OWNED:
                (project / path).write_text(PROJECT_TEXT, encoding="utf-8")
            _commit(project, "filled in by the project")
            template_owned = "docs/FLAKY_TESTS.md"
            for path in (*PROJECT_OWNED, template_owned):
                with (template / _template_source(path)).open("a", encoding="utf-8") as source:
                    source.write(TEMPLATE_CHANGE)
            _commit(template, "v1.1")
            _run(*GIT, "tag", "v1.1.0", cwd=template)

            _run(COPIER, "update", "--defaults", cwd=project)

            self.assertTrue(
                (project / template_owned).read_text(encoding="utf-8").endswith(TEMPLATE_CHANGE),
                f"copier update did not bring the new version of {template_owned}",
            )
            for path in PROJECT_OWNED:
                with self.subTest(path=path):
                    self.assertEqual((project / path).read_text(encoding="utf-8"), PROJECT_TEXT, f"copier update changed {path}")

    def test_template_files_stay_out_of_the_project(self) -> None:
        # _subdirectory keeps the template repository's own files (plugin,
        # docs, CI) out of every generated project
        for name in ("copier.yml", "plugins", "docs/INVENTORY.md", "docs/adr/0001-use-copier.md", ".github"):
            self.assertFalse((self.project / name).exists(), f"{name} leaked into the generated project")


if __name__ == "__main__":
    unittest.main()
