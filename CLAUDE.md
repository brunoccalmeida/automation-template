# automation-template - Project rules

Rules for this repository only. The ones that apply to every project are in [`.claude/rules/core.md`](.claude/rules/core.md), which comes from the template and is not edited here.

## Contracts

Values that the core and the [`mission`](plugins/mission/README.md) plugin use in this repository. The artifact published today is the plugin itself, so `check` is its validation and `test` is the tests of its hooks, until Mission 1 (#2) brings the template's tests.

| Contract | Value |
| --- | --- |
| `check` | `npm ci --prefix .github/tools/claude-cli` once, then `python3 .github/scripts/validate_plugins.py` (on Windows, pass the script the absolute path of `.github\tools\claude-cli\node_modules\.bin\claude.cmd`) |
| `test` | `python3 -m unittest discover -s tests` (tests of the plugin's hooks; they need `sh` and `git` on the `PATH` and fail without them; on Windows, `python` or `py -3`, with Git Bash on the `PATH`) |
| `smoke` | None: there is no template to generate a project from yet (Mission 1, #2) |
| `main-branch` | `main` |
| `gate` | `ci-passed` |
| `session-summary` | `docs/PROJECT_SESSION_SUMMARY.md` |

## Exceptions to the core

- **"Everything written to the repository is in English":** the review eval fixtures (`plugins/mission/evals/review/**/mission.diff`, `plugins/mission/evals/review/fixtures/`) and the graders that quote them keep their Brazilian Portuguese. Why: they are the historical diffs of merged missions, reviewed again by the suite; translating them would change what the reviewer is measured on and break the comparison with the recorded baselines.

## Template architecture rules

This repository is a [Copier](https://copier.readthedocs.io/) template for test automation projects: a **core** that every project inherits and one **pack** per tool (`ts-playwright`, `python-behave-selenium`). The decisions are in `docs/adr/`; the evidence for what goes in, in `docs/INVENTORY.md`.

- **The core names no stack** (tool, language, target type): it defines contracts that each pack implements through Copier variables ([ADR 0003](docs/adr/0003-stack-agnostic-core-defines-contracts.md)).
- **One pack per tool, not per test type**; the test type is an option inside the pack ([ADR 0002](docs/adr/0002-core-plus-packs-split-by-tool.md)).
- **Walking skeleton, no domain abstraction:** infrastructure, conventions as documented folders, and one smoke; no `BasePage`, page objects, API clients or authentication.
- **Evidence first:** what is not proven in the source projects stays out (rule of three).
- **Keep what belongs to the template apart from what belongs to the generated project:** the project adds its own files instead of editing the template's, so `copier update` does not conflict.
- **The template is tested by generating a project:** it does not run on its own; the test generates a project and validates the result.

## Ruleset as code

[`.github/rulesets/protect-main.json`](.github/rulesets/protect-main.json) describes the active ruleset (id 27584439), but editing the file does not change GitHub. Changed the file: apply it with `gh api -X PUT repos/{owner}/{repo}/rulesets/27584439 --input .github/rulesets/protect-main.json` and check with `gh api repos/{owner}/{repo}/rulesets/27584439`; changed it in the web interface: bring the change into the file. The automatic drift check is left to Mission 4 (#6).

## Changes to the plugin itself

The mission is closed by the published version (installed from GitHub, `autoUpdate: false`), not by the branch's. To try the branch's version, start a session with `claude --plugin-dir ./plugins/mission`, which overrides the installed one for that session only ([Plugin loading reference](https://code.claude.com/docs/en/plugins/loading.md#name-conflicts)). After the merge, `claude plugin update mission@brunoccalmeida-plugins`.
