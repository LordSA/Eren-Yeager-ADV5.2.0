import logging
import logging.config
import subprocess
import asyncio 
from pyrogram import filters
from pyrogram.types import Message
from info import LOG_CHANNEL, ADMINS, PM2_BOT_NAME

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.filters_mdb import filters_db
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types

async def run_shell_command(command: str) -> (str, str):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode().strip(), stderr.decode().strip()

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
    git_pull = subprocess.run(["git", "pull"], capture_output=True, text=True)
    git_output = git_pull.stdout + git_pull.stderr

    if "Already up to date." in git_output:
        await client.send_message(owner, "✅ Bot is already up-to-date.")
    else:
        await client.send_message(owner, f"📦 Update available:\n<code>{git_output}</code>")
        await client.send_message(LOG_CHANNEL, f"📦 Update check logs:\n<code>{git_output}</code>")

# ---------------- UPDATE BOT ----------------
@app.on_message(filters.command("update") & filters.user(ADMINS))
async def update_bot(client: Client, message: Message):
    owner = message.from_user.id

    if not PM2_BOT_NAME:
        return await client.send_message(owner, "⚠️ **Error:** `PM2_BOT_NAME` is not set in your env. Cannot restart.")

    await client.send_message(owner, "🚀 Update started...")

    stdout, stderr = await run_shell_command("git pull")
    git_output = stdout + "\n" + stderr

    if "Already up to date." in git_output:
        await client.send_message(owner, "✅ Bot is already up-to-date.")
        return

    await client.send_message(LOG_CHANNEL, f"📦 Git Pull Logs:\n<code>{git_output}</code>")
    await client.send_message(LOG_CHANNEL, "✅ `git pull` complete.\n\n2. Installing requirements...")

    pip_command = f"{sys.executable} -m pip install -r requirements.txt"
    stdout_pip, stderr_pip = await run_shell_command(pip_command)
    pip_output = stdout_pip + "\n" + stderr_pip

    await client.send_message(LOG_CHANNEL, f"📦 Pip Install Logs:\n<code>{pip_output}</code>")

    await client.send_message(owner, "✅ Update finished. Bot restarting...")

    await asyncio.sleep(2)

    await run_shell_command(f"pm2 restart {PM2_BOT_NAME}")

app.run()