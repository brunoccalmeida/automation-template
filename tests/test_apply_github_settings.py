"""Tests for .github/scripts/apply-github-settings.sh, which /new-project runs (#74).

The script applies through the GitHub API what the template's files cannot:
the labels the mission cycle uses, the merge settings, Dependabot alerts and
security updates (#98), and the ruleset in .github/rulesets/protect-main.json.
This repository and every generated
project share it (held identical by tests/test_template.py), so the tests run
this repository's copy, from a temporary project root that holds only the
ruleset, with a fake ``gh`` first on the PATH that records every call.

The calls were also seen working against the real API on a throwaway
repository (the mission record in #74's pull request); these tests keep a
later edit from dropping a setting or hiding a failed call.

Run: python3 -m unittest discover -s tests -v
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".github" / "scripts" / "apply-github-settings.sh"
RULESET = ".github/rulesets/protect-main.json"
RULESET_NAME = json.loads((ROOT / RULESET).read_text(encoding="utf-8"))["name"]
SH = shutil.which("sh")
TIMEOUT_SECONDS = 30
# The labels the mission cycle reads: the priorities of core.md's mission
# start, blocked, and reviewer-miss for the mission plugin's answer key (#38)
LABELS = {
    "priority: P0": ("B60205", "Blocking: CI red or tests untrustworthy"),
    "priority: P1": ("D93F0B", "Security or visibility"),
    "priority: P2": ("FBCA04", "Technical debt"),
    "blocked": ("B60205", "Waiting on an external dependency"),
    "reviewer-miss": ("B60205", "Fixes a defect mission:reviewer let through; links the mission that shipped it"),
}
# Squash only, with the PR title and body, which carry the mission record
# (close-mission); auto-merge for ship-pr; merged branches deleted, as in
# every source project
MERGE_SETTINGS = {
    "allow_squash_merge": "true",
    "allow_merge_commit": "false",
    "allow_rebase_merge": "false",
    "allow_auto_merge": "true",
    "delete_branch_on_merge": "true",
    "squash_merge_commit_title": "PR_TITLE",
    "squash_merge_commit_message": "PR_BODY",
}
# One call per line, its arguments separated by the unit separator
FAKE_GH = r"""#!/bin/sh
printf '%s\037' "$@" >> "$FAKE_GH_LOG"
printf '\n' >> "$FAKE_GH_LOG"
case "$*" in
*"$FAKE_GH_FAIL_ON"*)
  if [ -n "$FAKE_GH_FAIL_ON" ]; then
    echo "HTTP 403: Resource not accessible by integration" >&2
    exit 1
  fi ;;
esac
case "$1 $2" in
"api repos/{owner}/{repo}/rulesets"*) [ -n "$FAKE_RULESET_IDS" ] && printf '%s\n' "$FAKE_RULESET_IDS" ;;
"api repos/{owner}/{repo}/vulnerability-alerts")
  if [ "$FAKE_ALERTS" = off ]; then
    echo "HTTP 404: Not Found" >&2
    exit 1
  fi ;;
