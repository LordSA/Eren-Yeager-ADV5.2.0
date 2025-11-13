# MADE BY LORD SA
import re
import ast
import math
import uuid
import random
import logging
import asyncio
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, VIDS
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid, ChatAdminRequired
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, FILE_ID_CACHE
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import filters_db
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


BUTTONS = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("വിളച്ചിൽ എടുകുന്നോ കുഞ്ഞിപുഴു നിനക്ക് വേണേൽ നി search ചെയ്യൂ കാരണം എനിക്ക് വേറെ പണി ഇല്ല😅. മാമനോടെ ഒന്നും തോന്നല്ലെ 😇", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.(പഴയതു മാറ്റിപ്പിടി)", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'filep' if settings['file_secure'] else 'file'
    btn = []
    for file in files:
        key = str(uuid.uuid4())[:8]
        FILE_ID_CACHE[key] = file.file_id
        if settings['button']:
            btn.append(
                [
                    InlineKeyboardButton(
                        text=f"© 『{get_size(file.file_size)}』 {file.file_name}", 
                        callback_data=f'{pre}#{key}' # Use short key
                    )
                ]
            )
        else:
            btn.append(
                [
                    InlineKeyboardButton(
                        text=f"© {file.file_name}", 
                        callback_data=f'{pre}#{key}' # Use short key
                    ),
                    InlineKeyboardButton(
                        text=f"『{get_size(file.file_size)}』",
                        callback_data=f'{pre}#{key}', # Use short key
                    ),
                ]
            )
    btn.insert(0, 
        [
            InlineKeyboardButton(f'🎬 {search} 🎬', 'reqst11')
        ]
    )
    btn.insert(1,
        [
            InlineKeyboardButton(f"『𝙵𝙸𝙻𝙴𝚂』", 'reqst11'),
            InlineKeyboardButton(f"『𝚃𝙸𝙿𝚂』", 'tips')
        ]
    )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("『𝙿𝚁𝙴𝚅』", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 𝙿𝙰𝙶𝙴𝚂 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"📃 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("『𝙽𝙴𝚇𝚃』", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("『𝙿𝚁𝙴𝚅』", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"📃 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("『𝙽𝙴𝚇𝚃』", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("വിളച്ചിൽ എടുകുന്നോ കുഞ്ഞിപുഴു നിനക്ക് വേണേൽ നി search ചെയ്യൂ കാരണം എനിക്ക് വേറെ പണി ഇല്ല😅. മാമനോടെ ഒന്നും തോന്നല്ലെ 😇", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer("You are clicking on an old button which is expired.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('Checking for Movie in database...')
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            k = await query.message.edit('𝚃𝙷𝙸𝚂 𝙼𝙾𝚅𝙸𝙴 I𝚂 𝙽𝙾𝚃 𝚈𝙴𝚃 𝚁𝙴𝙻𝙴𝙰𝚂𝙴𝙳 𝙾𝚁 𝙰𝙳𝙳𝙴𝙳 𝚃𝙾 𝙳𝙰𝚃𝙰𝙱𝙰𝚂𝙴(എടെ ഇതു ആ പെട്ടിയിൽ ഇല്ല)😅')
            await asyncio.sleep(10)
            await k.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Piracy Is Crime')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Piracy Is Crime')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Piracy Is Crime')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await filters_db.del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!(ഇത് നിനക്കുള്ളതല്ല നി വേറെ നോക്ക്😉)", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Piracy Is Crime')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode="md")
        return await query.answer('Piracy Is Crime')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Piracy Is Crime')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await filters_db.find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
            
    if query.data.startswith("file"):
        ident, key = query.data.split("#")
        logger.info(f"User {query.from_user.id} clicked file button. Ident: {ident}, Key: {key}")
        print(f"[DEBUG] File button clicked - ident: {ident}, file_id: {key}")
        
        file_id = FILE_ID_CACHE.get(key)
        if not file_id:
            logger.warning(f"File key {key} not found in cache. Button may be expired.")
            await query.answer("This button has expired. Please send the request again.", show_alert=True)
            return
        logger.info(f"Retrieved file_id {file_id} from cache for key {key}")
        try:
            files_ = await get_file_details(file_id)
            print(f"[DEBUG] Files retrieved: {files_}")
            
            if not files_:
                logger.error(f"File_id {file_id} not found in database (get_file_details).")
                return await query.answer('No such file exist.', show_alert=True)
            
            file = files_
            title = file.file_name
            size = get_size(file.file_size)
            f_caption = file.caption
            logger.info(f"Attempting to check settings for chat {query.message.chat.id}")
            settings = await get_settings(query.message.chat.id)
            
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption = CUSTOM_FILE_CAPTION.format(
                        file_name='' if title is None else title,
                        file_size='' if size is None else size,
                        file_caption='' if f_caption is None else f_caption
                    )
                except Exception as e:
                    logger.exception(e)
            
            if f_caption is None:
                f_caption = f"{title}"

            if AUTH_CHANNEL and not await is_subscribed(client, query):
                logger.info(f"User {query.from_user.id} not subscribed. Sending join message to PM.")
                auth_payload = f"auth_{ident}_{key}"
                await query.answer(
                    url=f"https://t.me/{temp.U_NAME}?start={auth_payload}",
                    text=script.JOIN_TXT
                )
                return
            
            if settings.get('botpm', False):
                logger.info(f"BotPM is True. Sending user to PM for file {file_id}.")
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{key}")
                return
            else:
                logger.info(f"BotPM is False. Attempting to send file {file_id} to group {query.message.chat.id}.")
                sent_message = await client.send_cached_media(
                    chat_id=query.message.chat.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                logger.info(f"Successfully sent file {file_id} to group {query.message.chat.id}.")
                await query.answer(f'Sending file to the group!', show_alert=False)
                await asyncio.sleep(300)
                try:
                    await sent_message.delete()
                    logger.info(f"Auto-deleted message {sent_message.id} from group.")
                except Exception as e:
                    logger.warning(f"Could not auto-delete message from group: {e}")
        except UserIsBlocked:
            logger.warning(f"Failed to send message/file: User {query.from_user.id} has blocked the bot.")
            await query.answer('I can\'t send you a PM! Unblock me first.', show_alert=True)
        
        except PeerIdInvalid:
            logger.warning(f"Failed to send message/file: User {query.from_user.id} has not started the bot (PeerIdInvalid).")
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{key}", text="I haven't started a chat with you! Click here to start, then try again.")

        except ChatAdminRequired:
            logger.warning(f"Failed to send file {file_id} to group {query.message.chat.id}: Bot is not admin.")
            await query.answer("I'm not an admin here! I need to be an admin to send files in the group.", show_alert=True)

        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            logger.error(f"CRITICAL: Failed to send file_id {file_id}. It is INVALID or DELETED from Telegram.", exc_info=True)
            await query.answer("Error: The file_id is invalid or the file has been deleted. Please re-index.", show_alert=True)

        except FloodWait as e:
            logger.warning(f"Failed to send file {file_id} to {query.message.chat.id}: FloodWait for {e.x} seconds.")
            await asyncio.sleep(e.x) 
            await query.answer(f"Slow down! You are being rate-limited. Please wait {e.x} seconds.", show_alert=True)

        except Exception as e:
            logger.error(f"Unknown error sending file {file_id} to {query.message.chat.id}", exc_info=True)
            await query.answer(f"An unknown error occurred. Check the logs.", show_alert=True)

         
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("Join the channel first!", show_alert=True)
            return
        
        ident, file_id = query.data.split("#")
        
        try:
            files_ = await get_file_details(file_id)
            if not files_:
                return await query.answer('No such file exist.', show_alert=True)
            
            file = files_
            title = file.file_name
            size = get_size(file.file_size)
            f_caption = file.caption
            
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption = CUSTOM_FILE_CAPTION.format(
                        file_name='' if title is None else title,
                        file_size='' if size is None else size,
                        file_caption='' if f_caption is None else f_caption
                    )
                except Exception as e:
                    logger.exception(e)
            
            if f_caption is None:
                f_caption = f"{title}"
            
            await query.answer()
            await client.send_cached_media(
                chat_id=query.from_user.id,
                file_id=file_id,
                caption=f_caption,
                protect_content=True if ident == 'checksubp' else False
            )
        except Exception as e:
            logger.exception(e)
            print(f"Error in checksub: {e}")
            await query.answer('An error occurred!', show_alert=True)
    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('➕ 𝕬𝙳𝙳 〽️𝙴 𝕿𝙾 𝖄𝙾𝚄𝚁 𝕲𝚁𝙾𝚄𝙾𝙿 ➕', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ], [
            InlineKeyboardButton('『𝕾𝙴𝙰𝚁𝙲𝙷』', switch_inline_query_current_chat=''),
            InlineKeyboardButton('『𝕾𝚄𝙿𝙿𝙾𝚁𝚃』', url='https://t.me/mwpro11')
        ], [
            InlineKeyboardButton('『𝙲𝙷𝙰𝙽𝙽𝙴𝙻』', url='https://t.me/+Sw4QUQp-kIU1NjY1')
 #           InlineKeyboardButton('『𝙶𝚁𝙾𝚄𝙿』', url='https://t.me/mwmoviespro')
        ], [
            InlineKeyboardButton('『𝙷𝙴𝙻𝙿』', callback_data='help'),
            InlineKeyboardButton('『𝕬𝙱𝙾𝚄𝚃』', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer('Piracy Is Crime')
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('『𝙼𝙰𝙽𝚄𝙰𝙻 𝙵𝙸𝙻𝚃𝙴𝚁』', callback_data='manuelfilter'),
            InlineKeyboardButton('『𝙰𝚄𝚃𝙾 𝙵𝙸𝙻𝚃𝙴𝚁』', callback_data='autofilter'),
            InlineKeyboardButton('『𝙲𝙾𝙽𝙽𝙴𝙲𝚃𝙸𝙾𝙽𝚂』', callback_data='coct')            
        ], [
            InlineKeyboardButton('『𝙿𝚄𝚁𝙶𝙴』', callback_data='purge'),
            InlineKeyboardButton('『𝕾𝚃𝙸𝙲𝙺𝙴𝚁 𝙸𝙳』', callback_data='stid'),  
            InlineKeyboardButton('『𝙸𝙼𝙳𝙱』', callback_data='extra')
        ], [            
            InlineKeyboardButton('『𝚃𝙷𝚄𝙶 𝙻𝙸𝙵𝙴』', callback_data='thug'),
            InlineKeyboardButton('『𝚃𝚃𝚂』', callback_data='tts'),
            InlineKeyboardButton('『𝙹𝚂𝙾𝙽』',callback_data='info')
        ], [
           
        ], [                        
            InlineKeyboardButton('『𝚃𝙴𝙻𝙴𝙶𝚁𝙰𝙿𝙷』', callback_data='tgraph'),            
            InlineKeyboardButton('『𝚂𝚄𝙿𝙿𝙾𝚁𝚃』', url='https://t.me/mwpro11'),
            InlineKeyboardButton('『𝙽𝙴𝚇𝚃』', callback_data='nxt1')
        ], [
            InlineKeyboardButton('『𝙷𝙾𝙼𝙴』', callback_data='start'),            
            InlineKeyboardButton('✴ 𝙿𝙸𝙽𝙶', callback_data='ping'),
            InlineKeyboardButton('『𝚂𝚃𝙰𝚃𝚄𝚂』', callback_data='stats')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),      
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('『𝚂𝚄𝙿𝙿𝙾𝚁𝚃』', url='https://t.me/mwpro11'),
            InlineKeyboardButton('『𝚂𝙾𝚄𝚁𝙲𝙴』', callback_data='source')
        ], [
            InlineKeyboardButton('『𝙷𝙾𝙼𝙴』', callback_data='start'),
            InlineKeyboardButton('『𝙲𝙻𝙾𝚂𝙴』', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),            
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "nxt1":
        buttons = [[
            InlineKeyboardButton('『𝙼𝚄𝚃𝙴』',callback_data='mute'),
            InlineKeyboardButton('『𝚁𝙴𝙿𝙾𝚁𝚃』',callback_data='report'),
            InlineKeyboardButton('『𝙺𝙸𝙲𝙺』', callback_data='kick')                                                       
        ], [
            InlineKeyboardButton('『𝙵𝚄𝙽』', callback_data='memes'),
 #       ], [
            InlineKeyboardButton('『𝙿𝙸𝙽』',callback_data='pin'),
            InlineKeyboardButton('『𝙻𝙾𝙶𝙾』', callback_data='logo')
        ], [
            InlineKeyboardButton('『𝚆𝙷𝙾𝙸𝚂』', callback_data='who'),
            InlineKeyboardButton('『𝙵𝙸𝙻𝙴 𝚂𝚃𝙾𝚁𝙴』', callback_data='flstr'),                                
            InlineKeyboardButton('『𝙱𝙰𝙽[𝙶]』',callback_data='bang')
        ], [            
            InlineKeyboardButton('『𝙿𝚁𝙴𝚅』', callback_data='help'),
            InlineKeyboardButton('『𝚂𝚄𝙿𝙿𝙾𝚁𝚃』', url='https://t.me/mwpro11')#,
 #           InlineKeyboardButton('『𝙽𝙴𝚇𝚃』', callback_data='')
        ], [
            InlineKeyboardButton('『𝙷𝙾𝙼𝙴』', callback_data='start'),            
            InlineKeyboardButton('✴ 𝙿𝙸𝙽𝙶', callback_data='ping'),
            InlineKeyboardButton('『𝚂𝚃𝙰𝚃𝚄𝚂』', callback_data='stats')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)        
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),            
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.SOURCE_TXT,           
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('『𝙱𝚄𝚃𝚃𝙾𝙽𝚂』', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='manuelfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "who":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.WHOIS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "report":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.RPT_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "tgraph":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.TGRAPH_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "tips":                   
        await query.answer(
            text=script.TIPS_TXT.format(query.from_user.mention),
            show_alert=True          
        )
    elif query.data == "logo":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.LOGO_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "bang":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.BAN_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "mute":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.MUTE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "thug":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.THUG_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "flstr":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.FILE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "pin":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.PIN_MESSAGE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "kick":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.KICK_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "purge":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.PURGE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "memes":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt1')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.MEMES_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "tts":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.TTS_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "info":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝖁𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.INFO_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "extra":
        buttons = [[                    
            InlineKeyboardButton('👩‍🦯 𝕭ack', callback_data='help'),
            InlineKeyboardButton('👮‍♂️ 𝕬𝙳𝙼𝙸𝙽', callback_data='admin')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "ping":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.PINGS_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "stid":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.STICKER_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='extra')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == 'reqst11':
        await query.answer(f"Hey {query.from_user.first_name} Bro 😍\n\n🎯 Click The Below Button The Files You Want... And Start The Bot Get The File and Go To Your House..😂\n\n Movie World", True)
   

    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text="◾◽◽"
        )
        await query.message.edit_text(
            text="◾◾◽"
        )
        await query.message.edit_text(
            text="◾◾◾"
        )
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data.startswith("setgs"):
        try:
            ident, set_type, status, grp_id = query.data.split("#")
            grpid = int(grp_id)
        except ValueError as e:
            logger.error(f"Error splitting callback data: {e}")
            return await query.answer("Error: Invalid button data.", show_alert=True)
        try:
            member = await client.get_chat_member(grp_id, query.from_user.id)
            if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await query.answer("You must be an Admin to change settings.", show_alert=True)
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return await query.answer("I can't check your permissions in that group.", show_alert=True)

        new_status = False if status == "True" else True
        await save_group_settings(grp_id, set_type, new_status)
        settings = await get_settings(grp_id)

        try:
            buttons = [
                [
                    InlineKeyboardButton('『𝙵𝙸𝙻𝚃𝙴𝚁 𝙱𝚄𝚃𝚃𝙾𝙽』',
                                         callback_data=f'setgs#button#{settings.get("button", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('𝚂𝙸𝙽𝙶𝙻𝙴' if settings.get("button", False) else '𝙳𝙾𝚄𝙱𝙻𝙴',
                                         callback_data=f'setgs#button#{settings.get("button", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝙱𝙾𝚃 𝙿𝙼』', callback_data=f'setgs#botpm#{settings.get("botpm", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings.get("botpm", False) else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#botpm#{settings.get("botpm", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝙵𝙸𝙻𝙴 𝚂𝙴𝙲𝚄𝚁𝙴』',
                                         callback_data=f'setgs#file_secure#{settings.get("file_secure", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings.get("file_secure", False) else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#file_secure#{settings.get("file_secure", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝙸𝙼𝙳𝙱』', callback_data=f'setgs#imdb#{settings.get("imdb", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings.get("imdb", False) else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#imdb#{settings.get("imdb", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝚂𝙿𝙴𝙻𝙻 𝙲𝙷𝙴𝙲𝙺』',
                                         callback_data=f'setgs#spell_check#{settings.get("spell_check", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings.get("spell_check", False) else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#spell_check#{settings.get("spell_check", False)}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚂𝙿𝙴𝙴𝙲𝙷』', callback_data=f'setgs#welcome#{settings.get("welcome", False)}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings.get("welcome", False) else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#welcome#{settings.get("welcome", False)}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer(f"{set_type.replace('_', ' ').upper()} set to {new_status}")
    #await query.answer('Piracy Is Crime')
        except MessageNotModified:
            await query.answer("Setting already changed.")
        except Exception as e:
            logger.error(f"Error rebuilding settings menu: {e}")
            await query.answer("Setting saved, but couldn't update menu.")

# A more robust auto_filter with debugging and error handling
async def auto_filter(client, msg, spoll=False):
    # --- 1. GETTING SETTINGS AND FILES ---
    if not spoll:
        message = msg
        try:
            settings = await get_settings(msg.chat.id)
        except Exception as e:
            logger.error(f"Failed to get settings: {e}")
            return  # Can't continue without settings

        if message.text.startswith("/"): return 
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        
        if 2 < len(message.text) < 100:
            search = message.text
            try:
                files, offset, total_results = await get_search_results(search.lower(), offset=0)
            except Exception as e:
                logger.error(f"Failed at get_search_results: {e}")
                return
                
            if not files:
                if settings.get("spell_check"): # Use .get() for safety
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        try:
            settings = await get_settings(msg.chat.id)
        except Exception as e:
            logger.error(f"Failed to get settings (spoll): {e}")
            return
        message = msg.message.reply_to_message 
        search, files, offset, total_results = spoll
    
    print(f"[DEBUG] auto_filter: Found {len(files)} files for '{search}'. Starting reply process.")

    # --- 2. BUILDING BUTTONS ---
    try:
        print("[DEBUG] auto_filter: Building buttons...")
        pre = 'filep' if settings['file_secure'] else 'file'
        btn = []
        for file in files:
            key = str(uuid.uuid4())[:8]
            FILE_ID_CACHE[key] = file.file_id
            if settings.get("button", False):
                btn.append(
                [
                    InlineKeyboardButton(
                        text=f"© 『{get_size(file.file_size)}』 {file.file_name}", 
                        callback_data=f'{pre}#{key}' # Use the short key
                    ),
                ]
            )
            else:
                btn.append(
                [
                    InlineKeyboardButton(
                        text=f"© {file.file_name}",
                        callback_data=f'{pre}#{key}', # Use the short key
                    ),
                    InlineKeyboardButton(
                        text=f"『{get_size(file.file_size)}』",
                        callback_data=f'{pre}#{key}', # Use the short key
                    ),
                ]
            )
        
        btn.insert(0, [InlineKeyboardButton(f'🎬 {search} 🎬', 'reqst11')])
        btn.insert(1, [InlineKeyboardButton(f"『𝙵𝙸𝙻𝙴𝚂』", 'reqst11'), InlineKeyboardButton(f'『𝚃𝙸𝙿𝚂』', 'tips')])
            
        if offset != "":
            key = f"{message.chat.id}-{message.id}"
            BUTTONS[key] = search
            req = message.from_user.id if message.from_user else 0
            btn.append(
                [InlineKeyboardButton(text=f"📃 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
                 InlineKeyboardButton(text="『𝙽𝙴𝚇𝚃』", callback_data=f"next_{req}_{key}_{offset}")]
            )
        else:
            btn.append(
                [InlineKeyboardButton(text="📃 1/1", callback_data="pages")]
            )
        print("[DEBUG] auto_filter: Button build complete.")
        
    except Exception as e:
        logger.exception(f"CRITICAL ERROR in auto_filter: Failed during BUTTON building: {e}")
        print(f"[DEBUG] auto_filter: FAILED at button building: {e}")
        return # Can't continue if buttons fail

    # --- 3. GETTING IMDB DATA AND FORMATTING CAPTION ---
    try:
        print("[DEBUG] auto_filter: Getting IMDB data...")
        # Use .get() for safe access to settings
        imdb = await get_poster(search, file=(files[0]).file_name) if settings.get("imdb") else None 
        print(f"[DEBUG] IMDB Result was: {imdb}")
        TEMPLATE = settings.get('template') 
        
        if not TEMPLATE:
            print("[DEBUG] auto_filter: No template found in settings! Using default.")
            TEMPLATE = "Here is what i found for your query {query}" # Default fallback

        if imdb:
            print("[DEBUG] auto_filter: IMDB data found. Formatting template.")
            # Use .get() for ALL keys to prevent crashing if a key is missing
            cap = TEMPLATE.format(
                query=search,
                title=imdb.get('title', 'N/A'),
                votes=imdb.get('votes', 'N/A'),
                aka=imdb.get("aka", 'N/A'),
                seasons=imdb.get("seasons", 'N/A'),
                box_office=imdb.get('box_office', 'N/A'),
                localized_title=imdb.get('localized_title', 'N/A'),
                kind=imdb.get('kind', 'N/A'),
                imdb_id=imdb.get("imdb_id", 'N/A'),
                cast=imdb.get("cast", 'N/A'),
                runtime=imdb.get("runtime", 'N/A'),
                countries=imdb.get("countries", 'N/A'),
                certificates=imdb.get("certificates", 'N/A'),
                languages=imdb.get("languages", 'N/A'),
                director=imdb.get("director", 'N/A'),
                writer=imdb.get("writer", 'N/A'),
                producer=imdb.get("producer", 'N/A'),
                composer=imdb.get("composer", 'N/A'),
                cinematographer=imdb.get("cinematographer", 'N/A'),
                music_team=imdb.get("music_team", 'N/A'),
                distributors=imdb.get("distributors", 'N/A'),
                release_date=imdb.get('release_date', 'N/A'),
                year=imdb.get('year', 'N/A'),
                genres=imdb.get('genres', 'N/A'),
                poster=imdb.get('poster'), # .get('poster') is fine, it will be None if missing
                plot=imdb.get('plot', 'N/A'),
                rating=imdb.get('rating', 'N/A'),
                url=imdb.get('url', 'N/A'),
                **locals()
            )
        else:
            print("[DEBUG] auto_filter: No IMDB data. Using simple caption.")
            # This is a safe fallback in case the template ONLY has {query}
            try:
                cap = TEMPLATE.format(query=search, **locals())
            except KeyError:
                cap = f"Here is what i found for your query {search}"

        print("[DEBUG] auto_filter: Caption formatted successfully.")
        
    except Exception as e:
        logger.exception(f"CRITICAL ERROR in auto_filter: Failed during IMDB/Caption formatting: {e}")
        print(f"[DEBUG] auto_filter: FAILED at IMDB/Caption: {e}")
        # FALLBACK: Send a simple message if IMDB/Template fails
        try:
            await message.reply_text(
                f"Here is what I found for your query `{search}`.\n\n_(An error occurred while fetching full details.)_",
                reply_markup=InlineKeyboardMarkup(btn) # btn was built in the first try block
            )
        except Exception as fallback_e:
            logger.error(f"Failed to send fallback message: {fallback_e}")
        return # Stop execution

    # --- 4. SENDING THE REPLY ---
    try:
        print("[DEBUG] auto_filter: Attempting to send reply...")
        if imdb and imdb.get('poster'):
            print("[DEBUG] auto_filter: Sending with photo...")
            try:
                await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1000],
                                          reply_markup=InlineKeyboardMarkup(btn))
            except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                print("[DEBUG] auto_filter: Photo failed, trying smaller poster.")
                pic = imdb.get('poster')
                poster = pic.replace('.jpg', "._V1_UX360.jpg") # Fixed your typo here
                await message.reply_photo(photo=poster, caption=cap[:1000], reply_markup=InlineKeyboardMarkup(btn))
            except Exception as e:
                logger.warning(f"Sending photo failed ({e}), sending as text.")
                print(f"[DEBUG] auto_filter: Photo failed ({e}), sending text.")
                await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
        else:
            print("[DEBUG] auto_filter: Sending as text (no poster)...")
            await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
            
        print("[DEBUG] auto_filter: Reply sent successfully.")
        
        if spoll:
            await msg.message.delete()
            
    except Exception as e:
        logger.exception(f"CRITICAL ERROR in auto_filter: Failed to send reply: {e}")
        print(f"[DEBUG] auto_filter: FAILED at sending reply: {e}")

async def advantage_spell_chok(msg):
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply("I couldn't find any movie in that name.")
        await asyncio.sleep(8)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)  # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))  # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)  # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        k = await msg.reply("I couldn't find anything related to that. Check your spelling")
        await asyncio.sleep(8)
        await k.delete()
        return
    SPELL_CHECK[msg.id] = movielist
    btn = [[
        InlineKeyboardButton(
            text=movie.strip(),
            callback_data=f"spolling#{user}#{k}",
        )
    ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'spolling#{user}#close_spellcheck')])
    await msg.reply("I couldn't find anything related to that\nDid you mean any one of these?",
                    reply_markup=InlineKeyboardMarkup(btn))


async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await filters_db.get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await filters_db.find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                    return True
                except Exception as e:
                    logger.exception(e)
                    return False
            else:
                return False
    return False
