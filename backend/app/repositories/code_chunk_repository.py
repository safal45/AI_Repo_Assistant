from app.database.database import get_db
from app.models.code_chunk import CodeChunk
from bson import ObjectId


async def create_chunks(chunks: list[CodeChunk]):
    if not chunks:
        return

    await get_db().code_chunks.insert_many(
        [chunk.model_dump() for chunk in chunks]
    )


async def get_chunks_by_repository(repository_id: str):
    return await get_db().code_chunks.find(
        {"repository_id": repository_id}
    ).to_list(length=None)


async def delete_chunks_by_repository(repository_id: str):
    await get_db().code_chunks.delete_many(
        {"repository_id": repository_id}
    )

async def update_chunk_embedding(
    chunk_id: str,
    embedding: list[float],
):
    await get_db().code_chunks.update_one(
        {
            "_id": ObjectId(chunk_id),
        },
        {
            "$set": {
                "embedding": embedding,
            }
        },
    )