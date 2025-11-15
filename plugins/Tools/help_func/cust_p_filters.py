from pyrogram import filters, enums
import logging
from info import ADMINS
from plugins.Tools.help_func.admin_check import admin_check

logger = logging.getLogger(__name__)

def f_sudo_filter(filt, client, message):
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

sudo_filter = filters.create(
    func=f_sudo_filter,
    name="SudoFilter"
)

def f_owner_filter(filt, client, message):
    user_id = message.from_user.id
    logger.info(f"[Filter Debug] User trying command: {user_id}")
    logger.info(f"[Filter Debug] ADMINS list: {ADMINS}")    
    if ADMINS and message.from_user and message.from_user.id in ADMINS:
        return True
    return False

owner_filter = filters.create(
    func=f_owner_filter,
    name="OwnerFilter"
)

async def f_admin_filter(filt, client, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return False
    return await admin_check(message)

admin_filter = filters.create(
    func=f_admin_filter,
    name="AdminFilter"
)