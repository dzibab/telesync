"""
Telegram client module for TeleSync application.
"""
import io

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
        self.uploader = SMBUploader()

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
        Streams all media from Telegram Saved Messages directly to SMB share.
        Uses a single SMB connection for multiple file uploads.

        Returns:
            int: Number of files uploaded
        """
        # Check if SMB is configured
        if not (config.SMB_HOST and config.SMB_SHARE and config.SMB_USER and config.SMB_PASSWORD):
            logger.error("SMB configuration not provided. Cannot continue.")
            return 0

        async with self.client:
            saved = await self.client.get_entity('me')
            offset_id = 0
            total = 0

            # Establish SMB connection before processing files
            if not self.uploader.connect():
                logger.error("Could not establish SMB connection. Aborting sync.")
                return 0

            try:
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

                            try:
                                # Stream directly from Telegram
                                file_stream = io.BytesIO()
                                await self.client.download_media(msg, file_stream)
                                file_stream.seek(0)  # Reset stream position to beginning

                                # Upload using the persistent connection
                                if self.uploader.upload_file(file_stream, file_name):
                                    logger.info(f"Uploaded to SMB: {file_name}")
                                    total += 1
                                else:
                                    logger.error(f"Failed to upload {file_name} to SMB")

                            except Exception as e:
                                logger.error(f"Failed to process {file_name}: {e}")

                    offset_id = messages[-1].id
            finally:
                # Always close the SMB connection when done
                self.uploader.close()

            logger.info(f"Uploaded {total} files to SMB share")
            return total