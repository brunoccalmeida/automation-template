# 16. Dependabot for the pinned CI tools

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

This repository's `dependabot.yml` covered `github-actions` only ([ADR 0012](0012-github-files-rendered-by-the-core.md)). Every other pin was bumped by hand, and a pin nobody bumps drifts behind its security fixes (#75). The pins: Copier, hash-locked in `.github/tools/copier/requirements.txt` ([ADR 0007](0007-test-the-template-by-generating-the-core.md)); the Claude Code CLI in `.github/tools/claude-cli/`, whose `postinstall` is approved for one version in `allowScripts` (#18); the pack's npm dependencies in `template/package.json.jinja` and `template/package-lock.json.jinja` ([ADR 0014](0014-ts-playwright-pack-walking-skeleton.md)); the action pins in `template/.github/workflows/*.yml.jinja`, osv-scanner's reusable workflow among them, and the osv-scanner binary in `tests/packs/` ([ADR 0015](0015-ts-playwright-pack-hardening.md)); gitleaks and zizmor's `version` in `core-checks.yml`; and the `.node-version` files.

Facts that shaped the decision (read 2026-11-26):

- **uv.** Dependabot's `uv` ecosystem is supported on GitHub.com and `cooldown` applies to it, as to `npm` and `github-actions`; cooldown never applies to security updates ([Dependabot options reference](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)). The documentation only says that the pip ecosystems support "updates to any `.txt` file" ([Supported ecosystems](https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories)) and says nothing about hashes. The implementation does: the `uv` updater reruns `uv pip compile` with options read from the compiled file, `--generate-hashes` when it has `--hash=sha`, `--universal` and `--python-version`, and updates the `.in` file (`uv/lib/dependabot/uv/file_updater/compile_file_updater.rb` in [dependabot-core](https://github.com/dependabot/dependabot-core)). The `pip` ecosystem compiles with pip-tools instead, a different resolver from the one that wrote the file.
- **`allowScripts`.** npm's `npm install-scripts approve` "writes pinned entries (`pkg@1.2.3`), which keep their approval narrowed to the specific version you reviewed"; npm 12 "silently skip[s] lifecycle scripts for any dependency that does not have a matching entry" ([npm install-scripts, v12](https://docs.npmjs.com/cli/v12/commands/npm-install-scripts)). Seen with npm 11.20.0 on Node 26.13.1, CI's Node: an entry naming 2.1.325 with 2.1.326 locked only warns ("1 package has install scripts not yet covered by allowScripts") and runs the script; with the script skipped (`npm ci --ignore-scripts`), `claude --version` exits 1 with "claude native binary not installed". dependabot-core has no reference to `allowScripts` (code search, 0 results), so a bump leaves the approval on the old version.
- **Template files.** For npm the documentation names `package.json` and the lock files; for `github-actions` with `directory: "/"`, Dependabot reads `/.github/workflows` and a root `action.yml` (options reference). No support is documented for a `.jinja` manifest or for a workflow outside `.github/workflows`, nor for version strings in arbitrary files, the kind of custom manager Renovate has.

## Decision

1. **Copier gets a `uv` entry** for `/.github/tools/copier`, weekly, with the core's 7-day cooldown.
2. **The CLI gets an `npm` entry** for `/.github/tools/claude-cli`, with the same cooldown, and `allowScripts` stays pinned to one version. `tests/test_ci_tools.py` fails while the `allowScripts` entry differs from the locked version, so Dependabot's pull request stays red until someone reviews the new version's `postinstall` and approves it; the test's message has the command.
3. **A pinned tool needs an entry.** The same test fails for a directory under `.github/tools/` with no Dependabot entry.
4. **The rest stays manual**, bumped with the change that needs it: the pack's lockfile and the template's action pins, osv-scanner included (Dependabot does not read `.jinja` files, and the generated project's own Dependabot bumps them after generation, [ADR 0012](0012-github-files-rendered-by-the-core.md)); the osv-scanner binary, gitleaks and zizmor's `version` (version strings in a test or a workflow, which no ecosystem reads); and the `.node-version` files.

## Alternatives

- **The `pip` ecosystem for Copier:** it also regenerates hashes, but it compiles with pip-tools, while the file's header and ADR 0007 name `uv pip compile`.
- **A name-only `allowScripts` entry (`"@anthropic-ai/claude-code": true`):** Dependabot's pull request would go green on its own, but a new version's `postinstall` would run in CI unreviewed, which the pinned entry exists to prevent (#18).
- **The CLI stays manual:** no red pull request to finish by hand, but the pin falls behind until someone remembers it.
- **A test that keeps the template's action pins equal to the root workflows', which Dependabot bumps:** it would catch drift for the actions both use; left out because nothing has drifted yet and the generated project bumps its own copies.

## Consequences

- Each CLI bump takes one commit by hand on Dependabot's branch: `npm install-scripts approve @anthropic-ai/claude-code` in `.github/tools/claude-cli`, after reading the release.
- Dependabot reads `dependabot.yml` from the default branch only, so the two entries are first proved by the first Dependabot run after the merge (the repository's Dependabot jobs), not in this pull request.
- A generated project starts with the template's pins as of its release, and its own Dependabot proposes the newer ones within the first week past the cooldown.
- A new tool under `.github/tools/` comes with a Dependabot entry, or the test fails.
