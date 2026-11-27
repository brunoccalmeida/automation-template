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

import hashlib
import http.server
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
import urllib.request
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
# Environment variables Claude Code sets in the commands its tools run
# (code.claude.com/docs/en/env-vars): the pack's reporter reads one of them,
# so every test starts without both and sets them only on purpose
AGENT_VARIABLES = ("CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION")
# The scanner the generated audit job runs: osv-scanner-action v2.7.1 runs the
# image ghcr.io/google/osv-scanner-action:v2.7.1 (its action.yml). The same
# release's binary, checked against the release's osv-scanner_SHA256SUMS, so
# the test proves the policy file the job reads. Bump both with the action
OSV_VERSION = "2.7.1"
OSV_BINARIES = {
    ("Linux", "x86_64"): ("osv-scanner_linux_amd64", "fb7dab19a8bd9bbe5c3189f09d4b7ee1820c9553a23bac202648a56efd2f6ee8"),
    ("Windows", "AMD64"): ("osv-scanner_windows_amd64.exe", "7121dcf420aefbbf89a7f0050c4d3094e079ff93afd334dfc96f16b02ec85800"),
    ("Darwin", "arm64"): ("osv-scanner_darwin_arm64", "b22c02877a811c8f78956e8643efa554932b7378f590d13f8e97d4e9448a29f3"),
}
# A lockfile with a release that has known advisories: lodash 4.17.20 (fixed
# in 4.17.21, GHSA-35jh-r3h4-6jhm among others)
VULNERABLE_LOCKFILE = {
    "name": "probe",
    "lockfileVersion": 3,
    "requires": True,
    "packages": {
        "": {"name": "probe", "dependencies": {"lodash": "4.17.20"}},
        "node_modules/lodash": {
            "version": "4.17.20",
            "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.20.tgz",
        },
    },
}
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
    env = {name: value for name, value in os.environ.items() if name not in ("BASE_URL", "CI", *AGENT_VARIABLES)}
    return {**env, **variables}


