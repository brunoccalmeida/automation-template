# 9. Contracts as Copier answers, the marketplace in the core, and this repository on its own core

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

Mission 2b (#4) had four open points:

- The contracts table of the generated `CLAUDE.md` read "Not set" in every row ([ADR 0008](0008-core-rules-and-documents-in-the-generated-project.md), consequences), although [ADR 0003](0003-stack-agnostic-core-defines-contracts.md) binds the contracts to Copier variables.
- [ADR 0004](0004-partial-resumption-with-a-plugin.md) (consequences) leaves Copier two jobs once the plugin carries the skills and the reviewer: render the contracts table and add the marketplace to `.claude/settings.json`.
- ADR 0003 asks for a test that fails when the core names a stack term. The issue also asks for a test that fails on a broken documentation link.
- ADR 0008 (decision 2) left open whether this repository generates its `core.md` from the template or keeps a copy that a test holds identical.

Facts behind the decision:

- A Copier question with a `default` takes that value under `--defaults`, and every answer is recorded in the answers file. `_skip_if_exists` renders a file on the first copy and skips it after that ([Configuring a template](https://copier.readthedocs.io/en/stable/configuring/)).
- A marketplace declared in `extraKnownMarketplaces` of the project's `.claude/settings.json` is offered to everyone who trusts the folder. `autoUpdate` defaults to `false` for third-party marketplaces when it is omitted ([Settings reference, `extraKnownMarketplaces`](https://code.claude.com/docs/en/settings-reference#extraknownmarketplaces), as quoted in the [plugin README](../../plugins/mission/README.md)).

## Decision

1. **One Copier question per contract that varies:** `cmd_check`, `cmd_test`, `cmd_smoke`, `main_branch` and `gate`, each defaulting to empty. An answer renders as code in the contracts table of `CLAUDE.md`, and an empty one as "Not set", so the plugin stops and asks instead of guessing. `session-summary` is not a question, because the core ships that file at a fixed path. No question has a value as its default, not even `main_branch`: the core cannot know the project's branch or CI, and a wrong default reads as a real value.
2. **The table stays in the project-owned `CLAUDE.md`** (ADR 0008, decision 1). Copier renders it once. After that, the project edits it like the rest of the file.
3. **`.claude/settings.json` is template-owned** and holds the same marketplace registration as this repository's file: `brunoccalmeida-plugins`, from GitHub, `autoUpdate: false`, with `mission` enabled. The test reads the marketplace name and the plugin list from `.claude-plugin/marketplace.json`, so a renamed marketplace or a new plugin breaks it.
4. **Harness tests run on the generated project:**
   - no stack term from a fixed list of tools, languages and stack settings (whole words, any case);
   - every relative Markdown link resolves, except declared placeholders such as the `NNNN-title.md` of the ADR template;
   - the always-loaded rules stay under the line limit (already there since #3).

   Words that are also plain English, such as "behave", stay off the list. The list covers names, not meaning; a reviewer still catches a stack phrased in other words (*judgment call*).
5. **This repository is not generated; it shares the template-owned files that apply to it.** It is the template's source, and its README and `CLAUDE.md` are its own. A copy of the template would render the project-owned files on top of them. The following files are shared and kept identical by a test:
   - `.claude/rules/core.md`
   - `.claude/rules/agent-rules.md`
   - `.claude/settings.json`
   - `.gitattributes`
   - `docs/ai-workflow/AGENT_TOKEN_SPEND.md`

   The test also fails when one of them disappears from here. The `docs/ai-workflow/` index, the flaky policy and the ADR and spike templates stay in the template only: the index links to documents this repository does not have, and this repository has no use for the others yet (YAGNI).

## Alternatives

- **The contracts in a template-owned file that `CLAUDE.md` imports**, re-rendered by `copier update` when an answer changes: already rejected in ADR 0008, because `CLAUDE.md` is where the project's rules are expected and an import saves no context.
- **Defaults taken from the source projects** (`main`, `ci-passed`): every source project uses them, but a core-only project has no CI yet. Defaults like these would render a gate that does not exist. The packs will answer them.
- **A symbolic link from `template/` to this repository's files:** a single copy on disk. But with `core.symlinks` false, Git checks symbolic links out as small plain files that hold the link text, and `git clone` sets it to false where it detects no support ([git-config, `core.symlinks`](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coresymlinks)). A Windows clone without that support would then render the link text instead of the rules. The identity test gets the same guarantee with no setup.

## Consequences

- Changing an answer later (`copier update --data ...`) does not change the contracts table, because `CLAUDE.md` is never rendered again. The project edits the table by hand. The answers file still records the original answer.
- A pack sets its contracts by answering these questions, for example through its own defaults, and adds no new question for them.
- The example in `core.md` that named a stack (`npm run lint`) is gone; the stack-term test found it.
- A permission or hook that Mission 3 (#5) adds to `.claude/settings.json` goes in the template's copy and in this repository's, or the identity test fails.
