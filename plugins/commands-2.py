# Made by Lord SA
import os
import logging
import mimetypes
import random
import asyncio
import aiohttp
import tempfile
import traceback
from asyncio import get_running_loop
from io import BytesIO
from Script import script
from time import time, sleep
from datetime import datetime
from pyrogram.errors import UserNotParticipant
from plugins.Tools.help_func.extract_user import extract_user
from plugins.Tools.help_func.last_online import last_online
from pyrogram import Client, filters
from urllib.parse import quote
from info import SUPPORT_CHAT
#from telegraph import upload_file
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, VIDS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
from database.gtrans_mdb import find_one
from plugins.Tools.help_func.admin_check import admin_check
from plugins.Tools.help_func.cust_p_filters import f_onw_fliter
from plugins.Tools.help_func.cust_p_filters import admin_fliter
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.errors.exceptions.bad_request_400 import ChatAdminRequired, UserAdminInvalid
import re
import json
import base64
import requests
logger = logging.getLogger(__name__)

m = None
i = 0
a = None
query = None

@Client.on_message(filters.command(["stickerid"]))
async def stickerid(bot, message):   
    if message.reply_to_message.sticker:
       await message.reply(f"**Sticker ID is**  \n `{message.reply_to_message.sticker.file_id}` \n \n ** Unique ID is ** \n\n`{message.reply_to_message.sticker.file_unique_id}`", quote=True)
    else: 
       await message.reply("Oops !! Not a sticker file")

@Client.on_message(filters.command(["json", 'js', 'showjson']))
async def jsonify(_, message):
    the_real_message = None
    reply_to_id = None

    if message.reply_to_message:
        the_real_message = message.reply_to_message
    else:
        the_real_message = message
    try:
        pk = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🚫 Cʟᴏsᴇ",
                        callback_data="close_data"
                    )
                ]
            ]
        )
        await message.reply_text(f"<code>{the_real_message}</code>", reply_markup=pk, quote=True)
    except Exception as e:
        with open("json.text", "w+", encoding="utf8") as out_file:
            out_file.write(str(the_real_message))
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🚫 Cʟᴏsᴇ",
                        callback_data="close_data"
                    )
                ]
            ]
        )
        await message.reply_document(
            document="json.text",
            caption=str(e),
            disable_notification=True,
            quote=True,
            reply_markup=reply_markup
        )            
        os.remove("json.text")

TG_MAX_SELECT_LEN = 400

@Client.on_message(
    filters.command("purge") &
    f_onw_fliter
)
async def purge(client, message):
    """ purge upto the replied message """
    if message.chat.type not in (("supergroup", "channel")):
        # https://t.me/c/1312712379/84174
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

@Client.on_message(
    filters.command(["pin"]) &
    admin_fliter
)
async def pin(_, message: Message):
    if not message.reply_to_message:
        return
    await message.reply_to_message.pin()

@Client.on_message(
    filters.command(["unpin"]) &
    admin_fliter
)
async def unpin(_, message: Message):
    if not message.reply_to_message:
        return
    await message.reply_to_message.unpin()

@Client.on_message(filters.incoming & ~filters.private & filters.command('inkick'))
def inkick(client, message):
  user = client.get_chat_member(message.chat.id, message.from_user.id)
  if user.status == ("creator"):
    if len(message.command) > 1:
      input_str = message.command
      sent_message = message.reply_text(script.START_KICK)
      sleep(20)
      sent_message.delete()
      message.delete()
      count = 0
      for member in client.iter_chat_members(message.chat.id):
        if member.user.status in input_str and not member.status in ('administrator', 'creator'):
          try:
            client.kick_chat_member(message.chat.id, member.user.id, int(time() + 45))
            count += 1
            sleep(1)
          except (ChatAdminRequired, UserAdminInvalid):
            sent_message.edit(script.ADMIN_REQUIRED)
            client.leave_chat(message.chat.id)
            break
          except FloodWait as e:
            sleep(e.x)
      try:
        sent_message.edit(script.KICKED.format(count))
      except ChatWriteForbidden:
        pass
    else:
      message.reply_text(script.INPUT_REQUIRED)
  else:
    sent_message = message.reply_text(script.CREATOR_REQUIRED)
    sleep(5)
    sent_message.delete()
    message.delete()

