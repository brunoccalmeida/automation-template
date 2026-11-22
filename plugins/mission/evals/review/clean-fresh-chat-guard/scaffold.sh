#!/bin/sh
# Workspace: the repository before PR #31, with the merged mission diff applied.
set -eu
here=$(dirname "$0")
exec sh "$here/../build-workspace.sh" f845d1b4e969233e42017b463b697c848176fa42 "$here/../fixtures/pr-31/issue.md" "$here/../fixtures/pr-31/mission.diff"
