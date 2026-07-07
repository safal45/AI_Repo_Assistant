from app.ai.embeddings.factory import get_embedding
from app.ai.llm.factory import get_llm

from app.repositories.search_repository import vector_search
from app.services.repository_service import get_owned_repository


async def chat(
    repository_id: str,
    current_user_id: str,
    question: str,
):
    await get_owned_repository(repository_id, current_user_id)

    embedding_provider = get_embedding()

    llm = get_llm()

    question_embedding = await embedding_provider.create_embedding(
        question
    )

    chunks = await vector_search(
        repository_id=repository_id,
        embedding=question_embedding,
        limit=5,
    )

    context = "\n\n".join(
        chunk["content"]
        for chunk in chunks
    )

    system_prompt = """
You are an expert software engineer.

Answer ONLY using the provided repository context.

If the answer is not present in the context,
reply exactly:

I couldn't find that information in the repository.

Never hallucinate.
"""

    prompt = f"""
Repository Context:

{context}

User Question:

{question}
"""

    answer = await llm.generate(
        prompt=prompt,
        system_prompt=system_prompt,
    )

    return {
        "answer": answer,
        "chunks_found": len(chunks),
    }