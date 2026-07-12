import shutil
import tempfile
import unittest
from pathlib import Path

from git import Repo

from app.agent.tools.git_blame import _git_blame


def _init_repo(repo_root: Path) -> Repo:
    repo = Repo.init(repo_root)

    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Alice")
        cw.set_value("user", "email", "alice@example.com")

    return repo


def _set_author(repo: Repo, name: str, email: str) -> None:
    with repo.config_writer() as cw:
        cw.set_value("user", "name", name)
        cw.set_value("user", "email", email)


def _write(repo_root: Path, relative_path: str, content: str) -> None:
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


class GitBlameToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo_root = Path(tempfile.mkdtemp())
        self.repo = _init_repo(self.repo_root)

    def tearDown(self):
        shutil.rmtree(self.repo_root, ignore_errors=True)

    async def test_blame_entire_file(self):
        _write(self.repo_root, "app.py", "line1\nline2\nline3\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")

        result = await _git_blame(self.repo_root, "app.py")

        self.assertTrue(result.success)
        self.assertIn("Commit:", result.content)
        self.assertIn("Author: Alice", result.content)
        self.assertIn("Affected Lines: 1-3", result.content)
        self.assertEqual(result.metadata["line_count"], 3)
        self.assertEqual(result.metadata["authors"], ["Alice"])

    async def test_blame_single_line_includes_source_text(self):
        _write(self.repo_root, "app.py", "line1\nline2\nline3\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")

        result = await _git_blame(self.repo_root, "app.py", line_number=2)

        self.assertTrue(result.success)
        self.assertIn("Affected Lines: 2-2", result.content)
        self.assertIn("Line 2: line2", result.content)
        self.assertEqual(result.metadata["line_count"], 1)
        self.assertNotIn("line1", result.content)
        self.assertNotIn("line3", result.content)

    async def test_missing_file_returns_failure(self):
        result = await _git_blame(self.repo_root, "does_not_exist.py")

        self.assertFalse(result.success)
        self.assertEqual(result.content, "File not found.")

    async def test_path_traversal_is_blocked(self):
        result = await _git_blame(self.repo_root, "/etc/passwd")

        self.assertFalse(result.success)
        self.assertIn("escapes the repository directory", result.content)

    async def test_multiple_authors_are_all_reported(self):
        _write(self.repo_root, "app.py", "line1\nline2\nline3\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")

        _set_author(self.repo, "Bob", "bob@example.com")
        _write(self.repo_root, "app.py", "line1\nCHANGED2\nline3\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Bob changes line2")

        result = await _git_blame(self.repo_root, "app.py")

        self.assertTrue(result.success)
        self.assertEqual(result.metadata["authors"], ["Alice", "Bob"])
        self.assertIn("Author: Bob", result.content)
        self.assertIn("Author: Alice", result.content)
        self.assertIn("Affected Lines: 2-2", result.content)  # Bob's block
        self.assertEqual(result.metadata["line_count"], 3)

    async def test_line_number_out_of_range_returns_clean_failure(self):
        _write(self.repo_root, "app.py", "line1\nline2\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")

        result = await _git_blame(self.repo_root, "app.py", line_number=99)

        self.assertFalse(result.success)
        self.assertIn("out of range", result.content)

    async def test_untracked_file_returns_clean_failure_not_a_crash(self):
        _write(self.repo_root, "tracked.py", "x\n")
        self.repo.index.add(["tracked.py"])
        self.repo.index.commit("Initial commit")

        _write(self.repo_root, "untracked.py", "y\n")

        result = await _git_blame(self.repo_root, "untracked.py")

        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
