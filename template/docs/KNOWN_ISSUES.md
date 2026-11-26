# Known issues

Defects in the application under test that this test suite found and that are still open.

**How they are tracked:** each entry has a test that asserts the **correct** behaviour, marked with the runner's expected-failure mechanism and linked to its entry here. While the defect exists, the test fails as expected and the run stays green. Once the defect is fixed, the test starts passing, the run fails, and that signals that the marker must be removed. The suite keeps documenting the defect and detects its fix, instead of hiding it behind a skipped test.

**Before marking a test:** confirm that it fails for the reason of the defect, not for another one. An expected failure accepts any failure, so a test broken for a different reason would pass unnoticed.

Entries are numbered in the order they were found and never renumbered. A fixed entry is deleted together with its marker, and the pull request that does it names the entry.

No known issues yet. Each entry follows this shape:

```markdown
## KI-1: short description of the defect

- **Where:** the part of the application where it shows
- **Expected:** the correct behaviour, with its source (specification, documentation, consistency with a similar case)
- **Actual:** what happens, with the exact status, message or value
- **Impact:** who is affected and how
- **Test:** the test that asserts the correct behaviour, as a link
```
