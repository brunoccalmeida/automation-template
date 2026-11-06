# 2. One repository: a shared core plus packs split by tool

- **Status:** Accepted
- **Date:** 2026-11-06

## Context

Future projects will differ in stack (TypeScript or Python, possibly .NET), in target (web, API, desktop, mobile) and in test type. The template must serve them without forcing one project's choices onto another, and without bringing back the drift that [ADR 0001](0001-use-copier.md) exists to remove.

Options considered:

| | A. One generic template | B. One template per test type | C. Core plus packs |
| --- | --- | --- | --- |
| Shape | One file set with conditionals for every stack and target | Separate repositories: web, API, desktop | One repository: the core is always rendered, packs are rendered by answer |
| Drift | None | Returns: the shared part is copied into every template | None: the shared part exists once |
| Readability | Files full of `if web / if desktop` branches | Each template is simple | Each pack is simple and isolated |
| Testing | Combinations explode | Simple, multiplied by the number of templates | CI renders one project per pack |

Template platforms converge on C. Backstage calls such starting points *golden paths*, and generators such as Nx and Yeoman compose small generators instead of duplicating large ones: composition over duplication.

The shared part, the harness, is the most valuable part of the template. Option B makes sense when variants share almost nothing or are owned by different teams; neither holds here.

## Decision

**One repository with a core and packs (option C). A pack is defined by its tool, not by its test type.**

- The **core** holds everything that does not depend on a stack: rules, skills, the reviewer agent, document templates, CI gate, ruleset, labels.
- A **pack** holds one tool chain: `ts-playwright` (from playwright-qa-starter-kit) and `python-behave-selenium` (from uat-automation-framework).
- **Test types are options inside a pack.** playwright-qa-starter-kit tests web and API in one project with one tool, sharing config, CI and report, as real projects usually do. Splitting packs by test type would force a choice that projects do not make.
- A new pack is created only when a real project needs a different tool chain (for example, a desktop project with FlaUI or Appium). No pack is written ahead of a project that proves it (rule of three).

## Consequences

- A generated project contains only the core and the chosen pack: it reads as if written for its target, with no configuration for stacks it does not use.
- Each pack ships a **walking skeleton** only: infrastructure (runner config, lint, type check, CI, report), conventions as documented empty folders, and one smoke test. No domain abstractions (base page, page objects, API clients, test data, authentication): they depend on the application and would be guessed before the problem is known.
- What enters the core or a pack is decided by evidence from the two source projects ([INVENTORY.md](../INVENTORY.md)), conservatively: with only two projects, anything in doubt stays out and moves up when a third project repeats it.
- The template's CI renders at least one project per pack and runs its checks.
