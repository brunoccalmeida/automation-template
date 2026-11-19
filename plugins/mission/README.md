# mission

A Claude Code plugin for working in **missions**: one GitHub issue per chat, a Definition of Done checked before the pull request, a read-only reviewer that compares the diff with the issue, and a merge decided by the branch ruleset through native auto-merge.

| Component | Invoke | What it does |
| --- | --- | --- |
| `close-mission` skill | `/mission:close-mission`, or Claude when the implementation is ready | Definition of Done: gates green, issues up to date, session summary, reviewer, pull request carrying the mission record |
| `ship-pr` skill | `/mission:ship-pr [pr-number]`, by the user only, as the first message of a fresh chat | Turns on squash auto-merge pinned to the head SHA and waits for the outcome |
| `reviewer` agent | `mission:reviewer`, called by `close-mission` | Reviews the mission diff against its issue and against what no automated gate covers |
| Fresh-chat guard (hook) | Runs by itself when `/mission:ship-pr` is typed | Blocks `/mission:ship-pr` in a chat that already has conversation; see [Ship in a fresh chat](#ship-in-a-fresh-chat) |
| Version check (hook) | Runs by itself when Claude Code starts | Warns when the installed plugin is not the published one; see [Updates](#updates) |

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
| `check` | Yes | Static gates: lint, types, formatting | `close-mission` (gates), `ship-pr` (after resolving a `DIRTY` conflict), `reviewer` (what to ignore) |
| `test` | Yes | The whole suite, with any precondition it needs to run as in CI (a service started, an environment variable set) | `close-mission`, `ship-pr` (after resolving a `DIRTY` conflict) |
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

## Ship in a fresh chat

Run `/mission:ship-pr <n>` as the **first message of a new chat**: `/clear` first, in the chat that implemented the mission. `ship-pr` needs nothing from that conversation (the pull request body holds the mission record, and the session summary holds the state), but every tool call re-sends the whole context, and waiting for CI and the merge takes dozens of calls. Measured on 8 missions of a project that uses this plugin, a fresh chat would have cost about 10% less per mission (6 to 14%) ([#30](https://github.com/brunoccalmeida/automation-template/issues/30)).

A habit fails, so the plugin enforces it with a [`UserPromptExpansion`](https://code.claude.com/docs/en/hooks.md#userpromptexpansion) hook ([`hooks/hooks.json`](hooks/hooks.json), [`scripts/require-fresh-chat.sh`](scripts/require-fresh-chat.sh)). That event fires when a typed slash command expands, the path a `PreToolUse` hook on `Skill` does not see. The hook reads the chat transcript and blocks the command, with a message saying to run `/clear`, when the transcript already holds an assistant reply. Other commands and plain prompts never reach it: its matcher is `^mission:ship-pr$`, anchored because a matcher with `:` is an unanchored regular expression ([Matcher patterns](https://code.claude.com/docs/en/hooks.md#matcher-patterns)).

- **It guards cost, not safety, so it fails open.** A missing or unreadable transcript allows the command and says why on stderr. With exit code 0, that stderr never reaches Claude; read it with debug logging ([Exit code 0](https://code.claude.com/docs/en/hooks.md#exit-code-0): "Claude never sees stderr from a hook that exits 0. To read it yourself [...] enable debug logging").
- **It needs `sh`, `grep` and `sed`**, present on macOS and Linux and in Git Bash, which runs plugin hooks on Windows. On Windows without Git Bash, hooks run in PowerShell ([Exec form and shell form](https://code.claude.com/docs/en/hooks.md#exec-form-and-shell-form)), `sh` is not found, and the hook fails open: `ship-pr` runs, unguarded.
- **Resuming a wait counts as prior conversation.** If a `ship-pr` wait was interrupted, `/clear` and run `/mission:ship-pr <n>` again; the skill reads the real state of the pull request first.

## Install in a project

From the project root, register the marketplace for everyone who clones the repository, install the plugin at project scope, and commit `.claude/settings.json`:

```sh
claude plugin marketplace add brunoccalmeida/automation-template --scope project
claude plugin install mission@brunoccalmeida-plugins --scope project
```

These commands need the `claude` CLI on `PATH`. With Claude Code installed only as the VS Code extension, it usually is not (`claude: command not found`). Either:

- **Call the extension's binary by its full path**, for example on Windows `"$USERPROFILE/.vscode/extensions/anthropic.claude-code-<version>-win32-x64/resources/native-binary/claude.exe" plugin ...`, with the same arguments as above.
- **Do it inside a Claude Code session in the project.** In a terminal session: `/plugin marketplace add brunoccalmeida/automation-template`, then `/plugin install mission@brunoccalmeida-plugins`, which opens the plugin's details instead of installing at once; choose **Install for all collaborators on this repository (project scope)** there ([Install and manage plugins](https://code.claude.com/docs/en/plugins/install.md#install-a-plugin)). In the VS Code panel, `/plugins` opens **Manage plugins**: add the marketplace on the **Marketplaces** tab, then install with **Install for this project** ([Install and manage plugins](https://code.claude.com/docs/en/plugins/install.md#install-a-plugin), VS Code tab). The in-session marketplace add documents no scope option ([`/plugin` in a session](https://code.claude.com/docs/en/plugins/cli-reference.md#plugin-in-a-session)), so check that `.claude/settings.json` ends up with the `extraKnownMarketplaces` entry shown under [Updates](#updates), and add it by hand if it does not: that entry is what registers the marketplace for everyone who clones the repository ([Host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md#register-the-marketplace-for-everyone-in-a-repository)).

Either way, commit `.claude/settings.json`. It enables the plugin for collaborators but does not download it: each one runs the install once per clone ([Choose an install scope](https://code.claude.com/docs/en/plugins/install.md#choose-an-install-scope)).

The repository is public, so cloning needs no credentials. On a machine without a GitHub SSH key, set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` so installs and updates from inside a session clone over HTTPS ([Host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md#serve-users-who-have-no-git-host-account)).

## Updates

The manifest has no `version`, so each install is pinned to the commit it was installed from and an update moves it to the latest commit ([Versions and updates](https://code.claude.com/docs/en/plugins/loading.md#versions-and-updates)). Auto-update stays off: update on purpose, and review what changed first.

Off is today's default for third-party marketplaces, but `claude plugin marketplace add` does not write it down. Declare `"autoUpdate": false` beside `source` in `.claude/settings.json` and commit it, so the decision is explicit and does not depend on a default that may change ([Settings reference, `extraKnownMarketplaces`](https://code.claude.com/docs/en/settings-reference#extraknownmarketplaces): "When omitted, [...] third-party marketplaces default to `false`"):

```json
{
  "extraKnownMarketplaces": {
    "brunoccalmeida-plugins": {
      "source": {
        "source": "github",
        "repo": "brunoccalmeida/automation-template"
      },
      "autoUpdate": false
    }
  },
  "enabledPlugins": {
    "mission@brunoccalmeida-plugins": true
  }
}
```

To update, run the first command in the shell or the second in a session ([Host a marketplace, Turn on auto-update](https://code.claude.com/docs/en/plugins/host-marketplace.md#turn-on-auto-update): "Without auto-update, users receive your changes when they run `/plugin marketplace update <name>` in a session or `claude plugin update <plugin>@<name>` in the shell"):

```sh
claude plugin update mission@brunoccalmeida-plugins
```

```text
/plugin marketplace update brunoccalmeida-plugins
```

### Warning when the plugin is outdated

Manual updates drift: after one merge, 4 of the 5 projects using the plugin were still on older versions, and nothing said so ([#32](https://github.com/brunoccalmeida/automation-template/issues/32)). Turning auto-update on would hide that drift instead of fixing it, since reviewing what changed is the point of updating on purpose. So the plugin makes the drift visible and leaves the update to you: a [`SessionStart`](https://code.claude.com/docs/en/hooks.md#sessionstart) hook ([`scripts/check-plugin-version.sh`](scripts/check-plugin-version.sh)) compares the installed version with the published one when Claude Code starts and, when they differ, shows both SHAs and the update command.

- **Installed version:** the name of the plugin's cache directory, which `${CLAUDE_PLUGIN_ROOT}` points at. With no `version` in the manifest, it is the marketplace commit SHA shortened to 12 characters ([How Claude Code computes the version](https://code.claude.com/docs/en/plugins/loading.md#how-claude-code-computes-the-version)).
- **Published version:** `HEAD` of the manifest's `repository`, read with `git ls-remote`, which needs no model and no GitHub API. It assumes the plugin lives in the marketplace repository it names, as this one does. A merge that touches only documentation also moves `HEAD`, and then `claude plugin update` really does install a new version, so the warning is accurate.
- **Shown to you, not to Claude:** the warning is a `systemMessage`, the "warning message shown to the user"; plain stdout and `additionalContext` from `SessionStart` enter Claude's context ([Hooks reference, SessionStart](https://code.claude.com/docs/en/hooks.md#sessionstart)) and would cost tokens every session.
- **Startup only:** the matcher is `startup`. The loaded version only changes when Claude Code launches, so `/clear`, resume and compaction never run it.
- **It fails open.** Offline, no `git`, no `repository` in the manifest, or a plugin loaded in place with `--plugin-dir` (its directory is not named after a commit): nothing is shown, and the reason goes to stderr, readable with debug logging. Claude's first reply waits for `SessionStart` hooks, so the hook's `timeout` is 10 seconds.

## Track the adoption from this repository

A mission that adopts or changes the plugin in a project is often tracked by an issue in this repository. The project's pull request closes that issue only if its description says `Closes brunoccalmeida/automation-template#N`: a bare `#N` points to the project's own repository ([Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword), "Issue in a different repository"). The keyword takes effect only when the pull request merges into the default branch.
