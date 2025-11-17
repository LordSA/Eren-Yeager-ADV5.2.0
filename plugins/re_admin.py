import logging
from pyrogram import filters, Client, enums
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant

logger = logging.getLogger(__name__)

@Client.on_message((filters.command("report") | filters.regex("@admin")) & filters.group)
async def report_user(client: Client, message: Message):
    if not message.reply_to_message:
        return 

    chat_id = message.chat.id
    reporter = message.from_user.mention
    
    try:
        admins = await client.get_chat_members(
            chat_id=chat_id, 
            filter=enums.ChatMembersFilter.ADMINISTRATORS
        )
    except Exception as e:
        logger.error(f"Failed to get admins for report: {e}")
        return

    mention_list = []
    for admin in admins:
        if admin.user.is_bot or admin.user.is_deleted:
            continue
        
        mention_list.append(admin.user.mention)

    if not mention_list:
        try:
            await message.reply_text("I couldn't find any admins to report this to.")
        except UserNotParticipant:
            pass
        return

    mentions = " ".join(mention_list)
    report_text = (
        f"⚠️ **Report!**\n\n"
        f"**From:** {reporter}\n"
        f"**Admins, please review this message:** {mentions}"
    )

    try:
        await client.send_message(
            chat_id=chat_id,
            text=report_text,
            reply_to_message_id=message.reply_to_message.id
        )
        
        await message.delete()
        
    except Exception as e:
        logger.error(f"Failed to send report mention in group: {e}")