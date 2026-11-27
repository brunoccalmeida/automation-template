"""Tests for the CI tools pinned in .github/tools/ and bumped by Dependabot (#75).

Each tool directory gets a Dependabot entry (.github/dependabot.yml), so a pin
does not drift behind its security fixes. Dependabot bumps the Claude Code CLI
in package.json and the lockfile but not npm's ``allowScripts``, which names
the one version whose ``postinstall`` was reviewed (npm docs, "npm
install-scripts": approve "writes pinned entries (``pkg@1.2.3``)"). A bump
would leave that approval on the old version: npm 11 only warns and runs the
script anyway, npm 12 skips it silently ("Install commands silently skip
lifecycle scripts for any dependency that does not have a matching entry").
This test makes the Dependabot pull request fail until someone reviews the new
version and approves it.

Run: python3 -m unittest discover -s tests -v
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / ".github" / "tools"
CLAUDE_CLI = TOOLS / "claude-cli"
CLAUDE_PACKAGE = "@anthropic-ai/claude-code"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"


class ClaudeCliTest(unittest.TestCase):
    def test_allow_scripts_approves_the_locked_version(self):
        manifest = json.loads((CLAUDE_CLI / "package.json").read_text(encoding="utf-8"))
        lockfile = json.loads((CLAUDE_CLI / "package-lock.json").read_text(encoding="utf-8"))
        locked = lockfile["packages"][f"node_modules/{CLAUDE_PACKAGE}"]["version"]
        approved = [key for key in manifest.get("allowScripts", {}) if key.startswith(f"{CLAUDE_PACKAGE}@")]
        self.assertEqual(
            approved,
            [f"{CLAUDE_PACKAGE}@{locked}"],
            f"allowScripts does not approve the locked {CLAUDE_PACKAGE}@{locked}: review the new version's "
            f"postinstall, then run `npm install-scripts approve {CLAUDE_PACKAGE}` in .github/tools/claude-cli "
            "and delete the old entry",
        )


class DependabotTest(unittest.TestCase):
    def test_every_pinned_tool_has_a_dependabot_entry(self):
        config = DEPENDABOT.read_text(encoding="utf-8")
        covered = set(re.findall(r'^\s*directory:\s*"(/[^"]*)"', config, re.MULTILINE))
        for tool in sorted(path for path in TOOLS.iterdir() if path.is_dir()):
            with self.subTest(tool=tool.name):
                self.assertIn(
                    f"/.github/tools/{tool.name}",
                    covered,
                    f".github/dependabot.yml has no entry for .github/tools/{tool.name}: add one with the "
                    "7-day cooldown, or record in an ADR why the tool stays manual",
                )


if __name__ == "__main__":
    unittest.main()
