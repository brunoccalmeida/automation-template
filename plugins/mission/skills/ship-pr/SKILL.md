---
name: ship-pr
description: Turns on auto-merge (squash) for a PR into the main branch, pinned to the head SHA, and waits for the result; the ruleset decides. Only the user triggers it, because the merge is a human decision.
disable-model-invocation: true
argument-hint: '[pr-number]'
model: opus
---

Merge PR $ARGUMENTS into the main branch (no number: the current branch's PR, `gh pr view --json number`). Names in backticks such as `main-branch`, `gate`, `check` and `test` are **contracts**: the real value is in the contracts table of the project's rules (format in `${CLAUDE_PLUGIN_ROOT}/README.md`). A contract missing from the table: stop and ask, never guess.

What decides whether the PR can merge is the `main-branch` **ruleset** (`gate` check green on the head SHA, branch up to date, linear history). The skill does not reimplement that decision: it turns on [auto-merge](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request), which merges only after every requirement passes, and waits for the result. Never `--admin`.

1. If another PR is open (`gh pr list`), stop and ask: one open PR at a time.
2. Read `gh pr view <n> --json state,headRefOid,mergeStateStatus`, one read per command.
   - `MERGED`: go to step 5.
   - `UNKNOWN` (right after a merge into the `main-branch` it has not been computed yet): read again, at most 3 times; if it persists, stop and report.
   - `BEHIND` or `DIRTY`: confirm with a second read, because a merge in progress shows these states for a moment. `BEHIND` confirmed: `gh pr update-branch <n>` and read again (the head SHA changed). `DIRTY` confirmed (a conflict; auto-merge would never merge): resolve it by **merging** the `main-branch` into the PR branch, never by rebasing. `git fetch origin`, `git merge origin/<main-branch>` on the PR branch, resolve the conflict, run `check` and `test`, commit and **plain push**; read again (the head SHA changed). A conflict that needs a content decision (both versions bring changes that exclude each other): stop and ask. Why merge: a rebase rewrites commits already published and only goes up with a force push, which the project's push guards usually deny; a merge only adds a commit. It is what `gh pr update-branch` does by default, and the squash brings a single commit to the `main-branch`, which stays linear all the same.
3. Check the message the squash will write: `gh pr view <n> --json title,body --jq '.title + "\n\n" + .body'` into a scratchpad file, then `sh "${CLAUDE_PLUGIN_ROOT}/scripts/check-closing-keywords.sh" <file>`. Exit 1: a closing keyword names an issue the body does not declare on a line of its own (`Closes #N`), and the merge would close it; stop, show the user the lines it names with a reworded body, and only with their agreement `gh pr edit <n> --body-file <file>` and run the check again (the head SHA does not change). Exit 2: the file could not be read; fix that, never skip the check. Then `gh pr merge <n> --auto --squash --match-head-commit <sha>`, alone in the command. `--match-head-commit` makes GitHub refuse the merge if the head changes after the read. With the PR already ready, `gh` merges directly instead of turning on auto-merge; step 4 covers both cases. Exit code other than 0: read stderr and stop. The squash title and body come from the PR, so review them first.
4. Wait for the **result**, not an intermediate state: checks are read by the head SHA (right after a push, `gh pr checks` still shows the previous commit's, or none) and the merge happens after them, asynchronously. Run this loop (Bash) in the background, waiting for the notification; it only exits on a final state:

   ```sh
   n=<n>; sha=<sha>; gate=<gate>; : "${n:?}" "${sha:?}" "${gate:?}"; deadline=$((SECONDS + 1800))
   until out=$(gh pr view "$n" --json state,autoMergeRequest --jq '"\(.state) \(.autoMergeRequest != null)"') \
     && result=$(gh api "repos/{owner}/{repo}/commits/$sha/check-runs?check_name=$gate" --jq '[.check_runs[] | select(.status == "completed")][0].conclusion // "pending"') \
     && { [ "${out%% *}" != OPEN ] || [ "${out#* }" = false ] || ! printf '%s\n' "$result" | grep -qxE 'pending|success|skipped|neutral'; }
   do [ "$SECONDS" -lt "$deadline" ] || { echo "timeout: $out $gate=$result" >&2; exit 1; }; sleep 30; done
   echo "$out $gate=$result"
   ```

   A network or API error counts as "not known yet" and the loop tries again; if it persists, the 30-minute deadline ends it with `timeout` and the last state read. `success`, `skipped` and `neutral` are the conclusions GitHub accepts in a required check.

   - `MERGED`: go to step 5.
   - `gate` failed: the PR does not merge. Diagnose from the log (`gh run view <run-id> --log-failed`) and, after pushing the fix, go back to step 2 (the SHA pinned in step 3 was the old one). Auto-merge **stays on**: a green re-run merges on its own; to prevent it, `gh pr merge <n> --disable-auto`.
   - `OPEN false` (auto-merge turned off, for example by a new head or `BEHIND`): go back to step 2.
   - `CLOSED` (PR closed without a merge): stop and report; do not reopen it or try to merge.
   - `timeout`: report the last state. A required check other than `gate`, pending or failed, also holds the merge and ends here: name it with `gh pr checks <n>`.
5. Confirm `MERGED` (`gh pr view <n> --json state`) and only then `git switch <main-branch>`, `git pull --ff-only` and delete the merged local branch. This chat is the only one that sees the merge, so close the mission here:
   - **Closed issues:** list the ones the PR closes with `gh pr view <n> --json closingIssuesReferences --jq '.closingIssuesReferences[].url'` (it includes those in another repository) and check each one with `gh issue view <url> --json state`. GitHub closes issues after the merge, asynchronously: an issue still `OPEN`, read again every 10 s until it closes, for at most 2 min; if it persists, report it to the user, without closing it by hand.
   - **Issues cited but not closed:** read the body (`gh pr view <n> --json body`) and check the state of every issue it cites outside that list. An empty list, or a cited issue still `OPEN`, is a warning to the user, who decides whether the PR should have closed it: no closing keyword reached it (in another repository, only `Closes owner/repo#N` closes it). That was the case of kit#51, which closed only kit#50 and cited automation-template#15 only as a link.
   - **A fact that came up in the merge** (e.g. a flaky check, repeated `BEHIND`) becomes an issue and goes into the next mission's summary, not into a new PR.
   - Say the mission is over and the next chat can start.
6. Deadline reached or failure, with the user possibly away: also notify with `PushNotification`, if the tool exists.
7. Interrupted wait (notified as stopped, or the session reopened): first read the real state (`gh pr view <n> --json state,autoMergeRequest,mergeStateStatus`), tell the user and only then resume from the right step; never assume the wait is still running.

**Limit:** background tasks die with the session, and nothing wakes a closed session. Auto-merge keeps going on GitHub, but no one reports. To resume through step 7, send an ordinary message in this chat, or `/clear` and `/mission:ship-pr <n>` as the first message of the fresh chat: typed again in a chat that already has a conversation, the command is blocked by the plugin.
