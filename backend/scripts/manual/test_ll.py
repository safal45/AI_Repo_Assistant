import asyncio

from app.ai.llm.factory import get_llm, settings


async def main():

    llm = get_llm()

    response = await llm.generate(
        prompt="What is your name and what infrastructure are you running on? Answer in one sentence.",
        system_prompt="You are running on groq's infrastructure using the llama-3.3-70b-versatile model.",
    )

    print(response)
    print(settings.LLM_PROVIDER)


asyncio.run(main())