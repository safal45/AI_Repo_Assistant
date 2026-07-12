from app.database.database import get_db


async def vector_search(
    repository_id: str,
    embedding: list[float],
    limit: int = 5,
):
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 100,
                "limit": limit,
                "filter": {
                    "repository_id": repository_id,
                },
            }
        }
    ]

    return await get_db().code_chunks.aggregate(
        pipeline
    ).to_list(length=limit)