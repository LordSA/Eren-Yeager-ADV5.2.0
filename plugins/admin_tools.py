import asyncio
import logging
from time import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.errors.exceptions.bad_request_400 import ChatAdminRequired, UserAdminInvalid
from plugins.Tools.help_func.admin_check import admin_check
from plugins.Tools.help_func.cust_p_filters import f_onw_fliter, admin_fliter
from Script import script
from info import ADMINS

# Get a logger for this file
logger = logging.getLogger(__name__)
TG_MAX_SELECT_LEN = 400

@Client.on_message(filters.command("purge") & f_onw_fliter)
async def purge(client, message):
    """ purge upto the replied message """
    if message.chat.type not in ("supergroup", "channel"):
        return
    is_admin = await admin_check(message)
    if not is_admin:
        return
    status_message = await message.reply_text("...", quote=True)
    await message.delete()
    message_ids = []
    count_del_etion_s = 0
    if message.reply_to_message:
        for a_s_message_id in range(
            message.reply_to_message.message_id,
            message.message_id
        ):
            message_ids.append(a_s_message_id)
            if len(message_ids) == TG_MAX_SELECT_LEN:
                await client.delete_messages(
                    chat_id=message.chat.id,
                    message_ids=message_ids,
                    revoke=True
                )
                count_del_etion_s += len(message_ids)
                message_ids = []
        if len(message_ids) > 0:
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=message_ids,
                revoke=True
            )
            count_del_etion_s += len(message_ids)

    await status_message.edit_text(
        f"deleted {count_del_etion_s} messages"
    )
    await asyncio.sleep(5)
    await status_message.delete()


@Client.on_message(filters.command(["pin"]) & admin_fliter)
async def pin(_, message: Message):
    if not message.reply_to_message:
        return
    await message.reply_to_message.pin()


@Client.on_message(filters.command(["unpin"]) & admin_fliter)
async def unpin(_, message: Message):
    if not message.reply_to_message:
        return
    await message.reply_to_message.unpin()


@Client.on_message(filters.incoming & ~filters.private & filters.command('inkick'))
async def inkick(client, message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == ("creator"):
        if len(message.command) > 1:
            input_str = message.command
            sent_message = await message.reply_text(script.START_KICK)
            await asyncio.sleep(20)
            await sent_message.delete()
            await message.delete()
            count = 0
            
            async for member in client.get_chat_members(message.chat.id): 
                if member.user.status in input_str and not member.status in ('administrator', 'creator'):
                    try:
                        await client.kick_chat_member(message.chat.id, member.user.id, int(time() + 45))
                        count += 1
                        await asyncio.sleep(1)
                    except (ChatAdminRequired, UserAdminInvalid):
                        await sent_message.edit(script.ADMIN_REQUIRED)
                        await client.leave_chat(message.chat.id)
                        break
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                    except Exception as e:
                        logger.error(f"Failed to kick user {member.user.id}: {e}")
            try:
                await sent_message.edit(script.KICKED.format(count))
            except ChatWriteForbidden:
                pass
        else:
            await message.reply_text(script.INPUT_REQUIRED)
    else:
        sent_message = await message.reply_text(script.CREATOR_REQUIRED)
        await asyncio.sleep(5)
        await sent_message.delete()
        await message.delete()


@Client.on_message(filters.incoming & ~filters.private & filters.command('dkick'))
async def dkick(client, message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == ("creator"):
        sent_message = await message.reply_text(script.START_KICK)
        await asyncio.sleep(20)
        await sent_message.delete()
        await message.delete()
        count = 0
        async for member in client.get_chat_members(message.chat.id): 
            if member.user.is_deleted and not member.status in ('administrator', 'creator'):
                try:
                    await client.kick_chat_member(message.chat.id, member.user.id, int(time() + 45))
                    count += 1
                    await asyncio.sleep(1)
                except (ChatAdminRequired, UserAdminInvalid):
                    await sent_message.edit(script.ADMIN_REQUIRED)
                    await client.leave_chat(message.chat.id)
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                except Exception as e:
                    logger.error(f"Failed to dkick user {member.user.id}: {e}")
        try:
            await sent_message.edit(script.DKICK.format(count))
        except ChatWriteForbidden:
            pass
    else:
        sent_message = await message.reply_text(script.CREATOR_REQUIRED)
        await asyncio.sleep(5)
        await sent_message.delete()
        await message.delete()


@Client.on_message(filters.incoming & ~filters.private & filters.command('instatus'))
async def instatus(client, message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status in ('administrator', 'creator', 'ADMINS'): 
        sent_message = await message.reply_text(script.FETCHING_INFO)
        recently = 0
        within_week = 0
        within_month = 0
        long_time_ago = 0
        deleted_acc = 0
        uncached = 0
        bot = 0
        
        async for member in client.get_chat_members(message.chat.id):
            user = member.user
            if user.is_deleted:
                deleted_acc += 1
            elif user.is_bot:
                bot += 1
            elif user.status == "recently":
                recently += 1
            elif user.status == "within_week":
                within_week += 1
            elif user.status == "within_month":
                within_month += 1
            elif user.status == "long_time_ago":
                long_time_ago += 1
            else:
                uncached += 1
        await sent_message.edit(script.STATUS.format(message.chat.title, recently, within_week, within_month, long_time_ago, deleted_acc, bot, uncached))