def _osv_scanner(directory: Path) -> Path:
    """Download the pinned osv-scanner into directory and check its SHA-256."""
    key = (platform.system(), platform.machine())
    if key not in OSV_BINARIES:
        raise RuntimeError(f"no pinned osv-scanner {OSV_VERSION} binary for {key}; add it from the release's SHA256SUMS")
    name, sha256 = OSV_BINARIES[key]
    url = f"https://github.com/google/osv-scanner/releases/download/v{OSV_VERSION}/{name}"
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310 (a fixed https URL)
        content = response.read()
    actual = hashlib.sha256(content).hexdigest()
    if actual != sha256:
        raise RuntimeError(f"{name} SHA-256 is {actual}, expected {sha256}")
    binary = directory / name
    binary.write_bytes(content)
    binary.chmod(0o755)
    return binary


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

    def test_output_is_compact_in_a_command_an_agent_runs(self) -> None:
        # The list reporter prints one line per test, named; dot prints one
        # character per test and only the failures in full (playwright.dev,
        # "Reporters"). An agent pays for every line it reads
        title = "the system under test answers"
        human = self._npm("test", BASE_URL=self.base_url)
        self.assertIn(title, human.stdout, "a person no longer sees each test")
        agent = self._npm("test", BASE_URL=self.base_url, CLAUDE_CODE_CHILD_SESSION="1")
        self.assertEqual(agent.returncode, 0, f"npm test failed under an agent:\n{agent.stdout}\n{agent.stderr}")
        self.assertNotIn(title, agent.stdout, "an agent still gets one line per test")
        self.assertRegex(agent.stdout, r"\b2 passed\b", "the summary is gone under an agent")

    def test_a_failure_stays_readable_in_compact_output(self) -> None:
        self._with_spec("untagged.spec.ts", UNTAGGED_FAILING_SPEC)
        result = self._npm("test", "--", "tests/api/untagged.spec.ts", BASE_URL=self.base_url, CLAUDE_CODE_CHILD_SESSION="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not part of the smoke", result.stdout, "the failing test is not named")
        self.assertIn("toBe", result.stdout, "the failed assertion is not shown")

    def test_ci_writes_the_html_report(self) -> None:
        report = self.project / "playwright-report"
        self.addCleanup(shutil.rmtree, report, True)
        result = self._npm("test", BASE_URL=self.base_url, CI="true")
        self.assertEqual(result.returncode, 0, f"npm test failed in CI:\n{result.stdout}\n{result.stderr}")
        self.assertTrue((report / "index.html").is_file(), "no HTML report in CI")

    def test_sentinel_fails_the_check_once_the_ignore_is_no_longer_needed(self) -> None:
        # The Dependabot ignore of the next TypeScript major has one reason:
        # typescript-eslint's peer rejects it. A peer that accepts it means
        # the ignore now only hides the upgrade, so `check` fails
        manifest = self.project / "node_modules" / "typescript-eslint" / "package.json"
        original = manifest.read_text(encoding="utf-8")
        self.addCleanup(manifest.write_text, original, encoding="utf-8", newline="\n")
        data = json.loads(original)
        data["peerDependencies"]["typescript"] = ">=4.8.4 <99.0.0"
        manifest.write_text(json.dumps(data), encoding="utf-8", newline="\n")
        result = self._npm("run", "check")
        self.assertNotEqual(result.returncode, 0, f"the check passed with an ignore that is no longer needed:\n{result.stdout}")
        self.assertIn(f"Remove the typescript ignore from {DEPENDABOT}", result.stdout + result.stderr)

    def test_ci_runs_the_pack_contracts_inside_the_gate(self) -> None:
        text = (self.project / CI_WORKFLOW).read_text(encoding="utf-8")
        for job, command in (("check", "npm run check"), ("test", "npm test")):
            with self.subTest(job=job):
                self.assertIn(f"\n  {job}:\n", text, f"no {job} job")
                self.assertIn(f"run: {command}\n", text)
        needs = re.search(rf"\n  {GATE}:\n(?:    .*\n)*?    needs: \[([^\]]*)\]", text)
        self.assertIsNotNone(needs, "no needs in the gate")
        self.assertEqual(sorted(part.strip() for part in needs.group(1).split(",")), ["audit", "check", "core-checks", "test"])
        self.assertIn("run: npm ci\n", text)
        self.assertIn("npx playwright install --with-deps chromium", text, "e2e needs the browser in CI")
        self.assertIn("node-version-file: .node-version", text)

    def test_dependabot_updates_npm_after_a_cooldown(self) -> None:
        text = (self.project / DEPENDABOT).read_text(encoding="utf-8")
        block = re.search(r'package-ecosystem: "npm"\n(?:      .*\n|    .*\n)*', text)
        self.assertIsNotNone(block, "no npm ecosystem")
        self.assertIn("default-days: 7", block.group(0))
        self.assertIn('versioning-strategy: "increase"', block.group(0))
        self.assertRegex(
            block.group(0),
            r'- dependency-name: "typescript"\n\s+update-types: \["version-update:semver-major"\]',
            "the TypeScript major that typescript-eslint rejects is not ignored",
        )

    def test_ci_uploads_the_html_report_even_when_tests_fail(self) -> None:
        text = (self.project / CI_WORKFLOW).read_text(encoding="utf-8")
        test_job = re.search(r"\n  test:\n(?:(?:    .*)?\n)*", text)
        self.assertIsNotNone(test_job, "no test job")
        upload = re.search(r"uses: actions/upload-artifact@[0-9a-f]{40} # v\S+\n(?:        .*\n)+", test_job.group(0))
        self.assertIsNotNone(upload, "the test job uploads no artifact")
        self.assertIn("path: playwright-report", upload.group(0))
        step = test_job.group(0)[: upload.start()].rsplit("- name:", 1)[1]
        self.assertIn("if: ${{ !cancelled() }}", step, "a failing run, the one worth reading, uploads no report")

    def test_ci_audits_the_lockfile_with_the_pinned_scanner(self) -> None:
        text = (self.project / CI_WORKFLOW).read_text(encoding="utf-8")
        audit = re.search(r"\n  audit:\n(?:(?:    .*)?\n)*", text)
        self.assertIsNotNone(audit, "no audit job")
        self.assertRegex(
            audit.group(0),
            rf"uses: google/osv-scanner-action/\.github/workflows/osv-scanner-reusable\.yml@[0-9a-f]{{40}} # v{re.escape(OSV_VERSION)}\n",
            "the audit job does not run the scanner version this test proves",
        )
        self.assertIn("--lockfile=package-lock.json", audit.group(0))
        self.assertIn("upload-sarif: false", audit.group(0))

    def test_git_ignores_local_and_generated_files(self) -> None:
        _ok("git", "init", "-q", cwd=self.project)
        self.addCleanup(shutil.rmtree, self.project / ".git", True)
        # A path inside each folder: a "folder/" pattern matches only
        # directories, and these do not exist until something writes them
        for path in (".env", "node_modules/x", "test-results/x", "playwright-report/index.html", "blob-report/x"):
            with self.subTest(path=path):
                self.assertEqual(_run("git", "check-ignore", "-q", path, cwd=self.project).returncode, 0, f"{path} is not ignored")
        self.assertNotEqual(_run("git", "check-ignore", "-q", ".env.example", cwd=self.project).returncode, 0, ".env.example is ignored")


