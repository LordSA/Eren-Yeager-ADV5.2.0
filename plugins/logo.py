import os
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message
import logging
logger = logging.getLogger(__name__)
FONT_PATH = "./plugins/resource/Chopsic.otf"

OUTPUT_PATH = "logo.png" # The file will be created and then deleted

@Client.on_message(filters.command('logo'))
async def logo_generator(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text('Provide Some Text To Draw!')
        return
    
    text = message.text.split(None, 1)[1]
    if not os.path.exists(FONT_PATH):
        logger.error(f"Font file not found at: {FONT_PATH}")
        await message.reply_text(
            f"⚠️ **Font File Missing!**\n\n"
            f"I can't find the font. Please ask the bot owner to set the `FONT_PATH` in the code."
        )
        return
    status_message = await message.reply_text('Creating your logo...wait!')
    
    try:
        img = Image.new('RGB', (1920, 1080), color='black')
        draw = ImageDraw.Draw(img)
        image_width, image_height = img.size
        try:
            font = ImageFont.truetype(FONT_PATH, 330)
        except Exception as e:
            logger.error(f"Error loading font: {e}")
            await status_message.edit_text(f"Error: Could not load the font at {FONT_PATH}. Make sure it's a valid .ttf or .otf file.")
            return
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (image_width - w) / 2
        y = (image_height - h) / 2
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        draw.text((x, y + 6), text, font=font, fill="black", stroke_width=25, stroke_fill="yellow")
        img.save(OUTPUT_PATH, "PNG")
        await client.send_photo(
            chat_id=message.chat.id,
            photo=OUTPUT_PATH,
            caption="Mysterious",
            reply_to_message_id=message.id 
        )

        await status_message.delete()

    except Exception as e:
        logger.error(f"Error in logo command: {e}")
        await status_message.edit_text(f'Error: {e}')
    
    finally:
        if os.path.exists(OUTPUT_PATH):
            os.remove(OUTPUT_PATH)