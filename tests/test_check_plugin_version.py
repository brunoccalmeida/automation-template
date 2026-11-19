"""Tests for the mission plugin hook that warns when the installed plugin is outdated.

Each test runs the command exactly as plugins/mission/hooks/hooks.json
declares it, through ``sh -c`` with ``CLAUDE_PLUGIN_ROOT`` exported, the way
Claude Code runs a shell-form plugin hook (Hooks reference, "Exec form and
shell form").

The plugin root is a synthetic cache entry shaped like a real one: a
directory named after the installed version, the commit SHA shortened to 12
characters (Plugin loading reference, "How Claude Code computes the
version"), holding the hook script and a manifest whose ``repository`` is a
local git repository. ``git ls-remote`` reads it without network, so the
published version is under the test's control.

Run: python3 -m unittest discover -s tests -v
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / "plugins" / "mission"
HOOKS_FILE = PLUGIN_ROOT / "hooks" / "hooks.json"
SH = shutil.which("sh")
GIT = shutil.which("git")
TIMEOUT_SECONDS = 30
UPDATE_COMMAND = "claude plugin update mission@brunoccalmeida-plugins"


def session_start_hooks() -> list[dict]:
    """The SessionStart matcher groups the plugin declares."""
    config = json.loads(HOOKS_FILE.read_text(encoding="utf-8"))
    return config["hooks"]["SessionStart"]


def git(*args: str, cwd: Path) -> str:
    identity = {
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    run = subprocess.run(
        [GIT, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, **identity},
        timeout=TIMEOUT_SECONDS,
        check=True,
    )
    return run.stdout.strip()


def make_published_repository(directory: Path) -> tuple[Path, str]:
    """A git repository with one commit; returns its path and HEAD SHA."""
    repository = directory / "published repo"
    repository.mkdir()
    git("init", "--quiet", cwd=repository)
    git("commit", "--quiet", "--allow-empty", "-m", "publish", cwd=repository)
    return repository, git("rev-parse", "HEAD", cwd=repository)


def make_cache_entry(directory: Path, version: str, repository: str | None) -> Path:
    """A plugin root like cache/<marketplace>/mission/<version>/."""
    root = directory / "cache" / version
    (root / "scripts").mkdir(parents=True)
    (root / ".claude-plugin").mkdir()
    for script in (PLUGIN_ROOT / "scripts").iterdir():
        shutil.copy(script, root / "scripts" / script.name)
    manifest = {"name": "mission", "description": "test"}
    if repository is not None:
        manifest["repository"] = repository
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return root


def run_hook(plugin_root: Path) -> subprocess.CompletedProcess:
    """Run the declared SessionStart command against this plugin root."""
    (group,) = session_start_hooks()
    (handler,) = group["hooks"]
    hook_input = {
        "session_id": "s1",
        "transcript_path": str(plugin_root / "transcript.jsonl"),
        "cwd": str(plugin_root),
        "hook_event_name": "SessionStart",
        "source": "startup",
    }
    return subprocess.run(
        [SH, "-c", handler["command"]],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": plugin_root.as_posix(), "GIT_TERMINAL_PROMPT": "0"},
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


@unittest.skipIf(SH is None or GIT is None, "sh or git not found on PATH")
class CheckPluginVersionTest(unittest.TestCase):
    def setUp(self) -> None:
        # A space in the path proves the command keeps it one argument
        self.directory = Path(tempfile.mkdtemp(prefix="plugin version "))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        self.repository, self.published = make_published_repository(self.directory)

    def assert_silent(self, run: subprocess.CompletedProcess) -> None:
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "", "nothing may reach the user or Claude's context")

    def assert_fails_open(self, run: subprocess.CompletedProcess, reason: str) -> None:
        self.assert_silent(run)
        # The specific reason, so an earlier exit cannot pass for this one
        self.assertIn(reason, run.stderr, "failing open must say why on stderr")
        self.assertIn("skipping", run.stderr)

    def test_warns_when_the_installed_version_is_not_the_published_one(self) -> None:
        installed = "0123456789ab"
        root = make_cache_entry(self.directory, installed, self.repository.as_posix())

        run = run_hook(root)

        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotEqual(run.stdout.strip(), "", f"no warning printed; stderr: {run.stderr}")
        output = json.loads(run.stdout)
        # systemMessage is shown to the user; plain stdout and additionalContext
        # would enter Claude's context on every session (Hooks reference)
        self.assertEqual(set(output), {"systemMessage"})
        message = output["systemMessage"]
        self.assertIn(installed, message)
        self.assertIn(self.published[:12], message)
        self.assertIn(UPDATE_COMMAND, message)

    def test_is_silent_when_the_installed_version_is_the_published_one(self) -> None:
        root = make_cache_entry(self.directory, self.published[:12], self.repository.as_posix())

        self.assert_silent(run_hook(root))

    def test_fails_open_when_the_published_version_cannot_be_read(self) -> None:
        # Stands for offline or an unreachable host: ls-remote fails the same way
        missing = (self.directory / "no such repo").as_posix()
        root = make_cache_entry(self.directory, "0123456789ab", missing)

        self.assert_fails_open(run_hook(root), "could not read HEAD")

    def test_fails_open_when_the_manifest_has_no_repository(self) -> None:
        root = make_cache_entry(self.directory, "0123456789ab", None)

        self.assert_fails_open(run_hook(root), "no repository")

    def test_fails_open_when_the_plugin_is_not_a_cached_install(self) -> None:
        # --plugin-dir loads the source directory in place, named after the plugin
        root = make_cache_entry(self.directory, "mission", self.repository.as_posix())

        self.assert_fails_open(run_hook(root), "not a cached install")


class MatcherTest(unittest.TestCase):
    """The loaded version only changes when Claude Code launches, so the hook
    runs on startup alone. A matcher of letters only is an exact string
    (Hooks reference, "Matcher patterns")."""

    def test_runs_on_startup_only(self) -> None:
        (group,) = session_start_hooks()
        self.assertEqual(group["matcher"], "startup")


if __name__ == "__main__":
    unittest.main()
