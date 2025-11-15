from pyrogram import Client
from pyrogram.types import Message
from typing import Tuple, Optional

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