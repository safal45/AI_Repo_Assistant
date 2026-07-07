import asyncio

from app.ai.embeddings.factory import get_embedding


async def main():

    embedding = get_embedding()

    vector = await embedding.create_embedding(
        "What is JWT authentication?"
    )

    print(type(vector))
    print(len(vector))
    print(vector[:10])   # first 10 values


asyncio.run(main())