---
paths:
  - "CLAUDE.md"
  - "AGENTS.md"
  - ".claude/rules/**"
  - ".claude/settings.json"
  - "docs/ai-workflow/**"
---

# Agent rules

- Always-loaded rules (`CLAUDE.md`, `AGENTS.md` where the project has one, and the files in `.claude/rules/` with no `paths:`, such as `core.md`) hold nothing that ages: no dates, counts, versions or project state. Those live in the `session-summary`.
- Always-loaded rules hold what every session needs. What only one kind of task needs goes in a path-scoped rule (`paths:` on the files that task touches), a skill or the docs. What a session needs before it reads its first file stays always-loaded, since a path-scoped rule loads only once a matching file is read, written or edited; what a person needs before starting the session goes in the docs.
- Do not repeat in a rule what a linter, a formatter or a test already enforces.
- A change that promises to save tokens is measured before and after, as described in [`docs/ai-workflow/AGENT_TOKEN_SPEND.md`](../../docs/ai-workflow/AGENT_TOKEN_SPEND.md).
- `core.md` and this file come from the template: change them in the template, not here, or `copier update` turns the edit into a conflict.
