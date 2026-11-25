# automation-template

A [Copier](https://copier.readthedocs.io/) template for test automation projects: an AI-assisted delivery harness (rules, skills, reviewer agent, CI gates) shared by every project, plus one pack per test stack.

It is extracted from two existing projects, [uat-automation-framework](https://github.com/brunoccalmeida/uat-automation-framework) (Python, Behave, Selenium) and [playwright-qa-starter-kit](https://github.com/brunoccalmeida/playwright-qa-starter-kit) (Playwright, TypeScript), which had grown the same harness by copy and paste.

> 🚧 Work in progress: the template is being built mission by mission. Today the repository ships the harness's Claude Code plugin; the Copier template is paused ([ADR 0004](docs/adr/0004-partial-resumption-with-a-plugin.md)).

## Claude Code plugin

The repository is also a Claude Code plugin marketplace, `brunoccalmeida-plugins`. Its [`mission`](plugins/mission/README.md) plugin carries the shared skills and reviewer agent: `/mission:close-mission`, `/mission:ship-pr` and `mission:reviewer`.

To use it in a project, run these from the project root, then commit `.claude/settings.json` so everyone who clones the project gets the same setup:

```sh
claude plugin marketplace add brunoccalmeida/automation-template --scope project
claude plugin install mission@brunoccalmeida-plugins --scope project
```

The plugin names contracts (`check`, `test`, `main-branch`, …) instead of commands, so each project declares the real values in a table in its rules. The [plugin README](plugins/mission/README.md) describes that table, the repository settings the skills rely on, and how to update.

This repository runs its own missions with the plugin, installed from GitHub exactly as an adopting project installs it, with its contract table in [`CLAUDE.md`](CLAUDE.md#contracts), the shared core rules in [`.claude/rules/core.md`](.claude/rules/core.md), its review checks in [REVIEW.md](REVIEW.md) and a `ci-passed` gate required by the main ruleset ([`.github/rulesets/`](.github/rulesets/)).

## Design

- [Architecture Decision Records](docs/adr/): why Copier, why a core plus packs split by tool, and why the core only defines contracts that each pack implements.
- [Inventory](docs/INVENTORY.md): every piece of the two source projects, classified as core, pack or application-specific, with the better of the two implementations.

## License

MIT, see [LICENSE](LICENSE).
