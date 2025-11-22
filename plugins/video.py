import os
import uuid
import asyncio
import logging
import yt_dlp
import static_ffmpeg
static_ffmpeg.add_paths()

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOAD_LOCATION = "./downloads"
VIDEO_SEARCH_CACHE = {} 

@Client.on_message(filters.command(["video", "vid", "vs"]))
async def video_search_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/video [Video Name]`\n\nExample: `/video Costa Rica 4k`")

    query = message.text.split(None, 1)[1]
    m = await message.reply_text("🔎 **Searching for video...**")

    try:
        ydl_opts = {
            'quiet': True,
            'noplaylist': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, f"ytsearch15:{query}", download=False)
            results = info.get('entries', [])

        if not results:
            return await m.edit("❌ **No results found.**")

        search_id = str(uuid.uuid4())[:8]
        VIDEO_SEARCH_CACHE[search_id] = results

        await send_video_page(m, search_id, 0, query)

    except Exception as e:
        await m.edit(f"❌ **Search Error:** `{str(e)}`")


async def send_video_page(message_object, search_id, offset, query_text):
    results = VIDEO_SEARCH_CACHE.get(search_id)
    if not results:
        return await message_object.edit("❌ **Session expired.** Please search again.")

    current_batch = results[offset : offset + 5]
    
    buttons = []
    for video in current_batch:
        title = video.get('title')
        vid_id = video.get('id')
        duration = video.get('duration')
        
        if duration:
            mins, secs = divmod(duration, 60)
            time_str = f"{int(mins)}:{int(secs):02d}"
        else:
            time_str = "N/A"

        if len(title) > 30:
            title = title[:30] + "..."

        buttons.append([InlineKeyboardButton(f"🎬 {title} [{time_str}]", callback_data=f"v_qual#{vid_id}")])

    nav_btns = []
    if offset >= 5:
        nav_btns.append(InlineKeyboardButton("⬅️ Back", callback_data=f"vspage#{search_id}#{offset - 5}"))
    
    if offset + 5 < len(results):
        nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"vspage#{search_id}#{offset + 5}"))

    buttons.append(nav_btns)
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_data")])

    text = f"🎬 **Select a Video:**\nSearch: `{query_text}`\nShowing: {offset+1}-{min(offset+5, len(results))}"
    
    await message_object.edit(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^vspage"), group=-1)
async def video_page_callback(client, query):
    try:
        _, search_id, offset_str = query.data.split("#")
        offset = int(offset_str)
        try:
            search_text = query.message.text.split("\n")[1].replace("Search: ", "")
        except:
            search_text = "Results"
        
        await send_video_page(query.message, search_id, offset, search_text)
        await query.answer()
    except Exception as e:
        logger.error(f"Page Nav Error: {e}")


@Client.on_callback_query(filters.regex("^v_qual"), group=-1)
async def video_quality_callback(client, query):
    vid_id = query.data.split("#")[1]
    
    buttons = [
        [
            InlineKeyboardButton("360p", callback_data=f"dl_vid#{vid_id}#360"),
            InlineKeyboardButton("480p", callback_data=f"dl_vid#{vid_id}#480")
        ],
        [
            InlineKeyboardButton("720p (HD)", callback_data=f"dl_vid#{vid_id}#720"),
            InlineKeyboardButton("1080p (FHD)", callback_data=f"dl_vid#{vid_id}#1080")
        ],
        [
            InlineKeyboardButton("1440p (2K)", callback_data=f"dl_vid#{vid_id}#1440"),
            InlineKeyboardButton("2160p (4K)", callback_data=f"dl_vid#{vid_id}#2160")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data=f"back_to_search")] 
    ]
    
    await query.message.edit(
        f"🎞 **Select Resolution:**\nhttps://youtu.be/{vid_id}\n\n*Note: 4K downloads may take longer and fail if over 2GB.*",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^dl_vid"), group=-1)
async def download_video_callback(client: Client, query: CallbackQuery):
    _, vid_id, height = query.data.split("#")
    height = int(height)
    link = f"https://www.youtube.com/watch?v={vid_id}"
    
    await query.answer(f"Initializing {height}p Download...", show_alert=False)
    status_msg = await query.message.edit(f"📥 **Downloading {height}p...**\nPlease wait, merging video & audio takes time.")

    if not os.path.isdir(DOWNLOAD_LOCATION):
        os.makedirs(DOWNLOAD_LOCATION)
    
    output_path = f"{DOWNLOAD_LOCATION}/{vid_id}_{height}.%(ext)s"

    try:
        format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"

        ydl_opts = {
            'format': format_str,
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'writethumbnail': True,
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = await asyncio.to_thread(ydl.extract_info, link, download=True)
            
        file_path = f"{DOWNLOAD_LOCATION}/{vid_id}_{height}.mp4"
        if not os.path.exists(file_path):
             file_path = f"{DOWNLOAD_LOCATION}/{vid_id}_{height}.mkv"
        
        title = info_dict.get('title', 'Unknown Video')
        duration = info_dict.get('duration')
        
        thumb_path = f"{DOWNLOAD_LOCATION}/{vid_id}_{height}.jpg"
        if not os.path.exists(thumb_path):
            thumb_path = f"{DOWNLOAD_LOCATION}/{vid_id}_{height}.webp"
        if not os.path.exists(thumb_path):
            thumb_path = None

        file_size = os.path.getsize(file_path)
        if file_size > 2 * 1024 * 1024 * 1024:
             await status_msg.edit("❌ **File too big!**\nTelegram cannot upload files larger than 2GB.")
             os.remove(file_path)
             return

        await status_msg.edit("📤 **Uploading...**")

        await client.send_video(
            chat_id=query.message.chat.id,
            video=file_path,
            caption=f"🎬 **{title}**\nquality: {height}p\nUploaded by {client.me.mention}",
            thumb=thumb_path,
            duration=duration,
            supports_streaming=True
        )

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Video DL Error: {e}")
        try:
            await status_msg.edit(f"❌ **Download Failed:**\n`{str(e)}`")
        except:
            pass
    
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if 'thumb_path' in locals() and thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)


@Client.on_callback_query(filters.regex("^close_data"))
async def close_callback(client, query):
    await query.message.delete()

@Client.on_callback_query(filters.regex("^back_to_search"))
async def back_to_search_callback(client, query):
    await query.message.delete()