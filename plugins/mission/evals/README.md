# Evals

Eval suites for the plugin, run with [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals.md). They measure which model each routed piece needs (see [Model routing](../README.md#model-routing)); they are not a CI gate, because every run is a paid `claude` session.

## `review/`: whether the reviewer finds what it should

The `reviewer` agent is the last gate before a pull request, and until this suite it had never been seen rejecting anything. Each case is a real merged mission of this repository, reviewed again: some with **one planted defect** that the reviewer's checklist or [`REVIEW.md`](../../../REVIEW.md) covers, some **clean**, to count false positives.

| Case | Base | Planted defect | Covered by |
| --- | --- | --- | --- |
| `missing-readme-section` | #31 | The plugin README changes are gone, although a new hook needs `sh` | `REVIEW.md`: a plugin change reaches the projects |
| `stack-term-in-skill` | #31 | `close-mission` says "Rode `npm test`" | `REVIEW.md`: the plugin names contracts, not tools |
| `missing-red-record` | #31 | The commit message lost its "How RED was seen" section | Checklist item 3: RED recorded |
| `fixed-time-wait` | #33 | A test helper sleeps 2 s and reads `poll()` instead of waiting for the hook to exit | Checklist item 4: wait for the final state |
| `clean-fresh-chat-guard` | #31 | None planted; 8 known real defects | Grader's list |
| `clean-version-check` | #33 | None planted; 3 known real defects | Grader's list |

The clean cases were meant to have nothing to report, and the first baseline proved them wrong: the reviewer reported findings in all 6 runs, and checked against the code almost all of them held. #31 and #33 were merged with defects their own reviews let through, the first recorded false negatives ([#39](https://github.com/brunoccalmeida/automation-template/issues/39), label `reviewer-miss`). So a clean case's grader lists the merged mission's **known real defects**, and `no-invented-findings` fails only on a finding outside that list; the one finding that did not hold came from the fixture itself (a reference to the "Reviewer findings" section this suite strips), and the fixture was fixed.

The issue suggested a CI job missing from `ci-passed`'s `needs` as a defect; it was left out because a CI step of this repository already rejects it, and the reviewer is told to ignore what a gate enforces: the key would have punished it for obeying.

| Grader | Type | Cases | Passes when |
| --- | --- | --- | --- |
| `dispatches-reviewer` | `tool_used` | all | The `Agent` tool was called with `mission:reviewer` |
| `finds-planted-defect` | `llm` | planted | The answer reports the planted defect, described only in the grader |
| `no-invented-findings` | `llm` | clean | Every finding the answer reports is in the case's list of known real defects |

### How a case is built

Each run starts in an empty directory and loads no `CLAUDE.md` ([How runs are isolated](https://code.claude.com/docs/en/plugin-evals.md#how-runs-are-isolated)), so each case seeds it with a `scaffold_script` ([Seed the workspace](https://code.claude.com/docs/en/plugin-evals.md#seed-the-workspace-or-conversation)). [`build-workspace.sh`](review/build-workspace.sh) extracts this repository at the commit the mission branched from (`git archive`) and applies the case's `mission.diff`, so the reviewer finds the surrounding code and `REVIEW.md`; the issue text and the diff go to `.scratchpad/`, as `close-mission` hands them over. Because no `CLAUDE.md` loads, the orchestrator tells the reviewer to read it and its imports first.

- **`mission.diff`** is the mission's commit message followed by `git diff --stat` and `git diff` against the base, the format `close-mission` hands the reviewer. The message keeps the record up to its "Reviewer findings" section, which did not exist when the reviewer ran. Clean cases use [`fixtures/pr-<n>/`](review/fixtures/); a planted case keeps its own copy, made by changing the merged files in a worktree and diffing again, so it always applies: `diff fixtures/pr-31/mission.diff stack-term-in-skill/mission.diff` shows the plant.
- **The script needs git and this repository**, which the docs do not promise: it finds itself through `$(dirname "$0")`, checked on native Windows, and fails the run if an input is missing or the patch does not apply.
- **The run directory sits inside a git repository** (the eval's temporary home has a `.git`), and from a subdirectory of a repository `git apply` skips every path outside it and still exits 0. The first baseline reviewed the code before the mission because of this, and the reviewer said so. The script sets `GIT_CEILING_DIRECTORIES` and then proves, without git, that every file in the diff holds its last added line; a mutant without the ceiling fails there.
- **The suite needs `--scaffold`.** Without it the workspace is empty and every review is of nothing.

### Arms and command

Same method as `research/`: orchestrator (`--model haiku`) and judge (`--judge-model opus`) pinned; the reviewer's model comes from its frontmatter. An arm is a **git worktree** of this repository whose `reviewer.md` differs, not a loose copy, because `git archive` needs the repository:

```sh
git worktree add --detach "$ARM" HEAD   # then edit $ARM/plugins/mission/agents/reviewer.md
cd "$ARM/plugins"
claude plugin eval ./mission --eval-dir evals --tag reviewer --runs 3 \
  --ablation none --model haiku --judge-model opus --scaffold \
  --threshold 0 --no-publish --trust-plugin --json "$ARM.json"
```

No shell is granted (`Agent`, `Read`, `Grep`, `Glob`), so it runs on native Windows. **Check `aggregates.casesTotal` is 6:** a case that fails to load (invalid YAML frontmatter, for example) is listed as `Couldn't load` and the command still exits 0 with a score of 0 over zero cases. Likewise `--case` takes **one** glob: `--case 'a*' 'b*'` silently runs only `a*`; run one command per glob.

### Decision rule for a change to the reviewer (written before the runs)

1. Before and after, 3 runs per case, same pinned orchestrator and judge.
2. A change is adopted only if `finds-planted-defect` and `no-invented-findings` pass rates are each **not lower** than the baseline's. Cost (`costUsd`) only breaks ties among changes that pass this test.
3. A run that ends in error counts as failed.
4. **Every `no-invented-findings` failure, in any arm, is read before scoring.** The known-defect lists came from the baseline reviewer's own runs, so a finding outside them may be a real defect no one listed yet, and scoring it as false would reward agreeing with the baseline model instead of being right (Goodhart). A finding that holds when checked against the code makes the run a pass and joins the case's list; if it is still on the main branch, it goes to a `reviewer-miss` issue. Record each decision here.

### Graders were seen failing (review)

Mutant reviewers on `haiku`, one run per case: one that always answers "Sem achados." failed `finds-planted-defect` on all 4 planted cases; one that reports style, names and wording as problems to fix failed `no-invented-findings` on both clean cases, before and after the known-defect lists. `dispatches-reviewer` failed on a run with `--disallow-tools Agent`. A first "noisy" mutant told to invent findings refused to, so the grader passed it correctly: the mutant has to model a real failure, not ask for a fabrication.

### Baseline (November 2026, Claude Code 2.1.327)

| Reviewer | `finds-planted-defect` | `no-invented-findings` | Cost, 18 runs |
| --- | --- | --- | --- |
| `opus`/`high` | 12/12 | 5/6 | US$ 5.72 (reviewer and orchestrator US$ 5.34, judge US$ 0.38) |

- **Planted defects:** found in every run, at US$ 0.20 to 0.38 a review.
- **The one false positive** (`clean-fresh-chat-guard`, run 2): the reviewer said the Windows evidence was ambiguous because Claude Code "probably" passes the plugin root with backslashes; the mission record shows the end-to-end check ran with the CLI on Windows. The same run found a real defect nobody had listed (`ship-pr` tells an interrupted wait to resume in the same chat, which the hook blocks); it was added to the case and to #39.
- **Runs not counted:** 6 reviews of an unpatched workspace (the `git apply` trap above) and 6 clean reviews graded before the known-defect lists, US$ 4.96 together; the Pro plan's 5-hour limit stopped the first attempt after 6 reviews.
- **Caveat:** in the baseline, the graders of `stack-term-in-skill` and `clean-fresh-chat-guard` were saved as cp1252 instead of UTF-8, so the judge read a few accented words garbled ("N�o reporte"); the files were fixed afterwards and the verdicts did not depend on those words. Item 8 of the `clean-fresh-chat-guard` list was added after the baseline.

## `research/`: which model the `researcher` agent runs on

Five documentation questions about Claude Code. Each answer was fixed before any run, quoted from the official page (one was corrected after the first runs, see [Writing a gold answer](#writing-a-gold-answer)), and lives only in the case's graders, which the agent under test cannot read. Each case has four graders:

| Grader | Type | Passes when |
| --- | --- | --- |
| `dispatches-researcher` | `tool_used` | The `Agent` tool was called with `mission:researcher` |
| `cites-official-source` | `regex` | The answer contains the URL of the page that holds the answer |
| `gold-facts` | `llm` | Every gold fact is stated |
| `no-wrong-facts` | `llm` | No claim contradicts the quoted reference |

### Method

Only the researcher's model varies. The main session in each case is an orchestrator told to dispatch `mission:researcher`, pass no `model` parameter (it would win over the frontmatter, see [Choose a model](https://code.claude.com/docs/en/sub-agents.md#choose-a-model)) and relay the answer. The orchestrator model (`--model haiku`) and the judge (`--judge-model opus`) are pinned, as the docs advise for comparable scores. `claude plugin eval` has no option to vary a subagent's model, so each arm is a copy of the plugin whose `researcher.md` differs only in its `model:` line:

```sh
# one copy per arm, e.g. $ARM/mission with "model: sonnet"
claude plugin eval "$ARM/mission" --eval-dir evals --tag researcher --runs 3 \
  --ablation none --model haiku --judge-model opus \
  --allow-tools "WebFetch(domain:code.claude.com)" WebSearch \
  --threshold 0 --no-publish --trust-plugin --json "$ARM/result.json"
```

`--ablation none` because the no-plugin arm has no `mission:researcher` to dispatch. The research needs no shell, so the suite runs on native Windows (shell-granting suites need WSL2).

### Decision rule (written before the runs)

1. Arms: Opus and Sonnet, 3 runs per case. Haiku runs only if Sonnet ties Opus.
2. Quality is the suite's `aggregates.overallScore`. A cheaper model is adopted only if its score is **not lower** than Opus's; otherwise the researcher stays on Opus. Cost (`costUsd`) only breaks the choice among models that pass this test.
3. A run that ends in error counts as a failed run, not as a skipped one.

### Graders were seen failing

Before the measurement, a mutant researcher (answers from memory, no sources, one wrong fact) ran the suite once; `gold-facts`, `no-wrong-facts` and `cites-official-source` failed on every case. `dispatches-researcher` failed on a run with `--disallow-tools Agent`.

### Writing a gold answer

Take it from **every** official page that covers the fact, not from the first passage found. The first gold for `plugin-agent-ignored-fields` came from the security note on the subagents page, which names three ignored fields; the plugin components page and the subagents frontmatter table name four (`initialPrompt` too). Both models found the fourth and the grader failed them for being right: the same failure in every run of every arm points at the grader, not at the model.

### Result (November 2026, Claude Code 2.1.327)

| Researcher | Score | Researcher cost, 15 runs |
| --- | --- | --- |
| Opus | 1.000 | US$ 2.14 |
| Sonnet | 1.000 | US$ 0.99 |
| Haiku | 0.983 | US$ 0.31 |

Sonnet ties Opus, so it was adopted; Haiku scored lower, so it was not. The researcher's model is read from the `modelUsage` of the `result` event in each run's trace (kept with `--keep-temp`), which proved every run used the intended model; the per-run `costUsd` minus `judgeCostUsd` equals that event's `total_cost_usd`.
