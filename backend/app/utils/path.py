from pathlib import Path

from app.config.settings import settings


def get_repository_path(repository_id: str) -> Path:
    """
    Returns the local path where a repository should be cloned.
    """

    base_path = Path(settings.REPOSITORIES_PATH)

    base_path.mkdir(parents=True, exist_ok=True)

    repo_path = base_path / repository_id

    repo_path.mkdir(parents=True, exist_ok=True)

    return repo_path