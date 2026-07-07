from app.config.settings import settings

from app.ai.embeddings.gemini_provider import GeminiEmbedding


def get_embedding():

    if settings.EMBEDDING_PROVIDER == "gemini":
        return GeminiEmbedding()

    raise ValueError(
        f"Unsupported Embedding Provider: {settings.EMBEDDING_PROVIDER}"
    )