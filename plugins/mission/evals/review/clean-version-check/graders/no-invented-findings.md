---
type: llm
---
The response is a code review of a pull request ("mission"), done against its issue, the project rules and `REVIEW.md`. The mission was merged; nothing was planted in it. Its real defects, each checked against the code after earlier runs of this suite, are listed below; this text is hidden from the reviewer.

Known real defects (a reviewer may report any of them, in any wording or language):

1. The comment of the `test-plugins` job in `.github/workflows/ci.yml` still describes the tests as running "on synthetic transcripts"; the new tests use a synthetic cache entry and a local git repository and need `git` on the runner.
2. `skipIf(SH is None or GIT is None)` skips the whole new test class when `sh` or `git` is missing, so `test` and the CI job pass without testing the hook: an error passing silently.
3. Some new tests were never seen failing for the right reason: the RED (`KeyError: 'SessionStart'`) only shows the hook was not declared, and the recorded mutations cover only some tests; for example the tests for a manifest without `repository`, for a plugin that is not a cached install, and for the `startup`-only matcher have no mutation.

PASS if every finding the response presents as a problem to fix matches one of the known defects, or the response reports no finding. Remarks the response explicitly marks as optional or as needing no change do not count as findings.
FAIL if at least one finding presented as a problem matches none of the known defects. A new finding is not necessarily false: if it holds when checked, it is added to this list (see "Decision rule" in `evals/README.md`).
