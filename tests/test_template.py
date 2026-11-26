"""Tests for the Copier template: generate a project and check the result.

The template does not run on its own, so it is tested by rendering it
(ADR 0001, consequences). setUpClass runs ``copier copy`` once, from this
checkout, into a temporary directory, with every answer given on the command
line, and each test checks one file of the generated project.

``--vcs-ref=HEAD`` makes Copier render the checked-out revision, including
uncommitted changes; without it, Copier renders the latest Git tag (Copier
docs, "Generating a project"), and the tests would check a release instead of
the change under test.

Run: python3 -m unittest discover -s tests -v
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
COPIER = shutil.which("copier")
TIMEOUT_SECONDS = 120
PROJECT_NAME = "Demo Project"


def setUpModule() -> None:
    """Fail, never skip, when Copier is missing.

    The ``test`` contract lists Copier as a precondition; skipping would
    print OK without rendering the template, an error passing in silence.
    """
    if COPIER is None:
        raise RuntimeError(
            "copier not found on PATH; install it in a virtual environment with "
            "pip install --require-hashes --only-binary :all: -r .github/tools/copier/requirements.txt"
        )


class GeneratedProjectTest(unittest.TestCase):
    project: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.project = Path(cls._tmp.name) / "project"
        result = subprocess.run(
            [
                COPIER,
                "copy",
                "--vcs-ref=HEAD",
                "--defaults",
                "--data",
                f"project_name={PROJECT_NAME}",
                str(TEMPLATE_ROOT),
                str(cls.project),
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            cls._tmp.cleanup()
            raise RuntimeError(f"copier copy failed ({result.returncode}):\n{result.stderr}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_readme_is_titled_with_the_project_name(self) -> None:
        readme = self.project / "README.md"
        self.assertTrue(readme.is_file(), f"README.md not rendered; generated: {sorted(p.name for p in self.project.iterdir())}")
        self.assertEqual(readme.read_text(encoding="utf-8").splitlines()[0], f"# {PROJECT_NAME}")

    def test_answers_file_records_the_answers_for_copier_update(self) -> None:
        # copier update needs a valid .copier-answers.yml in the project
        # (Copier docs, "Updating a project")
        answers = self.project / ".copier-answers.yml"
        self.assertTrue(answers.is_file(), f".copier-answers.yml not rendered; generated: {sorted(p.name for p in self.project.iterdir())}")
        lines = answers.read_text(encoding="utf-8").splitlines()
        self.assertIn(f"project_name: {PROJECT_NAME}", lines)
        self.assertTrue(any(line.startswith("_src_path: ") for line in lines), f"no _src_path in:\n{lines}")

    def test_template_files_stay_out_of_the_project(self) -> None:
        # _subdirectory keeps the template repository's own files (plugin,
        # docs, CI) out of every generated project
        for name in ("copier.yml", "plugins", "docs", ".github"):
            self.assertFalse((self.project / name).exists(), f"{name} leaked into the generated project")


if __name__ == "__main__":
    unittest.main()
