"""
Telegram client module for TeleSync application.
"""
import os

from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from telethon.tl.functions.messages import GetHistoryRequest

from logger import get_logger
import config
from smb_uploader import SMBUploader

logger = get_logger('telegram_client')


class TelegramSavedMessagesClient:
    """Class for interacting with Telegram's Saved Messages feature."""

    def __init__(self):
        self.client = TelegramClient(config.SESSION, config.API_ID, config.API_HASH)

    @staticmethod
    def get_file_name(msg):
        """
        Extracts an appropriate filename from a Telegram message.

        Args:
            msg: The Telegram message object

        Returns:
            str: A filename for the media in the message
        """
        if msg.file and msg.file.name:
            return msg.file.name
        elif msg.photo:
            return f"photo_{msg.id}.jpg"
        else:
            return f"file_{msg.id}"

    async def sync_saved_files(self):
        """
        Downloads all media from Telegram Saved Messages that hasn't been downloaded yet.
        Also uploads each downloaded file to SMB if configured.

        Returns:
            int: Number of files downloaded
        """
        os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

        async with self.client:
            saved = await self.client.get_entity('me')
            offset_id = 0
            total = 0

            while True:
                history = await self.client(GetHistoryRequest(
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
                        file_name = self.get_file_name(msg)
                        file_path = os.path.join(config.DOWNLOAD_DIR, file_name)

                        if os.path.exists(file_path):
                            logger.info(f"Skipping existing file: {file_name}")
                            continue

                        try:
                            await self.client.download_media(msg, file_path)
                            logger.info(f"Downloaded: {file_name}")
                            total += 1

                            # Upload to SMB if configured
                            SMBUploader.upload(file_path, file_name)

                        except Exception as e:
                            logger.error(f"Failed to download {file_name}: {e}")

                offset_id = messages[-1].id

            logger.info(f"Downloaded {total} files to '{config.DOWNLOAD_DIR}'")
            return total