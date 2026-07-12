import shutil
import tempfile
import unittest
from pathlib import Path

from git import Repo

from app.agent.tools.git_diff import _git_diff


def _init_repo(repo_root: Path) -> Repo:
    repo = Repo.init(repo_root)

    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test Author")
        cw.set_value("user", "email", "test@example.com")

    return repo


def _write(repo_root: Path, relative_path: str, content: str) -> None:
    target = repo_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


class GitDiffToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo_root = Path(tempfile.mkdtemp())
        self.repo = _init_repo(self.repo_root)

    def tearDown(self):
        shutil.rmtree(self.repo_root, ignore_errors=True)

    async def test_valid_commit_returns_raw_unified_diff(self):
        _write(self.repo_root, "app.py", "line1\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")

        _write(self.repo_root, "app.py", "line1\nline2\n")
        self.repo.index.add(["app.py"])
        second = self.repo.index.commit("Add line2")

        result = await _git_diff(self.repo_root, second.hexsha)

        self.assertTrue(result.success)
        self.assertIn("diff --git a/app.py b/app.py", result.content)
        self.assertIn("+line2", result.content)
        self.assertNotIn("-line1", result.content)
        self.assertEqual(result.metadata["commit"], second.hexsha)
        self.assertEqual(result.metadata["files_changed"], 1)

    async def test_invalid_commit_hash_returns_clean_failure(self):
        _write(self.repo_root, "app.py", "line1\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")

        result = await _git_diff(self.repo_root, "deadbeefdeadbeef")

        self.assertFalse(result.success)
        self.assertIn("was not found", result.content)

    async def test_initial_commit_diffs_against_empty_tree(self):
        _write(self.repo_root, "app.py", "line1\nline2\n")
        self.repo.index.add(["app.py"])
        initial = self.repo.index.commit("Initial commit")

        result = await _git_diff(self.repo_root, initial.hexsha)

        self.assertTrue(result.success)
        self.assertIn("diff --git a/app.py b/app.py", result.content)
        self.assertIn("--- /dev/null", result.content)
        self.assertIn("+line1", result.content)
        self.assertIn("+line2", result.content)
        self.assertEqual(result.metadata["files_changed"], 1)

    async def test_multiple_file_changes_are_all_included(self):
        _write(self.repo_root, "a.txt", "a1\n")
        _write(self.repo_root, "b.txt", "b1\n")
        self.repo.index.add(["a.txt", "b.txt"])
        self.repo.index.commit("Initial commit")

        _write(self.repo_root, "a.txt", "a1\na2\n")
        _write(self.repo_root, "c.txt", "c1\n")
        self.repo.index.add(["a.txt", "c.txt"])
        self.repo.index.remove(["b.txt"])
        second = self.repo.index.commit("Modify a, add c, delete b")

        result = await _git_diff(self.repo_root, second.hexsha)

        self.assertTrue(result.success)
        self.assertEqual(result.metadata["files_changed"], 3)
        self.assertIn("diff --git a/a.txt b/a.txt", result.content)
        self.assertIn("diff --git a/c.txt b/c.txt", result.content)
        self.assertIn("diff --git a/b.txt b/b.txt", result.content)
        self.assertIn("+++ /dev/null", result.content)  # b.txt deleted
        self.assertIn("--- /dev/null", result.content)  # c.txt added

    async def test_metadata_contains_commit_and_file_count(self):
        _write(self.repo_root, "app.py", "line1\n")
        self.repo.index.add(["app.py"])
        commit = self.repo.index.commit("Initial commit")

        result = await _git_diff(self.repo_root, commit.hexsha[:8])

        self.assertTrue(result.success)
        self.assertEqual(result.metadata["commit"], commit.hexsha)
        self.assertEqual(result.metadata["files_changed"], 1)

    async def test_context_lines_controls_hunk_context(self):
        lines = [f"line{i}" for i in range(10)]
        _write(self.repo_root, "app.py", "\n".join(lines) + "\n")
        self.repo.index.add(["app.py"])
        self.repo.index.commit("Initial commit")

        lines[5] = "CHANGED"
        _write(self.repo_root, "app.py", "\n".join(lines) + "\n")
        self.repo.index.add(["app.py"])
        second = self.repo.index.commit("Change line 5")

        result = await _git_diff(self.repo_root, second.hexsha, context_lines=1)

        self.assertTrue(result.success)
        self.assertIn("-line5", result.content)
        self.assertIn("+CHANGED", result.content)
        self.assertNotIn("line0", result.content)


if __name__ == "__main__":
    unittest.main()
