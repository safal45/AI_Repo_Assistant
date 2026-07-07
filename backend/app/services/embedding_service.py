from app.ai.embeddings.factory import get_embedding
from app.repositories.code_chunk_repository import (
    get_chunks_by_repository,
    update_chunk_embedding,
)
from app.services.repository_service import get_owned_repository


async def generate_embeddings(
    repository_id: str,
    current_user_id: str,
):
    """
    Generate embeddings for all chunks in a repository
    and store them in MongoDB.
    """

    await get_owned_repository(repository_id, current_user_id)

    embedding_provider = get_embedding()

    chunks = await get_chunks_by_repository(repository_id)

    for chunk in chunks:
        vector = await embedding_provider.create_embedding(
            chunk["content"]
        )

        await update_chunk_embedding(
            chunk_id=str(chunk["_id"]),
            embedding=vector,
        )

    return {
        "message": "Embeddings generated successfully.",
        "chunks": len(chunks),
    }