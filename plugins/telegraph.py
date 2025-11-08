import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegraph import upload_file

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("tgraph"))
async def telegraph_handler(client, message: Message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply("Reply to a supported media file")

    if not replied.media:
        return await message.reply("Reply to a valid media file")

    status_msg = await message.reply("Processing...")
    
    file_path = None
    try:
        await status_msg.edit_text("📥 Downloading...")
        
        file_path = await client.download_media(replied)
        
        if not file_path:
            return await status_msg.edit_text("❌ Failed to download media")
        
        await status_msg.edit_text("📤 Uploading to Telegraph...")
        
        response = upload_file(file_path)
        link = f"https://telegra.ph{response[0]}"
        
        await status_msg.delete()
        
        await message.reply(
            f"<b>🌐 Telegraph Link:</b>\n\n<code>{link}</code>",
            quote=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Open Link", url=link),
                    InlineKeyboardButton("Share", url=f"https://telegram.me/share/url?url={link}")
                ]
            ])
        )
        
    except Exception as e:
        logger.exception(f"Telegraph upload failed: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass