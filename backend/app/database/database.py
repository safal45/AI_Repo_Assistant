# ye notanki kar rha ki motor phle event pr stuck h aage nhi bad rha

# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config.settings import settings


# client = AsyncIOMotorClient(settings.MONGODB_URI)

# db = client[settings.DATABASE_NAME]


import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

_client = None
_loop = None


def get_db():
    global _client, _loop

    current_loop = asyncio.get_event_loop()

    if _client is None or _loop is not current_loop:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
        _loop = current_loop

    return _client[settings.DATABASE_NAME]