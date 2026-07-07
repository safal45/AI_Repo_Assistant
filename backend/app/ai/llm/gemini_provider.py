from app.ai.llm.base import BaseLLM


class GeminiLLM(BaseLLM):

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        raise NotImplementedError("Coming soon")