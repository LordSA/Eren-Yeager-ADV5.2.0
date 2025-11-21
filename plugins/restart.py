import os
import sys
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from info import ADMINS, PM2_BOT_NAME, LOG_CHANNEL

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart_bot_handler(client: Client, message: Message):
    await message.reply_text("🔄 **Restarting Bot...**")
    
    if LOG_CHANNEL:
        try:
            log_message = (
                f"🔄 **System Restart Initiated**\n\n"
                f"👤 **Admin:** {message.from_user.mention}\n"
                f"📅 **Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
                f"⚙️ **Mode:** `{'PM2' if PM2_BOT_NAME else 'Python'}`"
            )
            await client.send_message(int(LOG_CHANNEL), log_message)
        except Exception as e:
            print(f"Error sending restart log: {e}")

    await asyncio.sleep(1)

    if PM2_BOT_NAME:
        os.system(f"pm2 restart {PM2_BOT_NAME}")
    else:
        os.execl(sys.executable, sys.executable, *sys.argv)