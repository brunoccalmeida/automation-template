#!/bin/sh
# SessionStart hook (matcher "startup"): warn the user when the installed
# plugin is not the published one (issue #32). Updates stay manual
# (autoUpdate: false); this makes the drift visible.
#
# Installed version: a cached marketplace install lives in a directory named
# after its version, and with no "version" in the manifest that is the
# commit SHA of the marketplace, shortened to 12 characters (Plugin loading
# reference, "How Claude Code computes the version"). ${CLAUDE_PLUGIN_ROOT}
# points at that directory.
#
# Published version: HEAD of the repository named by "repository" in the
# manifest, read with git ls-remote. It assumes the plugin is hosted in the
# marketplace repository it names, as this one is. A merge that touches only
# documentation also moves HEAD, and then an update really does install a
# new version, so the warning is accurate, not noise.
#
# The warning goes out as systemMessage, shown to the user only: plain stdout
# and additionalContext would enter Claude's context on every session
# (Hooks reference, SessionStart). It guards visibility, not safety:
# anything unexpected prints nothing and says why on stderr. POSIX sh, grep,
# sed and git only, because the plugin runs in projects of any stack, and on
# Windows through Git Bash.

say() {
  printf 'check-plugin-version: %s\n' "$*" >&2
}

root=${CLAUDE_PLUGIN_ROOT:-}
if [ -z "$root" ]; then
  say "CLAUDE_PLUGIN_ROOT is not set; skipping"
  exit 0
fi

installed=$(basename "$root")
if ! printf '%s\n' "$installed" | grep -qxE '[0-9a-f]{12}'; then
  # --plugin-dir and local marketplaces load the source in place
  say "plugin root is not a cached install named after a commit: $root; skipping"
  exit 0
fi

# "repository" from the manifest, JSON-unescaped. No jq: it is not on every
# machine.
manifest="$root/.claude-plugin/plugin.json"
repository=$(tr -d '\r\n' <"$manifest" 2>/dev/null |
  sed -nE 's/.*"repository"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p' |
  sed -e 's/\\"/"/g' -e 's/\\\//\//g' -e 's/\\\\/\\/g')
if [ -z "$repository" ]; then
  say "no repository in $manifest; skipping"
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  say "git not found; skipping"
  exit 0
fi

# GIT_TERMINAL_PROMPT=0: a repository that asks for credentials fails at once
# instead of waiting for input nobody can type. git's own error goes to stderr.
published=$(GIT_TERMINAL_PROMPT=0 git ls-remote "$repository" HEAD | tr -d '\r' |
  sed -nE 's/^([0-9a-f]{40})[[:space:]]+HEAD$/\1/p' | cut -c1-12)
if [ -z "$published" ]; then
  say "could not read HEAD of $repository; skipping"
  exit 0
fi

if [ "$installed" = "$published" ]; then
  exit 0
fi

printf '{"systemMessage":"%s"}\n' "Plugin mission desatualizado: instalado $installed, publicado $published. Para atualizar, rode no shell claude plugin update mission@brunoccalmeida-plugins. O 'Restart to apply changes' que ele mostra no fim quer dizer: rode /reload-plugins nesta sessão ou abra uma sessão nova; até lá, a sessão aberta segue com a versão antiga."
