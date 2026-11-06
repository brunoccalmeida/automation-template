# 1. Distribute the template with Copier

- **Status:** Accepted
- **Date:** 2026-11-06

## Context

Two projects, [uat-automation-framework](https://github.com/brunoccalmeida/uat-automation-framework) and [playwright-qa-starter-kit](https://github.com/brunoccalmeida/playwright-qa-starter-kit), carry the same AI-assisted delivery harness: always-loaded rules, a Definition of Done skill, a merge skill, a read-only reviewer agent, a session summary and a CI gate. The second project copied it from the first by hand, and the copies have already drifted apart (see [INVENTORY.md](../INVENTORY.md)): each project improved pieces the other never received.

Creating a project from a template is the easy part. The hard part is the second day: when the template improves, every project created from it should be able to receive the improvement without someone remembering to copy it.

Options considered:

| Option | Creates a project | Asks questions (stack, names) | Brings later template changes into existing projects |
| --- | --- | --- | --- |
| GitHub template repository | Yes, one copy | No | No: the new repository keeps no link to the template |
| Claude Code plugin | Only skills, agents, hooks and commands | No | Yes, but only for what the plugin carries: not `CLAUDE.md`, Copilot instructions, CI workflows, Dependabot or project config |
| [Copier](https://copier.readthedocs.io/) | Yes | Yes, and renders only the files that match the answers | Yes, with `copier update` |

## Decision

Use **Copier**.

`copier update` regenerates a fresh project from the template version the project was created from, computes the diff between that and the project (the project's own changes), applies the new template version and reapplies the project's diff on top of it ([Updating a project](https://copier.readthedocs.io/en/stable/updating/)). This is a three-way merge: changes made by the template and changes made by the project are told apart, and only real overlaps become conflicts, as in `git merge`.

A Claude Code plugin is not rejected, only deferred (YAGNI): if skills ever change often enough that running `copier update` becomes a burden, they can move to a plugin that complements Copier.

## Consequences

- The template must be versioned with **Git tags**: `copier update` checks out the latest tag by default.
- A generated project keeps a `.copier-answers.yml` file. It is never edited by hand: the Copier documentation calls manual edits "an unsupported way to update". Answers change through `copier update` itself.
- Template files use Jinja (`{{ variable }}`), so the template cannot run as it is: it must be **rendered to be tested**. The template therefore needs its own CI that generates a project and validates it (Mission 1, the template's walking skeleton).
- Updates conflict when a project edits a file the template owns. Files are split by owner: the template owns its files, and a project adds its own next to them (for example, project rules imported by `CLAUDE.md` next to the core rules) instead of editing the template's copy.
- Conflicts surface as inline markers by default; generated projects need a check that refuses committed conflict markers.
- Copier is a Python tool, needed only by whoever creates or updates a project, not by the generated project at run time.
