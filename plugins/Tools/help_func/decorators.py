import logging
from functools import wraps
from pyrogram import enums
from pyrogram.errors import ChatAdminRequired
from info import ADMINS
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)

def check_group_admin(func):
    """
    Decorator to check if the user is an admin in the correct group.
    It injects 'grp_id' and 'title' as kwargs into the decorated function.
    """
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        userid = message.from_user.id if message.from_user else None
        if not userid:
            return await message.reply("You are an anonymous admin. Use /connect in PM.")

        chat_type = message.chat.type
        
        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if not grpid:
                return await message.reply_text("I'm not connected to any groups!")
            grp_id = int(grpid)
            try:
                chat = await client.get_chat(grp_id)
                title = chat.title
            except Exception:
                return await message.reply_text("Make sure I'm still in your group and an admin!")
        
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = message.chat.id
            title = message.chat.title
        
        else:
            return await message.reply("This command only works in groups or in PM.")

        try:
            st = await client.get_chat_member(grp_id, userid)
        except ChatAdminRequired:
            return await message.reply("I'm not an admin in this group to check your status!")
            
        if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
        ):
            return 
        try:
            return await func(client, message, grp_id, title, *args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in decorated function {func.__name__}: {e}")
            await message.reply(f"An error occurred: {e}")

    return wrapper