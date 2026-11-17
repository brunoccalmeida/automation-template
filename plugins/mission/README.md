# mission

A Claude Code plugin for working in **missions**: one GitHub issue per chat, a Definition of Done checked before the pull request, a read-only reviewer that compares the diff with the issue, and a merge decided by the branch ruleset through native auto-merge.

| Component | Invoke | What it does |
| --- | --- | --- |
| `close-mission` skill | `/mission:close-mission`, or Claude when the implementation is ready | Definition of Done: gates green, issues up to date, session summary, reviewer, pull request carrying the mission record |
| `ship-pr` skill | `/mission:ship-pr [pr-number]`, by the user only | Turns on squash auto-merge pinned to the head SHA and waits for the outcome |
| `reviewer` agent | `mission:reviewer`, called by `close-mission` | Reviews the mission diff against its issue and against what no automated gate covers |

The plugin is the same for every project: it carries no per-project variables. It names **contracts**, and each project declares the real command or value behind each contract in its own rules, as described below. The skills and the reviewer are written in Brazilian Portuguese, the language of the rules of the projects that use them.

## What a project must provide

### 1. A contract table in its rules

Add this table to the project's always-loaded rules (the file `CLAUDE.md` imports, or `.claude/rules/`), so both the main session and the reviewer see it. The first column holds the contract names exactly as written here; the heading and the other columns may be in the project's language. The values below are an example taken from a Playwright project: the skills and the agent never name a tool, and this README does only to show what a filled-in table looks like.

```markdown
## Contracts

| Contract | Value |
| --- | --- |
| `check` | `npm run check` |
| `test` | `npx playwright test` |
| `smoke` | `npx playwright test --grep @smoke` |
| `main-branch` | `main` |
| `gate` | `ci-passed` |
| `session-summary` | `docs/PROJECT_SESSION_SUMMARY.md` |
```

| Contract | Required | Meaning | Used by |
| --- | --- | --- | --- |
| `check` | Yes | Static gates: lint, types, formatting | `close-mission` (gates), `reviewer` (what to ignore) |
| `test` | Yes | The whole suite, with any precondition it needs to run as in CI (a service started, an environment variable set) | `close-mission` |
| `smoke` | No | The system under test is reachable and the pipeline works end to end | `close-mission`, when present |
| `main-branch` | Yes | The branch pull requests merge into | `close-mission`, `ship-pr` |
| `gate` | Yes | Name of the single check run the ruleset requires, which aggregates the others | `ship-pr` |
| `session-summary` | Yes | Path of the file that holds the project's state between chats | `close-mission` |

When a contract the skill needs is missing, the skill stops and asks instead of guessing.

### 2. Repository settings

`ship-pr` and `close-mission` rely on these GitHub settings:

- **Squash merging** allowed, with the **pull request title and description** as the default commit message (`squash_merge_commit_message` = `PR_BODY`). The mission record lives in the pull request body, and this setting is what writes it into the main branch's history.
- **Auto-merge** allowed.
- A **ruleset** on the main branch that requires the `gate` check, an up-to-date branch and linear history.
- Labels `priority: P0`, `priority: P1` and `priority: P2`.

### 3. Optional: `REVIEW.md` at the repository root

Project-specific review checks go in `REVIEW.md` at the repository root, free-form Markdown, the file Anthropic's [Code Review](https://code.claude.com/docs/en/code-review-customize.md) reads for review-only instructions. The `reviewer` agent reads it when it exists and treats it as additions to its own list and as things to skip. Keep general project rules in `CLAUDE.md`, which the reviewer already loads. Example, from the same Playwright project:

```markdown
# Review instructions

## Always check

- Waits use web-first assertions; a response wait is registered before the action that triggers it.
- Each test creates its own data in the shared environment.

## Do not report

- Anything `tsc`, ESLint and Prettier already enforce.
```

## Install in a project

From the project root, register the marketplace for everyone who clones the repository, install the plugin at project scope, and commit `.claude/settings.json`:

```sh
claude plugin marketplace add brunoccalmeida/automation-template --scope project
claude plugin install mission@brunoccalmeida-plugins --scope project
```

The repository is public, so cloning needs no credentials. On a machine without a GitHub SSH key, set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` so installs and updates from inside a session clone over HTTPS ([Host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md#serve-users-who-have-no-git-host-account)).

## Updates

The manifest has no `version`, so each install is pinned to the commit it was installed from and an update moves it to the latest commit ([Versions and updates](https://code.claude.com/docs/en/plugins/loading.md#versions-and-updates)). Auto-update is off for third-party marketplaces by default and stays off: update on purpose, and review what changed first.

```sh
claude plugin update mission@brunoccalmeida-plugins
```
