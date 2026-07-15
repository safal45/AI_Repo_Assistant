from pathlib import Path

from git import Repo
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

    except Exception as e:
        # Broad on purpose: a bad URL, DNS/network failure, auth failure,
        # or disk error can all surface as different exception types here
        # (not just GitCommandError) - every one of them must become a
        # GitCloneError so create_new_repository's except block actually
        # catches it and marks the repository "failed" instead of letting
        # it escape as an unhandled 500 with the DB left in "pending".
        raise GitCloneError(
            f"Failed to clone repository: {e}"
        )