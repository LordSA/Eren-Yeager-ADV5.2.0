from pyrogram.types import Message
from pyrogram import enums
import logging
logger = logging.getLogger(__name__)

async def admin_check(message: Message) -> bool:
    if not message.from_user:
        return False
    if message.chat.type not in [enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
        return False

    if message.from_user.id in [
        777000,  # Telegram Service Notifications
        1087968824  # GroupAnonymousBot
    ]:
        return True

    client = message._client
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        check_status = await client.get_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False
    admin_statuses = [
        enums.ChatMemberStatus.OWNER,
        enums.ChatMemberStatus.ADMINISTRATOR
    ]
    
    if check_status.status not in admin_statuses:
        return False
    else:
        return True