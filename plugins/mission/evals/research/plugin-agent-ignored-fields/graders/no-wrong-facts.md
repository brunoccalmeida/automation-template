---
type: llm
---
The question was: "Which subagent frontmatter fields does Claude Code ignore when it loads a subagent from a plugin?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/plugins/components.md#frontmatter-fields-in-plugin-agents):

> **Ignored fields**: `permissionMode`, `hooks`, `mcpServers`, and `initialPrompt`. An agent file can't add hooks or MCP servers on its own, so add those as plugin hooks and MCP servers instead
(The subagents page, https://code.claude.com/docs/en/sub-agents.md, marks the same four rows "Ignored for plugin subagents" in its frontmatter table; its security note names only `hooks`, `mcpServers` and `permissionMode`.)
The same page also documents two edge cases, which are true and are not contradictions: "A `name` longer than 256 characters: Claude Code ignores it and names the agent after its file" and "Frontmatter that doesn't parse: the agent still loads with every field ignored".

Judge only whether the response states something false about what the question asks. Ignore missing facts and ignore extra claims that the reference neither confirms nor contradicts.
PASS if no claim in the response contradicts the reference.
FAIL if any claim contradicts the reference, for example: saying that, in a plugin agent whose frontmatter parses, `model`, `effort`, `tools`, `description` or any field other than `permissionMode`, `hooks`, `mcpServers` and `initialPrompt` is ignored.
