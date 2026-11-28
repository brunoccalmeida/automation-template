# automation-template - Project rules

Rules for this repository only. The ones that apply to every project are in [`.claude/rules/core.md`](.claude/rules/core.md), which comes from the template and is not edited here.

## Contracts

Values that the core and the [`mission`](plugins/mission/README.md) plugin use in this repository. `check` is the validation of the plugin; `test` covers the plugin's hooks and the Copier template, which is tested by generating a project from it.

| Contract | Value |
| --- | --- |
| `check` | `npm ci --prefix tools/claude-cli` once, then `python3 .github/scripts/validate_plugins.py` (on Windows, pass the script the absolute path of `tools\claude-cli\node_modules\.bin\claude.cmd`) |
| `test` | `pip install --require-hashes --only-binary :all: -r tools/copier/requirements.txt` once, in a virtual environment, then `python3 -m unittest discover -s tests` (tests of the plugin's hooks and of the template; they need `sh`, `git` and `copier` on the `PATH` and fail without them; on Windows, `python` or `py -3`, with Git Bash on the `PATH`) and `python3 -m unittest discover -s tests/packs` (the `ts-playwright` pack, generated and run; it also needs Node and npm, and downloads Chromium on the first run) |
| `smoke` | None: the template has no stack of its own to run |
| `main-branch` | `main` |
| `gate` | `ci-passed` |
| `session-summary` | `docs/PROJECT_SESSION_SUMMARY.md` |

## Language

Documentation language: English

## Exceptions to the core

- **"Code and commit messages are in English" and the documentation language above:** the review eval fixtures (`plugins/mission/evals/review/**/mission.diff`, `plugins/mission/evals/review/fixtures/`) and the graders that quote them keep their Brazilian Portuguese. Why: they are the historical diffs of merged missions, reviewed again by the suite; translating them would change what the reviewer is measured on and break the comparison with the recorded baselines.

## Template architecture rules

- **The core names no stack** (tool, language, target type): it defines contracts that each pack implements through Copier variables ([ADR 0003](docs/adr/0003-stack-agnostic-core-defines-contracts.md)).
- **One pack per tool, not per test type**; the test type is an option inside the pack ([ADR 0002](docs/adr/0002-core-plus-packs-split-by-tool.md)).
- **Walking skeleton, no domain abstraction:** infrastructure, conventions as documented folders, and one smoke; no `BasePage`, page objects, API clients or authentication.
- **Evidence first:** what is not proven in the source projects ([`docs/INVENTORY.md`](docs/INVENTORY.md)) stays out (rule of three).
- **Keep what belongs to the template apart from what belongs to the generated project:** the project adds its own files instead of editing the template's, so `copier update` does not conflict.
- **The template is tested by generating a project:** it does not run on its own; the test generates a project and validates the result.
