import os
import asyncio
import logging

from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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


def get_file_name(msg):
    if msg.file and msg.file.name:
        return msg.file.name
    elif msg.photo:
        return f"photo_{msg.id}.jpg"
    else:
        return f"file_{msg.id}"


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
                if msg.media and isinstance(msg.media, (MessageMediaDocument, MessageMediaPhoto)):
                    file_name = get_file_name(msg)
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


def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Run once immediately for testing
    scheduler.add_job(sync_saved_files, 'date')
    # Schedule daily at 2 a.m.
    scheduler.add_job(sync_saved_files, 'cron', hour=2, minute=0)
    scheduler.start()
    logger.info('Scheduler started: sync will run immediately and then daily at 2 a.m.')
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass


def main():
    start_scheduler()


if __name__ == "__main__":
    main()
