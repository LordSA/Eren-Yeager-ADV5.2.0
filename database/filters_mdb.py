import motor.motor_asyncio
from pyrogram import enums
from info import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class FilterDB:
    def __init__(self, uri, db_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[db_name]
        self.col = self.db['filters']

    async def create_index(self):
        """
        Creates a compound index for fast searching.
        Run this once in your bot's on_startup.
        """
        await self.col.create_index(
            [("group_id", 1), ("text", 1)],
            unique=True
        )
        logger.info("Created filter database index.")

    async def add_filter(self, grp_id, text, reply_text, btn, file, alert):
        """Adds or updates a filter in the single collection"""
        data = {
            "group_id": int(grp_id),
            "text": str(text),
            "reply": str(reply_text),
            "btn": str(btn),
            "file": str(file),
            "alert": str(alert),
        }

        try:
            await self.col.update_one(
                {"group_id": int(grp_id), "text": str(text)},
                {"$set": data},
                upsert=True
            )
        except Exception as e:
            logger.exception(f"Error adding filter: {e}")

    async def find_filter(self, group_id, name):
        """Finds a filter in the single collection"""
        try:
            file = await self.col.find_one(
                {"group_id": int(group_id), "text": name}
            )
            if not file:
                return None, None, None, None

            return (
                file.get("reply"),
                file.get("btn"),
                file.get("alert"),
                file.get("file")
            )
        except Exception as e:
            logger.exception(f"Error finding filter: {e}")
            return None, None, None, None

    async def get_filters(self, group_id):
        """Gets all filter names for a specific group"""
        texts = []
        try:
            cursor = self.col.find({"group_id": int(group_id)})
            async for file in cursor:
                texts.append(file["text"])
        except Exception as e:
            logger.exception(f"Error getting filters: {e}")
        return texts

    async def delete_filter(self, message, text, group_id):
        """Deletes a filter. Faster (1 query instead of 2)."""
        
        query = {"group_id": int(group_id), "text": text}
        result = await self.col.delete_one(query)

        if result.deleted_count == 1:
            await message.reply_text(
                f"`{text}` deleted. I'll not respond to that filter anymore.",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN,
            )
        else:
            await message.reply_text("Couldn't find that filter!", quote=True)

    async def del_all(self, message, group_id, title):
        """Deletes all filters for a group. Much faster now."""
        try:
            result = await self.col.delete_many({"group_id": int(group_id)})

            if result.deleted_count > 0:
                await message.edit_text(f"All {result.deleted_count} filters from {title} have been removed.")
            else:
                await message.edit_text(f"Nothing to remove in {title}!")
                
        except Exception as e:
            await message.edit_text("Couldn't remove all filters from group!")
            logger.exception(f"Error deleting all filters: {e}")

    async def count_filters(self, group_id):
        """Counts all filters for a specific group."""
        count = await self.col.count_documents({"group_id": int(group_id)})
        return count if count > 0 else False

    async def filter_stats(self):
        """
        Gets total stats. This is now
        INCREDIBLY FAST (2 queries instead of N+1).
        """
        total_count = await self.col.count_documents({})
        total_collections = len(await self.col.distinct("group_id"))

        return total_collections, total_count

filters_db = FilterDB(DATABASE_URI, DATABASE_NAME)