from pyrogram import Client, filters, enums
from pyrogram.types import Message
from typing import Tuple, Optional

def extract_user(client: Client, message: Message) -> Tuple[Optional[int], Optional[str]]:
    user_id = None
    user_first_name = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name
    
    elif len(message.command) > 1:
        text = message.command[1]
        
        if text.startswith("@"):
            try:
                user_id = text
                user_first_name = text
            except Exception:
                pass
        
        elif text.isdigit():
            user_id = int(text)
            user_first_name = text 
            
    return user_id, user_first_name

@Client.on_message(filters.command("gunban") & filters.admin)
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

@Client.on_message(filters.command("unmute") & filters.admin)
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