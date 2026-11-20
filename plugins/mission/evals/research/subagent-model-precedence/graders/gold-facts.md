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

PASS if the response states every one of these facts, in any wording or language: (1) the per-invocation `model` parameter comes first; (2) then the `model` field of the subagent definition; (3) then the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable; (4) then the main conversation's (parent's) model, last. The four must appear in this order.
FAIL if any of these facts is missing, or stated only as a guess.
