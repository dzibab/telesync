import os
import asyncio
import logging

from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION = 'telesync_session'
DOWNLOAD_DIR = 'downloads'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)


async def sync_saved_files():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        saved = await client.get_entity('me')
        offset_id = 0
        total = 0
        while True:
            history = await client(GetHistoryRequest(
                peer=saved,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))
            messages = history.messages
            if not messages:
                break
            for msg in messages:
                if msg.media:
                    if isinstance(msg.media, (MessageMediaDocument, MessageMediaPhoto)):
                        # Get file name from message
                        file_name = None
                        if msg.file and msg.file.name:
                            file_name = msg.file.name
                        elif msg.photo:
                            # For photos, Telethon generates a name if not present
                            file_name = f"photo_{msg.id}.jpg"
                        else:
                            file_name = f"file_{msg.id}"
                        file_path = os.path.join(DOWNLOAD_DIR, file_name)
                        if os.path.exists(file_path):
                            logger.info(f"Skipping existing file: {file_name}")
                            continue
                        try:
                            await client.download_media(msg, file_path)
                            logger.info(f"Downloaded: {file_name}")
                            total += 1
                        except Exception as e:
                            logger.error(f"Failed to download {file_name}: {e}")
            offset_id = messages[-1].id
        logger.info(f"Downloaded {total} files to '{DOWNLOAD_DIR}'")


def main():
    asyncio.run(sync_saved_files())


if __name__ == "__main__":
    main()
