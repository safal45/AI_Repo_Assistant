from datetime import datetime
from bson import ObjectId
from app.database.database import get_db
from app.models.repository import Repository


async def create_repository(repository: Repository):
    result = await get_db().repositories.insert_one(
        repository.model_dump()
    )

    return await get_db().repositories.find_one(
        {"_id": result.inserted_id}
    )

async def get_repository_by_id(repository_id: str):
    return await get_db().repositories.find_one(
        {"_id": ObjectId(repository_id)}
    )

async def get_repositories_by_owner(owner_id: str):
    return await get_db().repositories.find(
        {"owner_id": owner_id}
    ).to_list(length=None)

async def get_repository_by_url(
    owner_id: str,
    github_url: str,
):
    ...

async def update_repository_status(
    repository_id: str,
    status: str,
):
    await get_db().repositories.update_one(
        {"_id": ObjectId(repository_id)},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow(),
            }
        },
    )