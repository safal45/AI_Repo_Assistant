from bson import ObjectId

from app.database.database import get_db
from app.models.user import User



async def get_user_by_email(email: str):
    return await get_db().users.find_one(
        {"email": email}
    )
    
async def get_user_by_id(user_id: str):
    return await get_db().users.find_one(
        {
            "_id": ObjectId(user_id)
        }
    )
async def create_user(user: User):
    result = await get_db().users.insert_one(user.model_dump())

    return await get_db().users.find_one(
        {"_id": result.inserted_id}
    )