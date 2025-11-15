from pyrogram import Client, filters, enums
from pyrogram.types import Message
from typing import Tuple, Optional
from plugins.Tools.help_func.cust_p_filters import admin_filter

async def extract_user(client: Client, message: Message) -> Tuple[Optional[int], Optional[str]]:
    user_id = None
    user_first_name = None
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name
    
    elif len(message.command) > 1:
        text = message.command[1]
        
        if text.startswith("@"):
            try:
                user = await client.get_users(text)
                user_id = user.id
                user_first_name = user.first_name
            except Exception:
                await message.reply_text("User not found.")
                return None, None
        
        elif text.isdigit():
            try:
                user_id = int(text)
                user_first_name = text 
            except ValueError:
                await message.reply_text("That's not a valid User ID.")
                return None, None
            
    return user_id, user_first_name

@Client.on_message(filters.command("gunban") & admin_filter)
async def unban_user(client: Client, message: Message):
    
    user_id, user_first_name = await extract_user(client, message)

    if not user_id:
        await message.reply_text("I can't find a user. Reply to someone or provide their user ID/username.")
        return

    try:
        await message.chat.unban_member(
            user_id=user_id
        )
    except Exception as error:
        await message.reply_text(str(error))
    else:
        await message.reply_text(
            f"✅ **Unbanned!**\n\n"
            f"User: <a href='tg://user?id={user_id}'>{user_first_name}</a>\n"
            f"They can now rejoin the group."
        )

@Client.on_message(filters.command("unmute") & admin_filter)
async def unmute_user(client: Client, message: Message):
    
    user_id, user_first_name = await extract_user(client, message)
    
    if not user_id:
        await message.reply_text("I can't find a user. Reply to someone or provide their user ID/username.")
        return

    try:
        await message.chat.unban_member(
            user_id=user_id
        )
    except Exception as error:
        await message.reply_text(str(error))
    else:
        await message.reply_text(
            f"✅ **Unmuted!**\n\n"
            f"User: <a href='tg://user?id={user_id}'>{user_first_name}</a>\n"
            f"They can now speak in the group."
        )