@Client.on_message(filters.incoming & ~filters.private & filters.command('dkick'))
def dkick(client, message):
  user = client.get_chat_member(message.chat.id, message.from_user.id)
  if user.status == ("creator"):
    sent_message = message.reply_text(script.START_KICK)
    sleep(20)
    sent_message.delete()
    message.delete()
    count = 0
    for member in client.iter_chat_members(message.chat.id):
      if member.user.is_deleted and not member.status in ('administrator', 'creator'):
        try:
          client.kick_chat_member(message.chat.id, member.user.id, int(time() + 45))
          count += 1
          sleep(1)
        except (ChatAdminRequired, UserAdminInvalid):
          sent_message.edit(script.ADMIN_REQUIRED)
          client.leave_chat(message.chat.id)
          break
        except FloodWait as e:
          sleep(e.x)
    try:
      sent_message.edit(script.DKICK.format(count))
    except ChatWriteForbidden:
      pass
  else:
    sent_message = message.reply_text(script.CREATOR_REQUIRED)
    sleep(5)
    sent_message.delete()
    message.delete()

@Client.on_message(filters.incoming & ~filters.private & filters.command('instatus'))
def instatus(client, message):
  user = client.get_chat_member(message.chat.id, message.from_user.id)
  if user.status in ('administrator', 'creator', 'ADMINS'):
    sent_message = message.reply_text(script.FETCHING_INFO)
    recently = 0
    within_week = 0
    within_month = 0
    long_time_ago = 0
    deleted_acc = 0
    uncached = 0
    bot = 0
    for member in client.iter_chat_members(message.chat.id):
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
    sent_message.edit(script.STATUS.format(message.chat.title, recently, within_week, within_month, long_time_ago, deleted_acc, bot, uncached))


#Share Text(Venel revert akikondim)

#Telegraph

@Client.on_message(filters.command(["tgmedia", "tgraph", "telegraph"]))
async def telegraph_handler(client, message: Message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply("Reply to a supported media file")

    status_msg = await message.reply("Processing, please wait...")

    # Check supported files & size (using the 5MB limit)
    if not (
        (replied.photo and replied.photo.file_size <= 5242880)
        or (replied.animation and replied.animation.file_size <= 5242880)
        or (
            replied.video
            and replied.video.file_name
            and replied.video.file_name.endswith(".mp4")
            and replied.video.file_size <= 5242880
        )
        or (
            replied.document
            and replied.document.file_name
            and replied.document.file_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4"))
            and replied.document.file_size <= 5242880
        )
    ):
        return await status_msg.edit_text("Not supported or file too large (max 5MB)!")

    download_location = None
    
    try:
        # --- 1. DOWNLOAD THE FILE ---
        await status_msg.edit_text("Downloading file...")
        download_location = await client.download_media(replied, file_name="downloads/")

        if download_location is None or not os.path.exists(download_location):
            return await status_msg.edit_text("❌ File download failed.")

        await status_msg.edit_text("Uploading to Telegraph...")

        # --- 2. UPLOAD THE FILE (Inner 'try' block) ---
        try:
            # --- NEW MIME TYPE LOGIC ---
            # Define the *exact* mime types Telegra.ph accepts
            MIME_MAP = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.mp4': 'video/mp4',
            }

            # Get the file extension
            file_ext = os.path.splitext(download_location)[1].lower()
            
            # Get the exact mime type from our map
            mime_type = MIME_MAP.get(file_ext)

            # If extension isn't in our map (shouldn't happen, but as a failsafe)
            if mime_type is None:
                # Fallback to guessing
                mime_type, _ = mimetypes.guess_type(download_location)
                if mime_type is None: 
                    # Last resort
                    mime_type = 'application/octet-stream'
            # --- END OF NEW MIME TYPE LOGIC ---

            # Open the file and prepare it for upload
            with open(download_location, 'rb') as f:
                files = {
                    'file': (
                        os.path.basename(download_location),  # Send the original filename
                        f,                                    # The file object
                        mime_type                             # The *correct* MIME type
                    )
                }
                
                response = requests.post(
                    'https://telegra.ph/upload',
                    files=files
                )
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                except requests.exceptions.JSONDecodeError:
                    return await status_msg.edit_text(f"Upload Error: Telegraph returned an invalid response (not JSON).")
            else:
                return await status_msg.edit_text(f"Upload Error: Telegraph server returned status code {response.status_code}. Response: {response.text}")

        except Exception as e:
            traceback.print_exc()
            return await status_msg.edit_text(f"Upload error: {e}")
        # --- END OF UPLOAD BLOCK ---


        # --- 3. HANDLE THE RESPONSE ---
        link = None
        if isinstance(response_json, list) and len(response_json) > 0:
            item = response_json[0]
            if isinstance(item, dict) and 'src' in item:
                link = f"https.telegra.ph{item['src']}"
            elif 'error' in item:
                 return await status_msg.edit_text(f"Telegraph Error: {item.get('error')}")
        
        if link is None:
            return await status_msg.edit_text(f"❌ Unexpected response from Telegraph API: {response_json}")
        # --- END OF RESPONSE HANDLING ---

        await status_msg.delete()

        # --- 4. SEND THE FINAL LINK ---
        await message.reply(
            f"<b>Link:</b>\n\n<code>{link}</code>",
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("『𝕺𝙿𝙴𝙽 B_𝕷𝙸𝙽𙺈』", url=link), # I fixed the broken unicode in the button
                        InlineKeyboardButton(
                            "『𝕾𝙷𝙰𝚁𝙴 𝕷𝙸𝙽𙺈』",
                            url=f"https://telegram.me/share/url?url={link}",
                        ),
                    ],
                    [InlineKeyboardButton("『𝙿𝚁𝙴𝚅』", callback_data="close_data")],
                ]
            ),
        )

    finally:
        if download_location and os.path.exists(download_location):
            os.remove(download_location)


