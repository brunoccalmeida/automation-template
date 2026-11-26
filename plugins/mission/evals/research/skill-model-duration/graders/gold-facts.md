---
type: llm
---
The question was: "If a Claude Code skill sets `model` in its frontmatter, how long does that model stay active, and what changes when the skill also sets `context: fork`?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/skills.md#frontmatter-reference, `model` row, read on 2026-11-25):

> Model for the turn when you run this skill with `/name`. [...] When Claude runs the skill, the session keeps its model. [...] With `context: fork`, the value is the forked subagent's per-invocation model.

PASS if the response states every one of these facts, in any wording or language: (1) when the user runs the skill with `/name`, the model applies for that turn; (2) when Claude runs the skill on its own, the session keeps its model; (3) with `context: fork`, the value is the forked subagent's model for that invocation.
FAIL if any of these facts is missing, or stated only as a guess.
