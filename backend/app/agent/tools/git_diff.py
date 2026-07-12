from pathlib import Path

from git import NULL_TREE, Repo
from git.exc import BadName, GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from app.agent.tool import Tool
from app.agent.tool_result import ToolResult
from app.utils.path import get_repository_path

DEFAULT_CONTEXT_LINES = 3


def _file_labels(diff) -> tuple[str, str]:
    a_path = diff.a_path or diff.b_path
    b_path = diff.b_path or diff.a_path
    return a_path, b_path


def _format_file_diff(diff) -> str:
    # Diff.diff only holds the hunk body, not the standard unified-diff
    # file headers - GitPython's structural attributes (new_file /
    # deleted_file / a_path / b_path) are what let us reconstruct a real
    # "diff --git ..." / "--- a/..." / "+++ b/..." header around it.
    a_path, b_path = _file_labels(diff)

    old_label = "/dev/null" if diff.new_file else f"a/{a_path}"
    new_label = "/dev/null" if diff.deleted_file else f"b/{b_path}"

    header = f"diff --git a/{a_path} b/{b_path}\n--- {old_label}\n+++ {new_label}\n"
    body = diff.diff.decode("utf-8", errors="replace") if diff.diff else ""

    return header + body


async def _git_diff(
    repository_path: Path,
    commit_hash: str,
    context_lines: int = DEFAULT_CONTEXT_LINES,
) -> ToolResult:
    # No filesystem path is ever taken from the caller here - every path
    # that ends up in the diff comes from git's own object database for
    # this repository (a_path/b_path on each Diff), so there is no way
    # for this tool to read anything outside repository_path.
    try:
        repo = Repo(repository_path)
        commit = repo.commit(commit_hash)

        if commit.parents:
            base = commit.parents[0]
            diffs = list(base.diff(commit, create_patch=True, unified=context_lines))
        else:
            # Initial commit - there is no parent to diff against, so
            # every line in every file it introduced counts as added.
            diffs = list(commit.diff(NULL_TREE, create_patch=True, unified=context_lines))
    except (InvalidGitRepositoryError, NoSuchPathError):
        return ToolResult(
            success=False,
            content="This repository could not be opened as a Git repository.",
            metadata={"commit": commit_hash},
        )
    except BadName:
        return ToolResult(
            success=False,
            content=f"Commit '{commit_hash}' was not found in this repository.",
            metadata={"commit": commit_hash},
        )
    except GitCommandError as e:
        return ToolResult(
            success=False,
            content=f"Failed to compute diff for commit '{commit_hash}': {e}",
            metadata={"commit": commit_hash},
        )
    except Exception as e:
        # Defensive catch-all: this tool must never let a raw exception
        # reach the Agent loop - any unexpected failure degrades to a
        # failed ToolResult instead.
        return ToolResult(
            success=False,
            content=f"Failed to compute diff for commit '{commit_hash}': {e}",
            metadata={"commit": commit_hash},
        )

    if not diffs:
        return ToolResult(
            success=True,
            content=f"Commit {commit.hexsha} introduced no file changes.",
            metadata={"commit": commit.hexsha, "files_changed": 0},
        )

    content = "\n".join(_format_file_diff(d) for d in diffs)

    return ToolResult(
        success=True,
        content=content,
        metadata={"commit": commit.hexsha, "files_changed": len(diffs)},
    )


def build_git_diff_tool(repository_id: str) -> Tool:
    repository_path = get_repository_path(repository_id)

    async def git_diff(
        commit_hash: str,
        context_lines: int = DEFAULT_CONTEXT_LINES,
    ) -> ToolResult:
        return await _git_diff(repository_path, commit_hash, context_lines)

    return Tool(
        name="git_diff",
        description=(
            "Return the raw unified diff - the actual code changes, not a "
            "summary - introduced by one commit, computed against its "
            "first parent (or against an empty tree if it is the "
            "repository's initial commit). Arguments: commit_hash "
            "(string, required) - a full or abbreviated commit SHA, "
            "usually obtained from git_history; context_lines (integer, "
            "optional, default 3) - lines of unchanged context shown "
            "around each change. Use this tool when the user asks what "
            "changed in a commit, wants to see the diff or patch, asks "
            "about code changes, or wants the latest modifications shown "
            "in detail. Use git_history first to find the right "
            "commit_hash if you do not already have one."
        ),
        function=git_diff,
    )
