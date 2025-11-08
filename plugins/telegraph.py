import os
import logging
import httpx
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

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
        
        await status_msg.edit_text("📤 Uploading...")
        
        # Try Telegraph first
        try:
            async with httpx.AsyncClient() as http_client:
                with open(file_path, 'rb') as f:
                    files = {'file': f}
                    response = await http_client.post(
                        'https://telegra.ph/upload',
                        files=files,
                        timeout=30.0
                    )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                    if isinstance(item, dict) and 'src' in item:
                        link = f"https://telegra.ph{item['src']}"
                    elif isinstance(item, str):
                        link = f"https://telegra.ph{item}"
                    else:
                        raise Exception("Invalid Telegraph response")
                else:
                    raise Exception("Empty Telegraph response")
            else:
                raise Exception(f"Telegraph returned {response.status_code}")
                
        except Exception as tg_error:
            # Fallback to catbox.moe
            logger.info(f"Telegraph failed ({tg_error}), trying catbox.moe...")
            await status_msg.edit_text("📤 Uploading to Catbox...")
            
            async with httpx.AsyncClient() as http_client:
                with open(file_path, 'rb') as f:
                    files = {'fileToUpload': f}
                    data = {'reqtype': 'fileupload'}
                    response = await http_client.post(
                        'https://catbox.moe/user/api.php',
                        files=files,
                        data=data,
                        timeout=60.0
                    )
            
            if response.status_code == 200:
                link = response.text.strip()
                if not link.startswith('http'):
                    return await status_msg.edit_text(f"❌ Invalid catbox response: {link}")
            else:
                return await status_msg.edit_text(f"❌ Both uploads failed")
        
        await status_msg.delete()
        
        await message.reply(
            f"<b>🌐 Link:</b>\n\n<code>{link}</code>",
            quote=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Open Link", url=link),
                    InlineKeyboardButton("Share", url=f"https://telegram.me/share/url?url={link}")
                ]
            ])
        )
        
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass