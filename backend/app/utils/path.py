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


def resolve_safe_path(repository_path: Path, relative_path: str) -> Path:
    """
    Resolve `relative_path` against `repository_path` and guarantee the
    result stays inside the repository.

    Every agent tool that accepts an LLM-supplied path must go through
    this - the LLM is not a trusted source of file paths, and this is
    what blocks path traversal (e.g. "../../../etc/passwd" or an
    absolute path escaping the repo root).
    """

    repository_root = repository_path.resolve()
    candidate = (repository_root / relative_path).resolve()

    if not candidate.is_relative_to(repository_root):
        raise ValueError(
            f"Path '{relative_path}' escapes the repository directory."
        )

    return candidate