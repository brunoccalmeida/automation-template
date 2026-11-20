---
type: llm
---
The question was: "In Claude Code, what is the default effort level of Opus 5.5 and of Sonnet 5.5, and which Claude Code version is needed to use Haiku 5.5?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/model-config.md):

> The model's default effort: Fable 5.2, Opus 5.5, Sonnet 5.5, and Haiku 5.5 default to `medium`
> Use v2.1.293 or later with Haiku 5.5.

Judge only whether the response states something false about what the question asks. Ignore missing facts and ignore extra claims that the reference neither confirms nor contradicts.
PASS if no claim in the response contradicts the reference.
FAIL if any claim contradicts the reference, for example: a default of `high` or `xhigh` for Opus 5.5 or Sonnet 5.5, or a version other than v2.1.293 for Haiku 5.5.
