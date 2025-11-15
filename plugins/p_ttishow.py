from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import ChatAdminRequired, PeerIdInvalid, MessageTooLong
from database.users_chats_db import db
from database.ia_filterdb import Media
from utils import get_size, temp, get_settings
from info import ADMINS, LOG_CHANNEL, SUPPORT_CHAT
from Script import script
import os
import io

# ----------------------------------- Helper functions ----------------------------------- #

async def send_support_message(bot, chat_id: int, text: str):
    """Send a message with a support button"""
    buttons = [[InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    try:
        await bot.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception:
        pass

def parse_command_args(message, default_reason="No reason Provided"):
    """Parse chat/user ID and reason from command"""
    parts = message.text.split(None, 2)
    if len(parts) == 1:
        return None, default_reason
    target = parts[1]
    reason = parts[2] if len(parts) > 2 else default_reason
    return target, reason

async def send_large_text(client, message, text, filename="chats.txt"):
    try:
        if len(text) > 4096:
            with io.BytesIO(text.encode()) as file:
                file.name = filename
                await client.send_document(
                    chat_id=message.chat.id,
                    document=file,
                    reply_to_message_id=message.id
                )
            await message.delete()
        else:
            await message.edit_text(text)
    except Exception as e:
        print(f"Error in send_large_text: {e}")
        await message.edit_text("An error occurred while sending the chat list.")

# ----------------------------------- Handlers ----------------------------------- #

@Client.on_message(filters.new_chat_members & filters.group)
async def handle_new_chat(bot, message):
    new_ids = [u.id for u in message.new_chat_members]
    is_me_added = temp.ME in new_ids

    # Bot was added
    if is_me_added:
        chat_id = message.chat.id
        if not await db.get_chat(chat_id):
            try:
                total_members = await bot.get_chat_members_count(chat_id)
            except Exception:
                total_members = "unknown"
            added_by = message.from_user.mention if message.from_user else "Anonymous"
            await bot.send_message(
                LOG_CHANNEL,
                script.LOG_TEXT_G.format(message.chat.title, chat_id, total_members, added_by)
            )
            await db.add_chat(chat_id, message.chat.title)

        if chat_id in temp.BANNED_CHATS:
            await send_support_message(
                bot, chat_id,
                "<b>CHAT NOT ALLOWED 🐞\n\nMy admins have restricted me from working here! "
                "Contact support if needed.</b>"
            )
            await bot.leave_chat(chat_id)
            return

        # Welcome message for groups
        buttons = [
            [InlineKeyboardButton("ℹ️ Help", url=f"https://t.me/{temp.U_NAME}?start=help"),
             InlineKeyboardButton("📢 Updates", url="https://t.me/mwpro11")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(
            f"<b>Thank you for adding me in {message.chat.title} ❣️\n\n"
            "If you have questions, contact support.</b>",
            reply_markup=reply_markup
        )

    # Human users joined
    else:
        settings = await get_settings(message.chat.id)
        if settings.get("welcome"):
            for user in message.new_chat_members:
                old_msg = temp.MELCOW.get("welcome")
                if old_msg:
                    try:
                        await old_msg.delete()
                    except Exception:
                        pass
                temp.MELCOW["welcome"] = await message.reply(
                    f"<b>Hey {user.mention}, Welcome to {message.chat.title}</b>"
                )

# ------------------------------- Admin Commands ------------------------------- #

@Client.on_message(filters.command("leave") & filters.user(ADMINS))
async def leave_chat(bot, message):
    if len(message.command) < 2:
        return await message.reply("Please provide a chat ID.")
    chat_id = message.command[1]
    chat_id = int(chat_id) if chat_id.isdigit() else chat_id
    await send_support_message(
        bot, chat_id,
        "<b>Hello friends, my admin told me to leave this group. "
        "Contact support to add me again.</b>"
    )
    await bot.leave_chat(chat_id)
    await message.reply(f"Left chat `{chat_id}` successfully.")

@Client.on_message(filters.command("disable") & filters.user(ADMINS))
async def disable_chat(bot, message):
    chat_id, reason = parse_command_args(message)
    if not chat_id:
        return await message.reply("Please provide a chat ID.")
    try:
        chat_id = int(chat_id)
    except ValueError:
        return await message.reply("Invalid chat ID.")

    chat_data = await db.get_chat(chat_id)
    if not chat_data:
        return await message.reply("Chat not found in DB.")
    if chat_data.get("is_disabled"):
        return await message.reply(f"Chat is already disabled.\nReason: {chat_data.get('reason')}")

    await db.disable_chat(chat_id, reason)
    temp.BANNED_CHATS.append(chat_id)
    await message.reply("Chat successfully disabled.")
    await send_support_message(
        bot, chat_id,
        f"<b>I have been disabled by admin.</b>\nReason: <code>{reason}</code>"
    )
    await bot.leave_chat(chat_id)

@Client.on_message(filters.command("enable") & filters.user(ADMINS))
async def enable_chat(bot, message):
    chat_id = message.command[1] if len(message.command) > 1 else None
    if not chat_id:
        return await message.reply("Please provide a chat ID.")
    try:
        chat_id = int(chat_id)
    except ValueError:
        return await message.reply("Invalid chat ID.")

    chat_data = await db.get_chat(chat_id)
    if not chat_data:
        return await message.reply("Chat not found in DB.")
    if not chat_data.get("is_disabled"):
        return await message.reply("Chat is not disabled.")

    await db.re_enable_chat(chat_id)
    if chat_id in temp.BANNED_CHATS:
        temp.BANNED_CHATS.remove(chat_id)
    await message.reply("Chat successfully re-enabled.")

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def bot_stats(bot, message):
    msg = await message.reply("Fetching stats...")
    total_users = await db.total_users_count()
    total_chats = await db.total_chat_count()
    total_files = await Media.count_documents({})
    db_size = await db.get_db_size()
    free_space = 536_870_912 - db_size
    await msg.edit(
        script.STATUS_TXT.format(
            total_files,
            total_users,
            total_chats,
            get_size(db_size),
            get_size(free_space)
        )
    )

@Client.on_message(filters.command("invite") & filters.user(ADMINS))
async def gen_invite(bot, message):
    chat_id = message.command[1] if len(message.command) > 1 else None
    if not chat_id:
        return await message.reply("Please provide a chat ID.")
    try:
        chat_id = int(chat_id)
    except ValueError:
        return await message.reply("Invalid chat ID.")

    try:
        link = await bot.create_chat_invite_link(chat_id)
        await message.reply(f"Here is your invite link: {link.invite_link}")
    except ChatAdminRequired:
        await message.reply("Failed to generate invite link. I need admin rights.")
    except Exception as e:
        await message.reply(f"Error: {e}")

# -------------------------- Ban/Unban Users -------------------------- #

async def handle_ban_unban(bot, message, ban=True):
    if len(message.command) < 2:
        return await message.reply("Please provide a user ID or username.")
    user_id, reason = parse_command_args(message)
    try:
        user_obj = await bot.get_users(user_id)
    except (PeerIdInvalid, IndexError):
        return await message.reply("Invalid user.")
    except Exception as e:
        return await message.reply(f"Error: {e}")

    status = await db.get_ban_status(user_obj.id)
    if ban:
        if status.get("is_banned"):
            return await message.reply(f"{user_obj.mention} is already banned.\nReason: {status.get('ban_reason')}")
        await db.ban_user(user_obj.id, reason)
        temp.BANNED_USERS.append(user_obj.id)
        await message.reply(f"Successfully banned {user_obj.mention}")
    else:
        if not status.get("is_banned"):
            return await message.reply(f"{user_obj.mention} is not banned.")
        await db.remove_ban(user_obj.id)
        if user_obj.id in temp.BANNED_USERS:
            temp.BANNED_USERS.remove(user_obj.id)
        await message.reply(f"Successfully unbanned {user_obj.mention}")

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(bot, message):
    await handle_ban_unban(bot, message, ban=True)

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_user(bot, message):
    await handle_ban_unban(bot, message, ban=False)

# -------------------------- List Users/Chats -------------------------- #

async def send_large_text(bot, message, text, filename):
    """Handles MessageTooLong by sending as file"""
    try:
        await message.edit(text)
    except MessageTooLong:
        with open(filename, "w+", encoding="utf-8") as f:
            f.write(text)
        await message.reply_document(filename, caption=f"List of {filename.split('.')[0]}")
        os.remove(filename)

@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def list_users(bot, message):
    msg = await message.reply("Getting list of users...")
    users = await db.get_all_users()
    text = "Users Saved In DB:\n\n"
    for user in users:
        text += f"<a href=tg://user?id={user['id']}>{user['name']}</a>"
        if user.get("ban_status", {}).get("is_banned"):
            text += " (Banned)"
        text += "\n"
    await send_large_text(bot, msg, text, "users.txt")

@Client.on_message(filters.command("chats") & filters.user(ADMINS))
async def list_chats(client, message):
    msg = await message.reply("Getting list of chats...")
    chats = await db.get_all_chats()
    text = "Chats Saved In DB:\n\n"
    
    for chat in chats:
        chat_name = chat.get('title') or chat.get('first_name') or "Unknown"
        text += f"**Title:** `{chat_name}`\n**ID:** `{chat['id']}`"
        
        if chat.get("chat_status", {}).get("is_disabled"):
            text += " (Disabled)"
        
        text += "\n\n"
    await send_large_text(client, msg, text, "chats.txt")
