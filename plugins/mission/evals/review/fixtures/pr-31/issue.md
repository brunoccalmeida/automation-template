# feat(mission): block /mission:ship-pr unless it is the first message of a fresh chat

## Problem

`/mission:ship-pr` usually runs at the end of the chat that implemented the mission, when the context is already 100k–290k tokens. Every tool call re-sends the whole conversation, so the ship-pr phase (CI waits, review rounds, merge) pays for that context on each of its 36–95 calls.

Measured on 8 local transcripts of a project that uses this plugin: running ship-pr in a fresh chat (~50k tokens of fixed context) instead would have saved **~6–14% of each mission's cost** (about 10% on average). ship-pr needs nothing from the conversation: the PR body holds the mission record and the session summary holds the state.

Remembering to `/clear` first is a habit, and habits fail. The plugin should enforce it.

## Proposal

Ship a `UserPromptExpansion` hook with the plugin (`plugins/mission/hooks/hooks.json` plus a script under `${CLAUDE_PLUGIN_ROOT}`):

- matcher: `mission:ship-pr` (the `command_name` of a plugin skill is `plugin:skill`)
- the script reads `transcript_path` from the hook input; if the transcript already holds any assistant message, it returns `{"decision": "block", "reason": "..."}` telling the user to run `/clear` and call `/mission:ship-pr` as the first message of the new chat
- a fresh chat has no assistant message, so the command passes

Why `UserPromptExpansion` and not `PreToolUse` on `Skill`: typing `/skillname` bypasses `PreToolUse`. The [hooks reference](https://code.claude.com/docs/en/hooks#userpromptexpansion) cites this exact use: "a hook matching `deploy` can block `/deploy` unless an approval file is present". Plugins can bundle hooks: [plugins reference](https://code.claude.com/docs/en/plugins-reference).

Why in the plugin and not in each project: the guard lives next to the skill it protects, and every project that uses `mission` gets it.

## Acceptance criteria

- [ ] `/mission:ship-pr` typed in a chat with prior conversation is blocked with an actionable message (RED: seen blocked)
- [ ] `/mission:ship-pr` typed as the first message after `/clear` runs normally
- [ ] Other commands and plain prompts are unaffected (the matcher does not fire)
- [ ] The script fails open (allows) when the transcript is missing or unreadable, and says so on stderr: it guards cost, not safety
- [ ] Works on Windows (Git Bash) and POSIX; the path is quoted or exec form is used
- [ ] `claude plugin validate` passes
- [ ] Plugin README documents the guard and the "ship-pr in a fresh chat" step; `close-mission` tells the user to `/clear` before ship-pr
- [ ] Plugin version bumped so consumers with `autoUpdate: false` can pick it up with `/plugin marketplace update`

