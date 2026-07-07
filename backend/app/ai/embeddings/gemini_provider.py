from google import genai

from app.ai.embeddings.base import BaseEmbedding
from app.config.settings import settings


class GeminiEmbedding(BaseEmbedding):

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    async def create_embedding(
        self,
        text: str,
    ) -> list[float]:

        response = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )

        return response.embeddings[0].values
    