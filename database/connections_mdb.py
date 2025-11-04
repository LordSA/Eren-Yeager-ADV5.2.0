from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
mycol = db['CONNECTION']


async def add_connection(group_id, user_id):
    if await mycol.find_one({"_id": user_id, "group_details.group_id": group_id}):
        return False
    group_details = {"group_id": group_id}
    
    try:
        await mycol.update_one(
            {"_id": user_id},
            {
                "$push": {"group_details": group_details},
                "$set": {"active_group": group_id},
                "$setOnInsert": {"_id": user_id}
            },
            upsert=True
        )
        return True
    except Exception as e:
        logger.exception(f"Some error occurred in add_connection! {e}")
        return False


async def active_connection(user_id):
    query = await mycol.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0}
    )
    if not query:
        return None
    return int(query.get("active_group")) if query.get("active_group") else None


async def all_connections(user_id):
    query = await mycol.find_one(
        {"_id": user_id},
        {"_id": 0, "active_group": 0}
    )
    return [x["group_id"] for x in query["group_details"]] if query else None


async def if_active(user_id, group_id):
    query = await mycol.find_one(
        {"_id": user_id},
        {"_id": 0, "group_details": 0}
    )
    return query and query.get("active_group") == group_id


async def make_active(user_id, group_id):
    update = await mycol.update_one(
        {"_id": user_id},
        {"$set": {"active_group": group_id}}
    )
    return update.modified_count != 0


async def make_inactive(user_id):
    update = await mycol.update_one(
        {"_id": user_id},
        {"$set": {"active_group": None}}
    )
    return update.modified_count != 0


async def delete_connection(user_id, group_id):
    try:
        update_result = await mycol.update_one(
            {"_id": user_id},
            {"$pull": {"group_details": {"group_id": group_id}}}
        )
        if update_result.modified_count == 0:
            return False
        query = await mycol.find_one({"_id": user_id}, {"_id": 0}).
        if query and query.get("active_group") != group_id:
            return True
        new_active_group = None
        if query and len(query["group_details"]) >= 1:
            new_active_group = query["group_details"][-1]["group_id"]
        await mycol.update_one(
            {"_id": user_id},
            {"$set": {"active_group": new_active_group}}
        )
        return True

    except Exception as e:
        logger.exception(f"Some error occurred in delete_connection! {e}")
        return False