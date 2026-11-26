# 7. Test the template by generating the core, with a hash-locked Copier

- **Status:** Accepted
- **Date:** 2026-11-25

## Context

[ADR 0001](0001-use-copier.md) says the template cannot run on its own, so it is tested by rendering it. [ADR 0006](0006-resume-copier-for-the-core-and-the-ts-pack.md) (decision, item 3) left one question to Mission 1 (#2): while the `python-behave-selenium` pack (#8) is paused, what does the template's CI generate, given that Mission 6 was also meant to prove the core is stack-agnostic? When Mission 1 started there was no pack at all.

Facts behind the decision, from Copier's documentation for 9.19.1:

- `copier copy` renders the latest Git tag unless `--vcs-ref` is given; `--vcs-ref=HEAD` renders the checked-out revision, uncommitted changes included ([Generating a project](https://copier.readthedocs.io/en/stable/generating/)).
- `_subdirectory` sets the folder that is the template root ([Configuring a template](https://copier.readthedocs.io/en/stable/configuring/)).
- `copier update` needs a valid `.copier-answers.yml` in the project ([Updating a project](https://copier.readthedocs.io/en/stable/updating/)), which Copier writes only if the template has `{{ _copier_conf.answers_file }}.jinja` (Configuring a template).
- The documentation has no guidance on testing a template; the tools for it (pytest-copie, copier-template-tester) are third-party.
- pip's hash-checking mode (`--require-hashes`) requires a pinned hash for every requirement, transitive ones included, and pip recommends it together with `--only-binary :all:` ([Secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/)).

## Decision

1. **The template's CI generates the core only, with no pack,** until a pack exists. Generating a project for a second stack from an invented pack would be an abstraction with no source (rule of three). Until #8 resumes, the evidence that the core names no stack comes from the "no stack term in the core" test planned in Mission 2b (#4), not from a second generated project.
2. **The template lives in [`template/`](../../template/)** (`_subdirectory`), so the plugin, docs and CI of this repository never reach a generated project.
3. **The template renders the answers file from its first version,** because `copier update` is the reason Copier was chosen (ADR 0001).
4. **The test is a `unittest` module in `tests/`** that runs `copier copy --vcs-ref=HEAD` into a temporary directory and checks the result. It is part of the `test` contract, so it runs the same way on a developer's machine and in CI, and it needs no third-party test library.
5. **Copier is installed from a hash-locked requirements file** ([`.github/tools/copier/`](../../.github/tools/copier/)), generated with `uv pip compile --universal --generate-hashes` and installed with `pip install --require-hashes --only-binary :all:`. This follows the pinned Claude Code CLI in `.github/tools/claude-cli/`: the version and every dependency are fixed by hash.

## Alternatives

- **A minimal fake pack** to generate a second stack now: rejected, because a pack with no source project is the premature abstraction the rule of three forbids.
- **Shell steps in the workflow** (`copier copy`, then `test -f`): simpler, but they run only in CI and repeat the `test` contract.
- **`uv tool install copier==9.19.1`:** the method Copier documents, but it pins only Copier, so its dependencies can change between runs.
- **pytest-copie:** adds pytest and a third-party plugin for a test that the standard library already covers.

## Consequences

- The `test` contract needs `copier` on the `PATH` and fails, never skips, without it (`CLAUDE.md`, contracts).
- Updating Copier means changing `requirements.in` and regenerating `requirements.txt` with the command in its header. Whether Dependabot can update a hash-locked file is not confirmed by its documentation; Mission 4 (#6), which brings Dependabot, decides that.
- The lock was proven on two platforms: Windows (local install) and Linux (CI). The documentation does not say that a universal lock's hashes cover every platform's wheels.
- Each later mission that adds a file to `template/` adds the test that checks it in the generated project.
