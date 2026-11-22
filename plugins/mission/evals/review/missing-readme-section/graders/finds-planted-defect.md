---
type: llm
---
The response is a code review of a pull request ("mission"), done against its issue, the project rules and `REVIEW.md`. The mission was planted with exactly one defect, described below; this text is hidden from the reviewer.

Planted defect: the mission adds a `UserPromptExpansion` hook to the plugin (`hooks/hooks.json`, `scripts/require-fresh-chat.sh`) that needs `sh`, `grep` and `sed` (Git Bash on Windows) and fails open without them, but `plugins/mission/README.md` is not changed at all: the README neither lists the hook nor explains what it needs or how it behaves, although the commit message says the README gained a "Ship in a fresh chat" section. `REVIEW.md` requires the plugin README to explain a change that alters what a project needs.

PASS if the response reports this defect as a finding, in any wording or language: the plugin README is missing the documentation of the new hook (or of the requirement it adds), or the commit message claims a README change that the diff does not contain.
FAIL if the response does not report it, mentions it only as acceptable, or reports it only as a question without saying it is a problem.
Ignore every other finding, right or wrong: another grader and the clean cases measure false positives.
