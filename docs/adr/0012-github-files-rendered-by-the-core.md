# 12. GitHub files rendered by the core: the CI caller, the ruleset, Dependabot and the mission templates

- **Status:** Accepted
- **Date:** 2026-11-26
- **Supersedes in part:** [ADR 0009](0009-contracts-as-copier-answers-and-a-shared-harness.md) ("No question has a value as its default"), for `main_branch` and `gate`

## Context

Mission 4 (#6) was split in two. This record covers Mission 4a: the files the template renders for GitHub. The API part goes to #74: labels, applying the ruleset and the merge settings through `/new-project`.

[ADR 0011](0011-ci-enforcement-as-a-reusable-core-workflow.md) (decision 5) left `core-checks.yml` in the generated project with no caller. [ADR 0010](0010-claude-code-enforcement-in-the-core.md) (decision 2) left pushes to the main branch to the server ruleset, which the generated project did not have. [ADR 0009](0009-contracts-as-copier-answers-and-a-shared-harness.md) gave no question a default, because "the core cannot know the project's branch or CI". Once the core renders the CI, it does know.

Evidence and sources (read 2026-11-26):

- **Dependabot.** The same `github-actions` block is in the kit, nextjs, the UAT and doc-intake-pipeline: weekly, grouped, `ci` prefix, 7-day cooldown ([inventory](../INVENTORY.md)). Dependabot reads `.github/dependabot.yml` and has no `extends` or preset key ([options reference](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)). zizmor's `dependabot-cooldown` audit flags fewer than 7 days by default ([zizmor audits](https://docs.zizmor.sh/audits/#dependabot-cooldown)). Probe with zizmor 1.32.0 on a generated project: `default-days: 3` gave "insufficient default-days configured (less than 7)" and exit 13.
- **Reference templates.** The Scientific Python cookie renders a `dependabot.yml` with only `github-actions`, as template-owned. Both it and copier-uv hard-code `main` in the CI trigger and ask no branch question ([cookie ci.yml](https://raw.githubusercontent.com/scientific-python/cookie/main/%7B%7Bcookiecutter.project_name%7D%7D/.github/workflows/ci.yml), [copier-uv ci.yml.jinja](https://raw.githubusercontent.com/pawamoy/copier-uv/main/project/.github/workflows/ci.yml.jinja)). copier-uv ships issue and PR templates; the cookie ships neither.
- **Templates.** Issue forms go in `.github/ISSUE_TEMPLATE/` and begin with `name`, `description` and `body`. GitHub still labels them "public preview" ([Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)). The PR template goes in `.github/pull_request_template.md` ([PR template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)). Neither OpenSSF Scorecard nor the Best Practices Badge asks for templates. Among the sources only the UAT has them (uat#148); `close-mission` already follows both when they exist.
- **Ruleset.** `~DEFAULT_BRANCH` in `conditions.ref_name.include` targets the default branch ([REST: rules](https://docs.github.com/en/rest/repos/rules)).

## Decision

1. **`.github/workflows/ci.yml` is rendered once and project-owned** (`_skip_if_exists`). It calls `core-checks.yml` as the `core-checks` job, and its gate job is named after the `gate` answer, with the same `needs` check as this repository's gate. The project adds its own jobs there.
2. **`gate` defaults to `ci-passed` and `main_branch` to `main`,** and both reject an empty answer. The gate is the name of a job the core itself renders. `main` is the branch of every source project and of both reference templates. The commands (`check`, `test`, `smoke`) still default to empty and render "Not set".
3. **`.github/rulesets/protect-main.json` is template-owned.** It is this repository's ruleset, with the required check rendered from `gate`; a test holds the two equal. `integration_id: 15368` comes from this repository's active ruleset as read through the API. No official page names it as the GitHub Actions app, so #74 proves it on a throwaway repository.
4. **`.github/dependabot.yml` is project-owned** and renders only the core's `github-actions` block. Packs and projects add their own ecosystems to the single file Dependabot reads. That follows this repository's rule that the project never edits template-owned files. zizmor enforces the cooldown in every project whoever owns the file.
5. **The Mission issue form and the PR template are template-owned.** The PR template's sections are the mission record that `close-mission` writes: decisions, sources, how the RED was seen, and the reviewer's three lists. There is no bug form and no `config.yml`: the mission cycle has no use for them yet (YAGNI). This repository uses both files, held identical by the shared-file test.

## Alternatives

- **No defaults, as in ADR 0009.** Every project would type a gate name the template has already chosen, and an empty `main_branch` would render a broken trigger.
- **A template-owned `dependabot.yml`, as in the Scientific Python cookie.** `copier update` would bring changes to the block, but a project with its own ecosystem would edit a template-owned file. When both sides change the same hunk, Copier leaves conflict markers to review by hand ([Updating](https://copier.readthedocs.io/en/stable/updating/)).
- **No templates until a third source (rule of three).** The inventory (§7) planned them as a gap to fill. The plugin already reads them, and the PR template is the one place that names the record's sections.

## Consequences

- A generated project's CI runs the core's checks. It is protected only after #74 applies the ruleset.
- `copier update` never brings changes to `ci.yml` or `dependabot.yml`. A fix to the core's block reaches existing projects only by hand.
- This repository now has `.github/dependabot.yml` for `github-actions`, which brings the zizmor-action bump of [ADR 0011](0011-ci-enforcement-as-a-reusable-core-workflow.md) (decision 4). ADR 0007 left the Copier `requirements.txt` (hash-locked) to this mission. Whether Dependabot can update it is still unconfirmed, as is the npm lockfile of the CLI, so both stay manual and go to their own issue.
- The issue form depends on a feature GitHub labels "public preview". If its syntax changes, the form changes with it.
