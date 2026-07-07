from abc import ABC, abstractmethod


class BaseEmbedding(ABC):

    @abstractmethod
    async def create_embedding(
        self,
        text: str,
    ) -> list[float]:
        """
        Convert text into an embedding vector.
        """
        pass