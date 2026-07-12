from app.ai.llm.base import BaseLLM


class GeminiLLM(BaseLLM):

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_mode: bool = False,
    ) -> str:
        raise NotImplementedError("Coming soon")