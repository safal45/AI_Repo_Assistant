from pathlib import Path

from git import Repo
from git.exc import GitCommandError
from app.models.repository import Repository
from app.exceptions.git import GitCloneError


def clone_repository(
    repository: Repository,
    local_path: Path,
) -> None:
    """
    Clone a GitHub repository to the given local path.

    Raises:
        GitCloneError: If cloning fails.
    """

    # Already cloned
    if any(local_path.iterdir()):
        return

    try:
        Repo.clone_from(
            repository.github_url,
            local_path,
        )

    except GitCommandError as e:
        raise GitCloneError(
            f"Failed to clone repository: {e}"
        )