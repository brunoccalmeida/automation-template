# Architecture Decision Records

Each file records one decision that is expensive to reverse: the context, the decision and its consequences, in the format proposed by Michael Nygard ([Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)).

An accepted record is never rewritten. A decision that changes gets a new record that supersedes the old one, so the history of *why* survives.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-use-copier.md) | Distribute the template with Copier | Accepted |
| [0002](0002-core-plus-packs-split-by-tool.md) | One repository: a shared core plus packs split by tool | Accepted |
| [0003](0003-stack-agnostic-core-defines-contracts.md) | The core is stack-agnostic and defines contracts that packs implement | Accepted |