@Client.on_message(filters.command('whois') & f_onw_fliter)
async def who_is(client, message):
    """ extract user information """
    status_message = await message.reply_text(
        "നിക്കു നെൻപ നോക്കട്ടെ 🙂"
    )
    from_user = None
    from_user_id, _ = extract_user(message)
    try:
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        await status_message.edit(str(error))
        return
    if from_user is None:
        await status_message.edit("no valid user_id / message specified")
        return
    
    first_name = from_user.first_name or ""
    last_name = from_user.last_name or ""
    username = from_user.username or ""
    
    message_out_str = (
        "<b>Name:</b> "
        f"<a href='tg://user?id={from_user.id}'>{first_name}</a>\n"
        f"<b>Suffix:</b> {last_name}\n"
        f"<b>Username:</b> @{username}\n"
        f"<b>User ID:</b> <code>{from_user.id}</code>\n"
        f"<b>User Link:</b> {from_user.mention}\n" if from_user.username else ""
        f"<b>Is Deleted:</b> True\n" if from_user.is_deleted else ""
        f"<b>Is Verified:</b> True" if from_user.is_verified else ""
        f"<b>Is Scam:</b> True" if from_user.is_scam else ""
        # f"<b>Is Fake:</b> True" if from_user.is_fake else ""
        f"<b>Last Seen:</b> <code>{last_online(from_user)}</code>\n\n"
    )

    if message.chat.type in ["supergroup", "channel"]:
        try:
            chat_member_p = await message.chat.get_member(from_user.id)
            joined_date = datetime.fromtimestamp(
                chat_member_p.joined_date or time.time()
            ).strftime("%Y.%m.%d %H:%M:%S")
            message_out_str += (
                "<b>Joined on:</b> <code>"
                f"{joined_date}"
                "</code>\n"
            )
        except UserNotParticipant:
            pass
    chat_photo = from_user.photo
    if chat_photo:
        local_user_photo = await client.download_media(
            message=chat_photo.big_file_id
        )
        await message.reply_photo(
            photo=local_user_photo,
            quote=True,
            caption=message_out_str,
            disable_notification=True
        )
        os.remove(local_user_photo)
    else:
        await message.reply_text(
            text=message_out_str,
            quote=True,
            disable_notification=True
        )
    await status_message.delete()
