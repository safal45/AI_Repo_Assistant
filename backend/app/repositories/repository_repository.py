from datetime import datetime

from bson import ObjectId

from app.database.database import db
from app.models.repository import Repository


async def create_repository(repository: Repository):
    result = await db.repositories.insert_one(
        repository.model_dump()
    )

    return await db.repositories.find_one(
        {"_id": result.inserted_id}
    )

async def get_repository_by_id(repository_id: str):
    return await db.repositories.find_one(
        {"_id": ObjectId(repository_id)}
    )

async def get_repository_by_url(
    owner_id: str,
    github_url: str,
):
    ...

async def update_repository_status(
    repository_id: str,
    status: str,
):
    await db.repositories.update_one(
        {"_id": ObjectId(repository_id)},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow(),
            }
        },
    )