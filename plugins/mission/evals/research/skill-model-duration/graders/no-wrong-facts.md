---
type: llm
---
The question was: "If a Claude Code skill sets `model` in its frontmatter, how long does that model stay active, and what changes when the skill also sets `context: fork`?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/skills.md#frontmatter-reference, `model` row, read on 2026-11-25):

> Model for the turn when you run this skill with `/name`. [...] When Claude runs the skill, the session keeps its model. [...] With `context: fork`, the value is the forked subagent's per-invocation model.

Judge only whether the response states something false about what the question asks. Ignore missing facts and ignore extra claims that the reference neither confirms nor contradicts.
PASS if no claim in the response contradicts the reference.
FAIL if any claim contradicts the reference, for example: saying the model stays for the rest of the session, that it also applies when Claude runs the skill on its own, or that `context: fork` ignores the skill's `model`.
