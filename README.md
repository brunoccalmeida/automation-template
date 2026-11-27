# automation-template

A [Copier](https://copier.readthedocs.io/) template for test automation projects: an AI-assisted delivery harness (rules, skills, reviewer agent, CI gates) shared by every project, plus one pack per test stack.

It is extracted from two existing projects, [uat-automation-framework](https://github.com/brunoccalmeida/uat-automation-framework) (Python, Behave, Selenium) and [playwright-qa-starter-kit](https://github.com/brunoccalmeida/playwright-qa-starter-kit) (Playwright, TypeScript), which had grown the same harness by copy and paste.

> 🚧 Work in progress: the template is being built mission by mission. Today the repository ships the harness's Claude Code plugin; the Copier template has resumed for the shared core and the `ts-playwright` pack ([ADR 0006](docs/adr/0006-resume-copier-for-the-core-and-the-ts-pack.md)). Its walking skeleton ([`copier.yml`](copier.yml), [`template/`](template/)) renders the core rules, the contracts table from the answers, the `mission` marketplace registration, deny rules for `--admin`, force push and `.env` and a `SessionStart` hook that lists the open issues and pull requests ([ADR 0010](docs/adr/0010-claude-code-enforcement-in-the-core.md)), a CI workflow whose gate job runs the core's checks (UTF-8 text, secret scan, workflow audit; [ADR 0011](docs/adr/0011-ci-enforcement-as-a-reusable-core-workflow.md)), the ruleset that requires that gate and a `/new-project` skill that applies it with the labels and merge settings ([ADR 0013](docs/adr/0013-new-project-applies-the-github-settings-with-a-shared-script.md)), Dependabot for GitHub Actions, a Mission issue form and a pull request template with the mission record ([ADR 0012](docs/adr/0012-github-files-rendered-by-the-core.md)), the document templates (session summary, known issues, flaky test policy, ADR, spike report) and the answers file `copier update` needs ([ADR 0008](docs/adr/0008-core-rules-and-documents-in-the-generated-project.md), [ADR 0009](docs/adr/0009-contracts-as-copier-answers-and-a-shared-harness.md)). The `pack` answer adds the `ts-playwright` walking skeleton, with `e2e` and `api` as options: runner config, an environment validated at startup, lint, type and format checks and one `@smoke` test per type ([ADR 0014](docs/adr/0014-ts-playwright-pack-walking-skeleton.md)), hardened with a vulnerability audit, a Dependabot ignore sentinel, compact output for the agent and the HTML report as a run artifact ([ADR 0015](docs/adr/0015-ts-playwright-pack-hardening.md)). CI tests the template by generating projects ([`tests/test_template.py`](tests/test_template.py)) and by running the pack's own commands in one ([`tests/packs/`](tests/packs/test_ts_playwright.py)); it is not ready for use yet.

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
