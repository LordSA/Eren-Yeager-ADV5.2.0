from pyrogram import (
    Client,
    filters
)
from pyrogram.types import (
    ChatPermissions
)
from plugins.Tools.help_func.admin_check import admin_check
from plugins.Tools.help_func.extract_user import extract_user
from plugins.Tools.help_func.string_handling import extract_time


@Client.on_message(filters.command("mute"))
async def mute_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        return

    user_id, user_first_name = extract_user(message)

    try:
        await message.chat.restrict_member(
            user_id=user_id,
            permissions=ChatPermissions(
            )
        )
    except Exception as error:
        await message.reply_text(
            str(error)
        )
    else:
        if str(user_id).lower().startswith("@"):
            await message.reply_text(
                "👍🏻 "
                f"{user_first_name}"
                " ആ വാഴയുടെ വായ അടച്ചു! 🤐"
            )
        else:
            await message.reply_text(
                "👍🏻 "
                f"<a href='tg://user?id={user_id}'>"
                "Of lavender"
                "</a>"
                " അവൻ്റെ വായാ അടച്ചിട്ടുണ്ട്! 🤐"
            )


@Client.on_message(filters.command("tmute"))
async def temp_mute_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        return

    if not len(message.command) > 1:
        return

    user_id, user_first_name = extract_user(message)

    until_date_val = extract_time(message.command[1])
    if until_date_val is None:
        await message.reply_text(
            (
                "Invalid time type specified. "
                "Expected m, h, or d, Got it: {}"
            ).format(
                message.command[1][-1]
            )
        )
        return

    try:
        await message.chat.restrict_member(
            user_id=user_id,
            permissions=ChatPermissions(
            ),
            until_date=until_date_val
        )
    except Exception as error:
        await message.reply_text(
            str(error)
        )
    else:
        if str(user_id).lower().startswith("@"):
            await message.reply_text(
                "മിണ്ടാതെ ഇരി കഴുതെ! 😠"
                f"{user_first_name}"
                f" muted for {message.command[1]}!"
            )
        else:
            await message.reply_text(
                "മിണ്ടാതെ ഇരി കഴുതേ! 😠"
                f"<a href='tg://user?id={user_id}'>"
                "Of lavender"
                "</a>"
                " Mouth "
                f" muted for {message.command[1]}!"
            )
