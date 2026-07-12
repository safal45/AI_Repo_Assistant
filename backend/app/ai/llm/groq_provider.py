from groq import Groq

from app.ai.llm.base import BaseLLM
from app.config.settings import settings


class GroqLLM(BaseLLM):

    def __init__(self):
        self.client = Groq(
            api_key=settings.GROQ_API_KEY
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_mode: bool = False,
    ) -> str:

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        kwargs = {}

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            **kwargs,
        )

        return response.choices[0].message.content