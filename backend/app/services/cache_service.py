import asyncio
import hashlib
import json
import redis.asyncio as redis
from app.config.settings import settings

_redis_client = None
_loop = None


def get_redis():
    global _redis_client, _loop
    
    current_loop = asyncio.get_running_loop()
    
    if _redis_client is None or _loop is not current_loop:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        _loop = current_loop
    
    return _redis_client


TTL_7_DAYS = 604800


async def get_cached_embedding(text: str) -> list[float] | None:
    hash_value = hashlib.md5(text.encode()).hexdigest()
    key = f"embedding:{hash_value}"
    
    cached_data = await get_redis().get(key)      # ← get_redis()
    
    if cached_data:
        return json.loads(cached_data)
    return None


async def cache_embedding(text: str, embedding: list[float]) -> None:
    hash_value = hashlib.md5(text.encode()).hexdigest()
    key = f"embedding:{hash_value}"
    
    stringified_embedding = json.dumps(embedding)
    
    await get_redis().set(key, stringified_embedding, ex=TTL_7_DAYS)   # ← get_redis()