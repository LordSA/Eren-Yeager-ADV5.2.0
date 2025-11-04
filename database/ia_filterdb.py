import logging
import re
from pymongo import IndexModel 
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError

from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# MongoDB client & database
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]

# umongo instance
instance = Instance.from_db(db)


@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')    
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        collection_name = COLLECTION_NAME
        indexes = [
            IndexModel(
                [('file_name', 'text'), ('caption', 'text')],
                name='search_index'
            )
        ]


# -------------------- Core Functions --------------------

async def save_file(media):
    """Save a media file to the database"""
    file_id = media.file_id
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))

    try:
        file = Media(
            file_id=file_id,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None
        )
    except ValidationError as e:
        logger.exception(f"Validation error while saving file: {e}")
        return False, 2

    try:
        await file.commit()
    except DuplicateKeyError:
        logger.warning(f"{getattr(media, 'file_name', 'NO_FILE')} is already saved in database")
        return False, 0
    except Exception as e:
        logger.exception(f"Unexpected error saving file: {e}")
        return False, 3

    logger.info(f"{getattr(media, 'file_name', 'NO_FILE')} saved to database")
    return True, 1


async def get_search_results(query, file_type=None, max_results=10, offset=0):
    """Search media files using MongoDB's $text operator (FAST)"""
    query = query.strip()
    if not query:
        return [], 0, 0 
    filter_query = {'$text': {'$search': query}}

    if USE_CAPTION_FILTER is False:
        pass 

    if file_type:
        filter_query['file_type'] = file_type

    total_results = await Media.count_documents(filter_query)
    next_offset = offset + max_results
    if next_offset > total_results:
        next_offset = ''
    cursor = Media.find(
        filter_query,
        projection={'score': {'$meta': 'textScore'}}
    ).sort(
        [('score', {'$meta': 'textScore'})] 
    ).skip(
        offset
    ).limit(
        max_results
    )
    
    files = await cursor.to_list(length=max_results)
    return files, next_offset, total_results


async def get_file_details(file_id):
    """Get full file details by file_id"""
    doc = await Media.find_one({'file_id': file_id})
    return doc