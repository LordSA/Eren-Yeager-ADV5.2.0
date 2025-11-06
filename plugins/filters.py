import io
import logging
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from plugins.Tools.help_func.decorators import check_group_admin
#from database.ia_filterdb import filters_db
from database.filters_mdb import filters_db
from database.connections_mdb import active_connection 

from utils import get_file_id, parser, split_quotes
from info import ADMINS

logger = logging.getLogger(__name__)

@Client.on_message(filters.command(['filter', 'add']) & filters.incoming)
@check_group_admin
async def addfilter(client, message, grp_id, title):
    args = message.text.html.split(None, 1)

    if len(args) < 2:
        return await message.reply_text("Command Incomplete :(", quote=True)

    extracted = split_quotes(args[1])
    text = extracted[0].lower()

    if not message.reply_to_message and len(extracted) < 2:
        return await message.reply_text("Add some content to save your filter!", quote=True)

    reply_text, btn, alert = "", "[]", None
    fileid = None

    if (len(extracted) >= 2) and not message.reply_to_message:
        reply_text, btn, alert = parser(extracted[1], text)
        if not reply_text:
            return await message.reply_text("You cannot have buttons alone, give some text to go with it!", quote=True)

    elif message.reply_to_message:
        msg = get_file_id(message.reply_to_message)
        if msg:
            fileid = msg.file_id
        
        if message.reply_to_message.reply_markup:
            btn = message.reply_to_message.reply_markup.inline_keyboard
            reply_text = message.reply_to_message.caption.html if message.reply_to_message.caption else message.reply_to_message.text.html
        
        elif message.reply_to_message.media:
            if message.reply_to_message.caption:
                reply_text = message.reply_to_message.caption.html
        
        elif message.reply_to_message.text:
            reply_text = message.reply_to_message.html
        
        if len(extracted) >= 2:
            reply_text, btn, alert = parser(extracted[1], text)

    await filters_db.add_filter(grp_id, text, reply_text, btn, fileid, alert)

    await message.reply_text(
        f"Filter for  `{text}`  added in  **{title}**",
        quote=True,
        parse_mode=enums.ParseMode.MARKDOWN
    )


@Client.on_message(filters.command(['viewfilters', 'filters']) & filters.incoming)
@check_group_admin
async def get_all(client, message, grp_id, title):
    texts = await filters_db.get_filters(grp_id)
    count = await filters_db.count_filters(grp_id)
    
    if not count:
        return await message.reply_text(f"There are no active filters in **{title}**")
    filter_list = [f" ×  `{text}`" for text in texts]
    header = f"Total number of filters in **{title}** : {count}\n\n"
    all_filters = header + "\n".join(filter_list)

    if len(all_filters) > 4096:
        with io.BytesIO(str.encode(all_filters.replace("`", ""))) as keyword_file:
            keyword_file.name = "keywords.txt"
            await message.reply_document(document=keyword_file, quote=True)
    else:
        await message.reply_text(
            text=all_filters,
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )

        
@Client.on_message(filters.command('del') & filters.incoming)
@check_group_admin
async def deletefilter(client, message, grp_id, title):
    try:
        cmd, text = message.text.split(" ", 1)
    except:
        return await message.reply_text(
            "<i>Mention the filtername which you wanna delete!</i>\n\n"
            "<code>/del filtername</code>\n\n"
            "Use /viewfilters to view all available filters",
            quote=True
        )

    query = text.lower()
    await filters_db.delete_filter(message, query, grp_id)

        
@Client.on_message(filters.command('delall') & filters.incoming)
@check_group_admin
async def delallconfirm(client, message, grp_id, title):
    await message.reply_text(
        f"This will delete all filters from '{title}'.\nDo you want to continue??",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="YES", callback_data=f"delallconfirm_{grp_id}")],
            [InlineKeyboardButton(text="CANCEL", callback_data="delallcancel")]
        ]),
        quote=True
    )


@Client.on_callback_query(filters.regex(r"^delall"))
async def delall_callback(client, cb: CallbackQuery):
    """Handles the /delall confirmation buttons"""
    
    userid = cb.from_user.id
    try:
        grp_id = int(cb.data.split("_")[1])
    except (IndexError, ValueError):
        return await cb.answer("Invalid callback data!", show_alert=True)

    try:
        st = await client.get_chat_member(grp_id, userid)
    except Exception as e:
        logger.error(e)
        return await cb.answer("Error checking admin status.", show_alert=True)
    if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
        if cb.data.startswith("delallconfirm"):
            chat = await client.get_chat(grp_id)
            title = chat.title
            await filters_db.del_all(cb.message, grp_id, title)
            await cb.answer("All filters have been deleted.", show_alert=True)
        
        elif cb.data == "delallcancel":
            await cb.message.edit_text("Deletion cancelled.")
            await cb.answer()
    else:
        await cb.answer("Only the group owner can do this!", show_alert=True)