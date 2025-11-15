import os
from time import time
from datetime import datetime
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import Message
from plugins.Tools.help_func.extract_user import extract_user
from plugins.Tools.help_func.last_online import last_online
from plugins.Tools.help_func.cust_p_filters import owner_filter

@Client.on_message(filters.command('whois') & owner_filter)
async def who_is(client, message: Message):
    """Extracts user information."""
    status_message = await message.reply_text(
        "നിക്കു നെൻപ നോക്കട്ടെ 🙂"
    )
    
    from_user = None
    from_user_id, _ = extract_user(message)
    try:
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        await status_message.edit(str(error))
        return
        
    if from_user is None:
        await status_message.edit("no valid user_id / message specified")
        return
    
    first_name = from_user.first_name or ""
    last_name = from_user.last_name or ""
    username = from_user.username or ""
    
    message_out_str = (
        "<b>Name:</b> "
        f"<a href='tg://user?id={from_user.id}'>{first_name}</a>\n"
        f"<b>Suffix:</b> {last_name}\n"
        f"<b>Username:</b> @{username}\n"
        f"<b>User ID:</b> <code>{from_user.id}</code>\n"
        + (f"<b>User Link:</b> {from_user.mention}\n" if from_user.username else "")
        + (f"<b>Is Deleted:</b> True\n" if from_user.is_deleted else "")
        + (f"<b>Is Verified:</b> True\n" if from_user.is_verified else "")
        + (f"<b>Is Scam:</b> True\n" if from_user.is_scam else "")
        + f"<b>Last Seen:</b> <code>{last_online(from_user)}</code>\n\n"
    )

    if message.chat.type in ["supergroup", "channel"]:
        try:
            chat_member_p = await message.chat.get_member(from_user.id)
            joined_date = datetime.fromtimestamp(
                chat_member_p.joined_date or time()
            ).strftime("%Y.%m.%d %H:%M:%S")
            message_out_str += (
                "<b>Joined on:</b> <code>"
                f"{joined_date}"
                "</code>\n"
            )
        except UserNotParticipant:
            pass
            
    chat_photo = from_user.photo
    if chat_photo:
        file_stream = await client.download_media(
            message=chat_photo.big_file_id,
            in_memory=True
        )
        await message.reply_photo(
            photo=file_stream, 
            quote=True,
            caption=message_out_str,
            disable_notification=True
        )
    else:
        await message.reply_text(
            text=message_out_str,
            quote=True,
            disable_notification=True
        )
        
    await status_message.delete()