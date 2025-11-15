from pyrogram import filters, enums
from info import ADMINS
from plugins.Tools.help_func.admin_check import admin_check

def f_sudo_filter(filt, client, message):
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

sudo_filter = filters.create(
    func=f_sudo_filter,
    name="SudoFilter"
)

def f_owner_filter(filt, client, message):
    if message.from_user:
        is_admin = message.from_user.id in ADMINS
        print(f"[Filter Debug] User: {message.from_user.id}, Is Admin: {is_admin}, ADMINS List: {ADMINS}")
        
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