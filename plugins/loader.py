import os
import sys
import ast
import json
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from info import ADMINS, PM2_BOT_NAME

REGISTRY_FILE = "plugin_registry.json"

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {}
    try:
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_to_registry(filename, url):
    data = load_registry()
    data[filename] = url
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def remove_from_registry(filename):
    data = load_registry()
    if filename in data:
        del data[filename]
        with open(REGISTRY_FILE, "w") as f:
            json.dump(data, f, indent=4)

@Client.on_message(filters.command(["plugins", "list_plugins"]) & filters.user(ADMINS))
async def list_plugins_handler(client: Client, message: Message):
    try:
        files = os.listdir("./plugins")
        registry = load_registry()
        
        plugin_list = [
            f for f in files 
            if f.endswith(".py") and not f.startswith("__")
        ]
        
        plugin_list.sort()
        
        if not plugin_list:
            return await message.reply_text("📂 **No plugins found.**")

        text = f"📂 **Installed Plugins ({len(plugin_list)}):**\n\n"
        for plugin in plugin_list:
            is_custom = "✨" if plugin in registry else "🔒"
            text += f"{is_custom} `{plugin}`\n"
        
        text += "\n**Legend:**\n✨ = Custom (Updatable)\n🔒 = System (Protected)"
        await message.reply_text(text)

    except Exception as e:
        await message.reply_text(f"❌ **Error listing plugins:**\n`{str(e)}`")

@Client.on_message(filters.command("install") & filters.user(ADMINS))
async def install_plugin_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Usage:** `/install [Gist Link] [Optional Name]`"
        )

    url = message.command[1]

    if "gist.github.com" in url and "raw" not in url:
        url = url.rstrip("/") + "/raw"

    sts = await message.reply_text("📥 **Fetching plugin...**")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return await sts.edit("❌ **Error:** Could not download file. Check link.")
                
                code = await response.text()
                final_url = str(response.url)
                
                if len(message.command) >= 3:
                    filename = message.command[2]
                else:
                    filename = final_url.split("/")[-1]

        if not filename.endswith(".py"):
            filename += ".py"

        try:
            ast.parse(code)
        except SyntaxError as e:
            return await sts.edit(
                f"❌ **Syntax Error Detected!**\n\n"
                f"Plugin **REJECTED**.\n"
                f"**Line {e.lineno}:** `{e.text.strip() if e.text else 'Unknown'}`\n"
                f"**Error:** `{e.msg}`"
            )
        except Exception as e:
            return await sts.edit(f"❌ **Validation Error:** `{str(e)}`")

        path = f"./plugins/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        save_to_registry(filename, url)

        await sts.edit(f"✅ **Installed:** `{filename}`\n🔄 Restarting...")
        await restart_bot()

    except Exception as e:
        await sts.edit(f"❌ **Install Failed:**\n`{str(e)}`")

@Client.on_message(filters.command(["pupdate", "plugin_update"]) & filters.user(ADMINS))
async def plugin_update_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/pupdate [FileName.py]`")

    filename = message.command[1]
    if not filename.endswith(".py"):
        filename += ".py"

    registry = load_registry()

    if filename not in registry:
        return await message.reply_text(
            f"❌ **Error:** `{filename}` is a pre-installed system plugin or was not installed via /install.\n\n"
            "I cannot update core files, only custom plugins."
        )

    url = registry[filename]
    sts = await message.reply_text(f"🔄 **Updating** `{filename}` from source...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return await sts.edit("❌ **Error:** Source URL is dead or inaccessible.")
                code = await response.text()

        try:
            ast.parse(code)
        except SyntaxError as e:
            return await sts.edit(f"❌ **Update Rejected (Syntax Error):**\n`{e.msg}`")

        path = f"./plugins/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        await sts.edit(f"✅ **Updated:** `{filename}`\n🔄 Restarting...")
        await restart_bot()

    except Exception as e:
        await sts.edit(f"❌ **Update Failed:**\n`{str(e)}`")

@Client.on_message(filters.command("uninstall") & filters.user(ADMINS))
async def uninstall_plugin_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Usage:** `/uninstall [FileName.py]`"
        )

    filename = message.command[1]
    
    if not filename.endswith(".py"):
        filename += ".py"

    if "/" in filename or "\\" in filename:
        return await message.reply_text("❌ **Error:** Invalid filename.")

    path = f"./plugins/{filename}"

    if not os.path.exists(path):
        return await message.reply_text(f"❌ **Error:** Plugin `{filename}` not found.")

    try:
        os.remove(path)
        remove_from_registry(filename)
        
        sts = await message.reply_text(f"🗑️ **Deleted:** `{filename}`\n🔄 Restarting...")
        await restart_bot()
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`")

async def restart_bot():
    await asyncio.sleep(2)
    if PM2_BOT_NAME:
        os.system(f"pm2 restart {PM2_BOT_NAME}")
    else:
        os.execl(sys.executable, sys.executable, *sys.argv)