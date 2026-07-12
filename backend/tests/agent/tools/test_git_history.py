import shutil
import tempfile
import unittest
from pathlib import Path

from git import Repo

from app.agent.tools.git_history import _git_history


def _init_repo(repo_root: Path) -> Repo:
    repo = Repo.init(repo_root)

    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test Author")
        cw.set_value("user", "email", "test@example.com")

    return repo


def _commit_file(
    repo: Repo,
    repo_root: Path,
    relative_path: str,
    content: str,
    message: str,
) -> None:
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)

    repo.index.add([relative_path])
    repo.index.commit(message)


class GitHistoryToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo_root = Path(tempfile.mkdtemp())
        self.repo = _init_repo(self.repo_root)

    def tearDown(self):
        shutil.rmtree(self.repo_root, ignore_errors=True)

    async def test_valid_file_returns_readable_history(self):
        _commit_file(self.repo, self.repo_root, "app.py", "print('v1')", "Initial commit")
        _commit_file(
            self.repo,
            self.repo_root,
            "app.py",
            "print('v2')",
            "Added JWT verification.",
        )

        result = await _git_history(self.repo_root, "app.py")

        self.assertTrue(result.success)
        self.assertIn("Added JWT verification.", result.content)
        self.assertIn("Test Author", result.content)
        self.assertIn("Commit:", result.content)
        self.assertIn("Date:", result.content)
        self.assertEqual(result.metadata["commit_count"], 2)
        self.assertEqual(result.metadata["authors"], ["Test Author"])
        self.assertIsNotNone(result.metadata["latest_commit"])

    async def test_missing_file_returns_failure(self):
        result = await _git_history(self.repo_root, "does_not_exist.py")

        self.assertFalse(result.success)
        self.assertEqual(result.content, "File not found.")

    async def test_path_traversal_is_blocked(self):
        result = await _git_history(self.repo_root, "/etc/passwd")

        self.assertFalse(result.success)
        self.assertIn("escapes the repository directory", result.content)

    async def test_file_with_no_history_is_reported_cleanly(self):
        untracked = self.repo_root / "untracked.py"
        untracked.write_text("print('never committed')")

        result = await _git_history(self.repo_root, "untracked.py")

        self.assertTrue(result.success)
        self.assertIn("No commit history found", result.content)
        self.assertEqual(result.metadata["commit_count"], 0)
        self.assertIsNone(result.metadata["latest_commit"])
        self.assertEqual(result.metadata["authors"], [])

    async def test_max_commits_limits_returned_history(self):
        for i in range(5):
            _commit_file(
                self.repo,
                self.repo_root,
                "app.py",
                f"print('v{i}')",
                f"Change number {i}",
            )

        result = await _git_history(self.repo_root, "app.py", max_commits=2)

        self.assertTrue(result.success)
        self.assertEqual(result.metadata["commit_count"], 2)
        self.assertEqual(result.content.count("Commit:"), 2)


if __name__ == "__main__":
    unittest.main()
