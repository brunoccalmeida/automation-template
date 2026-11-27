#!/bin/sh
# Fail when a commit message would close an issue the pull request does not
# declare it closes (issue #94).
#
# Usage: sh check-closing-keywords.sh <message-file>
# The file holds the message the squash writes to the main branch: the PR
# title, a blank line and the PR body.
#
# GitHub closes the issue named after a closing keyword in a commit message
# on the default branch. A commit message is plain text, so backticks do not
# protect a quoted keyword, and a line break between the keyword and the
# reference does not stop the match: both closed issues by mistake here
# (#82 from the squash of #83, #91 from the squash of #93). The issues the PR
# closes are the ones on a line that holds only keywords and references, as
# the first line of the PR template does (`Closes #N`); every other closing
# keyword must name one of them.
#
# Exit 0: no stray keyword. Exit 1: one or more, each named with its line on
# stderr. Exit 2: unusable input. POSIX sh and awk only, because the plugin
# runs in projects of any stack, and on Windows through Git Bash.

say() {
  printf 'check-closing-keywords: %s\n' "$*" >&2
}

if [ "$#" -ne 1 ]; then
  say "usage: sh check-closing-keywords.sh <message-file>"
  exit 2
fi
if [ ! -f "$1" ] || [ ! -r "$1" ]; then
  say "cannot read the message file: $1"
  exit 2
fi

# C locale: tolower keeps the byte length, so a position found in the
# lowercased text holds in the original too
LC_ALL=C awk '
{
  sub(/\r$/, "")
  lines[NR] = $0
  text = (NR == 1) ? $0 : text "\n" $0
}
END {
  keyword = "(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)"
  # What may sit between a keyword and its reference: spaces and line breaks,
  # a colon (documented) and markdown marks, which are text in a commit
  ref = "(https?://github\\.com/[a-z0-9_.-]+/[a-z0-9_.-]+/issues/[0-9]+|[a-z0-9_.-]+/[a-z0-9_.-]+#[0-9]+|#[0-9]+)"
  gap = "[[:space:]`*_:]*"
  declaration = "^" keyword "[[:space:]:]*" ref "([[:space:]]*,[[:space:]]*(" keyword "[[:space:]:]*)?" ref ")*[[:space:]]*$"

  for (i = 1; i <= NR; i++) {
    rest = tolower(lines[i])
    if (rest !~ declaration) continue
    while (match(rest, ref)) {
      declared[substr(rest, RSTART, RLENGTH)] = 1
      rest = substr(rest, RSTART + RLENGTH)
    }
  }

  lower = tolower(text)
  offset = 0
  found = 0
  while (match(substr(lower, offset + 1), "(^|[^a-z0-9])" keyword gap ref)) {
    start = offset + RSTART
    length_ = RLENGTH
    offset = start + length_ - 1
    if (substr(lower, start, 1) !~ /[a-z]/) { start++; length_-- }
    hit = substr(lower, start, length_)
    sub("^" keyword gap, "", hit)
    if (hit in declared) continue
    before = substr(text, 1, start - 1)
    line = 1 + gsub(/\n/, "\n", before)
    quote = substr(text, start, length_)
    gsub(/\n/, " ", quote)
    reference = substr(text, start + length_ - length(hit), length(hit))
    printf "check-closing-keywords: line %d: \"%s\" closes %s when this message reaches the default branch, but no line of its own declares it (Closes %s, as the first line of the PR body). Reword it without a closing keyword, for example \"close the issue by hand\".\n", line, quote, reference, reference
    found = 1
  }
  exit found
}
' "$1" >&2
