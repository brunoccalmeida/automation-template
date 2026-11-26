# 8. Core rules and documents in the generated project: ownership, line endings and retries

- **Status:** Accepted
- **Date:** 2026-11-25

## Context

Mission 2a (#3) puts the core rules and the document templates into [`template/`](../../template/). Three questions had to be answered for that, two of them left open in [INVENTORY §8](../INVENTORY.md#8-decisions-left-to-the-phases-mission):

- **Who owns each file.** The architecture rule says the project adds its own files instead of editing the template's, so `copier update` does not conflict (`CLAUDE.md`). But some of the files the core ships exist to be filled in by the project: its README, `CLAUDE.md`, session summary, known issues and ADR index.
- **Line endings.** The kit, nextjs and doc-intake use `* text=auto eol=lf`; the UAT uses `* text=auto`, which leaves line endings on disk to each machine.
- **Retries in CI.** The kit retries and fails the run on a pass-on-retry (`failOnFlakyTests`); the UAT forbids retries. Both policies say the instability must stay visible and tracked.

Facts behind the decision:

- Copier copies a file without the `.jinja` suffix as it is; `_skip_if_exists` lists "files/folders that must be skipped only if they already exist, but always be present", in gitignore-style patterns, and recreates them on `update` only when they are missing ([Configuring a template](https://copier.readthedocs.io/en/stable/configuring/)). `copier update` reapplies the project's diff on the new template version and leaves conflict markers where they clash ([Updating a project](https://copier.readthedocs.io/en/stable/updating/)).
- With `text` set, Git normalises line endings to LF in the index; `eol=lf` "uses the same line endings in the working directory as in the index when the file is checked out", and `core.autocrlf` or `core.eol` decide only "if the `eol` attribute is unspecified for a file". With `text=auto`, Git converts only what it detects as text ([gitattributes](https://git-scm.com/docs/gitattributes)).
- Claude Code loads `CLAUDE.md` and every `.claude/rules/` file without `paths:` at launch, loads a path-scoped rule when it reads or edits a matching file, and targets "under 200 lines per CLAUDE.md file" ([Memory](https://code.claude.com/docs/en/memory.md)).
- Fowler: non-deterministic tests make a team ignore red builds, and quarantine needs a numeric or time limit ([Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)).

## Decision

1. **Two kinds of file in `template/`.** The project-owned ones (`README.md`, `CLAUDE.md`, `docs/PROJECT_SESSION_SUMMARY.md`, `docs/KNOWN_ISSUES.md`, `docs/adr/README.md`) are in `_skip_if_exists`: rendered on the first copy, never overwritten after that. Every other file is template-owned (`.claude/rules/core.md`, `.claude/rules/agent-rules.md`, the flaky policy, the ADR and spike templates, `docs/ai-workflow/`) and is changed in the template only; `copier update` keeps it current.
2. **`core.md` has one source.** The template ships the same file this repository loads, and a test fails if the two differ. Mission 2b (#4) decides whether this repository then generates it instead.
3. **`* text=auto eol=lf` in the core.** The same bytes on every OS make a diff across clones meaningful, and LF-only formatters pass after a fresh checkout on Windows. The UAT's objection (LF forced on the Windows disk) costs nothing with current editors (*judgment call*), and a project that needs CRLF for a file type can add a more specific pattern.
4. **Retries: the core sets the invariant, the pack sets the mechanism.** "A retry never passes a build": a test that needed more than one attempt fails the run. A pack meets it either with no automatic retries, or with retries only when the runner reports a pass on retry as its own outcome and the run fails on it. Each pack enforces its choice with a check that was seen failing.
5. **The core names no stack and no target type**, so the flaky policy and the known-issues file speak of "the runner's expected-failure mechanism" and "the part of the application", and the pack documents its markers and evidence.

## Alternatives

- **Everything template-owned, with project text in separate files** (for example, the contracts in a file `CLAUDE.md` imports): keeps `copier update` free of conflicts, but `CLAUDE.md` is where Claude Code and every project expect project rules, and an import saves no context.
- **Everything updated by Copier, conflicts resolved by hand:** each template change to a file every project fills in would become a conflict in every project.
- **No line-ending policy in the core:** leaves the divergence the inventory found, with no tie-breaker.
- **One retry mechanism for every stack:** forbidding retries throws away the evidence a runner with a "flaky" outcome gives; allowing them everywhere lets a runner that reports a pass on retry as a plain pass hide flakes.

## Consequences

- A project changes `core.md`, `agent-rules.md` or a template-owned document through the template, never in place; `agent-rules.md` says so where it applies.
- A template change to a project-owned file reaches only new projects. A change existing projects need goes in a template-owned file or in the release notes.
- The contracts in the generated `CLAUDE.md` read "Not set" until Mission 2b (#4) turns them into Copier variables.
- The Google Testing Blog post the source policies cite for the definition of a flaky test could not be read (the page returned no body), so the core policy cites Fowler only.
