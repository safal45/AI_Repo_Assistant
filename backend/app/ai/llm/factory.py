from app.config.settings import settings

from app.ai.llm.gemini_provider import GeminiLLM
from app.ai.llm.groq_provider import GroqLLM


def get_llm():

    if settings.LLM_PROVIDER == "groq":
        return GroqLLM()

    if settings.LLM_PROVIDER == "gemini":
        return GeminiLLM()
    


    raise ValueError(
        f"Unsupported LLM Provider: {settings.LLM_PROVIDER}"
    )