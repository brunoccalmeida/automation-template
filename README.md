# automation-template

A [Copier](https://copier.readthedocs.io/) template for test automation projects: an AI-assisted delivery harness (rules, skills, reviewer agent, CI gates) shared by every project, plus one pack per test stack.

It is extracted from two existing projects, [uat-automation-framework](https://github.com/brunoccalmeida/uat-automation-framework) (Python, Behave, Selenium) and [playwright-qa-starter-kit](https://github.com/brunoccalmeida/playwright-qa-starter-kit) (Playwright, TypeScript), which had grown the same harness by copy and paste.

> 🚧 Work in progress: the template is being built mission by mission.

## Design

- [Architecture Decision Records](docs/adr/): why Copier, why a core plus packs split by tool, and why the core only defines contracts that each pack implements.
- [Inventory](docs/INVENTORY.md) (Portuguese): every piece of the two source projects, classified as core, pack or application-specific, with the better of the two implementations.

## License

MIT, see [LICENSE](LICENSE).
