import unittest
import asyncio
from app.services.cache_service import get_cached_embedding, cache_embedding


class CacheTests(unittest.TestCase):
    def test_cache_miss_returns_none(self):
        result = asyncio.run(get_cached_embedding("random_text_xyz_12345"))
        self.assertIsNone(result)

    def test_cache_stores_and_retrieves(self):
        text = "test query"
        embedding = [0.1, 0.2, 0.3]

        async def _run():
            await cache_embedding(text, embedding)
            return await get_cached_embedding(text)

        result = asyncio.run(_run())
        self.assertEqual(result, embedding)