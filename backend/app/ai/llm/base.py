from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Base interface for all LLM providers.
    Every provider (Groq, Gemini, OpenAI, Claude, etc.)
    must implement the generate() method.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a response from the language model.

        Args:
            prompt: User input.
            system_prompt: Optional instruction for the model.
            json_mode: If True, constrain the provider to return a single
                JSON object rather than free-form text, when supported.

        Returns:
            Generated response as a string.
        """
        pass