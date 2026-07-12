import asyncio

from app.models.repository import Repository
from app.repositories.repository_repository import (
    create_repository,
    get_repositories_by_owner,
    get_repository_by_id,
    update_repository_status,
)
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
)
from app.serializers.repository_serializer import serialize_repository
from app.services.git_service import clone_repository
from app.utils.path import get_repository_path
from app.exceptions.git import GitCloneError
from fastapi import HTTPException, status

async def create_new_repository(
    repository: RepositoryCreate,
    current_user: dict,
) -> RepositoryResponse:

    repo_name = str(repository.github_url).rstrip("/").split("/")[-1]

    db_repository = Repository(
        owner_id=str(current_user["_id"]),
        github_url=str(repository.github_url),
        name=repo_name,
    )

    created_repository = await create_repository(
        db_repository
    )
    repository_id = str(created_repository["_id"])

    local_path = get_repository_path(repository_id)

    try:
        await asyncio.to_thread(
            clone_repository,
            db_repository,
            local_path,
        )

        await update_repository_status(
            repository_id,
            "ready",
        )

    except GitCloneError:

        await update_repository_status(
            repository_id,
            "failed",
        )

        raise HTTPException(
            status_code=400,
            detail="Failed to clone repository",
        )

    return serialize_repository(created_repository)

async def list_owned_repositories(
    current_user_id: str,
) -> list[RepositoryResponse]:

    repositories = await get_repositories_by_owner(current_user_id)

    return [
        serialize_repository(repository)
        for repository in repositories
    ]

async def get_owned_repository(
    repository_id: str,
    current_user_id: str,
) -> dict:

    repository = await get_repository_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    if str(repository["owner_id"]) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository",
        )

    return repository

