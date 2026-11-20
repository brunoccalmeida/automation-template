---
description: Order in which Claude Code picks a subagent's model
tags: [researcher]
max_turns: 10
timeout_seconds: 900
allowed_tools: [Agent]
---

Use the `mission:researcher` agent to answer the question below. Do not answer it yourself and do not pass a `model` parameter to the agent. When it returns, reply with its answer as returned, including the source URLs it cites.

Question: In Claude Code, when more than one source sets a subagent's model, in what order does Claude Code pick one?
