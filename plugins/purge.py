import asyncio
from info import ADMINS
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from plugins.admin_tools import logger
from plugins.Tools.help_func.cust_p_filters import f_owner_filter, admin_filter

@Client.on_message(filters.command("purge") & admin_filter)
async def purge(client, message):
    logger.info(f"Purge command triggered by user: {message.from_user.id}")
    if message.chat.type not in (enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL):
        await message.reply_text("This command only works in supergroups and channels.")
        return

    if not message.reply_to_message:
        await message.reply_text("Reply to a message to start purging from there.")
        return

    try:
        status_message = await message.reply_text("Processing...", quote=True)
        await message.delete()
    except ChatAdminRequired:
        await message.reply_text("I need to be an admin with 'Can delete messages' permission.")
        return
    except Exception as e:
        logger.error(f"Error on initial purge setup: {e}")
        return

    message_ids = []
    count_deleted = 0
    
    for message_id in range(
        message.reply_to_message.id,
        message.id
    ):
        message_ids.append(message_id)
        
        if len(message_ids) == 100:
            try:
                await client.delete_messages(
                    chat_id=message.chat.id,
                    message_ids=message_ids,
                    revoke=True
                )
                count_deleted += len(message_ids)
            except FloodWait as e:
                logger.warning(f"FloodWait of {e.value}s during purge")
                await asyncio.sleep(e.value)
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
            count_deleted += len(message_ids)
        except FloodWait as e:
            logger.warning(f"FloodWait of {e.value}s during final purge")
            await asyncio.sleep(e.value)
        except Exception as e:
            logger.error(f"Error during final purge delete: {e}")

    await status_message.edit_text(
        f"✅ Purged {count_deleted} messages."
    )
    await asyncio.sleep(5)
    await status_message.delete()