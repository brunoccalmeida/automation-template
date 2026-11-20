---
type: llm
---
The question was: "If a Claude Code skill sets `model` in its frontmatter, how long does that model stay active, and what changes when the skill also sets `context: fork`?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/skills.md#frontmatter-reference):

> Model to use when this skill is active. The override applies for the rest of the current turn and isn't saved to settings. The session model resumes when you send your next prompt. [...] With `context: fork`, the value sets the forked subagent's model instead

Judge only whether the response states something false about what the question asks. Ignore missing facts and ignore extra claims that the reference neither confirms nor contradicts.
PASS if no claim in the response contradicts the reference.
FAIL if any claim contradicts the reference, for example: saying the model stays for the rest of the session, is saved to settings, or that `context: fork` ignores the skill's `model`.
