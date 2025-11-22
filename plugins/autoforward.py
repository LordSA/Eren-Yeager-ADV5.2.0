import os
import json
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from info import ADMINS

DB_FILE = "autoforward_db.json"

def load_fw_data():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_fw_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_forward(source_id, dest_id):
    data = load_fw_data()
    data[str(source_id)] = int(dest_id)
    save_fw_data(data)

def del_forward(source_id):
    data = load_fw_data()
    if str(source_id) in data:
        del data[str(source_id)]
        save_fw_data(data)
        return True
    return False

@Client.on_message(filters.command(["autofw", "addfw"]))
async def add_autoforward_handler(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text(
            "❌ **Usage:** `/autofw [Source_ID] [Dest_ID]`\n\n"
            "Example: `/autofw -100123456789 -100987654321`"
        )

    try:
        source_id = int(message.command[1])
        dest_id = int(message.command[2])
    except ValueError:
        return await message.reply_text("❌ **Error:** IDs must be numbers.")

    try:
        s_chat = await client.get_chat(source_id)
        d_chat = await client.get_chat(dest_id)
    except Exception as e:
        return await message.reply_text(f"❌ **Error:** I cannot access one of the channels.\nMake sure I am Admin in both!\n\n`{e}`")

    add_forward(source_id, dest_id)
    
    await message.reply_text(
        f"✅ **Auto-Forwarder Connected!**\n\n"
        f"📤 **Source:** {s_chat.title} (`{source_id}`)\n"
        f"📥 **Dest:** {d_chat.title} (`{dest_id}`)"
    )

@Client.on_message(filters.command(["unfw", "delfw"]))
async def delete_autoforward_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/unfw [Source_ID]`")

    try:
        source_id = message.command[1]
        success = del_forward(source_id)
        
        if success:
            await message.reply_text(f"✅ Stopped forwarding from `{source_id}`.")
        else:
            await message.reply_text(f"❌ No active forwarder found for `{source_id}`.")
            
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command("listfw"))
async def list_autoforward_handler(client: Client, message: Message):
    data = load_fw_data()
    if not data:
        return await message.reply_text("📂 No auto-forwarders active.")

    text = "🔄 **Active Forwarders:**\n\n"
    for src, dst in data.items():
        text += f"🔹 `{src}` ➔ `{dst}`\n"
    
    await message.reply_text(text)

@Client.on_message(filters.channel)
async def auto_forward_logic(client: Client, message: Message):
    data = load_fw_data()
    source_id = str(message.chat.id)

    if source_id in data:
        dest_id = data[source_id]
        
        try:
            await message.forward(dest_id)
        except Exception as e:
            print(f"[AutoFW] Failed to forward from {source_id}: {e}")