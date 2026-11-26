# Inventory of the source projects

Mission 0 survey (2026-11-06): what exists in [uat-automation-framework](https://github.com/brunoccalmeida/uat-automation-framework) (**UAT**, Python/Behave/Selenium, 130+ PRs) and in [playwright-qa-starter-kit](https://github.com/brunoccalmeida/playwright-qa-starter-kit) (**kit**, Playwright/TS, Mission 3 in progress), which side does it better, and where each piece goes. It is the evidence behind every "in or out" decision in the template ([ADR 0002](adr/0002-core-plus-packs-split-by-tool.md)).

## How to read

**Category** (where the piece will live):

- **C — core contract:** the same intent in both projects and independent of the stack. Goes to the core, without naming a tool ([ADR 0003](adr/0003-stack-agnostic-core-defines-contracts.md)).
- **P — pack implementation:** same shape, stack-specific content. Goes to the pack, as a walking skeleton.
- **A — application-specific:** depends on Sauce Demo or Restful Booker. Stays out.

**Better:** which side serves as the base (UAT, kit, both combined, or none = gap). **Phase:** where it goes in the [plan](PROJECT_SESSION_SUMMARY.md#mission-plan).

Stance: with only two projects, **when in doubt, leave it out** (rule of three). It moves up into the template when a third project repeats the pattern.

**Third source (Mission A, 2026-11-17):** [playwright-nextjs-e2e-ci](https://github.com/brunoccalmeida/playwright-nextjs-e2e-ci) (**nextjs**, Playwright/TS over a frozen Next.js app) repeats the harness and fired the [partial resumption](adr/0004-partial-resumption-with-a-plugin.md). For now it counts only as a source for the plugin pieces ([§2](#mission-a-the-four-versions-of-the-plugin-pieces)); the per-piece tables keep the two original sources; since Copier resumed ([ADR 0006](adr/0006-resume-copier-for-the-core-and-the-ts-pack.md)), each extraction mission reviews its pieces against every source ([fourth and fifth sources](#fourth-and-fifth-sources-2026-11-25)).

## Fourth and fifth sources (2026-11-25)

Survey behind [ADR 0006](adr/0006-resume-copier-for-the-core-and-the-ts-pack.md), read from the local clones on 2026-11-25. It adds [doc-intake-pipeline](https://github.com/brunoccalmeida/doc-intake-pipeline) (**doc-intake**: Python/uv, a document extraction pipeline with an LLM; not a test automation project) and **supabase-app-hardening** (**supabase**: set up on 2026-11-25, plan and rules only, no Git yet). The per-piece tables below still compare the UAT and the kit; each extraction mission reviews its pieces against all sources.

| Piece | kit | UAT | nextjs | doc-intake | supabase |
| --- | --- | --- | --- | --- | --- |
| `mission` plugin in `.claude/settings.json` | Yes | Yes | Yes | Yes | Yes |
| Rules file imported by `CLAUDE.md` | `.github/copilot-instructions.md` | `AGENTS.md` | `.github/copilot-instructions.md` | `AGENTS.md` | `AGENTS.md`, in pt-BR, its own text |
| [`core.md`](../.claude/rules/core.md) adopted (#45) | No | No | No | No | No |
| `ci-passed` gate | Yes | Yes | Yes | Yes | Planned, copied from nextjs |
| zizmor in CI | Yes | Yes | Yes | Yes | Planned |
| Dependabot `cooldown` | Yes | Yes | Yes | Yes | Planned, copied from nextjs |
| `persist-credentials: false` | Yes | Yes | Yes | Yes | — |
| `deny` list in `.claude/settings.json` | Yes | Yes | Yes | Yes | Yes |
| `.gitattributes` | `* text=auto eol=lf` | `* text=auto` (LF in the repository, platform endings on disk) | `* text=auto eol=lf` | `* text=auto eol=lf` | — |
| Flaky policy | `docs/FLAKY_TESTS.md`: retries only diagnose, a flake fails the run | `docs/FLAKY_TESTS.md`: no retries, a re-run on the same SHA confirms | None | None | — |
| Known issue marking | `test.fail()` + `knownIssue()` + `KNOWN_ISSUES.md` | Asserts the defect (§6; Sauce Demo's defects are intentional) | `test.fail()` + `knownIssue()` + `KNOWN_ISSUES.md` (same as the kit) | — | `test.fail()` + `knownIssue()`, copied from nextjs |

What it shows: the §8 line-ending question has three of four projects on `eol=lf`; the §8 retry question is a difference of mechanism, since the kit and the UAT now state the same policy; and the copies still drift, because the core lives in two different files and no project carries `core.md`.

## 1. Always-loaded rules (`.github/copilot-instructions.md`, imported by `CLAUDE.md`)

| Section | UAT | kit | Better | Cat. | Phase |
| --- | --- | --- | --- | --- | --- |
| `CLAUDE.md` with `@import` | Identical (summary in `docs/ai-workflow/`) | Identical (summary in `docs/`) | Tie | C | 2a |
| Golden rule (RED) | "TDD" + Behave/pytest double loop | "Every test was seen failing", with two paths: test before the support code, or mutation; also applies to gates | **kit**: stack-agnostic and fits third-party SUTs | C (the double loop goes to the Python pack: P) | 2a / 6 |
| Always-on best practices | Has the extra rule "custom investigation only when the saving exceeds the cost; estimates are labeled" | Short version | **Combined** | C | 2a |
| Mission cycle | Same, and states that handoff never depends on the user | Same | Combined; the "chat start" steps move from the rule to the `start-mission` skill and the `SessionStart` hook | C | 2b / 3 |
| Token spend | More complete: web docs by section, fixed model per chat, measure before/after, `AGENT_TOKEN_SPEND.md` | Summary | **UAT** | C | 2a |
| Stack testing section | Double loop, unit/integration/E2E hierarchy | API/E2E hierarchy, isolation, locators, `test.fail` | Each in its own stack | P (isolation and known bug become policy: C) | 2a / 5 / 6 |
| Wait for the final state | Principle + table; has the extra rule "final state equal to the initial one: change the initial one before acting" | Principle + table | **UAT** for the principle; table rows per stack | C (CI/GitHub rows) + P (tool rows) | 2a |
| Diagnosing errors | With a concrete example | With the Playwright tools | Tie | C + examples in the pack | 2a |
| Communication | "Always pt-BR; code in English" | More precise: commits and README in English | **kit** | C | 2a |
| Dependencies | Poetry; **two vulnerability sources** (Dependabot + `pip-audit`) | Exact npm; `overrides` instead of `audit fix --force`; check *peer dependencies* | Combined: principles in the core (committed lock, exact version, major = human decision, two sources), commands in the pack | C + P | 2a |
| Git and PR | Explains **why** one open PR at a time (up-to-date branch required) | Shorter | **UAT** | C | 2a |
| Principles (Zen) | Identical | Identical | Tie | C | 2a |
| Path-scoped rules (`.claude/rules/` = `.github/instructions/`) | Yes: Python, Selenium, workflows, Poetry | **Missing** | **UAT** | Mechanism C; content P, except `workflows.md` (C, minus the `pip-audit` line) | 2a |

**Mission 2a (#3):** the template ships [`core.md`](../.claude/rules/core.md) as #45 merged it, plus a path-scoped `agent-rules.md`. The C rows of this table that #45 left out without a record, and where each one goes:

- **Dependencies** (core principles): Mission 4 (#6), with the core's Dependabot; the commands go to each pack. The generated core has no dependency yet (YAGNI).
- **`workflows.md`** (path-scoped): the mission that brings the core's first workflow, Mission 3 (#5) or 4 (#6); a rule for files that do not exist would never load.
- **Principles (Zen)**, the UAT's extra rule in "Wait for the final state" (a final state equal to the initial one: change the initial one first) and the why of one open pull request at a time: left out. The core keeps only what cannot be inferred and stays under its line limit; a mission that hits the gap reopens it with an issue (*judgment call*).

## 2. Skills and agent

| Piece | UAT | kit | Better | Cat. | Phase |
| --- | --- | --- | --- | --- | --- |
| `close-mission` | No "Green gates"; has "a fact that surfaces at merge becomes an issue, not a new PR"; README translations step (A) | Has step 1 "Green gates" and the explicit `git diff main...HEAD` | **kit** + the UAT's closing sentence | C (`{{ cmd_check }}`) | 2b |
| `ship-pr` | `merge_when_green.py` (187 lines + tests, depends on Poetry) | **Native auto-merge** with `--match-head-commit` and a shell wait loop; no script | **kit**: less code, no stack dependency | C | 2b |
| `reviewer` | 5 items | 6 items: **+ isolation in the shared environment** | **kit** | C, with the line "ignore what X already enforces" as the pack's extension point | 2b |
| `start-mission` | Missing | Missing | Gap | C | 2b |

The first three rows stand as history: Mission A (#14) moved these pieces into the `mission` plugin, comparing the four versions below, and the link to the commands became each project's contracts table, not `{{ cmd_check }}` ([ADR 0004](adr/0004-partial-resumption-with-a-plugin.md)).

### Mission A: the four versions of the plugin pieces

Comparison of 2026-11-17 between kit, UAT, nextjs and this repository (**tpl**). No hash matches for `close-mission` and `reviewer`; `ship-pr` (and `.claude/settings.json`) is identical between kit and nextjs, and this repository has no `ship-pr`. "New" marks what no version had.

**`close-mission`**

| Passage | Versions | Wins | Why |
| --- | --- | --- | --- |
| Green gates | kit/nextjs: `npm run check`/`pnpm check` "and the tests"; UAT: detailed commands, "on the final state of the branch", "a red gate is fixed before the reviewer, never skipped"; tpl: template checks | **UAT** (both sentences), with the `check`, `test` and `smoke` contracts | The sentences are stack-agnostic; the commands go to the contracts table |
| Session summary | kit/nextjs/tpl: state + a "Mission N" section with decisions, sources, RED; UAT: state only, history in the PR body; tpl: "a lasting decision goes to an ADR" | **UAT + tpl**: summary with state only; lasting decision in a rule or ADR | The UAT summary had turned into history (cells of 1,200+ characters) before it changed; ADR 0004 §8 has the sources |
| Summary path | `docs/` in kit/nextjs/tpl; `docs/ai-workflow/` in the UAT | `session-summary` contract | Differs per project, no tie-breaker |
| README | Translations in the UAT (A); generic in the others | Generic | The translations step belongs to the app |
| Reviewer | kit/nextjs/tpl: `git diff main...HEAD` saved to the scratchpad; UAT: "summary included", "run the gates again" | **Combined** + **new:** the issue text also goes in a file | The reviewer only has `Read`, `Grep` and `Glob`: with just the issue number, it cannot read it |
| PR | kit/nextjs/tpl: `Closes #N`, "ask for the merge"; UAT: follows `.github/pull_request_template.md` and the issue forms, asks for `/ship-pr` | **UAT** (conditional: "if it exists") + **new:** the PR body is the mission record, and the skill checks that the squash uses the PR description | Without `PR_BODY`, the record does not reach Git: the UAT uses `COMMIT_MESSAGES` today (finding for Mission C2, #23) |
| After merge | UAT/tpl: "a fact that surfaces at merge becomes an issue, not a new PR" | **UAT/tpl** | Avoids a PR just for the record |

**`ship-pr`**

| Passage | Versions | Wins | Why |
| --- | --- | --- | --- |
| Mechanism | kit/nextjs: native auto-merge + shell loop; UAT: native auto-merge + `scripts/wait_for_merge.py` (Poetry) | **kit/nextjs** | No stack dependency; the UAT script also exists to warn about Codecov checks (A) |
| `UNKNOWN` | kit: "until it leaves" (no limit); UAT: at most 3 reads, then stops and reports | **UAT** | *Fail fast*: a state that does not resolve does not become an endless wait |
| `BEHIND`/`DIRTY` | kit: acts on the first read; UAT: confirms on a second one (#160, a merge in progress shows these states for an instant) | **UAT** + **new:** `DIRTY` resolved by merging the main branch, never rebase + force push | Evidence of a real failure in the UAT; the merge came from the kit pilot (#19): the rulesets deny force push |
| Accepted `gate` conclusions | kit: only `success`; UAT: `success`, `skipped`, `neutral` | **UAT** | They are the ones GitHub accepts on a required check; the kit's predicate stops the wait as if the check had failed (mutation recorded in the commit) |
| After a failure | UAT: auto-merge stays on; `--disable-auto` to prevent it | **UAT** | A green re-run merges by itself; the user needs to know |
| Interrupted wait and session limit | Only the UAT handles it | **UAT** | A background task dies with the session |
| Branch and check | Fixed: `main`/`master`, `ci-passed` | `main-branch` and `gate` contracts | The UAT uses `master` |
| Required check besides the `gate` | UAT also requires `pip-audit`; no version waits for it | Gap: the `timeout` names the check | Mission C2 (#23) decides between joining it to the gate or waiting for it |

**`reviewer`**

| Passage | Versions | Wins | Why |
| --- | --- | --- | --- |
| Where the rules are | A different fixed path in each (`copilot-instructions.md`, `AGENTS.md` + `.claude/rules/`, `tests.md`, `docs/adr/`) | "Already in your context" + `REVIEW.md` at the root | Subagents load the `CLAUDE.md` hierarchy; `REVIEW.md` is Anthropic's convention for review-only instructions (ADR 0004) |
| Waiting for the final state | kit/nextjs: with Playwright examples; UAT/tpl: generic | **UAT/tpl** | The stack examples go to each project's `REVIEW.md` |
| Isolation | kit: shared environment; UAT: Behave fixtures and workers; nextjs: new database per job; tpl: replaced by "template architecture" | Generic core ("clean state, creates its own data, does not depend on order") | The specifics go to `REVIEW.md` |
| Own items | nextjs: "frozen app"; tpl: "template architecture" | Each project's `REVIEW.md` | They apply to one project only (Missions C and D) |
| "Ignore what X already enforces" | List of tools per stack | `check` contract + `REVIEW.md` | Stack-agnostic |
| A claim about an external tool cites the source | Only tpl | **tpl** | All the rules forbid citing from memory |

**Fresh-chat guard on `ship-pr` (#30, 2026-11-19).** A new piece, with no version in the source projects; the evidence is a measurement, not a repetition. In 8 mission transcripts of a project that uses the plugin, `ship-pr` ran at the end of the implementation chat, with 100k to 290k tokens of context, and resent that context in each of its 36 to 95 calls. In a fresh chat (about 50k fixed tokens), each mission would cost 6% to 14% less (10% on average). Running `/clear` before `ship-pr` is a habit, and habits fail; so it becomes a plugin hook, next to the skill it protects.

**Outdated plugin warning (#32, 2026-11-19).** A new piece, with no version in the source projects; the evidence is an observation. After #31 merged, 4 of the 5 projects that use the plugin were still on old versions (`f845d1b`, `84b2bf3`), with no warning at all. `autoUpdate: false` is a decision (update on purpose, reviewing the change), so the piece is visibility, not updating: a `SessionStart` hook that compares the installed version with the published one.

**`researcher` agent and model routing (#34, 2026-11-20).** New pieces, with no version in the source projects; the evidence is a rule already in use and a measurement. The rule "check the official documentation before proposing" applies in all four projects and was followed by the main session, on the most expensive model; the researcher follows it in a subagent with its own context. Its model came from a `claude plugin eval` suite (5 questions, 3 runs, answer key fixed beforehand; one of them corrected after the first round, with the case re-run): Sonnet tied with Opus (1.000) at about half the cost, and Haiku came in lower (0.983). The `reviewer` stopped inheriting the session's model and was pinned to `opus`/`high`.

**Reviewer answer key (#38, 2026-11-22).** New pieces, with no version in the source projects; the evidence is an observed gap and the golden rule. The bodies of the merged PRs record the reviewer's findings, almost all applied, and no defect it let through; the reviewer is a gate and had never been seen rejecting anything. The capture (false positives and negatives in three lists in the PR body, `reviewer-miss` label) applies to every project that uses the plugin; the `evals/review/` suite reuses merged missions of this repository. Building it exposed another gap: the reviewer received only the `git diff`, without the commit messages, and has no `git`, so it could never check the RED record; `close-mission` now hands the messages over too.

## 3. Configuration and tests of the harness itself

| Piece | UAT | kit | Better | Cat. | Phase |
| --- | --- | --- | --- | --- | --- |
| `test_agent_rules.py` | 200-line limit, identical Claude/Copilot copies, skill metadata, read-only reviewer | Missing: nothing stops the kit from going past 200 lines | **UAT** | C (the LTeX/cSpell/pyright tests are P or go away) | 2b |
| `test_doc_links.py` | Blocks broken links in `.md` | Missing | **UAT** | C | 2b |
| `PreToolUse` hook that compacts test output | `filter_test_output.py` (`pytest -q`, `behave -f progress2`) | Missing | **UAT** | P (the runner changes per stack; the kit can use `--reporter=line`) | 5 / 6 |
| LSP plugin | `pyright-lsp` | Missing | **UAT** | P | 5 / 6 |
| `allow`/`deny` permissions | Missing | Missing | Gap: "never `--admin`" is still only text | C | 3 |
| `SessionStart` hook, secrets hook | Missing | Missing | Gap | C | 3 |
| Versioned `.vscode/` | Yes (cSpell `en,pt_BR,es`, extensions) | Not versioned | UAT | P (extensions per stack); out until there is evidence of value in the core | 5 / 6 |

## 4. Documentation

| Piece | UAT | kit | Better | Cat. | Phase |
| --- | --- | --- | --- | --- | --- |
| `PROJECT_SESSION_SUMMARY.md` | 137 lines; the state table **turned into history**: cells with more than 1,200 characters | Short, with a state table and a **mission plan** | **kit** in shape; the UAT's problem justifies the ADRs (lasting decisions leave the summary) | C (template) | 2a |
| ADRs | Missing | Missing | Gap (this repository already uses them: `docs/adr/`) | C (template) | 2a |
| `KNOWN_ISSUES.md` | Missing | `KI-n` with expected/observed/impact/test, and the warning "confirm that the test fails for the reason of the bug" | **kit** | C (template) | 2a |
| Spike report | Missing | Spike findings inside the summary | kit (content); its own template is missing | C (template) | 2a |
| Flaky test policy | Improvised in #129 (instrument, no retry, citing Fowler) | `retries: 2` in CI, flaky visible in the report | **Neither** has a written policy, and they diverge (see §8) | C | 2a |
| `docs/ai-workflow/` (English index + `AGENT_TOKEN_SPEND.md`) | Yes | No | **UAT** | C | 2a |
| README in 3 languages + metrics validator (452 lines) | Yes | No | — | A/optional: out (YAGNI) | — |

## 5. CI and GitHub

| Piece | UAT | kit | Better | Cat. | Phase |
| --- | --- | --- | --- | --- | --- |
| `ci-passed` gate (single required check, `always()`, allow list) | `check_needs.py` + `test_ci_gate.py` (Python) | Inline in `yq`/`jq`, and **checks that the gate depends on every job** | **kit**: no stack dependency | C | D (#28) in this repo · 2b |
| Actions pinned by SHA | Yes, **enforced** by `test_workflow_pinning.py` | Yes, but nothing enforces it | **UAT** (enforcement); assess whether zizmor replaces the test | C | 3 |
| Workflow hardening | `permissions: contents: read`; **no** workflow-level `concurrency` (only in the Pages deploy job), `persist-credentials: false` or `timeout-minutes` | All four | **kit** | C | 1 |
| Dependabot | Grouped; `docker-compose` ecosystem | Grouped + **7-day `cooldown`** + `versioning-strategy` | **kit** (`github-actions` block in the core, ecosystem block in the pack) | C + P | 4 / 5 / 6 |
| Dependabot `ignore` sentinel | Missing | `check-dependency-ignores.ts` fails `check` when the ignore expires | **kit** | Pattern C, implementation P | 5 |
| Second vulnerability source, daily | `pip-audit --strict` (PR + daily) | **Missing** | **UAT** | Pattern C, implementation P | 5 / 6 |
| Local hooks before commit | `pre-commit` (also run in CI) | Missing | **UAT**, with a caveat: `rev: v5.0.0` by tag (contradicts the SHA rule) and the `pre-commit-hooks` repository repeated | P | 6 |
| Encoding check (UTF-8, no NUL) | `check_text_encoding.py` (the `.gitignore` in UTF-16, generated by PowerShell, matched nothing, #26) | Missing | **UAT**; the problem is Windows', not the stack's | C | 3 |
| Ruleset | "Protect master" (`ci-passed` + `pip-audit`) | "Protect main" (`ci-passed`) | Tie; the core uses `main` | C | This repo: Mission D (#28), as code in `.github/rulesets/` · generated project: 4 |
| `priority: P0/P1/P2` labels | Same | Same | Tie | C | This repo: 0 · generated project: 4 |
| Repository config (squash only, auto-merge, PR title/body) | Auto-merge off | Configured | kit | C | This repo: 0 · generated project: 4 |
| Issue and PR templates | Missing | Missing | Gap | C | 4 |
| `.gitattributes` | `* text=auto` (rejected `eol=lf`) | `* text=auto eol=lf` (Prettier requires LF) | They diverge (see §8) | C | 2a |
| Published report | Allure on Pages + Codecov via OIDC | Planned (kit Mission 6) | UAT | P | 5 / 6 |
| Selenium Grid in `compose.yaml` by digest, same source locally and in CI | Yes (*dev/prod parity*) | — | UAT | P | 6 |

## 6. Test code

### Infrastructure (goes to the pack)

| Piece | UAT | kit | Better | Cat. |
| --- | --- | --- | --- | --- |
| Configuration | `config.yaml` committed with URL and password; CLI > env > YAML hierarchy written by hand (`config_resolver.py`, 172 lines); no validation: a missing key raises `KeyError` at use | Environment variables validated with zod at startup (*fail fast*, the message names the variable); `.env.example`; the shell wins over `.env` | **kit** (Twelve-Factor, factor III) | Contract C, implementation P |
| Runner config | — | `forbidOnly` in CI; trace off in CI because it would record the password in plain text (documented decision) | **kit** | P |
| Failure evidence | Screenshot + URL in Allure; integration artifacts in CI (#129) | `expectJson` fails with URL + response body | Both; the contract is "the failure carries evidence to diagnose without reproducing" | Contract C, implementation P |
| Smoke | `smoke.feature` with `@smoke`, but coupled to Sauce Demo | Missing | Gap in both: smoke = "SUT reachable" | Contract C, implementation P |

### Conventions (only the shape goes to the pack)

| Piece | UAT | kit | Better | Cat. |
| --- | --- | --- | --- | --- |
| Folders | `core/`, `pages/`, `features/steps/`, `tests/{unit,integration,helpers}` | `src/{api,config,data}`, `tests/{api}`, `tests/fixtures.ts` | Each in its own stack | P (empty folders with a README) |
| Known app bug | The scenario **asserts the defect** (`problem_user` sees the wrong product). Legitimate on Sauce Demo, where the defect is intentional, but generalized it turns a bug into expected behavior | `test.fail()` **asserts the correct behavior** and points to `KNOWN_ISSUES.md`; warns when the bug is fixed | **kit** | Policy C, marking P |
| Data isolation | Fixed pre-registered users (Sauce Demo keeps no state between sessions) | A fixture creates unique data per test (shared environment) | **kit** as the general rule | Policy C |

### Domain abstractions (stay out)

`BasePage` (249 lines), page objects, steps and features of the UAT; API clients, zod schemas, `factories.ts` and specs of the kit. They depend on the app (**A**). Their reusable **ideas** are already in the rules, not in the code: wait for the destination page after navigating in a SPA, remove the old error before resubmitting a form, wait for the element to stop moving (`wait_until_stable`, Playwright's "Stable" *actionability check*).

### Test quality (goes to the Phase 8 backlog)

- **UAT, tests that repeat the code.** Example: `assert LoginPage.USERNAME_INPUT == (By.ID, "user-name")` in `tests/test_login_page.py`. A test like that breaks on every refactor and catches no bug: it is the *change-detector test* (Google Testing Blog, "Change-Detector Tests Considered Harmful"). The page object unit tests with `Mock` check that `type()` was called with the locator, that is, they test the implementation, while the 96 integration tests with a real browser already cover the contract with the DOM. The 656 unit tests are inflated by this pattern. Candidates for removal, assessed one by one in Mission 8b.
- **UAT, configuration.** URL and password in `config.yaml` work for a public demo, but the pattern does not fit a real client: migrate to validated environment variables, as in the kit.
- **kit, security.** No second vulnerability source (`npm audit` or equivalent) and no local gate before commit.
- **kit, outdated harness.** No path-scoped rules, no harness tests, no output hook, no LSP (§1 and §3; adopting the template in Mission 8a solves it).

## 7. Gaps in both projects

Neither has them, and the template will:

| Gap | Phase |
| --- | --- |
| `allow`/`deny` permissions in `.claude/settings.json` (`--admin`, `push --force`, push to `main`) | 3 |
| `SessionStart` hook (summary + open issues) and a hook that blocks reading/editing `.env` | 3 |
| gitleaks and zizmor in CI; Scorecard | 3 / 7 |
| Issue templates (mission with acceptance criteria) and PR template | 4 |
| `start-mission` and `/new-project` skills (labels, ruleset, plan issues) | 2b / 4 |
| ADRs, flaky policy, spike report template | 2a |
| CI for the template itself, generating one project per pack and validating it | 1 |

## 8. Decisions left to the phase's mission

- **Line endings (2a).** The UAT rejected `eol=lf` because it forces LF on the Windows disk; the kit needs it because Prettier requires LF. This repository uses `eol=lf` (current editors handle LF well on Windows). Confirm with the Git documentation before putting it in the core. **Decided (Mission 2a, #3):** `* text=auto eol=lf` in the core ([ADR 0008](adr/0008-core-rules-and-documents-in-the-generated-project.md)).
- **Retries in CI (2a, flaky policy).** The kit uses `retries: 2` and relies on the report to show the flaky test; the UAT refused retries in #129 citing Fowler ("re-running until it passes makes the test useless"). The policy has to decide with sources, and what the core requires is that the instability stays **visible and tracked** (an issue), whatever the mechanism. **Decided (Mission 2a, #3):** the core sets the invariant "a retry never passes a build"; each pack picks no retries, or retries that only diagnose and fail the run ([ADR 0008](adr/0008-core-rules-and-documents-in-the-generated-project.md)).
- **This repository's harness (2a/2b).** To work in missions right away, this repository has a minimal copy of the kit's harness (`CLAUDE.md`, rules, `close-mission`, `reviewer`). It is the third hand-made copy, the very problem the template solves. Phase 2 should make this repository use the core (*dogfooding*): generated by it, or with a test that compares the two versions. **Update (Mission D, #17):** `close-mission`, `ship-pr` and `reviewer` now come from the `mission` plugin, installed from this repository; only `CLAUDE.md` and the rules remain hand-made, which Phase 2 resolves.
