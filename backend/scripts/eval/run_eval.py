import asyncio
import json
import sys
import time
from pathlib import Path
from app.ai.embeddings.factory import get_embedding_with_cache
from app.repositories.search_repository import vector_search

DEFAULT_REPOSITORY_ID = "REPLACE_WITH_REAL_REPOSITORY_ID"
EVAL_CASES_PATH = Path(__file__).parent / "eval_cases.json"
TOP_K = 5


async def run_eval():
    repository_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REPOSITORY_ID

    cases = json.loads(EVAL_CASES_PATH.read_text())

    hits = 0
    latencies = []

    for case in cases:
        question = case["question"]
        expected_files = set(case["expected_files"])

        start = time.time()

        embedding = await get_embedding_with_cache(question)

        chunks = await vector_search(
            repository_id=repository_id,
            embedding=embedding,
            limit=TOP_K,
        )

        latency = time.time() - start
        latencies.append(latency)

        retrieved_files = {chunk["file_path"] for chunk in chunks}
        hit = bool(retrieved_files & expected_files)

        if hit:
            hits += 1

        print(f"[{'HIT' if hit else 'MISS'}] ({latency:.3f}s) {question}")
        print(f"    expected:   {sorted(expected_files)}")
        print(f"    retrieved:  {sorted(retrieved_files)}")

    total = len(cases)
    hit_rate = hits / total if total else 0.0
    avg_latency = sum(latencies) / total if total else 0.0

    print()
    print(f"hit_rate:    {hit_rate:.1%} ({hits}/{total})")
    print(f"avg_latency: {avg_latency:.3f}s")


asyncio.run(run_eval())
