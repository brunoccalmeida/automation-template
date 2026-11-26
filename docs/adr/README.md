# Architecture Decision Records

Each file records one decision that is expensive to reverse: the context, the decision and its consequences, in the format proposed by Michael Nygard ([Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)).

An accepted record is never rewritten. A decision that changes gets a new record that supersedes the old one, so the history of *why* survives.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-use-copier.md) | Distribute the template with Copier | Accepted; partly superseded by 0004 |
| [0002](0002-core-plus-packs-split-by-tool.md) | One repository: a shared core plus packs split by tool | Accepted |
| [0003](0003-stack-agnostic-core-defines-contracts.md) | The core is stack-agnostic and defines contracts that packs implement | Accepted; partly superseded by 0004 |
| [0004](0004-partial-resumption-with-a-plugin.md) | Partial resumption: distribute the shared harness as a Claude Code plugin | Accepted; partly superseded by 0006 |
| [0005](0005-keep-seen-failing-as-the-core-testing-principle.md) | Keep "every test was seen failing" as the core's only testing principle | Accepted |
| [0006](0006-resume-copier-for-the-core-and-the-ts-pack.md) | Resume Copier for the core and the `ts-playwright` pack | Accepted |
| [0007](0007-test-the-template-by-generating-the-core.md) | Test the template by generating the core, with a hash-locked Copier | Accepted |
| [0008](0008-core-rules-and-documents-in-the-generated-project.md) | Core rules and documents in the generated project: ownership, line endings and retries | Accepted |
| [0009](0009-contracts-as-copier-answers-and-a-shared-harness.md) | Contracts as Copier answers, the marketplace in the core, and this repository on its own core | Accepted |
| [0010](0010-claude-code-enforcement-in-the-core.md) | Claude Code enforcement in the core: deny rules and a SessionStart hook | Accepted |
| [0011](0011-ci-enforcement-as-a-reusable-core-workflow.md) | CI enforcement in the core: a reusable workflow with encoding, secret scan and workflow audit | Accepted |
