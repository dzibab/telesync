"""
TeleSync - Streams media files from Telegram Saved Messages directly to SMB shares.

This is the main entry point for the TeleSync application.
"""

import asyncio

from logger import get_logger
from scheduler import TelegramSyncScheduler

logger = get_logger("main")


async def main():
    """Main application entry point."""
    logger.info("Starting TeleSync application")

    # Create and start the scheduler
    scheduler = TelegramSyncScheduler()
    await scheduler.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
