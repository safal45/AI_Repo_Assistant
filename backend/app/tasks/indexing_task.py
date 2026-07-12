import asyncio
from app.config.celery_app import celery_app
from app.services.indexing_service import index_repository
from app.repositories.repository_repository import update_repository_status

@celery_app.task(name="index_repository_task")
def index_repository_task(repository_id, current_user_id):
    try:
        asyncio.run(index_repository(repository_id, current_user_id))
    except Exception as e:
        asyncio.run(update_repository_status(repository_id, "failed"))
        raise