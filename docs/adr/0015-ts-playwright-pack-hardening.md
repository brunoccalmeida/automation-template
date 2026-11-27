# 15. Hardening of the `ts-playwright` pack

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

Mission 5a (#7, [ADR 0014](0014-ts-playwright-pack-walking-skeleton.md)) shipped the pack's walking skeleton and left four pieces of playwright-qa-starter-kit and uat-automation-framework to this mission: a vulnerability audit, a sentinel for the Dependabot ignore, compact test output for the agent, and a published HTML report. The kit's pinned Playwright image was a candidate too, if the install step proved slow or flaky.

Facts that shaped the decision (read 2026-11-26):

- **The ignore has a reason today.** `typescript@latest` is 7.0.2, and the newest typescript-eslint (8.74.0) declares the peer `typescript: >=4.8.4 <6.1.0` (`npm view`). With no ignore, Dependabot opens the TypeScript 7 PR in every generated project, and `npm ci` rejects it.
- **Vulnerability audit.** `npm audit` exits non-zero according to `--audit-level` and has no per-advisory exception ([npm audit, v11](https://docs.npmjs.com/cli/v11/commands/npm-audit)). OSV-Scanner reads the GitHub Advisory Database among its sources ([OSV data](https://google.github.io/osv.dev/data/)), and `osv-scanner.toml` takes `[[IgnoredVulns]]` with an optional `effectiveUntil`, "after which the ignore will no longer apply" ([Configuration](https://google.github.io/osv-scanner/configuration/)). The kit needed such an exception (picomatch, no patched release). The official reusable workflow v2.7.1 runs the image `ghcr.io/google/osv-scanner-action:v2.7.1` and fails the job from its reporter step, not from the scanner's exit code (its `osv-scanner-reusable.yml` and `action.yml` at that tag).
- **Agent output.** Claude Code sets `CLAUDECODE=1` in the subprocesses it spawns, IDE terminals included, and names `CLAUDE_CODE_CHILD_SESSION` to tell a process spawned by a tool call or hook ([Environment variables](https://code.claude.com/docs/en/env-vars)). The `dot` reporter prints one character per passing test ([Reporters](https://playwright.dev/docs/test-reporters)). Playwright 1.65 adds a default printing reporter when none of the configured ones prints to stdout (seen: a `null` reporter still printed the run), and reads `CLAUDECODE` only to keep the HTML report from opening (`isCodingAgent` in `playwright-core`). The UAT rewrites the `pytest` and `behave` commands in a `PreToolUse` hook instead.
- **Publishing.** "GitHub Pages sites are publicly available on the internet, even if the repository for the site is private"; only GitHub Enterprise Cloud publishes privately; on GitHub Free the repository must be public ([Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site), [Changing the visibility](https://docs.github.com/en/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)). The kit publishes on Pages only because it added a redacting reporter and turns traces off in CI, since a trace stores request bodies; the pack keeps `trace: 'on-first-retry'`.

## Decision

1. **The audit is an `audit` job in the generated CI** that calls the OSV-Scanner reusable workflow, pinned by SHA (v2.7.1), on `package-lock.json`, without SARIF upload, inside the gate's `needs`. The pack ships `osv-scanner.toml` with the kit's policy: a known vulnerability fails; a patched version goes into `overrides`; only an unpatched, non-exploitable one gets an exception with a reason, an `effectiveUntil` at most 30 days ahead and a tracking issue.
2. **The template's CI runs the same scanner.** `tests/packs/` downloads the osv-scanner v2.7.1 binary of the job's release, checks its SHA-256 against the release's `SHA256SUMS`, and proves that the generated lockfile is clean, that a lockfile with lodash 4.17.20 fails, and that an exception holds until its date and not after. A test keeps the job's version comment equal to the binary's.
3. **The Dependabot ignore of the TypeScript major comes with the kit's sentinel,** `scripts/check-dependency-ignores.ts`, run by `npm run check`: it fails once the installed typescript-eslint accepts the next major while the ignore is still there. It brings `semver`, `yaml` and `@types/semver`, pinned at versions older than the cooldown.
4. **Compact output is chosen by the config, not by a hook.** `playwright.config.ts` uses `dot` when `CLAUDE_CODE_CHILD_SESSION` is set (read in `src/config/env.ts` with the other variables; its presence counts, not its value, which Claude Code owns), `list` otherwise, and CI keeps its reporters.
5. **The HTML report is an artifact of the run,** written by the `html` reporter in CI and uploaded by the `test` job even when tests fail (`!cancelled()`), kept 14 days. No Pages site.
6. **No Playwright image.** The install step stays: nothing has shown it slow or flaky in the pack.

## Alternatives

- **`npm audit` in `check`:** runs with no extra tool, but an advisory with no fix would block every build until someone turned the gate off.
- **OSV seen once on a throwaway repository:** no new pin to bump, but no regression test of the policy file.
- **A `PreToolUse` hook, as in the UAT:** it needs a hook in `.claude/settings.json`, which is template-owned, shared with this repository and must not name a stack ([ADR 0003](0003-stack-agnostic-core-defines-contracts.md)); and it covers only the command shapes its pattern knows, while the config covers `npm test`, `npm run smoke` and `npx playwright test` alike. `CLAUDECODE` instead of `CLAUDE_CODE_CHILD_SESSION`: it is also set in the IDE's integrated terminal, where a person reads the output.
- **Publishing on GitHub Pages, as the kit does:** public even from a private repository, so every generated project would need the kit's redaction and no traces in CI; a project that wants it adds the `report` and `deploy` jobs itself. A Copier question for it: configuration no one asked for, and twice the paths to test.
- **The pinned Playwright image:** sturdier against the runner's apt mirror (kit#24), but it brings a tag-sync check with it, for a failure seen once in another repository.

## Consequences

- osv-scanner is pinned twice: the reusable workflow in `template/.github/workflows/ci.yml.jinja` and the binary in `tests/packs/test_ts_playwright.py`; bump both together (the test fails if the versions differ). It is one more pin for #75.
- `tests/packs/` downloads the scanner on every run and queries the OSV API: the template's CI fails when a pinned dependency of the pack gets an advisory, as a generated project's would.
- A generated project's report is downloaded from the run's artifacts, not browsed at a URL.
- The ignore and the sentinel live in project-owned files (`dependabot.yml`, `scripts/`); once TypeScript 7 is accepted, the project deletes both.
- `_exclude` patterns follow gitignore rules: a bare `scripts` also matched the core's `.github/scripts`, so the pack's folder is excluded as `/scripts`.
