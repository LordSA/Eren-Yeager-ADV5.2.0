import re
import time
from typing import List, Tuple
from pyrogram.types import Message, InlineKeyboardButton, User

BTN_URL_REGEX = re.compile(
    r"(\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\))"
)

def button_markdown_parser(msg: Message) -> Tuple[str, List[List[InlineKeyboardButton]]]:
    markdown_note = None
    if msg.media:
        if msg.caption:
            markdown_note = msg.caption.markdown
    else:
        markdown_note = msg.text.markdown

    note_data = ""
    buttons = []
    if markdown_note is None:
        return note_data, buttons

    if markdown_note.startswith("/"):
        args = markdown_note.split(None, 2)
        
        if len(args) < 3:
            return "", []
        
        markdown_note = args[2]

    prev = 0
    for match in BTN_URL_REGEX.finditer(markdown_note):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            if bool(match.group(4)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3)
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3)
                )])
            note_data += markdown_note[prev:match.start(1)]
            prev = match.end(1)
        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += markdown_note[prev:]

    return note_data, buttons


def extract_time(time_val: str):
    if any(time_val.endswith(unit) for unit in ('s', 'm', 'h', 'd')):
        unit = time_val[-1]
        time_num = time_val[:-1]
        if not time_num.isdigit():
            return None

        if unit == 's':
            bantime = int(time.time() + int(time_num))
        elif unit == 'm':
            bantime = int(time.time() + int(time_num) * 60)
        elif unit == 'h':
            bantime = int(time.time() + int(time_num) * 60 * 60)
        elif unit == 'd':
            bantime = int(time.time() + int(time_num) * 24 * 60 * 60)
        else:
            return None
        return bantime
    else:
        return None


def format_welcome_caption(html_string: str, user: User) -> str:
    return html_string.format(
        dc_id=user.dc_id,
        first_name=user.first_name or "",
        id=user.id,
        last_name=user.last_name or "",
        mention=user.mention,
        username=user.username or ""
    )