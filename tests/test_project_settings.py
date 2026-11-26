"""Tests for the enforcement in the template-owned .claude/settings.json (#5).

This repository and every generated project share the file (ADR 0009, held
identical by tests/test_template.py), so the tests read this repository's copy.

Deny rules: Claude Code's matcher is not callable from a test, so the probes
run against the documented semantics (Permissions, "Wildcard patterns": a
``*`` matches any text, including spaces; a rule with no ``*`` matches one
exact command; "How path patterns match": a bare filename matches at any
depth, and a ``!`` deny pattern carves its paths out of the rules before it).
Some commands were also tried in the real Claude Code (the mission record
in #5's pull request lists which); these tests keep a later edit from
dropping or weakening a rule.

SessionStart hook: each test runs the command exactly as the settings declare
it, through ``sh -c`` with ``CLAUDE_PROJECT_DIR`` exported, the way Claude Code
runs a shell-form hook (Hooks reference, "Exec form and shell form"), with a
fake ``gh`` first on the PATH.

Run: python3 -m unittest discover -s tests -v
"""

import fnmatch
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
SH = shutil.which("sh")
TIMEOUT_SECONDS = 30
SHELL_TOOLS = ("Bash", "PowerShell")
# Commands core.md forbids ("never --admin"; DIRTY is resolved by merge,
# never by force push) and ordinary commands that must still run
BLOCKED_COMMANDS = (
    "gh pr merge 12 --squash --admin",
    "gh pr merge --admin 12",
    "git push --force origin feat/x",
    "git push --force-with-lease origin feat/x",
    "git push -f origin feat/x",
    "git push origin feat/x -f",
    "git push origin +feat/x",
)
ALLOWED_COMMANDS = (
    "git push origin feat/x",
    "git push -u origin feat/x",
    "git push --follow-tags origin feat/x",
    "gh pr merge 12 --squash --auto",
)
BLOCKED_READS = (".env", ".env.local", "config/.env", "config/.env.production")
ALLOWED_READS = (".env.example", "config/.env.example", "README.md")
ISSUE_LINE = "71\tOPEN\tMission 3b: Enforce the rules in CI"
PR_LINE = "72\tfeat: enforce the rules in Claude Code\tfeat/5-claude-code-enforcement\tOPEN"


def _deny_rules(tool: str) -> list[str]:
    """The deny patterns for one tool, in order, without the Tool(...) wrapper."""
    prefix = f"{tool}("
    return [rule[len(prefix):-1] for rule in SETTINGS.get("permissions", {}).get("deny", []) if rule.startswith(prefix) and rule.endswith(")")]


def _command_denied(tool: str, command: str) -> bool:
    for pattern in _deny_rules(tool):
        regex = ".*".join(map(re.escape, pattern.split("*")))
        if re.fullmatch(regex, command, re.DOTALL):
            return True
        # A trailing " *" that is the only wildcard also matches the bare command
        if pattern.count("*") == 1 and pattern.endswith(" *") and command == pattern[:-2]:
            return True
    return False


def _read_denied(path: str) -> bool:
    """Bare filename patterns only: each matches the file name at any depth."""
    denied = False
    name = PurePosixPath(path).name
    for pattern in _deny_rules("Read"):
        negated = pattern.startswith("!")
        if fnmatch.fnmatchcase(name, pattern.lstrip("!")):
            denied = not negated
    return denied


def setUpModule() -> None:
    """Fail, never skip, when sh is missing: the hook runs through it."""
    if SH is None:
        raise RuntimeError("sh not found on PATH; the SessionStart hook test runs the hook through it")


class DenyRulesTest(unittest.TestCase):
    def test_forbidden_commands_are_denied_in_every_shell(self) -> None:
        for tool in SHELL_TOOLS:
            for command in BLOCKED_COMMANDS:
                with self.subTest(tool=tool, command=command):
                    self.assertTrue(_command_denied(tool, command), f"no {tool} deny rule matches: {command}")

    def test_ordinary_commands_are_not_denied(self) -> None:
        for tool in SHELL_TOOLS:
            for command in ALLOWED_COMMANDS:
                with self.subTest(tool=tool, command=command):
                    self.assertFalse(_command_denied(tool, command), f"a {tool} deny rule blocks an ordinary command: {command}")

    def test_env_files_are_denied_except_the_example(self) -> None:
        # A Read deny rule also blocks Edit and Write on the same path
        # (Permissions, "How path patterns match")
        for path in BLOCKED_READS:
            with self.subTest(path=path):
                self.assertTrue(_read_denied(path), f"no Read deny rule matches {path}")
        for path in ALLOWED_READS:
            with self.subTest(path=path):
                self.assertFalse(_read_denied(path), f"a Read deny rule blocks {path}")


class SessionStartHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _hook(self) -> dict:
        groups = SETTINGS.get("hooks", {}).get("SessionStart", [])
        self.assertEqual(len(groups), 1, f"expected one SessionStart group: {groups}")
        return groups[0]

    def _fake_gh(self, script: str) -> None:
        gh = self.bin / "gh"
        gh.write_text("#!/bin/sh\n" + script, encoding="utf-8", newline="\n")
        gh.chmod(0o755)

    def _run(self) -> subprocess.CompletedProcess:
        (handler,) = self._hook()["hooks"]
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT), "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}"}
        return subprocess.run([SH, "-c", handler["command"]], cwd=ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def test_runs_on_a_new_session_and_after_clear_only(self) -> None:
        # resume and compact keep the conversation, which already has the state
        self.assertEqual(sorted(self._hook()["matcher"].split("|")), ["clear", "startup"])

    def test_lists_open_issues_and_pull_requests_and_points_at_the_summary(self) -> None:
        self._fake_gh(f'case "$1 $2" in\n"issue list") printf "{ISSUE_LINE}\\n" ;;\n"pr list") printf "{PR_LINE}\\n" ;;\nesac\n')
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("session-summary", result.stdout)
        self.assertIn(ISSUE_LINE, result.stdout)
        self.assertIn(PR_LINE, result.stdout)

    def test_says_none_for_an_empty_list(self) -> None:
        # gh prints nothing when no issue or pull request is open
        self._fake_gh("exit 0\n")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"Open issues:\s*none")
        self.assertRegex(result.stdout, r"Open pull requests:\s*none")

    def test_names_the_cause_when_gh_fails(self) -> None:
        # Claude sees the reason instead of an empty list it would read as
        # "nothing open"
        self._fake_gh('echo "To get started with GitHub CLI, please run:  gh auth login" >&2\nexit 4\n')
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("gh issue list", result.stdout)
        self.assertIn("gh auth login", result.stdout)
        self.assertNotRegex(result.stdout, r"Open issues:\s*none")


if __name__ == "__main__":
    unittest.main()
