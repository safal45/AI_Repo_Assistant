from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from app.agent.tool import Tool
from app.agent.tool_result import ToolResult
from app.utils.path import get_repository_path

DEFAULT_MAX_COMMITS = 10

COMMIT_SEPARATOR = "\n----------------------------------------------------\n\n"


def _format_commit(commit) -> str:
    return (
        f"Commit: {commit.hexsha[:7]}\n"
        f"Author: {commit.author.name}\n"
        f"Date: {commit.committed_datetime.date().isoformat()}\n"
        f"Message:\n{commit.message.strip()}\n"
    )


async def _git_log(
    repository_path: Path,
    max_commits: int = DEFAULT_MAX_COMMITS,
) -> ToolResult:
    try:
        repo = Repo(repository_path)

        commits = list(
            repo.iter_commits(max_count=max(max_commits, 0))
        )
    except (InvalidGitRepositoryError, NoSuchPathError):
        return ToolResult(
            success=False,
            content="This repository could not be opened as a Git repository.",
            metadata={},
        )
    except GitCommandError as e:
        return ToolResult(
            success=False,
            content=f"Failed to read Git history for this repository: {e}",
            metadata={},
        )
    except ValueError:
        # GitPython raises ValueError when HEAD has no commits yet
        # (a brand-new, still-empty repository) - that is not a
        # failure, it just means there is no history yet.
        commits = []
    except Exception as e:
        # Defensive catch-all: a tool must never let a raw exception
        # reach the Agent loop - any unexpected failure degrades to a
        # failed ToolResult instead.
        return ToolResult(
            success=False,
            content=f"Failed to read Git history for this repository: {e}",
            metadata={},
        )

    if not commits:
        return ToolResult(
            success=True,
            content="No commit history found for this repository.",
            metadata={
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
            "commit_count": len(commits),
            "latest_commit": commits[0].hexsha,
            "authors": authors,
        },
    )


def build_git_log_tool(repository_id: str) -> Tool:
    repository_path = get_repository_path(repository_id)

    async def git_log(
        max_commits: int = DEFAULT_MAX_COMMITS,
    ) -> ToolResult:
        return await _git_log(repository_path, max_commits)

    return Tool(
        name="git_log",
        description=(
            "Return the most recent Git commits for the whole repository "
            "(not scoped to one file) - commit hash, author, date, and "
            "commit message for each. Argument: max_commits (integer, "
            "optional, default 10) - maximum number of commits to return, "
            "most recent first. Use this tool when the user asks for the "
            "repository's last/latest/recent commits, its overall commit "
            "log, or general recent activity, without naming a specific "
            "file. Use git_history instead when the question is about one "
            "particular file's history."
        ),
        function=git_log,
    )