class AuditPolicyTest(unittest.TestCase):
    """The generated project's audit, run with the scanner its CI job runs.

    Each probe copies the generated osv-scanner.toml next to a lockfile, so the
    scan reads the policy the project ships. Exit code 1 means vulnerabilities
    were found; anything else non-zero is a scan error (osv-scanner, "Usage",
    return codes), which must not pass for a finding.
    """

    project: Path
    scanner: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.project = root / "project"
        try:
            _generate(cls.project, "[e2e, api]")
            cls.scanner = _osv_scanner(root)
        except Exception:
            cls._tmp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _scan(self, directory: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return _run(str(self.scanner), *args, "--lockfile=package-lock.json", cwd=directory)

    def _vulnerable(self, extra_policy: str = "") -> Path:
        directory = Path(tempfile.mkdtemp(dir=self._tmp.name))
        (directory / "package-lock.json").write_text(json.dumps(VULNERABLE_LOCKFILE), encoding="utf-8", newline="\n")
        policy = (self.project / "osv-scanner.toml").read_text(encoding="utf-8")
        (directory / "osv-scanner.toml").write_text(policy + extra_policy, encoding="utf-8", newline="\n")
        return directory

    def _exceptions(self, directory: Path, until: str) -> str:
        """An exception for every advisory found in directory, effective until the given date."""
        found = self._scan(directory, "--format=json")
        self.assertEqual(found.returncode, 1, f"the probe found no vulnerability:\n{found.stdout}\n{found.stderr}")
        ids = sorted(
            {
                vulnerability["id"]
                for result in json.loads(found.stdout)["results"]
                for package in result["packages"]
                for vulnerability in package["vulnerabilities"]
            }
        )
        return "".join(
            f'\n[[IgnoredVulns]]\nid = "{vid}"\neffectiveUntil = {until}\nreason = "Probe of the policy"\n' for vid in ids
        )

    def test_the_generated_lockfile_has_no_known_vulnerability(self) -> None:
        result = self._scan(self.project)
        self.assertEqual(result.returncode, 0, f"the pack's pins carry a known vulnerability:\n{result.stdout}\n{result.stderr}")

    def test_a_known_vulnerability_fails_the_audit(self) -> None:
        result = self._scan(self._vulnerable())
        self.assertEqual(result.returncode, 1, f"the audit did not report lodash 4.17.20:\n{result.stdout}\n{result.stderr}")
        self.assertIn("lodash", result.stdout)

    def test_an_exception_holds_only_until_it_expires(self) -> None:
        probe = self._vulnerable()
        for until, expected in (("2999-01-01", 0), ("2000-01-01", 1)):
            with self.subTest(effective_until=until):
                directory = self._vulnerable(self._exceptions(probe, until))
                result = self._scan(directory)
                self.assertEqual(result.returncode, expected, f"exception until {until}:\n{result.stdout}\n{result.stderr}")


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
            for path in ("package.json", "package-lock.json", "playwright.config.ts", ".node-version", "tests", "src", "scripts", ".env.example", ".gitignore", "osv-scanner.toml"):
                with self.subTest(path=path):
                    self.assertFalse((project / path).exists(), f"{path} rendered with no pack")


if __name__ == "__main__":
    unittest.main()
