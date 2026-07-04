from fastapi import APIRouter

from app.database.database import db

router = APIRouter()


@router.get("/health")
async def health():
    await db.command("ping")

    return {
        "status": "healthy"
    }