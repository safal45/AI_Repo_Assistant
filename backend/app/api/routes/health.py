from fastapi import APIRouter

from app.database.database import get_db

router = APIRouter()


@router.get("/health")
async def health():
    await get_db().command("ping")

    return {
        "status": "healthy"
    }