---
type: llm
---
The question was: "Which subagent frontmatter fields does Claude Code ignore when it loads a subagent from a plugin?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/plugins/components.md#frontmatter-fields-in-plugin-agents):

> **Ignored fields**: `permissionMode`, `hooks`, `mcpServers`, and `initialPrompt`. An agent file can't add hooks or MCP servers on its own, so add those as plugin hooks and MCP servers instead
(The subagents page, https://code.claude.com/docs/en/sub-agents.md, marks the same four rows "Ignored for plugin subagents" in its frontmatter table; its security note names only `hooks`, `mcpServers` and `permissionMode`.)
The same page also documents two edge cases, which are true and are not contradictions: "A `name` longer than 256 characters: Claude Code ignores it and names the agent after its file" and "Frontmatter that doesn't parse: the agent still loads with every field ignored".

PASS if the response states every one of these facts, in any wording or language: the ignored fields are `permissionMode`, `hooks`, `mcpServers` and `initialPrompt` (all four).
FAIL if any of these facts is missing, or stated only as a guess.
