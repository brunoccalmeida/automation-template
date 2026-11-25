# Session summary

Project state between chats. Read at the start of each mission (see `.claude/rules/core.md`, mission cycle). Detailed history lives in Git: each mission's record (decisions, sources, how the RED was seen, findings) goes in the **pull request body**, which the squash writes to `main`; lasting decisions go to `docs/adr/`. This file keeps only the **state** and the **next mission** ([ADR 0004](adr/0004-partial-resumption-with-a-plugin.md), item 8). The "Mission 0" section below predates that rule and stays as history.

## Current state

| Item | State |
| --- | --- |
| Situation | **Partial resumption: plugin** (2026-11-17, [ADR 0004](adr/0004-partial-resumption-with-a-plugin.md)). Copier stays paused ([Pause](#pause)). **Plugin queue done:** A (#14), B (#15, kit), A.1 (#19, #20, #21), C1 (#22, nextjs), C2 (#23, UAT) and D (#17, this repository) |
| Delivered | Marketplace `brunoccalmeida-plugins` with the [`mission`](../plugins/mission/README.md) plugin: `/mission:close-mission`, `/mission:ship-pr`, `mission:reviewer` and the guard that only lets `ship-pr` run as the first message of a fresh chat (`UserPromptExpansion` hook, #30), the outdated-plugin warning at session start (`SessionStart` hook, #32), the `mission:researcher` agent and model routing by measurement (#34: `reviewer` on `opus`/`high`, `researcher` on `sonnet`, `close-mission` on `inherit`, `ship-pr` on `opus`; `claude plugin eval` suite in [`plugins/mission/evals/`](../plugins/mission/evals/README.md)), the reviewer answer key (#38: false positives and negatives recorded in the PR, `reviewer-miss` label, `evals/review/` suite with an `opus`/`high` baseline; the reviewer now receives the commit messages), post-merge closing in `ship-pr` (#39: confirms the issues the PR closes, including in another repository, and ends the mission) and reloading after installing or updating from the shell (#25: README and version warning translate the CLI's "Restart to apply changes"), in use in all four projects, including this one (installed from GitHub, `autoUpdate: false`). Since #48 the skills, agents and hook messages are in English, measured with no loss against the Portuguese baselines (reviewer `opus`/`high` 12/12 and 5/6; researcher `sonnet` 1.000) |
| Rules | In layers (#45): user (`~/.claude/CLAUDE.md` and `language` in `settings.json`), core ([`.claude/rules/core.md`](../.claude/rules/core.md), the same in every project, not edited in the project) and project ([`CLAUDE.md`](../CLAUDE.md): contracts, exceptions to the core, rules for this repository only). The rules file shared with Copilot is gone (#26). Everything is in English (#46, #48) except the review eval fixtures and the graders that quote them (exception in `CLAUDE.md`) |
| Next mission | **[#40](https://github.com/brunoccalmeida/automation-template/issues/40)** (P2): measure the reviewer on cheaper arms against the English `opus`/`high` result recorded in the evals README by #48. The pending work in the other projects (row below) runs in a chat of each repository |
| Queue | Plugin (P2): #40 (measure the reviewer on a cheaper model), #35 (the same for `ship-pr`, under WSL2) and #51 (`reviewer-miss`: see eight hook tests fail on their own assertion). On Max, the two #48 suites ran at once in about 15% of a 5-hour window, so the limit no longer constrains the arms; Fable access is still unchecked · Rules (P2): #50 (evaluate whether TDD alone is current best practice or needs complementary principles) · #26 (Copilot and the plugin) closed as *not planned*: there is no plan to use Copilot; reopen if that changes · Copier: #2 to #11, paused |
| Pending in the kit | Update the plugin and delete the local rule that works around `DIRTY` (kit#52) |
| Pending in the projects | Update the plugin (`claude plugin update mission@brunoccalmeida-plugins`) in this repository, the kit, nextjs and the UAT to get the fresh-chat guard (#30), the version warning (#32), the researcher with model routing (#34), the reviewer miss capture (#38: create the `reviewer-miss` label in each project) the confirmation of closed issues in `ship-pr` (#39) and the English prompts and hook messages (#48); no contract change. After that, the warning itself points at the next gaps. Copy [`core.md`](../.claude/rules/core.md) unchanged to the kit, nextjs and the UAT and reduce each one's rules to the project layer (#45, one mission per repository); a `diff` against this file shows the divergence |
| Open PRs | none after the merge |
| Gates | `ci-passed`, the only check required by the "Protect main" ruleset ([`.github/rulesets/`](../.github/rulesets/protect-main.json), #28): aggregates `validate-plugins` (marketplace and each plugin; fails on an error or *warning*, except the omitted `version`) and `test-plugins` (tests of the plugin's hooks, `tests/`), and fails if a workflow job is missing from `needs` |
| CI tool | Claude Code CLI 2.1.326 pinned with a lockfile in `.github/tools/claude-cli/`; a version bump needs the `postinstall` approved again (`allowScripts` is tied to the version) |
| Decisions | [ADR 0001](adr/0001-use-copier.md) Copier · [ADR 0002](adr/0002-core-plus-packs-split-by-tool.md) core + packs by tool · [ADR 0003](adr/0003-stack-agnostic-core-defines-contracts.md) stack-agnostic core with contracts · [ADR 0004](adr/0004-partial-resumption-with-a-plugin.md) partial resumption with a plugin |
| Evidence | [INVENTORY.md](INVENTORY.md): pieces of the source projects classified (core / pack / app); nextjs as the third source and the comparison of the four versions of the plugin pieces |
| Pitfalls | `/mission:ship-pr` only runs as the first message of a fresh chat: `/clear` first (#30). The [`/memory` documentation](https://code.claude.com/docs/en/memory.md#view-and-edit-with-/memory) mentions "CLAUDE.md, CLAUDE.local.md, and other memory file locations", without naming `.claude/rules/`; to prove a rule loads, ask a `claude -p` to quote a passage of it from memory and repeat without the file, which should give "not loaded" (#45). A plugin change is closed by the published version; the branch's is tried with `claude --plugin-dir ./plugins/mission`, and after the merge, `claude plugin update mission@brunoccalmeida-plugins` (rules, Git). With `--plugin-dir`, the version warning (#32) stays silent on purpose: the directory has no SHA name; to see it, copy the plugin to a directory named after an old SHA. A plugin installed or updated from the shell only loads after `/reload-plugins` or a new session; that is what the "Restart to apply changes" of `claude plugin update` means (#25). A PR in another repository only closes an issue here with `Closes brunoccalmeida/automation-template#N` (#15 stayed open because of that). `test` needs `sh` and `git` on the `PATH` and fails without them instead of skipping (#39). To run the gate on Windows, pass the script the absolute path of `.github\tools\claude-cli\node_modules\.bin\claude.cmd`; if it fails with `UnicodeDecodeError`, `claude.exe` is missing (incomplete local install): run `npm ci --prefix .github/tools/claude-cli`. Evals (#34): the answer key comes from every page that covers the fact, not the first one; `--keep-temp` leaves one `claude-eval-*` per run in `%TEMP%`, to delete afterwards. `claude plugin eval` exits 0 even with no case loaded (check `casesTotal`) and `--case` accepts a single glob. The `review/` suite needs `--scaffold`; on the Pro plan, the 5-hour limit stopped the baseline after 6 reviews on `opus` (#38). A `research/` gold quoted from live documentation ages: a fact failing in every run means read the page again first (#48) |

## Mission plan

| Phase | # | Issue | Mission | Deliverable |
| --- | --- | --- | --- | --- |
| 0. Foundation | 0 | #1 | Foundation | Repository, 3 ADRs, inventory, this repository's minimal harness, issues |
| 1. Template skeleton | 1 | #2 | Walking skeleton | Minimal `copier.yml`, one generated file, CI that runs `copier copy` and validates the result, as a new job in the `needs` of `ci-passed` (gate and ruleset came in Mission D, #28). First test seen failing |
| 2. Stack-agnostic core | 2a | #3 | Rules and docs | Core rules, `CLAUDE.md`, path-scoped rules; templates: session summary, KNOWN_ISSUES, ADR, flaky policy, spike report |
| | 2b | #4 | Skills, reviewer and harness tests | `start-mission`, `close-mission`, `ship-pr` (native auto-merge), `reviewer` with extension points; commands as Copier variables; tests: line limit, identical Claude/Copilot copies, links, **no stack term in the core** |
| 3. Enforcement | 3 | #5 | Permissions, hooks and security | `allow`/`deny`, `SessionStart` hook, secrets hook, encoding check, gitleaks, zizmor |
| 4. GitHub | 4 | #6 | GitHub bootstrap | Labels, ruleset, merge config, issue/PR templates, core Dependabot, `/new-project` skill |
| 5. TS pack | 5 | #7 | `ts-playwright` pack | Walking skeleton with e2e/api options, extracted from the kit |
| 6. Python pack | 6 | #8 | `python-behave-selenium` pack | Walking skeleton extracted from the UAT; proves the core is stack-agnostic |
| 7. Release | 7 | #9 | v1.0 | Tag, portfolio README with a diagram and "how to use", Scorecard |
| 8. Backlog | 8a | #10 | Adopt in the kit | `copier` in playwright-qa-starter-kit + fixes the template does not cover |
| | 8b | #11 | Adopt in the UAT | The same in uat-automation-framework; proves `copier update` on a real project |
| Plugin | A | #14 | Harness plugin | Marketplace + `mission` plugin, project contract, validation gate in CI (done) |
| | B | #15 | Kit pilot | Contracts table, `REVIEW.md`, plugin in project scope, one real mission end to end (done, kit#51) |
| | A.1 | #19, #20, #21 | Pilot fixes | `DIRTY` by merge in `ship-pr`; install without the CLI on the PATH and explicit `autoUpdate` in the README (done) |
| | C1 | #22 | nextjs | The same in playwright-nextjs-e2e-ci (replaces half of #16) (done, nextjs#54) |
| | C2 | #23 | UAT | The same in the UAT; squash with the PR description, wait script, `pip-audit` (replaces half of #16) (done, UAT#181) |
| | D | #17 | Dogfooding | This repository uses its own plugin; `ci-passed` gate and ruleset (#28) taken from Mission 1 (done) |

Mission 2b (#4) shrinks: the skills and the reviewer already live in the plugin; Copier only renders the contracts table and the marketplace registration ([ADR 0004](adr/0004-partial-resumption-with-a-plugin.md), consequences).

Principle: each piece comes in with the mission that uses it (YAGNI), and each phase is born tested by the Phase 1 CI.

## Mission 0 (#1)

**Decisions** (conversations of 2026-11-06, recorded in the ADRs): Copier for `copier update` (3-way merge), not a *template repository* (copy with no link) nor a plugin (covers only what Claude Code reads); one repository with core + packs split by **tool**, not by test type; a stack-agnostic core that defines contracts (`check`, `test`, `smoke`, per-environment configuration) bound to the commands by Copier variables; pack skeleton as a walking skeleton, no domain abstraction. README, ADRs, issues and commits in English; internal rules and docs in pt-BR (translated to English in #46, except the plugin's skills, agents and hook messages, left to #48).

**Sources consulted:** Copier, [Updating a project](https://copier.readthedocs.io/en/stable/updating/) (regenerates the old version, computes the project's diff and reapplies it on the new one; requires tags in the template and a clean project; never edit `.copier-answers.yml` by hand); Nygard, *Documenting Architecture Decisions*; Twelve-Factor App, factor III.

**RED:** does not apply to this mission, which only delivers documentation; there is no gate to prove. The template's first test, seen failing, is an acceptance criterion of Mission 1.

**Inventory findings** (details in [INVENTORY.md](INVENTORY.md)):

- The kit is the best base for `ship-pr`, `close-mission`, `reviewer`, a `ci-passed` gate without a script, workflow hardening, Dependabot with `cooldown` and per-environment validated configuration; the UAT, for path-scoped rules, harness tests, output hook, SHA enforcement, a second vulnerability source and the encoding check.
- UAT test code: tests that repeat the code (a locator equal to itself) and page object unit tests that only check mock calls; they go to Mission 8b.
- Neither has a flaky policy, and they diverge (retry in the kit, no retry in the UAT); `.gitattributes` diverges too. Decide in Mission 2a.
- This repository has the third hand-made copy of the harness, only to work in missions until Phase 2, which should make it use its own core.

**Backlog in the source repositories** (opened with the user's confirmation): playwright-qa-starter-kit#15 and uat-automation-framework#134, linked to Missions 8a (#10) and 8b (#11).

## Pause

**Decision (2026-11-06):** the template is paused until the first paid automation job.

**Why:**

- **Rule of three.** The template is extracted from two projects, and the "evidence first" rule asks for three. The inventory already shows divergences with no tie-breaker (flaky policy, `.gitattributes`); the first client project is the third case that separates what is truly common from what is coincidence. Extracting earlier is premature abstraction.
- **Priority.** Portfolio and paid work come first: the client buys tests running in their CI, not the workflow. The cost of not having the template (porting improvements by hand between repositories) is low and linear; the template still has 10 missions.

**Consequences:**

- Reverses the earlier decision to fix the source projects only after the template: until the resumption, improvements go into them by hand.
- playwright-qa-starter-kit#15 and uat-automation-framework#134 get the `blocked` label.
- Nothing is lost: ADRs, [INVENTORY.md](INVENTORY.md) and issues #2 to #11 remain valid. On resumption, review the inventory with what the client project showed to be repeatable.

**Trigger to resume:** the first paid automation job completed (or a third project that needs the same harness).

**2026-11-17:** the second trigger fired (playwright-nextjs-e2e-ci). Only the plugin resumed ([ADR 0004](adr/0004-partial-resumption-with-a-plugin.md)); Copier stays paused for the same reasons.

## Recommended next mission

**[#40](https://github.com/brunoccalmeida/automation-template/issues/40)**, whose baseline is now the English `opus`/`high` result (#48), then [#35](https://github.com/brunoccalmeida/automation-template/issues/35); [#51](https://github.com/brunoccalmeida/automation-template/issues/51) and [#50](https://github.com/brunoccalmeida/automation-template/issues/50) are P2 too. On Max the usage limit is no longer a constraint for the arms (#48); check whether Fable runs before including it as an arm. The known defects of the clean cases in `evals/review/` remain valid, because they describe the historical diffs of #31 and #33, not `main`.

Outside this repository, the pending work in the projects (update the plugin, create the `reviewer-miss` label, kit#52, copy `core.md` and reduce the rules to the project layer) runs one mission per repository. Copier (#2 to #11) waits for the trigger of the [Pause](#pause) and of [ADR 0004](adr/0004-partial-resumption-with-a-plugin.md).
