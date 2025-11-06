import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

@Client.on_message(filters.command(["json", 'js', 'showjson']))
async def jsonify(_, message: Message):
    """Sends the full JSON object of a message for debugging."""
    
    the_real_message = message.reply_to_message or message

    try:
        # Try sending as a text message
        pk = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="🚫 Cʟᴏsᴇ", callback_data="close_data")]]
        )
        await message.reply_text(f"<code>{the_real_message}</code>", reply_markup=pk, quote=True)
    
    except Exception as e:
        # If it fails (usually too long), send as a file
        with open("json.text", "w+", encoding="utf8") as out_file:
            out_file.write(str(the_real_message))
        
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="🚫 Cʟᴏsᴇ", callback_data="close_data")]]
        )
        await message.reply_document(
            document="json.text",
            caption=str(e),
            quote=True,
            reply_markup=reply_markup
        )
        os.remove("json.text")