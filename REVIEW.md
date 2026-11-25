# Review instructions

Checks specific to this repository, read by `mission:reviewer` on top of its own list. General rules live in `.claude/rules/core.md` and `CLAUDE.md`, which the reviewer already loads.

## Always check

- **The core names no stack:** no tool, language or target type (`npm`, `pytest`, `playwright`, `BASE_URL`…) outside a pack; the core speaks in contracts ([ADR 0003](docs/adr/0003-stack-agnostic-core-defines-contracts.md)). This applies to `.claude/rules/core.md`, which may name a value only as an example of the contracts table.
- **The pack brings no domain abstraction:** a walking skeleton with only infrastructure, documented folders and one smoke; no `BasePage`, page objects, API clients or authentication.
- **What goes in has evidence:** each new piece of the template or the plugin appears in [`docs/INVENTORY.md`](docs/INVENTORY.md) or in an ADR in [`docs/adr/`](docs/adr/); without that, it stays out (rule of three).
- **The plugin names no stack and no fixed branch:** skills and agents in `plugins/` name contracts (`check`, `test`, `smoke`, `main-branch`, `gate`, `session-summary`), never a command, tool, `main`/`master` or `ci-passed`. The plugin README may name a value only as an example of the contracts table.
- **A plugin change reaches the projects:** if the change alters what a project has to provide (contract, repository configuration, installation), the plugin README explains it, with a source.
- **A new gate was seen failing:** a new CI job goes into the `needs` of `ci-passed`, and the mission record says how it was seen failing.

## Do not report

- What `validate-plugins` already enforces (manifest, frontmatter, the fields of skills and agents).
