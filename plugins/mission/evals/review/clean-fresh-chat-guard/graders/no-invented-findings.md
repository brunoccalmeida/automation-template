---
type: llm
---
The response is a code review of a pull request ("mission"), done against its issue, the project rules and `REVIEW.md`. The mission was merged; nothing was planted in it. Its real defects, each checked against the code after earlier runs of this suite, are listed below; this text is hidden from the reviewer.

Known real defects (a reviewer may report any of them, in any wording or language):

1. `REVIEW.md`, "Não reporte", still says the repository has no test suite beyond the plugin validation, although the mission adds `tests/` and the `test-plugins` job: future reviews skip test isolation.
2. Step 7 of `close-mission` (after the merge: confirm the issues closed, say the mission ended, turn merge facts into issues) is left without anyone to run it: step 6 now sends `ship-pr` to a fresh chat, and `ship-pr` does none of it.
3. The hook tests are skipped (`skipIf(SH is None)`) when `sh` is not on `PATH`, so the `test` contract prints OK without testing the hook: an error passing silently.
4. The new `test-plugins` CI job was never seen failing in CI itself (`REVIEW.md`: a new gate is seen rejecting); the RED was seen only locally and in a container.
5. The criterion "`/mission:ship-pr` after `/clear` runs normally" is not proven end to end after a real `/clear` (only a new `-p` session and synthetic transcripts), so it is not shown that the hook receives the new transcript path.
6. The session summary says the guard is "em uso nos quatro projetos" while its own "Pendência nos projetos" row says three projects still have to update to receive it.
7. The `*)` branch of `require-fresh-chat.sh` (grep fails to read the transcript) has no test.
8. `ship-pr` was not updated and now contradicts the hook: its step 7 and its "Limite" say an interrupted wait resumes from "the next message or chat", but typing `/mission:ship-pr` again in a chat that already has conversation is blocked; only the plugin README says to `/clear` first.
9. Several new tests were never seen failing on their own assertion: the RED (`FileNotFoundError` for `hooks.json`) stops every test before its assertion, and the three recorded mutations cover only the unanchored matcher, the quoted assistant text and the JSON escapes; `test_blocks_ship_pr_in_a_chat_with_prior_conversation`, `test_allows_ship_pr_as_the_first_message_after_clear`, the three `test_fails_open_*` tests and `test_matches_ship_pr` have no mutation.

PASS if every finding the response presents as a problem to fix matches one of the known defects, or the response reports no finding. Remarks the response explicitly marks as optional or as needing no change do not count as findings.
FAIL if at least one finding presented as a problem matches none of the known defects. A new finding is not necessarily false: if it holds when checked, it is added to this list (see "Decision rule" in `evals/README.md`).
