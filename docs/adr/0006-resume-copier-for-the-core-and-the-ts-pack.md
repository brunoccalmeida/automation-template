# 6. Resume Copier for the core and the `ts-playwright` pack

- **Status:** Accepted
- **Date:** 2026-11-25
- **Supersedes in part:** [ADR 0004](0004-partial-resumption-with-a-plugin.md) ("Copier stays paused"), for the core and the `ts-playwright` pack

## Context

The template was paused on 2026-11-06 for two reasons ([session summary, Pause](../PROJECT_SESSION_SUMMARY.md#pause)):

1. **Rule of three.** Two source projects could not tell what is common from what is coincidence, and two divergences had no tie-breaker: line endings and retries in CI ([INVENTORY.md §8](../INVENTORY.md#8-decisions-left-to-the-phases-mission)).
2. **Priority.** The cost of having no template, porting improvements by hand, was judged "low and linear".

ADR 0004 resumed only the plugin on 2026-11-17 and kept Copier paused for the same reasons. A survey of the local projects on 2026-11-25 ([INVENTORY.md, fourth and fifth sources](../INVENTORY.md#fourth-and-fifth-sources-2026-11-25)) found:

- **The harness is in four repositories, and a fifth started today.** The kit, the UAT, the nextjs project and doc-intake-pipeline (a Python pipeline with an LLM, not a test automation project) all use the `mission` plugin, a `ci-passed` gate, zizmor, Dependabot with `cooldown`, `persist-credentials: false` and a `deny` list in `.claude/settings.json`. supabase-app-hardening was set up by hand on 2026-11-25.
- **The divergences of §8 have an answer.** All four store LF in the repository, and three use `* text=auto eol=lf` (the UAT keeps `* text=auto`). The kit and the UAT now share the same flaky policy: a retry only diagnoses, and a flake fails the run.
- **The hand-made copies keep drifting.** The rules live in `.github/copilot-instructions.md` in two projects and `AGENTS.md` in the other two; none has adopted [`core.md`](../../.claude/rules/core.md) (#45). supabase-app-hardening wrote its own pt-BR version of the rules instead of copying `core.md`, and its plan copies `ci.yml`, `dependabot.yml` and `KNOWN_ISSUES` from the nextjs project by hand.

## Decision

**Resume Copier for the core (Missions 1 to 4, #2 to #6) and the `ts-playwright` pack (#7). Keep the `python-behave-selenium` pack (#8) paused.**

1. **The core passes the rule of three** with four sources, two languages, and projects outside test automation. That last point is also evidence for [ADR 0003](0003-stack-agnostic-core-defines-contracts.md): what the four share names no stack.
2. **The `ts-playwright` pack has two sources (kit, nextjs) and a third planned** (supabase-app-hardening, Playwright test runner). It comes after Missions 1 to 4, so the third source has time to exist. If it still has no Playwright suite in Git when #7 starts, #7 checks the rule of three again before extracting anything.
3. **The `python-behave-selenium` pack has one source** (the UAT); doc-intake-pipeline is Python but uses neither Behave nor Selenium. #8 resumes when a second Behave/Selenium project exists. Mission 6 was also meant to prove the core is stack-agnostic; until #8 resumes, a generated project for a second stack has to come from somewhere else, decided in Mission 1 (#2) when the template's CI picks what it generates.
4. **The priority reason is revised, not dropped.** The cost of copying by hand is not linear: it is (changes to the core) × (projects), and the number of projects doubled since the pause. Each new project copies the harness on its first day, which is where drift starts (judgment, from the evidence above).

## Alternatives

- **Keep the pause and copy `core.md` by hand.** It solves the rules file only; CI, Dependabot, `.gitattributes`, the flaky policy and the templates would still be copied one project at a time, and supabase-app-hardening shows a new project does not copy even `core.md`.
- **Resume everything, including #8.** It would extract a Python pack from a single source, which is the premature abstraction the pause was meant to avoid.

## Consequences

- #2 loses the `blocked` label and becomes the next mission; #8 gets `blocked`.
- [INVENTORY.md](../INVENTORY.md) counts four sources for the core; the per-piece tables are reviewed against them in the mission that extracts each piece, not all at once.
- The decisions left in INVENTORY §8 are still made in Mission 2a (#3), with sources, but now with four projects of evidence.
- The pending propagation work in the other projects (plugin update, `core.md` copy, kit#52) stays as it is: a copied `core.md` is the same file Copier will render.
- The template now serves projects outside test automation. How the README presents it is left to Mission 7 (#9).
