"""Tests for the ts-playwright pack: generate a project with it and run its contracts.

A pack is proven by running what the generated project runs, as the template's
CI of pawamoy/copier-uv does: npm ci, then the check, test and smoke commands
the pack writes into the contracts table. The smoke needs a system under test,
so each test serves a page from a local HTTP server and points BASE_URL at it;
nothing depends on a site outside the machine.

This module lives outside the core's tests (tests/packs/ has no __init__.py,
so ``discover -s tests`` does not reach it) because it needs Node and a
browser, which the core does not; the template's CI runs it in a job of its
own.

Run: python3 -m unittest discover -s tests/packs -v
"""

import http.server
import os
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent.parent
COPIER = shutil.which("copier")
NPM = shutil.which("npm")
NPX = shutil.which("npx")
TIMEOUT_SECONDS = 600
PACK = "ts-playwright"
CONTRACTS = {"check": "`npm run check`", "test": "`npm test`", "smoke": "`npm run smoke`"}
# Files of each test type, by path in the generated project
TYPE_FILES = {"api": "tests/api/smoke.spec.ts", "e2e": "tests/e2e/smoke.spec.ts"}
CI_WORKFLOW = ".github/workflows/ci.yml"
DEPENDABOT = ".github/dependabot.yml"
GATE = "ci-passed"
SUT_PAGE = b"<!doctype html><html><head><title>System under test</title></head><body>Up</body></html>"
# A test that only passes on its retry: Playwright reports it as flaky
# (playwright.dev, "Retries")
FLAKY_SPEC = """import { test, expect } from '@playwright/test';

test('passes only on a retry', () => {
  expect(test.info().retry).toBeGreaterThan(0);
});
"""
# A failing test without the smoke tag: the smoke command must not run it
UNTAGGED_FAILING_SPEC = """import { test, expect } from '@playwright/test';

test('not part of the smoke', () => {
  expect(1).toBe(2);
});
"""


def _run(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=cwd, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)


