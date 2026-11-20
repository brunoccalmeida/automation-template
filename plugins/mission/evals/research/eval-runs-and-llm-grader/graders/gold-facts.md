---
type: llm
---
The question was: "In `claude plugin eval`, how many runs does a case get by default, and when does an `llm` grader pass?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/plugin-evals.md):

> | `runs` | `3` | Runs per arm, 1 to 50. `--runs` overrides it |
> | `llm` | `criteria`, `focus` | A judge model votes PASS on the rubric in at least two of three votes. |

PASS if the response states every one of these facts, in any wording or language: (1) 3 runs by default (per arm); (2) an `llm` grader passes when the judge votes PASS in at least two of three votes.
FAIL if any of these facts is missing, or stated only as a guess.
