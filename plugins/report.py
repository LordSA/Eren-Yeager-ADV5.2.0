import logging
from pyrogram import filters, Client, enums
from pyrogram.types import Message

logger = logging.getLogger(__name__)

@Client.on_message((filters.command("report") | filters.regex("@admin")) & filters.group)
async def report_user(client: Client, message: Message):
    if not message.reply_to_message:
        return 

    chat_id = message.chat.id
    reporter = message.from_user.mention
    
    admins = await client.get_chat_members(
        chat_id=chat_id, 
        filter=enums.ChatMembersFilter.ADMINISTRATORS
    )
    
    success = False
    
    report = f"⚠️ **Report**\n\n"
    report += f"**Reporter:** {reporter}\n"
    report += f"**Message:** {message.reply_to_message.link}"
    
    for admin in admins:
        if admin.user.is_bot:
            continue
            
        try:
            reported_post = await message.reply_to_message.forward(admin.user.id)
            
            await reported_post.reply_text(
                text=report,
                disable_web_page_preview=True
            )
            
            success = True
            
        except Exception as e:
            logger.warning(f"Failed to report to admin {admin.user.id}: {e}")
            pass
            
    if success:
        await message.reply_text("𝖱𝖾Ghmr-Re'd 𝗍𝗈 𝖠𝖽𝗆𝗂𝗇𝗌!")