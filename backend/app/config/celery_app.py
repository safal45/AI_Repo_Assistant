from celery import Celery
from app.config.settings import settings

celery_app = Celery(
    "ai_repo_assistant",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

from app.tasks import indexing_task  
