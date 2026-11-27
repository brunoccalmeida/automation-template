# 13. `/new-project` applies the GitHub settings with a shared script

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

[ADR 0012](0012-github-files-rendered-by-the-core.md) renders `.github/rulesets/protect-main.json`, but a file changes nothing on GitHub. A generated project is protected only after something applies the ruleset, the labels the mission cycle reads, and the merge settings. That is Mission 4b (#74). ADR 0012 also left two facts unproved: that the required check's context is the gate job's name, and that `integration_id: 15368` is the GitHub Actions app.

Evidence and sources (read 2026-11-26):

- **API.** A ruleset is created with `POST /repos/{owner}/{repo}/rulesets` and replaced with `PUT .../rulesets/{id}`. The list takes `includes_parents`, which defaults to `true` ([REST: rules](https://docs.github.com/en/rest/repos/rules)). `PATCH /repos/{owner}/{repo}` sets `allow_*_merge`, `allow_auto_merge`, `delete_branch_on_merge`, and `squash_merge_commit_title`, which is "required when using `squash_merge_commit_message`" ([REST: Update a repository](https://docs.github.com/en/rest/repos/repos#update-a-repository)). `gh label create --force` updates a label that already exists ([gh manual](https://cli.github.com/manual/gh_label_create)).
- **Context of a workflow check.** "Workflow: The name format is `<job name>`" ([Troubleshooting rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/troubleshooting-rules)). The probe below confirmed it.
- **15368.** `gh api apps/github-actions` returns `{"id":15368,"slug":"github-actions","name":"GitHub Actions"}` ([REST: Get an app](https://docs.github.com/en/rest/apps/apps#get-an-app)).
- **Plan.** [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) names only GitHub Team and Enterprise. The probe below ran on a public repository on GitHub Free and the ruleset was applied and enforced.
- **Merge settings in the sources.** All four sources that could be read (the kit, nextjs, the UAT, doc-intake-pipeline) have squash with `PR_TITLE` and `PR_BODY`, auto-merge, and `delete_branch_on_merge: true`. The kit and nextjs also turn off merge commits and rebase.
- **Skills.** `.claude/skills/<name>/SKILL.md` is invoked as `/<name>`. `disable-model-invocation: true` keeps Claude from loading the skill on its own ([Skills](https://code.claude.com/docs/en/skills.md), "Frontmatter reference").

**Probe** on the throwaway public repository `new-project-probe-74`, generated from this branch:

- The script ran twice. Each run exited 0, and the second replaced the ruleset instead of adding one (a single id, 28202676).
- The read-back returned the five labels, the merge settings, and five rules active on `main`, with `required_status_checks [{"context":"ci-passed","integration_id":15368}]`.
- A direct push to `main` was refused: "Changes must be made through a pull request", "Required status check "ci-passed" is expected".
- A PR with a UTF-16 file failed `ci-passed`, so `gh pr merge` refused with "the base branch policy prohibits the merge". The check run `ci-passed` came from app 15368 `github-actions`.
- The same PR, fixed, merged by auto-merge once the gate was green. So the required context matches the check the gate produces.
- The squash commit on `main` carried the PR's title and body, and the head branch was deleted.

## Decision

1. **A thin skill over a POSIX `sh` script.** `/new-project` (`template/.claude/skills/new-project/SKILL.md`) checks the target (admin permission, default branch = `main-branch`), asks the user to confirm, runs `.github/scripts/apply-github-settings.sh` and reads every value back. The script makes the calls. A script gives the same result on every run, a fake `gh` can test it (`tests/test_apply_github_settings.py`), and it runs without Claude. It uses `sh` and `gh` only, like the core's other scripts.
2. **The script can run again.** Labels use `--force`. The ruleset is found by the name in the file and replaced, or created when none has that name. It fails when two rulesets share the name, instead of guessing which one to replace. `includes_parents=false` keeps an organization ruleset out of the lookup. The first failed call stops the script with gh's error and the step it was on.
3. **The merge settings are squash only, with `PR_TITLE` and `PR_BODY`, auto-merge, and merged branches deleted.** `delete_branch_on_merge` is not in #74's list, but every source sets it.
4. **This repository uses the same script.** It is a shared file, held identical by the shared-file test. The "Ruleset as code" rule in `CLAUDE.md` now runs it. Applying the file again is how ruleset drift is fixed. There is no automatic drift check in CI: reading the ruleset needs a token with admin access that the workflow does not have.
5. **The skill is template-owned and lives only in `template/`.** This repository applies its settings with the script directly.

## Alternatives

- **A skill in prose that lists the `gh` commands.** It is shorter, but no test can check it, and each run depends on how the model reads it.
- **Applying the ruleset by a hard-coded id, as this repository did.** That only works after the first create, and a generated project has no id yet.
- **A drift check in CI.** It needs a token with admin read on the repository, a secret every project would have to manage. Left out until a drift actually happens.

## Consequences

- A generated project is protected once its user runs `/new-project`. The project's session summary names it as the first step.
- The labels' names, colors and descriptions live in the script. A label the plugin starts to read goes there too.
- A private repository on GitHub Free is untested. There, a failed ruleset call is the expected cause, and the skill says so.
