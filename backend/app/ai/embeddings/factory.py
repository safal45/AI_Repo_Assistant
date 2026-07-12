from app.config.settings import settings

from app.ai.embeddings.gemini_provider import GeminiEmbedding
from app.services.cache_service import cache_embedding, get_cached_embedding


def get_embedding():

    if settings.EMBEDDING_PROVIDER == "gemini":
        return GeminiEmbedding()

    raise ValueError(
        f"Unsupported Embedding Provider: {settings.EMBEDDING_PROVIDER}"
    )

async def get_embedding_with_cache(text: str) -> list[float]:
    cached = await get_cached_embedding(text)
    if cached is not None:
        return cached
    
    embedding_provider = get_embedding()
    embedding = await embedding_provider.create_embedding(text)
    
    await cache_embedding(text, embedding)
    return embedding