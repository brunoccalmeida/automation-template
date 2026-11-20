---
type: llm
---
The question was: "In Claude Code, what is the default effort level of Opus 5.5 and of Sonnet 5.5, and which Claude Code version is needed to use Haiku 5.5?"

Reference, quoted from the official documentation (https://code.claude.com/docs/en/model-config.md):

> The model's default effort: Fable 5.2, Opus 5.5, Sonnet 5.5, and Haiku 5.5 default to `medium`
> Use v2.1.293 or later with Haiku 5.5.

PASS if the response states every one of these facts, in any wording or language: (1) Opus 5.5 defaults to `medium`; (2) Sonnet 5.5 defaults to `medium`; (3) Haiku 5.5 needs Claude Code v2.1.293 or later.
FAIL if any of these facts is missing, or stated only as a guess.
