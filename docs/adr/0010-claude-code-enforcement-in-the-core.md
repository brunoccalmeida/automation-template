# 10. Claude Code enforcement in the core: deny rules and a SessionStart hook

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

Mission 3a (#5) turns rules of [`core.md`](../../.claude/rules/core.md) that were only text into enforcement in the template-owned `.claude/settings.json`, which this repository shares ([ADR 0009](0009-contracts-as-copier-answers-and-a-shared-harness.md)). The issue asks for:

- deny rules for `gh pr merge --admin`, force push and push to the main branch;
- allow rules for read-only commands;
- a `SessionStart` hook with the summary and the open issues;
- a hook that blocks reading or editing `.env`.

The CI side of the issue moved to #71.

Evidence: kit, nextjs, doc-intake and supabase carry the same deny list. It blocks `--admin`, force push, push to `main` and `.env`, written once for `Bash(...)` and once for `PowerShell(...)`. The UAT has the same list with `master`. None of the five has allow rules or a `SessionStart` hook of its own ([inventory](../INVENTORY.md#fourth-and-fifth-sources-2026-11-25)).

Facts, all from the [Permissions](https://code.claude.com/docs/en/permissions.md) and [Hooks](https://code.claude.com/docs/en/hooks.md) references (read 2026-11-26, Claude Code 2.1.327):

- **Bash and PowerShell rules match the command text.** A deny rule "covers the invocation Claude usually produces and isn't a security boundary around the program": `Bash(git push *)` does not stop `git -C . push origin main` (Permissions, "What a Bash rule doesn't match"). PowerShell rules "use the same shape as Bash rules" (Permissions, "PowerShell").
- **Deny rules block in every mode.** They apply before allow rules and before workspace trust (Permissions, "Manage permissions", "Project allow rules and workspace trust").
- **Read rules use gitignore patterns, and `!` is a real negation.** A bare filename matches at any depth, and a `!` deny pattern carves its paths out of the rules listed before it in the same file. A `Read` deny also blocks Edit and Write on the same path (Permissions, "How path patterns match").
- **Read and Edit denies reach some Bash commands.** In a Bash command they apply to redirection targets and to recognized file commands such as `cat`, `head`, `tail`, `sed` and `tee`. They do not apply to `grep -r pattern .` or to a script that opens the file itself; for that, the reference points to the sandbox (Permissions, "What Read and Edit rules cover").
- **Some commands already run without a prompt.** `ls`, `cat`, `grep`, `find` and the read-only forms of `git` do, in every mode, and the set is not configurable (Permissions, "Read-only commands").
- **SessionStart output is capped.** Plain stdout of a `SessionStart` hook enters Claude's context, up to 10,000 characters. Longer output is replaced by a file path and a 2,000-character preview (Hooks, "SessionStart"). The session summaries measure 17 KB to 125 KB in the source projects, 20 KB here.

## Decision

1. **Deny `--admin` and force push for both shells, and nothing branch-specific.** The rules are `gh pr merge *--admin*`, `git push *--force*`, `git push -f*`, `git push * -f*` and `git push * +*`. They hold in any project, because `core.md` forbids `--admin` and resolves `DIRTY` by merge.
2. **No local deny for pushing to the main branch.** The branch is a Copier answer (`main_branch`, empty by default), and the shared `settings.json` is static. The GitHub ruleset already blocks direct and force pushes on `~DEFAULT_BRANCH` whatever its name, on the server, where a rewritten command cannot get around it. Mission 4 (#6) brings the ruleset to the generated project.
3. **`.env` is protected by deny rules only:** `Read(.env)`, `Read(.env.*)`, `Read(!.env.example)`. The `Edit(...)` copies of the source projects are dropped, because a `Read` deny already covers Edit and Write. There is no separate hook. A `PreToolUse` hook would also read only the command text, so it would add `grep -r` and still miss a script. The sandbox is the boundary that does not depend on the text, and turning it on is the project's call (*judgment call*).
4. **No allow rules.** None of the five sources has them, and the read-only `git` forms already run without a prompt (rule of three, YAGNI). One comes in when a project shows a prompt that gets in the way.
5. **A `SessionStart` hook on `startup` and `clear` that does the first step of the mission cycle.** It lists the open issues and pull requests with `gh` and points at the `session-summary` named in `CLAUDE.md`, without printing the summary, which is over the cap. It does not run on `resume` or `compact`, because those keep the conversation and its state. When `gh` fails, the error stands where the list would be, so Claude does not read the failure as "nothing open". The script is template-owned and shared: `.claude/hooks/session-start.sh`, in POSIX `sh`, like the plugin's hooks.

## Alternatives

- **Render `settings.json` from `main_branch`** to deny pushes to the branch by name. It breaks the identity with this repository's copy, it has nothing to render when the answer is empty, and it duplicates a server rule with a weaker one.
- **Print the session summary from the hook.** It goes over the 10,000-character cap in every source project, so Claude would get the preview and read the file anyway.
- **Put the hook in the `mission` plugin.** The mission cycle is a core rule, and the plugin's `SessionStart` hook watches the plugin's own version. The core hook also covers a project that has not installed the plugin yet.

## Consequences

- The deny rules are tested against the documented matching semantics ([`tests/test_project_settings.py`](../../tests/test_project_settings.py)), and some were tried in Claude Code 2.1.327 itself: the Bash rules for `--force` and `--admin` and `cat .env` were seen blocking, and `cat .env.example` and a plain push ran. The PowerShell rules, the `+` and trailing `-f` forms and the Read tool on `.env` were not seen blocking in Claude Code; the mission record lists them. A deny rule that becomes wrong in a future Claude Code version only shows up when someone runs those commands again.
- The source projects keep their longer lists until they adopt the template (#10, #11); the extra rules are harmless.
- Each new session and each `/clear` runs `gh` twice. Without network or `gh` authentication, the hook says so in the context instead of listing.
