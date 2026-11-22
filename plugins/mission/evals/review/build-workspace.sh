#!/bin/sh
# Builds the workspace of a review case, called by each case's scaffold.sh
# from the empty run directory (the agent's working directory):
#
#   sh build-workspace.sh <base-commit> <issue.md> <mission.diff>
#
# The workspace is this repository at <base-commit>, the commit the mission
# branched from, with <mission.diff> applied, so the reviewer finds the code
# around each change and REVIEW.md as it would in the real repository. The two
# inputs close-mission hands the reviewer go to .scratchpad/, as in a real run.
#
# Fails loudly: a missing file or a patch that does not apply ends the run
# with an error instead of a review of the wrong workspace.
set -eu

base=$1
issue=$2
mission_diff=$3
# The top level, not this directory: run from a subdirectory, git archive
# keeps only that subdirectory's tree.
repository=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)

for file in "$issue" "$mission_diff"; do
  [ -f "$file" ] || { echo "build-workspace: missing input $file" >&2; exit 1; }
done

git -C "$repository" archive "$base" | tar -x -f -
# Outside a repository, git apply works like patch; it ignores the commit
# message that precedes the first "diff --git" line. The eval puts the
# workspace inside a repository (its home directory has a .git), and from a
# subdirectory of a repository git apply skips every path outside it and
# still exits 0. The ceiling keeps git from finding that repository.
GIT_CEILING_DIRECTORIES=$(dirname "$PWD")
export GIT_CEILING_DIRECTORIES
git apply "$mission_diff"

# Proof without git, which has already failed silently once: every file the
# diff creates or changes exists in the workspace and holds the diff's last
# added line for it.
sed -n 's|^+++ b/||p' "$mission_diff" | while IFS= read -r path; do
  last_added=$(awk -v target="+++ b/$path" '
    /^diff --git / { inside = 0 }
    $0 == target   { inside = 1; next }
    inside && /^\+/ { line = substr($0, 2) }
    END { print line }' "$mission_diff")
  [ -f "$path" ] && grep -qF -- "$last_added" "$path" ||
    { echo "build-workspace: $path does not hold the mission diff" >&2; exit 1; }
done

mkdir .scratchpad
cp "$issue" .scratchpad/issue.md
cp "$mission_diff" .scratchpad/mission.diff
