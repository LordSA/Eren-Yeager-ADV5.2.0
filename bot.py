import sys
import logging
import logging.config
import subprocess
import asyncio 
from pyrogram import filters, types, Client, __version__ 
from pyrogram.types import Message
from info import LOG_CHANNEL, ADMINS, PM2_BOT_NAME, SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR

# Get logging configurations
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)
logger.info("Bot is starting with logging configured from file...")

from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.filters_mdb import filters_db
from database.users_chats_db import db
from utils import temp, run_shell_command

class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        await filters_db.create_index()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
app = Bot()
#OWNER_ID = ADMINS

# ---------------- CHECK UPDATE ----------------
@app.on_message(filters.command("checkupdate") & filters.user(ADMINS))
async def check_update(client: Client, message: Message):
    owner = message.from_user.id
    await client.send_message(owner, "🔍 Checking for updates...")
    stdout, stderr = await run_shell_command("git pull origin main") 
    git_output = stdout + "\n" + stderr

    if "Already up to date." in git_output:
        await client.send_message(owner, "✅ Bot is already up-to-date.")
    else:
        await client.send_message(owner, f"📦 Update available:\n<code>{git_output}</code>")
        if LOG_CHANNEL:
            await client.send_message(LOG_CHANNEL, f"📦 Update check logs:\n<code>{git_output}</code>")

# ---------------- UPDATE BOT ----------------
@app.on_message(filters.command("update") & filters.user(ADMINS))
async def update_bot(client: Client, message: Message):
    
    status_message = await message.reply_text("🚀 **Update started...**")

    if not PM2_BOT_NAME:
        return await status_message.edit_text(
            "⚠️ **Error:** `PM2_BOT_NAME` is not set in your env. Cannot restart."
        )

    # [FIX] Changed 'testing' back to 'main'
    await status_message.edit_text("🌍 **Fetching updates from Git...**\n\n`git fetch --all && git reset --hard origin/main`")

    update_cmd = "git fetch --all && git reset --hard origin/main"
    
    try:
        stdout, stderr = await run_shell_command(update_cmd)
    except Exception as e:
        await status_message.edit_text(f"❌ **Update failed!**\n\n**Error:**\n`{e}`")
        return

    git_output = (stdout or "") + "\n" + (stderr or "")

    if "Already up to date." in git_output and "Fast-forward" not in git_output:
        await status_message.edit_text("✅ Bot is already up-to-date. No changes found.")
        return

    if "error" in git_output.lower() or "fatal" in git_output.lower():
        if "already up to date" not in git_output.lower():
            await status_message.edit_text(f"❌ **Git pull failed!**\n\n**Full Log:**\n<code>{git_output}</code>")
            return

    await status_message.edit_text(
        f"✅ **Git pull successful.**\n\n**Full Log:**\n<code>{git_output}</code>\n\n"
        "📦 **Installing requirements...**\n\n`pip install -r requirements.txt`"
    )

    pip_command = f"{sys.executable} -m pip install -r requirements.txt"
    stdout_pip, stderr_pip = await run_shell_command(pip_command)
    pip_output = (stdout_pip or "") + "\n" + (stderr_pip or "")

    await status_message.edit_text(
        f"✅ **Requirements installed.**\n\n**Full Log:**\n<code>{pip_output}</code>\n\n"
        f"🔄 **Restarting bot via PM2...**\n\n`pm2 restart {PM2_BOT_NAME}`"
    )

    if LOG_CHANNEL:
        try:
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=f"📦 **Update: Git Pull Logs**\n<code>{git_output}</code>"
            )
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=f"📦 **Update: Pip Install Logs**\n<code>{pip_output}</code>"
            )
        except Exception as e:
            print(f"Error sending to LOG_CHANNEL: {e}")
            await status_message.edit_text(f"✅ Update complete. Restarting...\n\n⚠️ **Note:** Could not send logs to LOG_CHANNEL. Error: {e}")

    await asyncio.sleep(2)

    try:
        await run_shell_command(f"pm2 restart {PM2_BOT_NAME}")
    except Exception as e:
        await status_message.edit_text(
            f"❌ **Restart failed!**\n\n**Error:**\n`{e}`\n\n"
            "You may need to restart manually."
        )

app.run()