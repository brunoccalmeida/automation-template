#!/bin/sh
# UserPromptExpansion hook for /mission:ship-pr: block it unless it is the
# first message of a fresh chat (after /clear), so the merge phase does not
# re-send the context of the chat that implemented the mission on every tool
# call (issue #30).
#
# A chat has prior conversation when its transcript holds an assistant
# record. The transcript may lag the current turn (Hooks reference, common
# input fields), but earlier turns are already written, and those are the
# ones that matter here.
#
# It guards cost, not safety: anything unexpected allows the command and
# says why on stderr. POSIX sh, grep and sed only, because the plugin runs in
# projects of any stack, and on Windows through Git Bash.

say() {
  printf 'require-fresh-chat: %s\n' "$*" >&2
}

input=$(cat)

# transcript_path from the hook input, JSON-unescaped. No jq: it is not on
# every machine. The pattern matches the real key only: inside a JSON string
# the quotes around a quoted key are escaped.
transcript=$(printf '%s' "$input" | tr -d '\r\n' |
  sed -nE 's/.*"transcript_path"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' |
  sed -e 's/\\"/"/g' -e 's/\\\//\//g' -e 's/\\\\/\\/g')

if [ -z "$transcript" ]; then
  say "no transcript_path in the hook input; allowing"
  exit 0
fi
if [ ! -f "$transcript" ] || [ ! -r "$transcript" ]; then
  say "transcript not readable as a file: $transcript; allowing"
  exit 0
fi

# Compact JSON, as Claude Code writes it. Quoted text inside a message is
# escaped (\"type\":\"assistant\"), so it never matches.
grep -q '"type":"assistant"' "$transcript"
case $? in
  0) ;;
  1) exit 0 ;;
  *)
    say "could not read the transcript: $transcript; allowing"
    exit 0
    ;;
esac

printf '%s\n' '{"decision":"block","reason":"/mission:ship-pr only runs as the first message of a fresh chat: this chat already has a conversation, and every tool call while waiting for the merge would resend all of that context. Run /clear and then /mission:ship-pr <n> again; the PR and the session summary hold everything the skill needs."}'
