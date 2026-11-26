"""Tests for .github/scripts/check-text-encoding.sh (#71).

The script is template-owned and shared with every generated project (held
identical by tests/test_template.py), so the tests run this repository's copy.
Each test builds a throwaway Git repository, stages its files and runs the
script there through sh, the way the CI job runs it.

The case behind the check: Windows PowerShell 5.1 writes UTF-16 with a byte
order mark (``Out-File``, ``>``), and Git then reads the file as binary: a
UTF-16 ``.gitignore`` in uat-automation-framework matched nothing (uat#26).

Run: python3 -m unittest discover -s tests -v
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".github" / "scripts" / "check-text-encoding.sh"
SH = shutil.which("sh")
GIT = ("git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false")
TIMEOUT_SECONDS = 30
UTF8_TEXT = "Ação e reação\n"
# The first bytes of a PNG: binary content that holds NUL and no byte order mark
PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


def setUpModule() -> None:
    """Fail, never skip, when sh or git is missing (the `test` contract)."""
    for tool in ("sh", "git"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} not found on PATH; on Windows, put Git Bash on the PATH")


class CheckTextEncodingTest(unittest.TestCase):
    def _check(self, files: dict[str, bytes], prepare=None) -> subprocess.CompletedProcess[str]:
        """Stage files in a new repository, run prepare(repository), then the script."""
        with tempfile.TemporaryDirectory() as tmp:
            repository = Path(tmp)
            subprocess.run([*GIT, "init", "-q"], cwd=repository, check=True, timeout=TIMEOUT_SECONDS)
            for name, content in files.items():
                path = repository / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            subprocess.run([*GIT, "add", "-A"], cwd=repository, check=True, timeout=TIMEOUT_SECONDS)
            if prepare is not None:
                prepare(repository)
            return subprocess.run(
                [SH, str(SCRIPT)], cwd=repository, capture_output=True, text=True, timeout=TIMEOUT_SECONDS
            )

    def assertRejected(self, result: subprocess.CompletedProcess[str], path: str, cause: str) -> None:
        self.assertEqual(result.returncode, 1, f"not rejected:\n{result.stdout}{result.stderr}")
        self.assertIn(path, result.stderr)
        self.assertIn(cause, result.stderr)

    def test_utf8_text_and_binary_files_pass(self) -> None:
        result = self._check({
            "README.md": UTF8_TEXT.encode("utf-8"),
            "docs/with space.md": UTF8_TEXT.encode("utf-8"),
            "empty.txt": b"",
            "logo.png": PNG_HEADER,
        })
        self.assertEqual(result.returncode, 0, f"rejected valid files:\n{result.stderr}")
        self.assertEqual(result.stderr, "")

    def test_utf16_little_endian_with_bom_is_rejected(self) -> None:
        # What Out-File writes by default in Windows PowerShell 5.1
        result = self._check({".gitignore": "﻿.env\n".encode("utf-16-le")})
        self.assertRejected(result, ".gitignore", "UTF-16")

    def test_utf16_big_endian_with_bom_is_rejected(self) -> None:
        result = self._check({"notes.txt": "﻿notes\n".encode("utf-16-be")})
        self.assertRejected(result, "notes.txt", "UTF-16")

    def test_text_that_is_not_utf8_is_rejected(self) -> None:
        # Latin-1 "ção": Git sees text (no NUL), but the bytes are not UTF-8
        result = self._check({"docs/latin1.md": "Ação\n".encode("latin-1")})
        self.assertRejected(result, "docs/latin1.md", "not UTF-8")

    def test_every_bad_file_is_reported(self) -> None:
        result = self._check({
            "a.txt": "Ação\n".encode("latin-1"),
            "b.txt": "﻿b\n".encode("utf-16-le"),
            "ok.txt": UTF8_TEXT.encode("utf-8"),
        })
        self.assertRejected(result, "a.txt", "not UTF-8")
        self.assertIn("b.txt", result.stderr)
        self.assertNotIn("ok.txt", result.stderr)

    def test_a_staged_file_missing_from_the_working_tree_is_reported(self) -> None:
        # Checking nothing under that name would pass a file nobody read
        result = self._check({"gone.txt": UTF8_TEXT.encode("utf-8")}, lambda repository: (repository / "gone.txt").unlink())
        self.assertRejected(result, "gone.txt", "not found in the working tree")

    def test_a_submodule_is_skipped(self) -> None:
        # A gitlink is a directory in the working tree; its files belong to
        # its own repository, so it is neither read nor reported
        def add_gitlink(repository: Path) -> None:
            (repository / "vendor" / "lib").mkdir(parents=True)
            subprocess.run(
                [*GIT, "update-index", "--add", "--cacheinfo", f"160000,{'1' * 40},vendor/lib"],
                cwd=repository, check=True, timeout=TIMEOUT_SECONDS,
            )

        result = self._check({"README.md": UTF8_TEXT.encode("utf-8")}, add_gitlink)
        self.assertEqual(result.returncode, 0, f"rejected a submodule:\n{result.stderr}")
        self.assertEqual(result.stderr, "")

    def test_outside_a_git_repository_fails_with_the_cause(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [SH, str(SCRIPT)], cwd=tmp, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
                env={"PATH": os.environ["PATH"], "GIT_CEILING_DIRECTORIES": str(Path(tmp).parent)},
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git", result.stderr)


if __name__ == "__main__":
    unittest.main()
