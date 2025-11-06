import motor.motor_asyncio
from info import (
    DATABASE_NAME,
    DATABASE_URI,
    IMDB,
    IMDB_TEMPLATE,
    MELCOW_NEW_USERS,
    P_TTI_SHOW_OFF,
    SINGLE_BUTTON,
    SPELL_CHECK_REPLY,
    PROTECT_CONTENT,
)
from typing import List, Tuple, Dict, Optional


class Database:
    def __init__(self, uri: str, database_name: str):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col_users = self.db.users
        self.col_groups = self.db.groups

    # -------------------- User Helpers --------------------
    def _new_user(self, user_id: int, name: str) -> Dict:
        return {
            "id": user_id,
            "name": name,
            "ban_status": {"is_banned": False, "ban_reason": ""},
        }

    async def add_user(self, user_id: int, name: str):
        user = self._new_user(user_id, name)
        await self.col_users.insert_one(user)

    async def is_user_exist(self, user_id: int) -> bool:
        return bool(await self.col_users.find_one({"id": int(user_id)}))

    async def total_users_count(self) -> int:
        return await self.col_users.count_documents({})

    async def ban_user(self, user_id: int, reason: str = "No Reason"):
        await self.col_users.update_one(
            {"id": int(user_id)},
            {"$set": {"ban_status": {"is_banned": True, "ban_reason": reason}}},
        )

    async def remove_ban(self, user_id: int):
        await self.col_users.update_one(
            {"id": int(user_id)},
            {"$set": {"ban_status": {"is_banned": False, "ban_reason": ""}}},
        )

    async def get_ban_status(self, user_id: int) -> Dict:
        default = {"is_banned": False, "ban_reason": ""}
        user = await self.col_users.find_one({"id": int(user_id)})
        return user.get("ban_status", default) if user else default

    async def get_all_users(self):
        cursor = self.col_users.find({})
        return [user async for user in cursor]

    async def delete_user(self, user_id: int):
        await self.col_users.delete_many({"id": int(user_id)})

    async def get_user(self, user_id: int) -> Optional[Dict]:
        return await self.col_users.find_one({"id": int(user_id)})

    # -------------------- Group Helpers --------------------
    def _new_group(self, group_id: int, title: str) -> Dict:
        return {
            "id": group_id,
            "title": title,
            "chat_status": {"is_disabled": False, "reason": ""},
        }

    async def add_chat(self, chat_id: int, title: str):
        chat = self._new_group(chat_id, title)
        await self.col_groups.insert_one(chat)

    async def get_chat(self, chat_id: int) -> Optional[Dict]:
        chat = await self.col_groups.find_one({"id": int(chat_id)})
        return chat.get("chat_status") if chat else None

    async def disable_chat(self, chat_id: int, reason: str = "No Reason"):
        await self.col_groups.update_one(
            {"id": int(chat_id)},
            {"$set": {"chat_status": {"is_disabled": True, "reason": reason}}},
        )

    async def re_enable_chat(self, chat_id: int):
        await self.col_groups.update_one(
            {"id": int(chat_id)},
            {"$set": {"chat_status": {"is_disabled": False, "reason": ""}}},
        )

    async def update_settings(self, chat_id: int, settings: Dict):
        await self.col_groups.update_one({"id": int(chat_id)}, {"$set": {"settings": settings}})

    async def get_settings(self, chat_id: int) -> Dict:
        default = {
            "button": SINGLE_BUTTON,
            "botpm": P_TTI_SHOW_OFF,
            "file_secure": PROTECT_CONTENT,
            "imdb": IMDB,
            "spell_check": SPELL_CHECK_REPLY,
            "welcome": MELCOW_NEW_USERS,
            "template": IMDB_TEMPLATE,
        }
        chat = await self.col_groups.find_one({"id": int(chat_id)})
        return chat.get("settings", default) if chat else default

    # -------------------- Stats --------------------
    async def total_chat_count(self) -> int:
        return await self.col_groups.count_documents({})

    async def get_all_chats(self):
        cursor = self.col_groups.find({})
        return [chat async for chat in cursor]

    async def get_db_size(self) -> int:
        stats = await self.db.command("dbstats")
        return stats.get("dataSize", 0)

    async def get_banned(self) -> Tuple[List[int], List[int]]:
        users_cursor = self.col_users.find({"ban_status.is_banned": True})
        groups_cursor = self.col_groups.find({"chat_status.is_disabled": True})
        b_users = [user["id"] async for user in users_cursor]
        b_chats = [chat["id"] async for chat in groups_cursor]
        return b_users, b_chats


# Global database instance
db = Database(DATABASE_URI, DATABASE_NAME)
