# 17. The pinned CI tools live outside `.github/`

- **Status:** Accepted
- **Date:** 2026-11-27
- **Supersedes in part:** [ADR 0016](0016-dependabot-for-the-pinned-ci-tools.md) (the `/.github/tools/` directories of its Dependabot entries) and the location named in [ADR 0007](0007-test-the-template-by-generating-the-core.md), item 5

## Context

The first Dependabot run after #75's merge bumped the Claude Code CLI from 2.1.326 to 2.1.329 in `/.github/tools/claude-cli`, and then GitHub refused to open the pull request: `POST /update_jobs/<id>/create_pull_request` answered `400 "The request contains invalid or unauthorized changes"`, which the updater records as `dependency_file_not_supported` (#82). The `uv` entry for `/.github/tools/copier` ran green only because Copier had nothing to bump.

Facts (read 2026-11-27):

- **The error label is generic.** dependabot-core maps that exact server message to `Dependabot::DependencyFileNotSupported` (`updater/lib/dependabot/api_client.rb` in [dependabot-core](https://github.com/dependabot/dependabot-core/blob/main/updater/lib/dependabot/api_client.rb)). The check that rejects the change runs on GitHub's side and is not in the open-source code.
- **Changes under `.github/` are refused outside `github-actions`.** [dependabot-core#15721](https://github.com/dependabot/dependabot-core/issues/15721) reports the same 400 for an npm entry at `/.github/semantic-release`. A commenter relays GitHub Support: this is intended behavior; under `.github/` only a few ecosystems, mainly `github-actions`, are accepted; no permission or `dependabot.yml` option changes it. [dependabot-core#15237](https://github.com/dependabot/dependabot-core/issues/15237) reports the same error for other ecosystems under `/.github/actions/`. The fix reported in both is to move the manifest out of `.github/`. GitHub's documentation does not state the rule ([Dependabot errors](https://docs.github.com/en/code-security/reference/supply-chain-security/troubleshoot-dependabot/dependabot-errors) has nothing on it). The Support statement is secondhand, and one commenter says their `.github/` setup started working again.

## Decision

1. **The pinned CI tools move to `tools/`** at the root: `tools/claude-cli` and `tools/copier`, with the Dependabot entries, CI, the contracts and the tests pointing there. Copier renders from `template/` (`_subdirectory`), so `tools/` stays out of the generated project, as `.github/tools/` did; a test checks it.
2. **A test enforces the rule:** `tests/test_ci_tools.py` fails for a Dependabot entry outside `github-actions` whose directory is under `/.github`.

## Alternatives

- **Wait for GitHub to relax the check:** the Support answer calls it intended, and the pin would keep drifting meanwhile.
- **Move only the CLI:** Copier's entry would hit the same refusal on its first real bump.
- **Bump the tools by hand again:** this is what ADR 0016 replaced.

## Consequences

- The fix is proved by the first Dependabot run after the merge: Dependabot reads `dependabot.yml` from the default branch only (ADR 0016). Its CLI pull request is then expected to fail `tests/test_ci_tools.py` until `allowScripts` is approved.
- The procedures of ADR 0016 stay; only the path changes (`npm install-scripts approve` runs in `tools/claude-cli`).
