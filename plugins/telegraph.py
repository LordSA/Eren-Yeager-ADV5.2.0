import os
import aiohttp
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)

def get_file_info(replied_message):
    """Extracts filename and extension from a message."""
    filename = "file"
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


@Client.on_message(filters.command("tgraph"))
async def telegraph_handler(client, message: Message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply("Reply to a supported media file")

    status_msg = await message.reply("Processing...")
    
    filename, file_ext = get_file_info(replied)
    
    SUPPORTED = ['.jpg', '.jpeg', '.png', '.gif', '.mp4']
    
    if file_ext not in SUPPORTED:
        return await status_msg.edit_text(f"Unsupported file type: {file_ext}\nSupported: {', '.join(SUPPORTED)}")
        
    file_path = None
    try:
        await status_msg.edit_text("Downloading...")
        
        # Download to temporary file
        file_path = await client.download_media(replied)
        
        await status_msg.edit_text("Uploading to Telegraph...")

        # Upload using aiohttp with file
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename=os.path.basename(file_path))
                
                async with session.post('https://telegra.ph/upload', data=form) as resp:
                    if resp.status == 200:
                        response_json = await resp.json()
                    else:
                        text = await resp.text()
                        return await status_msg.edit_text(f"Upload failed: {resp.status}\n{text}")

    except Exception as e:
        logger.exception(f"Telegraph upload failed: {e}")
        return await status_msg.edit_text(f"Error: {str(e)}")
    finally:
        # Clean up temporary file
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