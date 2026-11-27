# 14. The `ts-playwright` pack as a walking skeleton chosen by an answer

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

Mission 5 (#7) brings the first pack ([ADR 0002](0002-core-plus-packs-split-by-tool.md)), extracted from playwright-qa-starter-kit, with e2e and api as options inside it. The issue listed about ten pieces; the mission was split on 2026-11-26: Mission 5a (#7) is the walking skeleton, and Mission 5b (#78) the hardening (vulnerability audit, Dependabot ignore sentinel, test-output hook, published HTML report).

**Rule of three, checked again** ([ADR 0006](0006-resume-copier-for-the-core-and-the-ts-pack.md), decision 2): supabase-app-hardening still has no Git repository, so the pack has two sources, the kit and playwright-nextjs-e2e-ci (nextjs). Only what both share goes in:

| Piece | kit | nextjs | In the pack |
| --- | --- | --- | --- |
| `api` and browser projects, `tests/api`, `tests/e2e` | Yes | Yes | Yes |
| Environment validated with zod at startup, message pointing at `.env.example` | Yes | Yes | Yes, read with `process.loadEnvFile` as in the kit (no dependency) |
| `forbidOnly` and `retries: 2` in CI | Yes | Yes | Yes, with `failOnFlakyTests` (the core's "a retry never passes a build", [ADR 0008](0008-core-rules-and-documents-in-the-generated-project.md)) |
| Strict `tsconfig` flags | Yes | Yes | Yes |
| ESLint `strictTypeChecked`, `no-floating-promises`, `eslint-plugin-playwright` | Yes | Yes | Yes |
| Rules that keep secrets out of report step titles | Yes | Yes | No: they protect the published report, which comes with #78 |
| Prettier, `.node-version` | Yes | Yes | Yes |
| A smoke test | No | No | Yes: the contract `smoke` asks for one ([ADR 0003](0003-stack-agnostic-core-defines-contracts.md)) |
| Domain abstractions (page objects, API clients, data factories, login setup) | Yes | Yes | No ([ADR 0002](0002-core-plus-packs-split-by-tool.md), consequences) |

Sources (read 2026-11-26):

- **Copier 9.19.1.** `multiselect: true` stores a list (since 9.1.0); `when` skips a question; a `default` can be a Jinja expression over earlier answers; `_exclude` patterns are rendered with Jinja ([Configuring a template](https://copier.readthedocs.io/en/stable/configuring/)). The documentation does not say which path a pattern is matched against. The code does: `match_exclude(dst_relpath)` in `copier/_main.py`, the rendered path, without `.jinja`. A pattern written with the suffix matched nothing; the stack-term test caught it. With `_subdirectory` set, the default exclude list is empty (`copier/_template.py`), so setting `_exclude` loses nothing.
- **Playwright 1.65.** A test is tagged with the `tag` details option and selected with `--grep` ([Annotations](https://playwright.dev/docs/test-annotations)). `failOnFlakyTests`, added in 1.52, exits with an error when a test is flaky ([TestConfig](https://playwright.dev/docs/api/class-testconfig)). The `request` fixture honours `baseURL` ([API testing](https://playwright.dev/docs/api-testing)). In CI the guide installs browsers with `npx playwright install --with-deps`, a browser can be named, and the official Docker image must match the package version ([CI](https://playwright.dev/docs/ci), [Browsers](https://playwright.dev/docs/browsers), [Docker](https://playwright.dev/docs/docker)). `npm init playwright` generates `trace: 'on-first-retry'` (create-playwright's `assets/playwright.config.ts`).
- **Node 26.** It became LTS on 2026-10-28 (nodejs/release `schedule.json`). `process.loadEnvFile` is no longer experimental since 24.10.0 ([process](https://nodejs.org/docs/latest-v26.x/api/process.html)); the documentation does not say whether a variable already in the environment wins over the file. A test of the pack proves it does.
- **Testing a template with a toolchain.** pawamoy/copier-uv's CI generates a project and runs the generated project's own checks and tests in a job of its own; cookiecutter-hypermodern-python runs the generated project's `nox` in its CI.

## Decision

1. **The pack is chosen by an answer.** `pack` (`none` or `ts-playwright`, default `none`, so a project without a pack is the core alone, as before) and, when it is `ts-playwright`, `test_types` (multiselect `e2e`, `api`, at least one). The contract commands default by pack: `npm run check`, `npm test`, `npm run smoke`.
2. **Files are left out by `_exclude`, by rendered path,** not by Jinja in each file name, so the pack's files keep their real names in `template/`.
3. **Every pack file is project-owned** (`_skip_if_exists`). A walking skeleton is a starting point: the project grows its dependencies, variables, Playwright projects, lint rules and the smoke itself, which ADR 0003 expects to be replaced. The core's files stay template-owned, and the pack's `.prettierignore` leaves them unformatted, so `copier update` still applies its changes without conflicts.
4. **One smoke per chosen type,** tagged `@smoke`: `api` asserts that `GET /` is OK through `request`; `e2e` opens `/` in Chromium. `npm run smoke` is `playwright test --grep @smoke`.
5. **The generated CI** adds `check` and `test` jobs to the gate's `needs`. `test` reads `BASE_URL` from an Actions variable (a URL is not a secret) and, with e2e, installs Chromium with `npx playwright install --with-deps chromium`. The kit's pinned Playwright image and the script that keeps its tag equal to the package version are left to #78 if needed (kit#24: the runner's apt mirror once spent a whole timeout).
6. **Dependencies are pinned exactly,** in a lockfile the template ships, at the newest version older than the core's 7-day cooldown within the kit's majors. With the kit's pins, `npm audit` found GHSA-g3hv-75wg-m249 (`minimatch` through `eslint` 10.14.0 and `typescript-eslint` 8.72.1); with eslint 10.15.0 and typescript-eslint 8.73.0 it finds none, so the pack needs no `overrides`. TypeScript stays on 6.0: typescript-eslint 8.73 requires `<6.1.0`. The generated `dependabot.yml` gets an `npm` block with the same cooldown.
7. **The template's CI proves the pack by running it.** `tests/packs/test_ts_playwright.py` generates projects with the pack and runs `npm ci`, the three contracts and probes (an unreachable system fails the smoke, a missing `BASE_URL` stops the run before any test, a flaky test fails a CI run, the shell wins over `.env`) against an HTTP server the test starts, so nothing depends on a site outside the machine. It runs in a job of its own, `pack-ts-playwright`, because it needs Node and a browser; `tests/packs/` has no `__init__.py`, so the core's `discover -s tests` does not reach it.

## Alternatives

- **The kit's versions as they are:** they carry GHSA-g3hv-75wg-m249, and the kit fixes it with an `overrides` pin; newer releases outside the cooldown fix it with no override.
- **The Playwright image in the generated CI now:** sturdier against the apt mirror, but it brings the tag-sync script with it, and the documentation's default is the install step.
- **The pack's test inside `tests/test_template.py`:** the core's `test` job and every local run of the core's tests would need Node and a browser.
- **A public site as the smoke target in the template's CI:** the template's build would fail when that site does.

## Consequences

- The `test` contract of this repository gains a second command, for the pack, which needs Node on the `PATH` and downloads Chromium on its first run.
- `template/package-lock.json.jinja` is a generated file: change `package.json.jinja`, regenerate the lockfile with `npm install` in a scratch directory and copy both, with the project name replaced by the template expression. Nothing bumps it yet; that is #75's question.
- A generated project's `test` job needs the `BASE_URL` Actions variable; without it, the job fails naming the variable.
- The core's stack-term test still runs on a project with no pack; the pack's files are the only place a stack is named.
