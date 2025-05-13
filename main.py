import os
import asyncio
import logging

from smb.SMBConnection import SMBConnection
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

# SMB config from environment
SMB_HOST = os.getenv('SMB_HOST')
SMB_SHARE = os.getenv('SMB_SHARE')
SMB_USER = os.getenv('SMB_USER')
SMB_PASSWORD = os.getenv('SMB_PASSWORD')
SMB_PATH = os.getenv('SMB_PATH', '')  # optional subfolder
SMB_DOMAIN = os.getenv('SMB_DOMAIN', '')  # optional, for Windows domains

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


def smb_upload(local_path, remote_name):
    """Upload a file to SMB share at the path specified by SMB_PATH in the .env file, ensuring the folder exists."""
    if not (SMB_HOST and SMB_SHARE and SMB_USER and SMB_PASSWORD):
        logger.debug("SMB config not provided, skipping SMB upload.")
        return
    try:
        from socket import gethostname
        client_name = gethostname()
        conn = SMBConnection(
            SMB_USER, SMB_PASSWORD, client_name, SMB_HOST, domain=SMB_DOMAIN, use_ntlm_v2=True
        )
        assert conn.connect(SMB_HOST, 139)
        # Clean up SMB_PATH: remove share name if present, and any leading/trailing slashes/spaces
        folder = SMB_PATH.strip().lstrip('/').lstrip('\\') if SMB_PATH else ''
        if folder.lower().startswith(SMB_SHARE.lower() + '/'):
            folder = folder[len(SMB_SHARE)+1:]
        elif folder.lower().startswith(SMB_SHARE.lower() + '\\'):
            folder = folder[len(SMB_SHARE)+1:]
        elif folder.lower() == SMB_SHARE.lower():
            folder = ''
        filename = remote_name
        # Recursively create folders if they don't exist
        remote_path = filename
        if folder:
            # Split and create each part if needed
            current = ''
            for part in folder.replace('\\', '/').split('/'):
                if not part:
                    continue
                current = f"{current}/{part}" if current else part
                try:
                    conn.listPath(SMB_SHARE, current)
                except Exception:
                    try:
                        conn.createDirectory(SMB_SHARE, current)
                        logger.info(f"Created SMB directory: {current}")
                    except Exception as e:
                        logger.error(f"Failed to create SMB directory {current}: {e}")
                        conn.close()
                        return
            remote_path = f"{folder}/{filename}"
        with open(local_path, 'rb') as f:
            conn.storeFile(SMB_SHARE, remote_path, f)
        conn.close()
        logger.info(f"Uploaded to SMB: {remote_path}")
    except Exception as e:
        logger.error(f"SMB upload failed for {remote_name}: {e}")


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
                        smb_upload(file_path, file_name)  # Upload to SMB if configured
                    except Exception as e:
                        logger.error(f"Failed to download {file_name}: {e}")
            offset_id = messages[-1].id
        logger.info(f"Downloaded {total} files to '{DOWNLOAD_DIR}'")


async def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Run once immediately for testing
    scheduler.add_job(sync_saved_files, 'date')
    # Schedule daily at 2 a.m.
    scheduler.add_job(sync_saved_files, 'cron', hour=2, minute=0)
    scheduler.start()
    logger.info('Scheduler started: sync will run immediately and then daily at 2 a.m.')
    try:
        while True:
            await asyncio.sleep(3600)  # Keep the loop alive
    except (KeyboardInterrupt, SystemExit):
        pass

async def main():
    await start_scheduler()

if __name__ == "__main__":
    asyncio.run(main())
