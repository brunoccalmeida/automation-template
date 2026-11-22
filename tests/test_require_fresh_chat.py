"""Tests for the mission plugin hook that keeps /mission:ship-pr to fresh chats.

Each test runs the command exactly as plugins/mission/hooks/hooks.json
declares it, through ``sh -c`` with ``CLAUDE_PLUGIN_ROOT`` exported, the way
Claude Code runs a shell-form plugin hook (Hooks reference, "Exec form and
shell form"). The hook input mirrors the documented UserPromptExpansion
input, and the transcripts are synthetic JSONL shaped like real ones: a chat
started by /clear holds user and system records but no assistant record.

Run: python3 -m unittest discover -s tests -v
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / "plugins" / "mission"
HOOKS_FILE = PLUGIN_ROOT / "hooks" / "hooks.json"
SH = shutil.which("sh")
TIMEOUT_SECONDS = 30


def setUpModule() -> None:
    """Fail, never skip, when a tool the hooks need is missing.

    The ``test`` contract lists these tools as preconditions; skipping would
    print OK without testing the hooks, an error passing in silence.
    """
    missing = [name for name, path in (("sh", SH),) if path is None]
    if missing:
        raise RuntimeError(f"not found on PATH: {', '.join(missing)}; the hook tests run the hooks through them")


# A chat that /clear just opened: what Claude Code writes before the first
# prompt of the new session reaches the model
FRESH_CHAT = [
    {"type": "mode", "mode": "normal", "sessionId": "s1"},
    {"type": "user", "message": {"role": "user", "content": "<command-name>/clear</command-name>"}},
    {"type": "system", "subtype": "local_command", "content": "<local-command-stdout></local-command-stdout>"},
]
ASSISTANT_REPLY = {
    "parentUuid": "u1",
    "message": {"id": "msg_1", "type": "message", "role": "assistant", "content": [{"type": "text", "text": "Hi"}]},
    "type": "assistant",
    "uuid": "a1",
}


def expansion_hooks() -> list[dict]:
    """The UserPromptExpansion matcher groups the plugin declares."""
    config = json.loads(HOOKS_FILE.read_text(encoding="utf-8"))
    return config["hooks"]["UserPromptExpansion"]


def write_transcript(directory: Path, records: list[dict]) -> Path:
    path = directory / "transcript.jsonl"
    # Compact separators, as Claude Code writes the transcript
    lines = (json.dumps(record, separators=(",", ":")) for record in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_hook(hook_input: dict) -> subprocess.CompletedProcess:
    """Run the declared command for /mission:ship-pr with this input."""
    (group,) = expansion_hooks()
    (handler,) = group["hooks"]
    return subprocess.run(
        [SH, "-c", handler["command"]],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT.as_posix()},
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


def ship_pr_input(transcript: Path | str | None) -> dict:
    hook_input = {
        "session_id": "s1",
        "cwd": str(PLUGIN_ROOT),
        "permission_mode": "default",
        "hook_event_name": "UserPromptExpansion",
        "expansion_type": "slash_command",
        "command_name": "mission:ship-pr",
        "command_args": "42",
        "command_source": "plugin",
        "prompt": "/mission:ship-pr 42",
    }
    if transcript is not None:
        hook_input["transcript_path"] = str(transcript)
    return hook_input


class RequireFreshChatTest(unittest.TestCase):
    def setUp(self) -> None:
        # A space in the path proves the command keeps it one argument
        self.directory = Path(tempfile.mkdtemp(prefix="fresh chat "))
        self.addCleanup(shutil.rmtree, self.directory)

    def assert_allowed_silently(self, run: subprocess.CompletedProcess) -> None:
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "", "an allowed command prints no decision")

    def assert_fails_open(self, run: subprocess.CompletedProcess) -> None:
        self.assert_allowed_silently(run)
        self.assertIn("allowing", run.stderr, "failing open must say so on stderr")

    def decision_of(self, run: subprocess.CompletedProcess) -> dict:
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotEqual(run.stdout.strip(), "", f"no decision printed; stderr: {run.stderr}")
        return json.loads(run.stdout)

    def test_blocks_ship_pr_in_a_chat_with_prior_conversation(self) -> None:
        transcript = write_transcript(self.directory, [*FRESH_CHAT, ASSISTANT_REPLY])

        run = run_hook(ship_pr_input(transcript))

        decision = self.decision_of(run)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("/clear", decision["reason"])
        self.assertIn("/mission:ship-pr", decision["reason"])

    def test_allows_ship_pr_as_the_first_message_after_clear(self) -> None:
        transcript = write_transcript(self.directory, FRESH_CHAT)

        self.assert_allowed_silently(run_hook(ship_pr_input(transcript)))

    def test_quoted_assistant_text_in_a_user_message_does_not_block(self) -> None:
        quoting = {"type": "user", "message": {"role": "user", "content": '{"type":"assistant"}'}}
        transcript = write_transcript(self.directory, [*FRESH_CHAT, quoting])

        self.assert_allowed_silently(run_hook(ship_pr_input(transcript)))

    def test_fails_open_when_the_transcript_is_missing(self) -> None:
        run = run_hook(ship_pr_input(self.directory / "missing.jsonl"))

        self.assert_fails_open(run)

    def test_fails_open_when_the_transcript_is_unreadable(self) -> None:
        # A directory: unreadable as a file on every platform, unlike chmod
        self.assert_fails_open(run_hook(ship_pr_input(self.directory)))

    def test_fails_open_when_the_input_has_no_transcript_path(self) -> None:
        self.assert_fails_open(run_hook(ship_pr_input(None)))

    @unittest.skipIf(os.name == "nt", "a backslash cannot be part of a file name on Windows")
    def test_reads_a_path_with_json_escapes(self) -> None:
        # On Windows every path above already arrives escaped (C:\\Users\\...)
        odd = self.directory / 'back\\slash "quote"'
        odd.mkdir()
        transcript = write_transcript(odd, [*FRESH_CHAT, ASSISTANT_REPLY])

        run = run_hook(ship_pr_input(transcript))

        self.assertEqual(self.decision_of(run)["decision"], "block")


class MatcherTest(unittest.TestCase):
    """The matcher contains ':', so Claude Code reads it as an unanchored
    JavaScript regular expression (Hooks reference, "Matcher patterns");
    Python's re.search agrees with RegExp.prototype.test for this pattern."""

    def setUp(self) -> None:
        (group,) = expansion_hooks()
        self.matcher = group["matcher"]

    def test_matches_ship_pr(self) -> None:
        self.assertRegex("mission:ship-pr", self.matcher)

    def test_does_not_match_other_commands(self) -> None:
        for command in ("mission:close-mission", "mission:ship-pr-later", "other:mission:ship-pr", "ship-pr"):
            with self.subTest(command=command):
                self.assertIsNone(re.search(self.matcher, command))


if __name__ == "__main__":
    unittest.main()
