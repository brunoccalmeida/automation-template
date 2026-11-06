# 3. The core is stack-agnostic and defines contracts that packs implement

- **Status:** Accepted
- **Date:** 2026-11-06

## Context

The rules and skills of both source projects name their tools directly: `npm run check`, `poetry run pytest`, `BASE_URL`, Playwright traces. Moved into a shared core as they are, they would make every future project look like a Node web project. Neither npm nor a URL is universal: a desktop project has an executable path instead of a URL, and a .NET project has no npm.

What is universal is the intent behind each of those commands and variables.

## Decision

**The core never names a stack, a tool or a target type. It defines contracts; each pack implements them.** This is dependency inversion applied to the template: the higher level (core) depends on abstractions, the details (packs) depend on them too.

| Contract (core) | Meaning | `ts-playwright` | `python-behave-selenium` |
| --- | --- | --- | --- |
| **check** | Static gates: lint, types, formatting | `npm run check` | `pre-commit run --all-files` |
| **test** | The whole suite | `npx playwright test` | `pytest` and `behave` |
| **smoke** | The system under test (SUT) is reachable and the pipeline works end to end | test tagged `@smoke` | scenario tagged `@smoke` |
| **configuration** | Comes from environment variables, validated at startup; every variable is documented in `.env.example`; `.env` is never committed; secrets never live in code | `BASE_URL`, … | `BASE_URL`, … |

The contracts are bound to commands through **Copier variables**: each pack declares its commands, and Copier writes the real command into rules, skills and CI when it renders a project. The template contains `{{ cmd_check }}`; the generated project contains `npm run check`, so whoever reads it, a person or an agent, sees the exact command that will run.

Configuration follows factor III of the [Twelve-Factor App](https://12factor.net/config): config lives in the environment, not in code. The variables themselves belong to the pack: a web pack asks for a base URL, a future desktop pack would ask for an executable path.

## Alternatives

- **A single task runner in every project** (`just`, `make`, Taskfile; GitHub's "Scripts to Rule Them All"): `just check` everywhere, whatever the language. Rejected for now: one more tool in every project, and `make` is awkward on Windows. Still available if the number of commands to standardise grows.

## Consequences

- The core cannot be read alone: the reader sees `{{ cmd_check }}` until a project is rendered. Generated projects, not the template, are what people read day to day.
- A test in the template's CI fails when the core mentions a stack term (`npm`, `pytest`, `playwright`, `BASE_URL`, …), so the rule is enforced by a machine, not by attention (Mission 2b).
- The smoke test of each pack proves reachability, not behaviour: it is a tracer bullet, expected to be replaced once the project's first real tests exist.
