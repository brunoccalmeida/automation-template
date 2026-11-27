#!/usr/bin/env python3
"""Validate the plugin marketplace and every plugin it lists.

Runs ``claude plugin validate --json`` on the marketplace root and on each
directory under ``plugins/``, and fails on any error or warning but one: the
missing ``version``, which the plugins omit on purpose so that installs track
commits (docs/adr/0004). This is ``--strict`` with that single exception;
``--strict`` itself rejects the missing version.

The exception matters because a warning can hide a broken component: an agent
or skill whose frontmatter block is missing still loads, with every field
ignored, so the read-only reviewer would get every tool and ``ship-pr`` would
lose ``disable-model-invocation``.

Not checked here: the plugin directory findings (``directory``), which the CLI
itself says do not change the result, and its advice.

Usage: python3 .github/scripts/validate_plugins.py [path-to-claude-cli]
Exit code 0 = valid; 1 = problems found, each printed; 2 = no usable report.
"""

import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

DEFAULT_CLI = "tools/claude-cli/node_modules/.bin/claude"
PLUGINS_DIR = Path("plugins")
# A hung CLI would otherwise run until the job's own timeout
CLI_TIMEOUT_SECONDS = 120


def is_tolerated(warning: dict) -> bool:
    """True only for the missing-version warning, at plugin or entry level."""
    path = warning.get("path") or ""
    message = warning.get("message") or ""
    return (path == "version" or path.endswith("→ version")) and message.startswith(
        "No version specified"
    )


def problems(report: dict) -> Iterator[str]:
    """Every error and every non-tolerated warning in one validation report."""
    sections = [report.get("manifest") or {}, *(report.get("contents") or [])]
    for section in sections:
        where = section.get("file", "?")
        for error in section.get("errors") or []:
            yield f"error   {where}: {error.get('path')}: {error.get('message')}"
        for warning in section.get("warnings") or []:
            if not is_tolerated(warning):
                yield f"warning {where}: {warning.get('path')}: {warning.get('message')}"


def validate(cli: str, target: Path) -> list[str] | None:
    """Problems found in one target, or None when the CLI gave no report."""
    run = subprocess.run(
        [cli, "plugin", "validate", str(target), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=CLI_TIMEOUT_SECONDS,
        check=False,
    )
    try:
        report = json.loads(run.stdout)
    except json.JSONDecodeError:
        print(
            f"no validation report for {target} (exit {run.returncode}):\n"
            f"{run.stdout}{run.stderr}",
            file=sys.stderr,
        )
        return None
    found = list(problems(report))
    if not report.get("success") and not found:
        found.append(f"error   {target}: validation failed with no error listed")
    provides = report.get("provides") or {}
    for kind in ("skills", "agents", "commands", "hooks", "mcpServers"):
        if provides.get(kind):
            print(f"  provides {kind}: {', '.join(map(str, provides[kind]))}")
    return found


def main() -> int:
    # The CLI's messages contain "→"; a Windows console or pipe defaults to
    # a code page without it, and the print would crash instead of report
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    cli = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CLI
    plugins = sorted(p for p in PLUGINS_DIR.iterdir() if p.is_dir())
    if not plugins:
        print(f"no plugin directory under {PLUGINS_DIR}/", file=sys.stderr)
        return 1
    failed = False
    for target in [Path("."), *plugins]:
        print(f"validate {target}")
        found = validate(cli, target)
        if found is None:
            return 2
        for line in found:
            print(f"  {line}")
        failed = failed or bool(found)
    print("FAILED" if failed else "OK: no error and no warning beyond the omitted version")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
