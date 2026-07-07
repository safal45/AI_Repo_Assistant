from app.schemas.repository import RepositoryResponse


def serialize_repository(repository: dict) -> RepositoryResponse:
    return RepositoryResponse(
        id=str(repository["_id"]),
        github_url=repository["github_url"],
        name=repository["name"],
        status=repository["status"],
        created_at=repository["created_at"],
    )