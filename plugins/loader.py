#Testing
#prefferred to not use, there will be chance for error

import os
import sys
import ast
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from info import ADMINS, PM2_BOT_NAME

@Client.on_message(filters.command(["plugins", "list_plugins"]) & filters.user(ADMINS))
async def list_plugins_handler(client: Client, message: Message):
    try:
        files = os.listdir("./plugins")
        
        plugin_list = [
            f for f in files 
            if f.endswith(".py") and not f.startswith("__")
        ]
        
        plugin_list.sort()
        
        if not plugin_list:
            return await message.reply_text("📂 **No plugins found.**")

        text = f"📂 **Installed Plugins ({len(plugin_list)}):**\n\n"
        for plugin in plugin_list:
            text += f"🔹 `{plugin}`\n"
        
        await message.reply_text(text)

    except Exception as e:
        await message.reply_text(f"❌ **Error listing plugins:**\n`{str(e)}`")

@Client.on_message(filters.command("install") & filters.user(ADMINS))
async def install_plugin_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Usage:** `/install [Raw Gist Link] [FileName.py]`"
        )

    url = message.command[1]

    if "gist.github.com" in url and "raw" not in url:
        url = url.rstrip("/") + "/raw"
    
    if len(message.command) >= 3:
        filename = message.command[2]
    else:
        filename = url.split("/")[-1]
        if not filename.endswith(".py"):
            filename = "gist_plugin.py"

    if not filename.endswith(".py"):
        filename += ".py"

    sts = await message.reply_text("📥 **Fetching plugin...**")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return await sts.edit("❌ **Error:** Could not download file. Check link.")
                code = await response.text()

        try:
            ast.parse(code)
        except SyntaxError as e:
            return await sts.edit(
                f"❌ **Syntax Error Detected!**\n\n"
                f"Plugin **REJECTED** to prevent crash.\n"
                f"**Line {e.lineno}:** `{e.text.strip() if e.text else 'Unknown'}`\n"
                f"**Error:** `{e.msg}`"
            )
        except Exception as e:
            return await sts.edit(f"❌ **Validation Error:** `{str(e)}`")

        path = f"./plugins/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        await sts.edit(f"✅ **Installed:** `{filename}`\n🔄 Restarting...")
        await restart_bot()

    except Exception as e:
        await sts.edit(f"❌ **Install Failed:**\n`{str(e)}`")

@Client.on_message(filters.command("uninstall") & filters.user(ADMINS))
async def uninstall_plugin_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Usage:** `/uninstall [FileName.py]`\n\n"
            "Example: `/uninstall song.py`"
        )

    filename = message.command[1]
    
    if not filename.endswith(".py"):
        filename += ".py"

    if "/" in filename or "\\" in filename:
        return await message.reply_text("❌ **Error:** You can only delete files inside the plugins folder.")

    path = f"./plugins/{filename}"

    if not os.path.exists(path):
        return await message.reply_text(f"❌ **Error:** Plugin `{filename}` not found.")

    try:
        os.remove(path)
        sts = await message.reply_text(f"🗑️ **Deleted:** `{filename}`\n🔄 Restarting to apply changes...")
        await restart_bot()
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`")

async def restart_bot():
    await asyncio.sleep(2)
    if PM2_BOT_NAME:
        os.system(f"pm2 restart {PM2_BOT_NAME}")
    else:
        os.execl(sys.executable, sys.executable, *sys.argv)