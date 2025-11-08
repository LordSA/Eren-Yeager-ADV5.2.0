import os
import requests
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)

def get_file_info(replied_message):
    """Extracts filename and extension from a message."""
    filename = "file"
    file_ext = None

    if replied_message.photo:
        file_ext = ".jpg"
    elif replied_message.animation:
        file_ext = ".gif"
    elif replied_message.document:
        filename = replied_message.document.file_name
        file_ext = os.path.splitext(filename)[1].lower()
    elif replied_message.video:
        file_ext = ".mp4"
    
    if not file_ext:
        file_ext = ""

    return file_ext


@Client.on_message(filters.command("tgraph"))
async def telegraph_handler(client, message: Message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply("Reply to a supported media file")

    status_msg = await message.reply("Processing...")
    
    file_ext = get_file_info(replied)
    
    # Map extensions to mime types
    MIME_MAP = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
    }
    
    mime_type = MIME_MAP.get(file_ext)
    
    if mime_type is None:
        return await status_msg.edit_text(f"Unsupported file type: {file_ext}\nSupported: jpg, jpeg, png, gif, mp4")
        
    file_path = None
    try:
        await status_msg.edit_text("Downloading...")
        file_path = await client.download_media(replied)
        
        await status_msg.edit_text("Uploading to Telegraph...")

        # Upload using requests in thread - THE KEY: filename must be 'file'
        def upload():
            with open(file_path, 'rb') as f:
                return requests.post(
                    'https://telegra.ph/upload',
                    files={'file': ('file', f, mime_type)}
                ).json()
        
        response_json = await asyncio.to_thread(upload)

    except Exception as e:
        logger.exception(f"Telegraph upload failed: {e}")
        return await status_msg.edit_text(f"Error: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

    # Process response
    link = None
    if isinstance(response_json, list) and len(response_json) > 0:
        item = response_json[0]
        if isinstance(item, dict) and 'src' in item:
            link = f"https://telegra.ph{item['src']}"
        elif 'error' in item:
            return await status_msg.edit_text(f"Telegraph Error: {item.get('error')}")
    
    if link is None:
        return await status_msg.edit_text(f"Unexpected response: {response_json}")

    await status_msg.delete()
    
    await message.reply(
        f"<b>Link:</b>\n\n<code>{link}</code>",
        quote=True,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Open Link", url=link),
                InlineKeyboardButton("Share", url=f"https://telegram.me/share/url?url={link}")
            ]
        ])
    )