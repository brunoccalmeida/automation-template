---
description: How long a skill's frontmatter model override lasts
tags: [researcher]
max_turns: 10
timeout_seconds: 900
allowed_tools: [Agent]
---

Use the `mission:researcher` agent to answer the question below. Do not answer it yourself and do not pass a `model` parameter to the agent. When it returns, reply with its answer as returned, including the source URLs it cites.

Question: If a Claude Code skill sets `model` in its frontmatter, how long does that model stay active, and what changes when the skill also sets `context: fork`?
