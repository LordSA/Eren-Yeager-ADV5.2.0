import asyncio
from info import ADMINS
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from plugins.Tools.help_func.admin_check import admin_check
from plugins.admin_tools import logger
from plugins.Tools.help_func.cust_p_filters import f_onw_fliter

@Client.on_message(filters.command("purge") & f_onw_fliter)
async def purge(client, message):
    if message.chat.type not in (enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL):
        return

    is_admin = await admin_check(message)
    if not is_admin:
        return

    try:
        status_message = await message.reply_text("Processing...", quote=True)
        await message.delete()
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with 'Can delete messages' permission.")
        return
    message_ids = []
    count_del_etion_s = 0
    if message.reply_to_message:
        for a_s_message_id in range(
            message.reply_to_message.id,
            message.id
        ):
            message_ids.append(a_s_message_id)
            if len(message_ids) == 100:
                try:
                    await client.delete_messages(
                        chat_id=message.chat.id,
                        message_ids=message_ids,
                        revoke=True
                    )
                    count_del_etion_s += len(message_ids)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                except Exception as e:
                    logger.error(f"Error during purge batch delete: {e}")
                
                message_ids = [] 
        if len(message_ids) > 0:
            try:
                await client.delete_messages(
                    chat_id=message.chat.id,
                    message_ids=message_ids,
                    revoke=True
                )
                count_del_etion_s += len(message_ids)
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except Exception as e:
                logger.error(f"Error during final purge delete: {e}")

    await status_message.edit_text(
        f"✅ Purged {count_del_etion_s} messages."
    )
    await asyncio.sleep(5)
    await status_message.delete()