from app.models.code_chunk import CodeChunk
from app.repositories.code_chunk_repository import (
    create_chunks,
    delete_chunks_by_repository,
)
from app.repositories.repository_repository import update_repository_status
from app.services.parser_service import parse_python_file
from app.services.repository_service import get_owned_repository
from app.services.scanner_service import detect_language, list_files
from app.utils.path import get_repository_path


class RepositoryNotClonedError(Exception):
    """Raised when indexing is attempted on a repository that was never
    cloned to disk (get_repository_path() always creates the directory
    itself, so a bare existence check can't catch this - presence of
    '.git' is what actually proves a clone happened)."""


class NoChunksIndexedError(Exception):
    """Raised when a clone exists but indexing produced zero chunks -
    surfacing this loudly instead of marking the repo 'indexed' with
    nothing in it."""


async def index_repository(
    repository_id: str,
    current_user_id: str,
) -> int:

    await get_owned_repository(repository_id, current_user_id)

    repository_path = get_repository_path(repository_id)

    if not (repository_path / ".git").exists():
        raise RepositoryNotClonedError(
            f"Repository '{repository_id}' has not been cloned to disk "
            f"(no .git found at {repository_path}) - cannot index."
        )

    files = list_files(repository_path)

    chunks: list[CodeChunk] = []

    for file in files:
        if detect_language(file) != "python":
            continue

        chunks.extend(
            parse_python_file(
                repository_id,
                file,
                repository_path,
            )
        )

    if not chunks:
        raise NoChunksIndexedError(
            f"Indexing repository '{repository_id}' produced 0 chunks."
        )

    await delete_chunks_by_repository(repository_id)
    await create_chunks(chunks)

    await update_repository_status(
        repository_id,
        "indexed",
    )

    return len(chunks)
