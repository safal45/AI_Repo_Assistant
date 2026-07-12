from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from app.agent.tool import Tool
from app.agent.tool_result import ToolResult
from app.utils.path import get_repository_path, resolve_safe_path

DEFAULT_MAX_COMMITS = 10

COMMIT_SEPARATOR = "\n----------------------------------------------------\n\n"


def _format_commit(commit) -> str:
    return (
        f"Commit: {commit.hexsha[:7]}\n"
        f"Author: {commit.author.name}\n"
        f"Date: {commit.committed_datetime.date().isoformat()}\n"
        f"Message:\n{commit.message.strip()}\n"
    )


async def _git_history(
    repository_path: Path,
    file_path: str,
    max_commits: int = DEFAULT_MAX_COMMITS,
) -> ToolResult:
    try:
        target = resolve_safe_path(repository_path, file_path)
    except ValueError as e:
        return ToolResult(
            success=False,
            content=str(e),
            metadata={"path": file_path},
        )

    if not target.is_file():
        return ToolResult(
            success=False,
            content="File not found.",
            metadata={"path": file_path},
        )

    try:
        repo = Repo(repository_path)
        relative_path = target.relative_to(repository_path.resolve())

        commits = list(
            repo.iter_commits(
                paths=str(relative_path),
                max_count=max(max_commits, 0),
            )
        )
    except (InvalidGitRepositoryError, NoSuchPathError):
        return ToolResult(
            success=False,
            content=f"'{file_path}' is not inside a Git repository.",
            metadata={"path": file_path},
        )
    except GitCommandError as e:
        return ToolResult(
            success=False,
            content=f"Failed to read Git history for '{file_path}': {e}",
            metadata={"path": file_path},
        )
    except ValueError:
        # GitPython raises ValueError when HEAD has no commits yet
        # (a brand-new, still-empty repository) - that is not a
        # failure, it just means there is no history for any file.
        commits = []
    except Exception as e:
        # Defensive catch-all: a tool must never let a raw exception
        # reach the Agent loop - any unexpected failure degrades to a
        # failed ToolResult instead.
        return ToolResult(
            success=False,
            content=f"Failed to read Git history for '{file_path}': {e}",
            metadata={"path": file_path},
        )

    if not commits:
        return ToolResult(
            success=True,
            content=f"No commit history found for '{file_path}'.",
            metadata={
                "path": file_path,
                "commit_count": 0,
                "latest_commit": None,
                "authors": [],
            },
        )

    content = COMMIT_SEPARATOR.join(_format_commit(commit) for commit in commits)
    authors = sorted({commit.author.name for commit in commits})

    return ToolResult(
        success=True,
        content=content,
        metadata={
            "path": file_path,
            "commit_count": len(commits),
            "latest_commit": commits[0].hexsha,
            "authors": authors,
        },
    )


def build_git_history_tool(repository_id: str) -> Tool:
    repository_path = get_repository_path(repository_id)

    async def git_history(
        file_path: str,
        max_commits: int = DEFAULT_MAX_COMMITS,
    ) -> ToolResult:
        return await _git_history(repository_path, file_path, max_commits)

    return Tool(
        name="git_history",
        description=(
            "Return the recent Git commit history for one file in the "
            "repository - commit hash, author, date, and commit message "
            'for each change. Arguments: file_path (string, required) - '
            "path relative to the repository root; max_commits (integer, "
            "optional, default 10) - maximum number of commits to return, "
            "most recent first. Use this tool when the user asks who "
            "changed something, when it was changed, why it was changed, "
            "what the recent commits or modifications to a file were, or "
            "wants its commit history. Does not show the diff content "
            "itself - only commit metadata and messages."
        ),
        function=git_history,
    )
