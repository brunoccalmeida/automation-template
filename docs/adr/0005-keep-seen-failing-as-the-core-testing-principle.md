# 5. Keep "every test was seen failing" as the core's only testing principle

- **Status:** Accepted
- **Date:** 2026-11-25

## Context

The core rules ([`core.md`](../../.claude/rules/core.md)) have one testing principle, "Every test was seen failing": test first (red, green, refactor) and, for a test that passes from the start, a manual mutation that proves it can fail. They are backed by "Never change a test just to make it pass". Issue #50 asked whether test-driven development (TDD) on its own is still what current practice recommends, or whether established complementary principles belong next to it.

The criterion used to decide was set before the research: a practice goes into the core only if it is **stack-agnostic** ([ADR 0003](0003-stack-agnostic-core-defines-contracts.md)) and **catches a failure that "seen failing" does not**. Anything else is recorded for the pack or mission it belongs to. The reason is that `core.md` is copied unchanged into every project, so each line there costs context in every chat and one propagation mission per repository.

## Evidence

Sourced facts. Items marked *(abstract)* were read through a search summary or the paper's abstract, not the full text.

| Practice | What the sources say | Catches what "seen failing" misses? | Stack-agnostic? |
| --- | --- | --- | --- |
| **TDD** (the current rule) | DORA recommends having developers "practice test-driven development by writing unit tests before writing production code" ([DORA, Test automation](https://dora.dev/capabilities/test-automation/)). Kent Beck's [Canon TDD](https://newsletter.kentbeck.com/p/canon-tdd) (2023) defines the cycle (test list, one runnable test, make it pass, optionally refactor) and lists the mistakes "delete assertions so the test pretends to pass" and "copying actual, computed values & pasting them into the expected values". Claude Code's [best practices](https://code.claude.com/docs/en/best-practices.md) ask for "a failing test it has to turn green". The empirical evidence is weaker: a meta-analysis found a "small effect in favor of TDD on functional quality", with inconclusive results on productivity (Rafique & Mišić, IEEE TSE 2013, *(abstract)*), and a study of professionals found no important effect from the test-first order itself ([Fucci et al. 2016](https://arxiv.org/abs/1611.05994), *(abstract)*). | — | Yes |
| **Automated mutation testing** | Google runs it on about 30% of diffs, during code review and on changed code only. The findings are not blocking unless a reviewer marks them mandatory, and the paper says computing an absolute mutation score is "infeasibly expensive" ([Practical Mutation Testing at Scale](https://ar5iv.labs.arxiv.org/html/2102.11378); [State of Mutation Testing at Google](https://research.google/pubs/state-of-mutation-testing-at-google/)). Equivalent mutants "cannot generally be detected automatically" (same paper). PIT and Stryker offer a score threshold that fails the build, off by default in Stryker (`break: null`). PIT warns: "Careful thought must therefore be given when selecting a threshold" ([PIT Maven](https://pitest.org/quickstart/maven/), [Stryker configuration](https://stryker-mutator.io/docs/stryker-js/configuration/)). | Partly: it mutates every changed line systematically, not only tests that passed from the start | No: one tool per language; the sources cover unit tests of production code, not E2E suites |
| **Property-based testing** | Generates the examples and shrinks a failure to a minimal case; fast-check says it "should not be viewed as a substitute" for example-based tests ([fast-check, Why property-based](https://fast-check.dev/docs/introduction/why-property-based/); [Hypothesis](https://hypothesis.works/articles/what-is-hypothesis/)). | Yes, for code with clear invariants | No: a technique for specific code, not a general principle |
| **Test pyramid / trophy / honeycomb** | Only the pyramid claims to hold "regardless of" architecture, and its author calls it "overly simplistic" from a modern point of view ([Fowler, Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)). Google gives 80/15/5 as "a very rough guideline" ([Software Engineering at Google, ch. 11](https://abseil.io/resources/swe-book/html/ch11.html)). The trophy ([Kent C. Dodds](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)) and the honeycomb ([Spotify](https://engineering.atspotify.com/2018/01/testing-of-microservices/)) are practitioner opinion. No source declares a consensus. | No: it shapes a suite, it does not validate a test | Yes, but see judgment |
| **Contract testing (Pact)** | Fits when you "control the development of both the consumer and the provider". It does not fit public APIs, a provider that does not also use Pact, or "general purpose mocking or stubbing tool for browser driven tests" ([Pact, What is it good for](https://docs.pact.io/getting_started/what_is_pact_good_for)). | Yes, integration drift, but only with control of both sides | No |
| **BDD** | Adds discovery and a shared language through concrete examples; it "does not replace your existing agile process, it enhances it" ([Cucumber, BDD](https://cucumber.io/docs/bdd/)). The page says nothing about when BDD is not needed. | No: it is a requirements practice | No: it is a pack's choice (`python-behave-selenium`) |
| **Static types** | Flow or TypeScript would have caught about 15% of the public JavaScript bugs studied (Gao et al., ICSE 2017, *(abstract)*); a later study found the evidence that TypeScript apps have better quality "insufficient" ([Bogner & Merkel 2022](https://arxiv.org/abs/2203.11115)). No primary source found treats types as a complement to a testing practice. | Partly, a class of bugs | No: it depends on the language; the `check` contract already covers it |
| **Isolation and flakiness** | "Each test should be completely isolated from another test and should run independently" ([Playwright, Best practices](https://playwright.dev/docs/best-practices)). "As you approach 1% flakiness, the tests begin to lose value" ([Software Engineering at Google, ch. 11](https://abseil.io/resources/swe-book/html/ch11.html)). | **Yes**: a test can be seen failing once and still pass or fail by order or chance | Yes as a principle; the official source read is one stack's |

## Decision

**The core's testing principle stays as it is. No practice is added and none replaces it.**

Judgment, applying the criterion above:

1. **TDD is still the recommended practice:** DORA and Canon TDD back it. The weak empirical evidence on test-first order does not weaken the rule, because the rule is about something else: a test that never failed proves nothing, whatever order it was written in. Canon TDD's listed mistakes are already in "Never change a test just to make it pass".
2. **Automated mutation testing is a pack option, not a gate.** Google, the largest documented user, runs it on changed code, does not block on it, and found no actionable global score. A score threshold in the core would go against that evidence, and the tool depends on the stack. The manual mutation in the current rule stays the stack-agnostic version.
3. **Property-based testing, contract testing, BDD and static types are pack choices.** Each depends on the stack or the kind of code. Contract testing also fails Pact's own fit criteria for the projects this template serves: they automate tests of systems they usually do not own, often through the browser.
4. **The test shape (pyramid and its variants) stays out.** No consensus is declared. A test automation project is usually the E2E or API layer of someone else's system, so a ratio rule would be misleading there.
5. **Isolation and flakiness pass the criterion, but they belong to Mission 2a ([#3](https://github.com/brunoccalmeida/automation-template/issues/3)).** That mission already plans the flaky-test policy and the CI retry decision. The source projects diverge on retries ([INVENTORY.md](../INVENTORY.md), §8: the kit retries, the UAT refuses), and "evidence first" says not to settle a divergence before there is a tie-breaker. The core already forbids a retry or a longer timeout that hides a failure. The sources above are the starting point for #3.

## Alternatives

- **Add automated mutation testing as a CI gate with a score threshold:** rejected by the Google evidence (non-blocking, changed code only, no actionable global score) and because the core names no stack.
- **Add a test-shape rule (pyramid ratios):** rejected; there is no consensus, and the ratios do not fit a project that is itself the top layer.
- **Add an isolation rule to the core now:** deferred to #3, which decides it together with the retry policy instead of in two places.

## Consequences

- `core.md` does not change, so nothing has to be propagated to the kit, nextjs and the UAT.
- Mission 2a (#3) starts its flaky-test policy from the isolation and flakiness sources above.
- The packs (#7, #8) may add mutation testing, property-based testing or contract testing as options, each justified in its own pack.
- Reopen when a new fact appears: a primary source that makes mutation testing a blocking gate in current practice, or a test-shape model that reaches declared consensus.
