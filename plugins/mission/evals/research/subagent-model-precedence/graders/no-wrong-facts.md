---
type: llm
---
The question was: "In Claude Code, when more than one source sets a subagent's model, in what order does Claude Code pick one?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/sub-agents.md#choose-a-model):

> When more than one source sets a model, Claude Code uses the first in this order:
> 1. The per-invocation `model` parameter, which Claude can pass when it starts the subagent. On an Agent tool call, the parameter takes a model alias, not a full model ID or `inherit`.
> 2. The `model` field in the subagent's definition, including `inherit`
> 3. The `CLAUDE_CODE_SUBAGENT_MODEL` environment variable
> 4. The main conversation's model, or the spawning subagent's model for a nested subagent

Judge only whether the response states something false about what the question asks. Ignore missing facts and ignore extra claims that the reference neither confirms nor contradicts.
PASS if no claim in the response contradicts the reference.
FAIL if any claim contradicts the reference, for example: putting the frontmatter `model` field above the per-invocation parameter, putting `CLAUDE_CODE_SUBAGENT_MODEL` first, or saying subagents default to Haiku.
