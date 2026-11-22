#!/bin/sh
# Workspace: the repository before PR #33, with this case's mission.diff (the planted defect) applied.
set -eu
here=$(dirname "$0")
exec sh "$here/../build-workspace.sh" e316a24e9826a2d35a76938bee7237617abc2d81 "$here/../fixtures/pr-33/issue.md" "$here/mission.diff"
