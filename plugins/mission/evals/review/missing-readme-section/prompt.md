---
description: 'Planted: #31 without the plugin README changes that document the new hook'
tags: [reviewer]
max_turns: 10
timeout_seconds: 1200
allowed_tools: [Agent, Read, Grep, Glob]
---

Use the `mission:reviewer` agent to review the mission in this workspace. Do not review it yourself and do not pass a `model` parameter to the agent. Give the agent exactly this task:

"Review this mission. The issue text is in `.scratchpad/issue.md`; the mission diff, preceded by its commit messages, is in `.scratchpad/mission.diff`. The repository is the current directory, with the mission applied. In this run the project rules are not in your context: read `CLAUDE.md` and the files it imports before you start."

When the agent returns, reply with its answer exactly as returned, nothing added.
