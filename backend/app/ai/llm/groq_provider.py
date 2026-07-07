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

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
        )

        return response.choices[0].message.content