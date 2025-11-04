from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
mycol = db["USER"]

async def set_lg_code(chat_id: int, lg_code: str):
    """
    Sets a user's language code.
    Creates the user if they don't exist (upsert=True).
    """
    await mycol.update_one(
        {"_id": chat_id},
        {"$set": {"lg_code": lg_code}},
        upsert=True
    )


async def unset_lg_code(chat_id: int):
    """
    Sets a user's language code to None.
    Creates the user if they don't exist (upsert=True).
    This function perfectly replaces the old 'insert' function.
    """
    await mycol.update_one(
        {"_id": chat_id},
        {"$set": {"lg_code": None}},
        upsert=True
    )


async def get_lg_code(chat_id: int):
    """Finds a user and returns *only* their lg_code."""
    doc = await mycol.find_one({"_id": chat_id}, {"lg_code": 1})
    return doc.get("lg_code") if doc else None


async def get_all_user_ids():
    """
    Gets a list of all user IDs in the collection.
    This is much faster than iterating a cursor.
    """
    return await mycol.distinct("_id")


async def get_user(id: int):
    """Gets the full document for a single user."""
    return await mycol.find_one({"_id": id})