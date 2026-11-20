---
type: llm
---
The question was: "If a Claude Code skill sets `model` in its frontmatter, how long does that model stay active, and what changes when the skill also sets `context: fork`?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/skills.md#frontmatter-reference):

> Model to use when this skill is active. The override applies for the rest of the current turn and isn't saved to settings. The session model resumes when you send your next prompt. [...] With `context: fork`, the value sets the forked subagent's model instead

PASS if the response states every one of these facts, in any wording or language: (1) the model applies for the rest of the current turn; (2) the session model resumes on the next prompt (it is not saved to settings); (3) with `context: fork`, the value sets the forked subagent's model instead of the session's.
FAIL if any of these facts is missing, or stated only as a guess.
