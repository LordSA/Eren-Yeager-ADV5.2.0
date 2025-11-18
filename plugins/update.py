import os
import sys
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from info import ADMINS, PM2_BOT_NAME

async def run_shell_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode().strip(), stderr.decode().strip()
async def get_active_branch():
    branch, _ = await run_shell_command("git rev-parse --abbrev-ref HEAD")
    return branch
async def apply_update(message_object, branch):
    await message_object.edit(f"🚀 **Update Started on branch `{branch}`...**\n\n1️⃣ Resetting Git...")
    await run_shell_command(f"git fetch origin {branch}")
    update_cmd = f"git reset --hard origin/{branch}"
    stdout, stderr = await run_shell_command(update_cmd)
    if stderr and "error" in stderr.lower():
        return await message_object.edit(f"❌ **Git Reset Failed!**\n\n`{stderr}`")
    await message_object.edit("2️⃣ **Installing Dependencies...**")
    pip_cmd = f"{sys.executable} -m pip install -r requirements.txt"
    await run_shell_command(pip_cmd)
    await message_object.edit("3️⃣ **Restarting Bot...**\n(Expect 10-20s downtime)")
    if PM2_BOT_NAME:
        await asyncio.sleep(1)
        await run_shell_command(f"pm2 restart {PM2_BOT_NAME}")
    else:
        os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.command("checkupdate") & filters.user(ADMINS))
async def check_update_handler(client: Client, message: Message):
    if not os.path.isdir(".git"):
        return await message.reply_text("❌ **Error:** Not a Git Repository.")
    sts = await message.reply_text("🔎 **Checking for updates...**")
    try:
        branch = await get_active_branch()
        if not branch:
            return await sts.edit("❌ Failed to detect git branch.")
        await run_shell_command(f"git fetch origin {branch}")
        commits_log, _ = await run_shell_command(f"git log HEAD..origin/{branch} --pretty=format:'● %s (%cr)'")
        if not commits_log:
            return await sts.edit(f"✅ **Bot is up-to-date.**\n\n**Branch:** `{branch}`")
        commit_list = commits_log.split("\n")
        changes = "\n".join(commit_list[:10])
        if len(commit_list) > 10:
            changes += f"\n\n...and {len(commit_list)-10} more."
        text = (
            f"📢 **Update Available!**\n\n"
            f"**Branch:** `{branch}`\n"
            f"**New Commits:** `{len(commit_list)}`\n\n"
            f"**📝 Changelog:**\n{changes}"
        )
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Apply Update Now", callback_data="do_update")]])
        await sts.edit(text, reply_markup=btn)
    except Exception as e:
        await sts.edit(f"❌ **Error:**\n`{str(e)}`")

@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def update_handler(client: Client, message: Message):
    if not os.path.isdir(".git"):
        return await message.reply_text("❌ **Error:** Not a Git Repository.")
    sts = await message.reply_text("🔄 **Initializing Update...**")    
    try:
        branch = await get_active_branch()
        if not branch:
            return await sts.edit("❌ Failed to detect git branch.")
        await apply_update(sts, branch)
    except Exception as e:
        await sts.edit(f"❌ **Error:**\n`{str(e)}`")

@Client.on_callback_query(filters.regex("^do_update$") & filters.user(ADMINS))
async def update_button_callback(client, query):
    await query.answer("Starting Update...", show_alert=True)
    branch = await get_active_branch()
    await apply_update(query.message, branch)