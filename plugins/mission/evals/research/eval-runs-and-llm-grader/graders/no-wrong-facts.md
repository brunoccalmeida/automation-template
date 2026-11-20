---
type: llm
---
The question was: "In `claude plugin eval`, how many runs does a case get by default, and when does an `llm` grader pass?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/plugin-evals.md):

> | `runs` | `3` | Runs per arm, 1 to 50. `--runs` overrides it |
> | `llm` | `criteria`, `focus` | A judge model votes PASS on the rubric in at least two of three votes. |

Judge only whether the response states something false about what the question asks. Ignore missing facts and ignore extra claims that the reference neither confirms nor contradicts.
PASS if no claim in the response contradicts the reference.
FAIL if any claim contradicts the reference, for example: a default other than 3 runs, a pass rule other than two of three votes (such as a single vote, unanimity, or a numeric threshold on the grader).
