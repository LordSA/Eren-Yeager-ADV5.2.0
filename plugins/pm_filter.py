# MADE BY LORD SA
import asyncio
import re
import ast
import math
import random
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, VIDS
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import filters_db
import logging

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
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"© 『{get_size(file.file_size)}』 {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"© {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"『{get_size(file.file_size)}』",
                    callback_data=f'files#{file.file_id}',
                ),
            ]
            for file in files
        ]
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
        ident, file_id = query.data.split("#")
        print(f"[DEBUG] File button clicked - ident: {ident}, file_id: {file_id}")
        
        try:
            files_ = await get_file_details(file_id)
            print(f"[DEBUG] Files retrieved: {files_}")
            if not files_:
                return await query.answer('No such file exist.', show_alert=True)
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer(f'Hey {query.from_user.first_name} Check PM, I have sent files in pm(നിൻ്റെ pm നോക്ക് അതിൽ ഞാൻ ഇട്ടിട്ടുണ്ട്)', show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn!(പൊട്ട എന്നെ unblock ചെയ്യൂ)', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness(വിളച്ചിൽ എടുകുന്നോ എന്നെ ചൂടാക്കാതെ പോയി സബ് ചെയ്യൂ🙄), But Don't Be Oversmart 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        try:
            files_ = await get_file_details(file_id)
            if not files_:
                return await query.answer('No such file exist.(അങ്ങനെ ഒരു സാധനവും ഇതിൽ ഇല്ല😑)',show_alert=True)
        
        files = files_[0]

        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
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
            InlineKeyboardButton('『𝙺𝙸𝙲𝙺』', callback_data='zombies')                                                       
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
    elif query.data == "zombies":
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
            text=script.ZOMBIES_TXT,
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
            InlineKeyboardButton('👩‍🦯 𝕭𝙰𝙲𝙺', callback_data='nxt2')
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
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('Piracy Is Crime')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('『𝙵𝙸𝙻𝚃𝙴𝚁 𝙱𝚄𝚃𝚃𝙾𝙽』',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝚂𝙸𝙽𝙶𝙻𝙴' if settings["button"] else '𝙳𝙾𝚄𝙱𝙻𝙴',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝙱𝙾𝚃 𝙿𝙼』', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings["botpm"] else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝙵𝙸𝙻𝙴 𝚂𝙴𝙲𝚄𝚁𝙴』',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings["file_secure"] else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝙸𝙼𝙳𝙱』', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings["imdb"] else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝚂𝙿𝙴𝙻𝙻 𝙲𝙷𝙴𝙲𝙺』',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings["spell_check"] else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('『𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚂𝙿𝙴𝙴𝙲𝙷』', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝚈𝙴𝚂' if settings["welcome"] else '❌ 𝙽𝙾',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('Piracy Is Crime')

async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(msg.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(msg)
                else:
                    return

        else:
            return
    else:
        settings = await get_settings(msg.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"© 『{get_size(file.file_size)}』 {file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"© {file.file_name}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"『{get_size(file.file_size)}』",
                    callback_data=f'{pre}#{file.file_id}',
                ),
            ]
            for file in files
        ]
    btn.insert(0, 
        [
            InlineKeyboardButton(f'🎬 {search} 🎬', 'reqst11')
        ]
    )
    btn.insert(1,
        [
            InlineKeyboardButton(f"『𝙵𝙸𝙻𝙴𝚂』", 'reqst11'),
            InlineKeyboardButton(f'『𝚃𝙸𝙿𝚂』', 'tips')
        ]
    )
        
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
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"Here is what i found for your query {search}"
    if imdb and imdb.get('poster'):
        try:
            await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1000],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            await message.reply_photo(photo=poster, caption=cap[:1000], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    else:
        await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    if spoll:
        await msg.message.delete()


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
                except Exception as e:
                    logger.exception(e)
                return True
    else:
        return False
