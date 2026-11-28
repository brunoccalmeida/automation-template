---
paths:
  - ".github/rulesets/protect-main.json"
  - ".github/scripts/apply-github-settings.sh"
---

# Ruleset as code

[`.github/rulesets/protect-main.json`](../../.github/rulesets/protect-main.json) describes the active ruleset (id 27584439), but editing the file does not change GitHub. Changed the file: apply it with `sh .github/scripts/apply-github-settings.sh` (the script `/new-project` runs in a generated project; it also reapplies the labels, the merge settings and Dependabot alerts and security updates) and check with `gh api repos/{owner}/{repo}/rulesets/27584439`; changed it in the web interface: bring the change into the file.
