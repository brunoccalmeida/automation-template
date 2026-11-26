# 11. CI enforcement in the core: a reusable workflow with encoding, secret scan and workflow audit

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

Mission 3b (#71) is the CI side of the enforcement split from #5 ([ADR 0010](0010-claude-code-enforcement-in-the-core.md)). It asks for:

- a UTF-8 encoding check;
- gitleaks;
- zizmor;
- actions pinned by full commit SHA.

It also asks whether zizmor's `unpinned-uses` can replace a dedicated test. Each check has to be seen blocking a probe, run as a job in the `needs` of the gate, and ship to the generated project where it names no stack ([ADR 0003](0003-stack-agnostic-core-defines-contracts.md)).

Evidence: the kit, the UAT and doc-intake-pipeline carry the same two jobs.

- **`secret-scan`** runs the gitleaks binary, pinned by version and SHA-256, with `--log-opts=HEAD --redact`.
- **`workflow-audit`** runs `zizmor-action` with `advanced-security: false` and a pinned `version`.

Only the UAT checks encoding (`scripts/check_text_encoding.py`, run by pre-commit) and SHA pinning (`test_workflow_pinning.py`). See the [inventory](../INVENTORY.md).

Facts, from the official documentation (read 2026-11-26) and from probes with zizmor 1.32.0 and gitleaks 8.30.1:

- **Pinning.** zizmor's `unpinned-uses` "applies a blanket hash-pinning policy: all actions must be pinned by SHA reference". An unmatched `uses:` gets the implicit `"*": hash-pin` rule, and since 1.20.0 first-party `actions/*` are included ([zizmor audits](https://docs.zizmor.sh/audits/#unpinned-uses)). Probe: `actions/checkout@v7` and `zizmorcore/zizmor-action@v0.8.1` each gave `error[unpinned-uses]`, and zizmor exited 14.
- **Self-repository syntax.** `$/` "resolves to your workflow's own repository at the exact commit that is running", needs no checkout, and works in reusable workflow calls. It is not available on GitHub Enterprise Server ([GitHub changelog, 2026-07-30](https://github.blog/changelog/2026-07-30-reference-same-repository-actions-with-self-repository-syntax/); [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)). zizmor's `self-repository` audit (since 1.30.0) flags a `./` call. The probe gave a `help[self-repository]` finding on `uses: ./.github/workflows/core-checks.yml`.
- **gitleaks-action licence.** Repositories of an organization "will need to obtain a free license key" ([gitleaks-action README](https://github.com/gitleaks/gitleaks-action)), while the scanner itself needs none. Probe: a token committed and then deleted in the next commit was found (`github-pat`, redacted), exit 1.
- **Why the encoding check exists.** Git classifies a file holding NUL bytes as binary (`git ls-files --eol` prints `i/-text`). UTF-16 always has NUL bytes for ASCII text, so a UTF-16 `.gitignore` is stored as binary and silently matches nothing (uat#26).

## Decision

1. **One reusable workflow, template-owned and shared:** `.github/workflows/core-checks.yml` (`on: workflow_call`), with three jobs: `text-encoding`, `secret-scan` and `workflow-audit`. This repository calls it as one job (`core-checks`, `uses: $/...`) in the `needs` of `ci-passed`. The called workflow's result is the result of all of its jobs. The calling workflow belongs to the project, which adds its own jobs there, and `copier update` keeps the reusable workflow current. That keeps template-owned and project-owned files apart.
2. **No pinning test of our own.** `unpinned-uses` under its default policy already rejects every action not pinned by SHA, so a dedicated test would duplicate it (DRY).
3. **The encoding check is a POSIX `sh` script** (`.github/scripts/check-text-encoding.sh`, shared), not the UAT's Python. The core names no stack, and `sh`, `git`, `iconv` and `od` exist on the runner and in Git Bash, the same precedent as the `SessionStart` hook. It checks only tracked files and uses Git's own split:
   - a file Git sees as text must decode as UTF-8;
   - a file Git sees as binary must not open with a UTF-16 byte order mark.
4. **Same pins as the source projects:** zizmor-action v0.8.1 with zizmor 1.32.0, and gitleaks 8.30.1. zizmor-action v0.9.2 (zizmor 1.33.1) came out 2026-11-23, inside the 7-day cooldown the source projects give Dependabot. It goes in through Dependabot once Mission 4 (#6) brings the core's Dependabot configuration (*judgment call*).
5. **The generated project gets the workflow and the script, but no caller yet.** The caller is a project-owned CI workflow with the gate job, whose name is the `gate` answer that the ruleset requires. It comes with the ruleset in Mission 4 (#6), so both name the same check. Until then a project generated from the core alone carries the checks, and nothing runs them.

## Alternatives

- **A template-owned `ci.yml` with the gate.** Each project would add its own jobs to a template-owned file, and `copier update` would conflict on it.
- **The encoding check in Python, as in the UAT.** It would make Python a requirement of the core in every project, and the stack-term test would reject it.
- **Require every binary file to be declared in `.gitattributes`.** That would close the gap below, but `.gitattributes` is template-owned, so every project with images would have to edit it.
- **Keep `./` and ignore `self-repository` inline.** `$/` is the syntax GitHub recommends for same-repository references, and it does not depend on a checkout.

## Consequences

- Known gap: UTF-16 without a byte order mark passes as binary. Windows PowerShell 5.1 writes the mark, which is the case seen in uat#26.
- [`tests/test_check_text_encoding.py`](../../tests/test_check_text_encoding.py) runs the script on throwaway repositories, and each of its branches was seen failing by mutation. gitleaks and zizmor were seen blocking the probes above. In CI, a probe commit on the pull request shows the three jobs failing `ci-passed`, and its revert shows them passing.
- `$/` does not work on GitHub Enterprise Server. A project hosted there calls the workflow with `./` and an inline `# zizmor: ignore[self-repository]` naming the reason.
- The gitleaks and zizmor versions are bumped by hand. Dependabot bumps the action, not its `version` input or the gitleaks release.
