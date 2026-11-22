---
type: llm
---
The response is a code review of a pull request ("mission"), done against its issue, the project rules and `REVIEW.md`. The mission was planted with exactly one defect, described below; this text is hidden from the reviewer.

Planted defect: step 6 of `plugins/mission/skills/close-mission/SKILL.md` now says "Rode `npm test` uma última vez". The plugin must name contracts (`test`), never a command or tool; `REVIEW.md` lists `npm` as an example of a stack term the plugin must not cite.

PASS if the response reports this defect as a finding, in any wording or language: the `close-mission` skill names a concrete command or tool (`npm test`/`npm`) instead of the `test` contract.
FAIL if the response does not report it, mentions it only as acceptable, or reports it only as a question without saying it is a problem.
Ignore every other finding, right or wrong: another grader and the clean cases measure false positives.
