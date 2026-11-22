# feat(mission): warn at session start when the installed plugin is outdated

## Problem

The `mission` plugin is installed per project with `autoUpdate: false` (a deliberate choice: updates are applied on purpose). The cost is silent drift: after #31 merged, 4 of the 5 projects using the plugin were still on older versions (`f845d1b`, `84b2bf3`) and nothing told the user. Remembering to run `claude plugin update` in every project is a habit, and habits fail.

Auto-update was considered and declined: keeping the update a conscious step is the point. What is missing is visibility.

## Proposal

Ship a `SessionStart` command hook with the plugin that compares the installed version with the published one and, when they differ, warns the user:

- **Matcher `startup`:** the loaded version only changes when Claude Code launches, so checking on `clear`, `resume` or `compact` would be noise.
- **Installed version:** for a plugin without `version` in its manifest, the cache directory is named after the commit SHA ([Plugin loading reference, Versions and updates](https://code.claude.com/docs/en/plugins/loading.md#how-claude-code-computes-the-version)), so it can be read from `${CLAUDE_PLUGIN_ROOT}`.
- **Published version:** `git ls-remote` on the marketplace repository (no model, sub-second).
- **Output through `systemMessage`** ("warning message shown to the user", [Hooks reference](https://code.claude.com/docs/en/hooks.md)), not plain stdout: on `SessionStart`, plain stdout and `additionalContext` are added to Claude's context and would cost tokens every session. A `command` hook calls no model, so the check costs no tokens.
- **Fail open:** offline, no `git`, or any error → no warning, session proceeds, reason on stderr (same policy as `require-fresh-chat.sh`).
- **Actionable message**, in pt-BR like the other guards: installed vs published SHA and the exact `claude plugin update mission@brunoccalmeida-plugins` command.

To investigate during the mission:

- Whether the computed version is the marketplace `HEAD` SHA or the last commit touching `plugins/mission/` (the cache directories suggest `HEAD`). If `HEAD`, a docs-only merge also triggers the warning. Decide between accepting that noise and comparing against the last commit under `plugins/mission/` (GitHub API: more moving parts).
- Confirm end to end that `systemMessage` from `SessionStart` is shown to the user and does not enter the model context.
- Network latency at startup: hook `timeout` low enough not to delay the session noticeably.

## Acceptance criteria

- [ ] An outdated install shows a warning at session startup with installed SHA, published SHA and the update command (RED: seen missing before the hook, then seen shown)
- [ ] An up-to-date install shows nothing
- [ ] Fails open, with the reason on stderr, when offline or when the published version cannot be read
- [ ] Does not fire on `clear`, `resume` or `compact`
- [ ] The warning does not add to the model context (verified end to end, not assumed)
- [ ] Works on Windows (Git Bash) and POSIX
- [ ] Tests in `tests/` and `claude plugin validate` pass
- [ ] Plugin README documents the check and why it replaces auto-update

