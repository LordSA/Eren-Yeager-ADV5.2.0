import os
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import logging

logger = logging.getLogger(__name__)

FONTS = {
    "Chopsic": "plugins/resource/Chopsic.otf",
    "Agile": "plugins/resource/agile.otf",
    "Brittany Signature": "plugins/resource/BrittanySignature.ttf",
    "Historic": "plugins/resource/Historic.otf",
    "Kamali": "plugins/resource/Kamali.ttf",
    "Open-Sans": "plugins/resource/OpenSans-Italic.ttf"
}

COLORS = {
    # Original
    "Gold": "gold",
    "Yellow": "yellow",
    "White": (255, 255, 255),
    "Blue": "blue",
    "Red": "red",
    "Green": "green",
    "Orange": "orange",
    "Purple": "purple",
    "Pink": "pink",
    "Cyan": "cyan",
    "Silver": "silver",
    "Magenta": "magenta",
    "Lime": "lime",
    "Aqua": "aqua"
}

OUTPUT_PATH = "logo.png"

@Client.on_message(filters.command('logo'))
async def logo_command_handler(client: Client, message: Message):
    
    text = ""
    if len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    else:
        await message.reply_text(
            "**How to use:**\n"
            "1. `/logo Your Text`\n"
            "2. Reply to a text message with `/logo`"
        )
        return
        
    if not os.path.exists(list(FONTS.values())[0]):
        logger.error(f"Cannot find default font at: {list(FONTS.values())[0]}")
        await message.reply_text(
            f"⚠️ **Font File Missing!**\n\n"
            f"I can't find the fonts. Please ask the bot owner to set them up."
        )
        return
        
    buttons = []
    for font_name in FONTS.keys():
        buttons.append(
            InlineKeyboardButton(font_name, callback_data=f"logo_font_{font_name}")
        )
    
    font_buttons = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]

    await message.reply_text(
        "**Select a font:**",
        reply_markup=InlineKeyboardMarkup(font_buttons),
        reply_to_message_id=message.id
    )

@Client.on_callback_query(filters.regex("^logo_font_"))
async def font_selection_handler(client: Client, callback_query: CallbackQuery):
    
    font_name = callback_query.data.split("_")[-1]
    
    buttons = []
    for color_name in COLORS.keys():
        buttons.append(
            InlineKeyboardButton(color_name, callback_data=f"logo_color_{color_name}_{font_name}")
        )
    
    color_buttons = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    
    await callback_query.message.edit_text(
        "**Select a stroke color:**",
        reply_markup=InlineKeyboardMarkup(color_buttons)
    )

@Client.on_callback_query(filters.regex("^logo_color_"))
async def color_selection_handler(client: Client, callback_query: CallbackQuery):
    
    await callback_query.answer("Creating your logo...")
    
    parts = callback_query.data.split("_")
    color_name = parts[2]
    font_name = parts[3]
    
    try:
        original_message = callback_query.message.reply_to_message
        text_parts = original_message.text.split(None, 1)
        if len(text_parts) > 1:
            text = text_parts[1]
        elif original_message.reply_to_message and original_message.reply_to_message.text:
            text = original_message.reply_to_message.text
        else:
            raise AttributeError("Could not find text")
            
    except Exception as e:
        logger.error(f"Could not find original text: {e}")
        await callback_query.message.edit_text("Error: Could not find the original text.")
        return

    font_path = FONTS.get(font_name)
    stroke_color = COLORS.get(color_name)
    
    if not font_path or not stroke_color:
        await callback_query.message.edit_text("Error: Invalid font or color.")
        return
        
    try:
        logo_file = await generate_logo(text, font_path, stroke_color)
        
        await client.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=logo_file,
            caption="Mysterious",
            reply_to_message_id=original_message.id
        )
        
        await callback_query.message.delete()
        
    except Exception as e:
        logger.error(f"Error in logo generation: {e}")
        await callback_query.message.edit_text(f'Error: {e}')
    
    finally:
        if os.path.exists(OUTPUT_PATH):
            os.remove(OUTPUT_PATH)

async def generate_logo(text: str, font_path: str, stroke_color) -> str:
    """Generates the logo and returns the path to the file."""
    
    img = Image.new('RGB', (1920, 1080), color='black')
    draw = ImageDraw.Draw(img)
    image_width, image_height = img.size
    
    font = ImageFont.truetype(font_path, 330)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    x = (image_width - w) / 2
    y = (image_height - h) / 2
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    draw.text((x, y + 6), text, font=font, fill="black", stroke_width=25, stroke_fill=stroke_color)
    
    img.save(OUTPUT_PATH, "PNG")
    return OUTPUT_PATH