def _ok(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    result = _run(*args, cwd=cwd, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result.stdout


def _generate(destination: Path, test_types: str) -> None:
    _ok(
        COPIER, "copy", "--vcs-ref=HEAD", "--defaults",
        "--data", "project_name=Demo Project", "--data", f"pack={PACK}", "--data", f"test_types={test_types}",
        str(TEMPLATE_ROOT), str(destination),
    )


def _environment(**variables: str) -> dict[str, str]:
    """The current environment without the variables the suite reads, plus the given ones."""
    env = {name: value for name, value in os.environ.items() if name not in ("BASE_URL", "CI")}
    return {**env, **variables}


def _free_port() -> int:
    """A port nothing listens on: bound, then released."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class _SystemUnderTest(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (the name http.server calls)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(SUT_PAGE)

    def log_message(self, *args: object) -> None:
        pass


def _serve() -> tuple[http.server.ThreadingHTTPServer, str]:
    """Start the system under test on a free local port; return it and its URL."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _SystemUnderTest)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def setUpModule() -> None:
    """Fail, never skip, when a tool the pack needs is missing."""
    missing = [name for name, path in (("copier", COPIER), ("npm", NPM), ("npx", NPX)) if path is None]
    if missing:
        raise RuntimeError(f"not found on PATH: {', '.join(missing)}; the ts-playwright tests need Copier and Node")


class PackProjectTest(unittest.TestCase):
    """A project with both test types, installed once and run against a local server."""

    project: Path
    base_url: str

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.project = Path(cls._tmp.name) / "project"
        cls._server, cls.base_url = _serve()
        try:
            _generate(cls.project, "[e2e, api]")
            _ok(NPM, "ci", "--no-fund", "--no-audit", cwd=cls.project)
            _ok(NPX, "playwright", "install", "chromium", cwd=cls.project)
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls._server.shutdown()
        cls._server.server_close()
        cls._tmp.cleanup()

    def _npm(self, *args: str, **variables: str) -> subprocess.CompletedProcess[str]:
        return _run(NPM, *args, cwd=self.project, env=_environment(**variables))

    def _with_spec(self, name: str, source: str) -> Path:
        spec = self.project / "tests" / "api" / name
        spec.write_text(source, encoding="utf-8", newline="\n")
        self.addCleanup(spec.unlink)
        return spec

    def test_claude_md_maps_the_pack_commands(self) -> None:
        text = (self.project / "CLAUDE.md").read_text(encoding="utf-8")
        for role, value in CONTRACTS.items():
            with self.subTest(role=role):
                self.assertIn(f"| `{role}` | {value} |", text)

    def test_check_passes(self) -> None:
        result = self._npm("run", "check")
        self.assertEqual(result.returncode, 0, f"npm run check failed:\n{result.stdout}\n{result.stderr}")

    def test_suite_passes_against_a_reachable_system(self) -> None:
        result = self._npm("test", BASE_URL=self.base_url)
        self.assertEqual(result.returncode, 0, f"npm test failed:\n{result.stdout}\n{result.stderr}")
        self.assertRegex(result.stdout, r"\b2 passed\b", "the suite did not run one smoke per test type")

    def test_smoke_runs_only_the_smoke_tests(self) -> None:
        self._with_spec("untagged.spec.ts", UNTAGGED_FAILING_SPEC)
        result = self._npm("run", "smoke", BASE_URL=self.base_url)
        self.assertEqual(result.returncode, 0, f"npm run smoke ran an untagged test:\n{result.stdout}\n{result.stderr}")
        self.assertRegex(result.stdout, r"\b2 passed\b")

    def test_smoke_fails_when_the_system_is_unreachable(self) -> None:
        result = self._npm("run", "smoke", BASE_URL=f"http://127.0.0.1:{_free_port()}")
        self.assertNotEqual(result.returncode, 0, f"the smoke passed with nothing listening:\n{result.stdout}")
        self.assertRegex(result.stdout, r"\b2 failed\b", "a smoke passed with nothing listening")

    def test_missing_configuration_fails_fast_naming_the_variable(self) -> None:
        # Twelve-Factor, factor III, and ADR 0003: configuration comes from
        # the environment and is validated at startup, before any test runs
        result = self._npm("test")
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, "the suite ran with no BASE_URL")
        self.assertIn("BASE_URL", output)
        self.assertIn(".env.example", output)
        self.assertNotRegex(output, r"\b\d+ (passed|failed)\b", "tests started before the configuration was validated")

    def test_shell_variables_win_over_the_env_file(self) -> None:
        # A one-off BASE_URL=... in the shell must not lose to a stale .env
        env_file = self.project / ".env"
        env_file.write_text(f"BASE_URL=http://127.0.0.1:{_free_port()}\n", encoding="utf-8", newline="\n")
        self.addCleanup(env_file.unlink)
        result = self._npm("run", "smoke", BASE_URL=self.base_url)
        self.assertEqual(result.returncode, 0, f"the .env value won over the shell:\n{result.stdout}\n{result.stderr}")

    def test_env_file_is_read_when_the_shell_has_no_value(self) -> None:
        env_file = self.project / ".env"
        env_file.write_text(f"BASE_URL={self.base_url}\n", encoding="utf-8", newline="\n")
        self.addCleanup(env_file.unlink)
        result = self._npm("run", "smoke")
        self.assertEqual(result.returncode, 0, f"the .env file was not read:\n{result.stdout}\n{result.stderr}")

    def test_a_flaky_test_fails_the_run_in_ci(self) -> None:
        # docs/FLAKY_TESTS.md: a retry never passes a build. Retries only
        # diagnose; failOnFlakyTests turns a flaky run red (playwright.dev,
        # TestConfig, failOnFlakyTests)
        self._with_spec("flaky.spec.ts", FLAKY_SPEC)
        result = self._npm("test", "--", "tests/api/flaky.spec.ts", BASE_URL=self.base_url, CI="true")
        self.assertRegex(result.stdout + result.stderr, r"\b1 flaky\b", "the test was not retried in CI")
        self.assertNotEqual(result.returncode, 0, "a flaky test passed the build")

    def test_ci_runs_the_pack_contracts_inside_the_gate(self) -> None:
        text = (self.project / CI_WORKFLOW).read_text(encoding="utf-8")
        for job, command in (("check", "npm run check"), ("test", "npm test")):
            with self.subTest(job=job):
                self.assertIn(f"\n  {job}:\n", text, f"no {job} job")
                self.assertIn(f"run: {command}\n", text)
        needs = re.search(rf"\n  {GATE}:\n(?:    .*\n)*?    needs: \[([^\]]*)\]", text)
        self.assertIsNotNone(needs, "no needs in the gate")
        self.assertEqual(sorted(part.strip() for part in needs.group(1).split(",")), ["check", "core-checks", "test"])
        self.assertIn("run: npm ci\n", text)
        self.assertIn("npx playwright install --with-deps chromium", text, "e2e needs the browser in CI")
        self.assertIn("node-version-file: .node-version", text)

    def test_dependabot_updates_npm_after_a_cooldown(self) -> None:
        text = (self.project / DEPENDABOT).read_text(encoding="utf-8")
        block = re.search(r'package-ecosystem: "npm"\n(?:      .*\n|    .*\n)*', text)
        self.assertIsNotNone(block, "no npm ecosystem")
        self.assertIn("default-days: 7", block.group(0))
        self.assertIn('versioning-strategy: "increase"', block.group(0))

    def test_git_ignores_local_and_generated_files(self) -> None:
        _ok("git", "init", "-q", cwd=self.project)
        self.addCleanup(shutil.rmtree, self.project / ".git", True)
        # A path inside each folder: a "folder/" pattern matches only
        # directories, and these do not exist until something writes them
        for path in (".env", "node_modules/x", "test-results/x", "playwright-report/index.html", "blob-report/x"):
            with self.subTest(path=path):
                self.assertEqual(_run("git", "check-ignore", "-q", path, cwd=self.project).returncode, 0, f"{path} is not ignored")
        self.assertNotEqual(_run("git", "check-ignore", "-q", ".env.example", cwd=self.project).returncode, 0, ".env.example is ignored")


class SingleTestTypeTest(unittest.TestCase):
    """A project with one test type has only that type's files, and still passes its contracts."""

    def test_each_type_alone(self) -> None:
        server, base_url = _serve()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        for test_type, other in (("api", "e2e"), ("e2e", "api")):
            with self.subTest(test_type=test_type), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp) / "project"
                _generate(project, f"[{test_type}]")
                self.assertTrue((project / TYPE_FILES[test_type]).is_file(), f"{TYPE_FILES[test_type]} not rendered")
                self.assertFalse((project / "tests" / other).exists(), f"tests/{other} rendered without {other}")
                workflow = (project / CI_WORKFLOW).read_text(encoding="utf-8")
                self.assertEqual("playwright install" in workflow, test_type == "e2e", "browser install does not follow the e2e option")
                _ok(NPM, "ci", "--no-fund", "--no-audit", cwd=project)
                if test_type == "e2e":
                    _ok(NPX, "playwright", "install", "chromium", cwd=project)
                for contract in (("run", "check"), ("test",), ("run", "smoke")):
                    result = _run(NPM, *contract, cwd=project, env=_environment(BASE_URL=base_url))
                    self.assertEqual(result.returncode, 0, f"npm {' '.join(contract)} failed:\n{result.stdout}\n{result.stderr}")


class PackQuestionsTest(unittest.TestCase):
    def test_the_pack_needs_at_least_one_test_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "test type"):
                _generate(Path(tmp) / "project", "[]")

    def test_without_a_pack_no_pack_file_is_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            _ok(COPIER, "copy", "--vcs-ref=HEAD", "--defaults", "--data", "project_name=Demo Project", str(TEMPLATE_ROOT), str(project))
            for path in ("package.json", "package-lock.json", "playwright.config.ts", ".node-version", "tests", "src", ".env.example", ".gitignore"):
                with self.subTest(path=path):
                    self.assertFalse((project / path).exists(), f"{path} rendered with no pack")


if __name__ == "__main__":
    unittest.main()
