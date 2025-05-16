"""
Task scheduler module for TeleSync application.
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from logger import get_logger
from telegram_client import TelegramSavedMessagesClient

logger = get_logger("scheduler")


class TelegramSyncScheduler:
    """Handles scheduling of periodic synchronization tasks."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.telegram_client = TelegramSavedMessagesClient()

    def configure_jobs(self):
        """Configure scheduled jobs."""
        # Run once immediately for testing
        self.scheduler.add_job(self.telegram_client.sync_saved_files, "date")

        # Schedule daily at 2 a.m.
        self.scheduler.add_job(
            self.telegram_client.sync_saved_files, "cron", hour=2, minute=0
        )

    async def start(self):
        """Start the scheduler and keep it running."""
        self.configure_jobs()
        self.scheduler.start()
        logger.info(
            "Scheduler started: sync will run immediately and then daily at 2 a.m."
        )

        try:
            while True:
                await asyncio.sleep(3600)  # Keep the loop alive
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopping...")
            self.scheduler.shutdown()
