from pyrogram.types import User
from pyrogram import enums
from datetime import datetime

def last_online(from_user: User) -> str:
    
    if from_user.is_bot:
        return "🤖 Bot :("
    if from_user.status == enums.UserStatus.ONLINE:
        return "Currently Online"
    if from_user.status == enums.UserStatus.OFFLINE:
        return datetime.fromtimestamp(from_user.last_online_date).strftime("%a, %d %b %Y, %H:%M:%S")
    if from_user.status == enums.UserStatus.RECENTLY:
        return "Recently"
    if from_user.status == enums.UserStatus.LAST_WEEK:
        return "Within the last week"       
    if from_user.status == enums.UserStatus.LAST_MONTH:
        return "Within the last month" 
    if from_user.status == enums.UserStatus.LONG_AGO:
        return "A long time ago :("

    return "Unknown status"