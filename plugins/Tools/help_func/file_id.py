from pyrogram.types import Message
from pyrogram import enums 
from typing import Union, Optional

MediaType = Union[
    "types.Audio", "types.Document", "types.Photo",
    "types.Sticker", "types.Video", "types.VideoNote",
    "types.Voice", "types.Animation"
]

def get_file_id(msg: Message) -> Optional[MediaType]:
    if not msg.media:
        return None 
    media_with_files = {
        enums.MessageMediaType.PHOTO,
        enums.MessageMediaType.ANIMATION,
        enums.MessageMediaType.AUDIO,
        enums.MessageMediaType.DOCUMENT,
        enums.MessageMediaType.VIDEO,
        enums.MessageMediaType.VIDEO_NOTE,
        enums.MessageMediaType.VOICE,
        enums.MessageMediaType.STICKER
    }

    if msg.media in media_with_files:
        return getattr(msg, msg.media.value)
    
    return None 