"api repos/{owner}/{repo}/automated-security-fixes") printf '%s\n' "$FAKE_SECURITY_UPDATES" ;;
esac
exit 0
"""


def setUpModule() -> None:
    """Fail, never skip, when sh is missing: the script runs through it."""
    if SH is None:
        raise RuntimeError("sh not found on PATH; the script under test runs through it")


class ApplyGithubSettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.bin, self.project, self.log = tmp / "bin", tmp / "project", tmp / "gh.log"
        self.bin.mkdir()
        (self.bin / "gh").write_text(FAKE_GH, encoding="utf-8", newline="\n")
        (self.bin / "gh").chmod(0o755)
        (self.project / ".github" / "rulesets").mkdir(parents=True)
        shutil.copy2(ROOT / RULESET, self.project / RULESET)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(
        self, ruleset_ids: str = "", fail_on: str = "", alerts: str = "on", security_updates: str = "true"
    ) -> subprocess.CompletedProcess:
        env = {
            **os.environ,
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH_LOG": str(self.log),
            "FAKE_RULESET_IDS": ruleset_ids,
            "FAKE_GH_FAIL_ON": fail_on,
            # What the read-back sees: GET vulnerability-alerts exits 1
            # (HTTP 404) when off; the --jq .enabled of automated-security-fixes
            "FAKE_ALERTS": alerts,
            "FAKE_SECURITY_UPDATES": security_updates,
        }
        return subprocess.run([SH, str(SCRIPT)], cwd=self.project, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def _calls(self) -> list[list[str]]:
        if not self.log.is_file():
            return []
        return [line.split("\x1f")[:-1] for line in self.log.read_text(encoding="utf-8").splitlines()]

    def _ruleset_writes(self) -> list[list[str]]:
        return [
            call
            for call in self._calls()
            if call[:3] in (["api", "-X", "POST"], ["api", "-X", "PUT"]) and call[3].startswith("repos/{owner}/{repo}/rulesets")
        ]

    @staticmethod
    def _option(call: list[str], flag: str) -> str:
        return call[call.index(flag) + 1]

    def test_creates_or_updates_every_label(self) -> None:
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        labels = {}
        for call in self._calls():
            if call[:2] == ["label", "create"]:
                self.assertIn("--force", call, f"label {call[2]} fails when it already exists")
                labels[call[2]] = (self._option(call, "--color"), self._option(call, "--description"))
        self.assertEqual(labels, LABELS)

    def test_sets_squash_only_merge_settings(self) -> None:
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        patches = [call for call in self._calls() if call[:4] == ["api", "-X", "PATCH", "repos/{owner}/{repo}"]]
        self.assertEqual(len(patches), 1, f"expected one PATCH of the repository: {self._calls()}")
        fields = dict(value.split("=", 1) for flag, value in zip(patches[0], patches[0][1:]) if flag in ("-F", "-f"))
        self.assertEqual(fields, MERGE_SETTINGS)

    def test_enables_dependabot_alerts_then_security_updates(self) -> None:
        # Security updates need alerts on, so alerts come first
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        puts = [call[3] for call in self._calls() if call[:3] == ["api", "-X", "PUT"]]
        self.assertEqual(
            puts,
            ["repos/{owner}/{repo}/vulnerability-alerts", "repos/{owner}/{repo}/automated-security-fixes"],
            f"expected alerts, then security updates: {self._calls()}",
        )

    def test_reads_back_both_dependabot_settings_after_enabling_them(self) -> None:
        self._run()
        calls = self._calls()
        enable_updates = calls.index(["api", "-X", "PUT", "repos/{owner}/{repo}/automated-security-fixes", "--silent"])
        reads = [call for call in calls[enable_updates + 1 :] if call[:1] == ["api"] and call[1] in (
            "repos/{owner}/{repo}/vulnerability-alerts", "repos/{owner}/{repo}/automated-security-fixes")]
        self.assertEqual([call[1] for call in reads], [
            "repos/{owner}/{repo}/vulnerability-alerts", "repos/{owner}/{repo}/automated-security-fixes"],
            f"expected both read back after enabling: {calls}")
        self.assertEqual(self._option(reads[1], "--jq"), ".enabled")

    def test_fails_when_dependabot_alerts_read_back_off(self) -> None:
        result = self._run(alerts="off")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Dependabot alerts", result.stderr)
        self.assertIn("HTTP 404", result.stderr)

    def test_fails_when_security_updates_read_back_off(self) -> None:
        result = self._run(security_updates="false")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Dependabot security updates", result.stderr)
        self.assertIn("false", result.stderr)

    def test_creates_the_ruleset_when_none_has_its_name(self) -> None:
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        writes = self._ruleset_writes()
        self.assertEqual(len(writes), 1, f"expected one ruleset write: {writes}")
        self.assertEqual(writes[0][3], "repos/{owner}/{repo}/rulesets")
        self.assertEqual(writes[0][2], "POST")
        self.assertEqual(self._option(writes[0], "--input"), RULESET)

    def test_updates_the_ruleset_that_has_its_name(self) -> None:
        # Running it again (or after the ruleset file changes) replaces the
        # ruleset instead of adding a second one
        result = self._run(ruleset_ids="27584439")
        self.assertEqual(result.returncode, 0, result.stderr)
        writes = self._ruleset_writes()
        self.assertEqual(len(writes), 1, f"expected one ruleset write: {writes}")
        self.assertEqual(writes[0][2:4], ["PUT", "repos/{owner}/{repo}/rulesets/27584439"])
        self.assertEqual(self._option(writes[0], "--input"), RULESET)

    def test_looks_up_the_ruleset_by_the_name_in_the_file(self) -> None:
        self._run()
        lookups = [call for call in self._calls() if call[:1] == ["api"] and call[1].startswith("repos/{owner}/{repo}/rulesets")]
        self.assertEqual(len(lookups), 1, f"expected one ruleset lookup: {self._calls()}")
        self.assertIn(f'"{RULESET_NAME}"', self._option(lookups[0], "--jq"))
        self.assertIn("--paginate", lookups[0], "a repository with more rulesets than one page would get a duplicate")
        self.assertIn("includes_parents=false", lookups[0][1], "an organization ruleset with the same name would be taken for the repository's")

    def test_fails_when_two_rulesets_share_its_name(self) -> None:
        result = self._run(ruleset_ids="1\n2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(RULESET_NAME, result.stderr)
        self.assertEqual(self._ruleset_writes(), [], "wrote a ruleset without knowing which one to replace")

    def test_stops_and_shows_the_cause_when_gh_fails(self) -> None:
        result = self._run(fail_on="PATCH")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HTTP 403", result.stderr)
        self.assertIn("merge settings", result.stderr)
        self.assertEqual(self._ruleset_writes(), [], "went on after a failed call")

    def test_fails_outside_the_project_root(self) -> None:
        (self.project / RULESET).unlink()
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(RULESET, result.stderr)
        self.assertEqual(self._calls(), [], "called GitHub without the ruleset to apply")


if __name__ == "__main__":
    unittest.main()
