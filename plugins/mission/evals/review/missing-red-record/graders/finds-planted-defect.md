---
type: llm
---
The response is a code review of a pull request ("mission"), done against its issue, the project rules and `REVIEW.md`. The mission was planted with exactly one defect, described below; this text is hidden from the reviewer.

Planted defect: the mission adds tests (`tests/test_require_fresh_chat.py`) and a CI job, but the commit message has no record of how any test or gate was seen failing (no RED, no mutation); the "How RED was seen" section was removed. The project rules require the commit to record how the RED was seen.

PASS if the response reports this defect as a finding, in any wording or language: the commit message (or mission record) does not say how the new tests were seen failing (no RED or mutation recorded).
FAIL if the response does not report it, mentions it only as acceptable, or reports it only as a question without saying it is a problem.
Ignore every other finding, right or wrong: another grader and the clean cases measure false positives.
