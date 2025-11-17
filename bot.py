import sys
import aiohttp
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
import utils

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
        utils.AIO_SESSION = aiohttp.ClientSession()
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
        if utils.AIO_SESSION:
            await utils.AIO_SESSION.close()
            
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
app = Bot()
#OWNER_ID = ADMINS

# ---------------- CHECK UPDATE ----------------
@app.on_message(filters.command("checkupdate") & filters.user(ADMINS))
async def check_update(client: Client, message: Message):
    owner = message.from_user.id
    await client.send_message(owner, "🔍 Checking for updates...")
    git_pull = subprocess.run(["git", "pull"], capture_output=True, text=True)
    git_output = git_pull.stdout + git_pull.stderr

    if "Already up to date." in git_output:
        await client.send_message(owner, "✅ Bot is already up-to-date.")
    else:
        await client.send_message(owner, f"📦 Update available:\n<code>{git_output}</code>")
        await client.send_message(LOG_CHANNEL, f"📦 Update check logs:\n<code>{git_output}</code>")

# ---------------- UPDATE BOT ----------------
@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def update_bot(client: Client, message: Message):
    
    status_message = await message.reply_text("🚀 **Update started...**")
    if not PM2_BOT_NAME:
        return await status_message.edit_text(
            "⚠️ **Error:** `PM2_BOT_NAME` is not set in your environment variables."
        )

    await status_message.edit_text("🌍 **Fetching updates from Git...**")
    
    update_cmd = "git fetch --all && git reset --hard origin/main"
    stdout, stderr = await run_shell_command(update_cmd)
    git_output = f"{stdout}\n{stderr}".strip()

    if "Already up to date" in git_output or "already up-to-date" in git_output.lower():
        return await status_message.edit_text("✅ Bot is already up-to-date. No changes found.")
    if not stdout and stderr:
        return await status_message.edit_text(
            f"❌ **Git pull failed!**\n\n```\n{git_output}\n```"
        )
    await status_message.edit_text(
        f"✅ **Git pull successful.**\n\n```\n{git_output[:500]}\n```\n\n"
        "📦 **Installing requirements...**"
    )
    pip_command = f"{sys.executable} -m pip install -r requirements.txt"
    stdout_pip, stderr_pip = await run_shell_command(pip_command)
    pip_output = f"{stdout_pip}\n{stderr_pip}".strip()

    await status_message.edit_text(
        "✅ **Requirements installed.**\n\n"
        f"🔄 **Restarting bot via PM2: `{PM2_BOT_NAME}`**"
    )
    if LOG_CHANNEL:
        try:
            await client.send_message(
                chat_id=int(LOG_CHANNEL),
                text=f"📦 **Git Pull Logs**\n```\n{git_output[:3000]}\n```"
            )
            await client.send_message(
                chat_id=int(LOG_CHANNEL),
                text=f"📦 **Pip Install Logs**\n```\n{pip_output[:3000]}\n```"
            )
        except Exception as e:
            print(f"Error sending to LOG_CHANNEL: {e}")

    await asyncio.sleep(2)
    restart_stdout, restart_stderr = await run_shell_command(f"pm2 restart {PM2_BOT_NAME}")
    
    if restart_stderr and "error" in restart_stderr.lower():
        await status_message.edit_text(
            f"❌ **PM2 Restart failed!**\n\n```\n{restart_stderr}\n```"
        )
    else:
        await status_message.edit_text("✅ **Update complete! Bot restarting...**")

app.run()