import os
import mimetypes
import traceback
import requests  # <-- 1. Import requests
import asyncio   # <-- 2. Import asyncio
import logging
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)

# --- Helper function to get filename and extension ---
def get_file_info(replied_message):
    """Extracts filename and extension from a message."""
    filename = "file" # Default
    file_ext = None

    if replied_message.photo:
        filename = "photo.jpg"
        file_ext = ".jpg"
    elif replied_message.animation:
        filename = "animation.gif"
        file_ext = ".gif"
    elif replied_message.document:
        filename = replied_message.document.file_name
    elif replied_message.video:
        filename = replied_message.video.file_name
    
    if filename and file_ext is None:
        file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext is None:
        file_ext = "" 
        filename = "file"

    return filename, file_ext


@Client.on_message(filters.command(["tgmedia", "tgraph", "telegraph"]))
async def telegraph_handler(client, message: Message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply("Reply to a supported media file")

    status_msg = await message.reply("Processing, please wait...")
    
    filename, file_ext = get_file_info(replied)
    
    MIME_MAP = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
    }
    mime_type = MIME_MAP.get(file_ext)
    
    if mime_type is None:
        return await status_msg.edit_text(f"Unsupported file type: ({file_ext})")
        
    try:
        await status_msg.edit_text("Downloading file to memory...")
        file_stream = await client.download_media(replied, in_memory=True)
        file_stream.seek(0)
        
        await status_msg.edit_text("Uploading to Telegraph...")

        # --- 3. THE FIX: Run blocking 'requests.post' in a thread ---
        
        # A. Prepare the 'files' data for the requests library
        files_data = {
            'file': (filename, file_stream, mime_type)
        }
        
        # B. Run the blocking 'requests.post' in an asyncio thread
        response = await asyncio.to_thread(
            requests.post,
            'https://telegra.ph/upload',
            files=files_data
        )

        if response.status_code == 200:
            response_json = response.json()
        else:
            return await status_msg.edit_text(f"Upload Error: Status {response.status_code}. Response: {response.text}")
        # --- END OF FIX ---

    except Exception as e:
        logger.exception(f"Telegraph handler failed: {e}")
        return await status_msg.edit_text(f"An error occurred: {e}")

    # --- Process the response ---
    link = None
    if isinstance(response_json, list) and len(response_json) > 0:
        item = response_json[0]
        if isinstance(item, dict) and 'src' in item:
            link = f"https://telegra.ph{item['src']}"
        elif 'error' in item:
             return await status_msg.edit_text(f"Telegraph Error: {item.get('error')}")
    
    if link is None:
        return await status_msg.edit_text(f"❌ Unexpected response: {response_json}")

    await status_msg.delete()
    
    await message.reply(
        f"<b>Link:</b>\n\n<code>{link}</code>",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("『𝕺𝙿𝙴𝙽 B_𝕷𝙸𝙽𙺈』", url=link), 
                    InlineKeyboardButton(
                        "『𝕾𝙷𝙰𝚁𝙴 𝕷𝙸𝙽𙺈』",
                        url=f"https://telegram.me/share/url?url={link}",
                    ),
                ],
                [InlineKeyboardButton("『𝙿𝚁𝙴𝚅』", callback_data="close_data")],
            ]
        ),
    )