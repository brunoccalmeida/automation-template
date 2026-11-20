# Evals

Eval suites for the plugin, run with [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals.md). They measure which model each routed piece needs (see [Model routing](../README.md#model-routing)); they are not a CI gate, because every run is a paid `claude` session.

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
