"""
Telegram Notification Queue Worker

Processes queued notifications with rate limiting to comply with Telegram's limits:
- 30 messages per second to different users
- 20 messages per minute to the same user
- 1 message per second to the same chat (bots)

Usage:
    python notification_worker.py
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramBadRequest

# Import backend services
from backend.app.core.database import AsyncSessionLocal
from backend.app.services.telegram_queue_service import TelegramQueueService
from backend.app.models.telegram_notification import TelegramNotification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notification_worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class NotificationWorker:
    """Worker for processing Telegram notification queue"""

    def __init__(self, bot_token: str, batch_size: int = 30):
        """
        Initialize worker

        Args:
            bot_token: Telegram bot token
            batch_size: Number of messages to process per second (max 30)
        """
        self.bot = Bot(token=bot_token)
        self.batch_size = min(batch_size, 30)  # Telegram limit: 30 msg/sec
        self.running = False

        logger.info(f"[Worker] Initialized with batch_size={self.batch_size}")

    async def process_notification(self, notification: TelegramNotification, db) -> bool:
        """
        Process a single notification

        Args:
            notification: Notification to process
            db: Database session

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Mark as processing
            await TelegramQueueService.mark_processing(db, notification.id)

            # Parse metadata
            import json
            metadata = json.loads(notification.notification_metadata) if notification.notification_metadata else {}

            photo_url = metadata.get('photo_url')

            # Send message
            if photo_url:
                # Send photo with caption
                await self.bot.send_photo(
                    chat_id=notification.telegram_id,
                    photo=photo_url,
                    caption=notification.message_text,
                    parse_mode=notification.parse_mode
                )
            else:
                # Send text message
                await self.bot.send_message(
                    chat_id=notification.telegram_id,
                    text=notification.message_text,
                    parse_mode=notification.parse_mode
                )

            # Mark as sent
            await TelegramQueueService.mark_sent(db, notification.id)

            logger.info(f"[Worker] ✓ Sent notification #{notification.id} to {notification.telegram_id}")
            return True

        except TelegramForbiddenError as e:
            # User blocked the bot - permanent failure
            logger.warning(f"[Worker] User {notification.telegram_id} blocked the bot")
            await TelegramQueueService.mark_failed(
                db, notification.id,
                f"User blocked bot: {str(e)}",
                permanent_failure=True
            )
            return False

        except TelegramBadRequest as e:
            # Bad request - permanent failure
            logger.error(f"[Worker] Bad request for notification #{notification.id}: {e}")
            await TelegramQueueService.mark_failed(
                db, notification.id,
                f"Bad request: {str(e)}",
                permanent_failure=True
            )
            return False

        except TelegramAPIError as e:
            # Temporary error - will retry
            logger.error(f"[Worker] Telegram API error for notification #{notification.id}: {e}")
            await TelegramQueueService.mark_failed(
                db, notification.id,
                f"Telegram API error: {str(e)}",
                permanent_failure=False
            )
            return False

        except Exception as e:
            # Unknown error - will retry
            logger.error(f"[Worker] Unexpected error for notification #{notification.id}: {e}", exc_info=True)
            await TelegramQueueService.mark_failed(
                db, notification.id,
                f"Unexpected error: {str(e)}",
                permanent_failure=False
            )
            return False

    async def process_batch(self):
        """Process a batch of notifications (max 30 per second)"""
        async with AsyncSessionLocal() as db:
            try:
                # Get pending notifications
                notifications = await TelegramQueueService.get_pending_messages(
                    db,
                    limit=self.batch_size,
                    include_scheduled=True
                )

                if not notifications:
                    return 0

                logger.info(f"[Worker] Processing batch of {len(notifications)} notifications")

                # Process all notifications in batch
                tasks = [self.process_notification(notif, db) for notif in notifications]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Count successes
                success_count = sum(1 for r in results if r is True)

                logger.info(f"[Worker] Batch complete: {success_count}/{len(notifications)} sent successfully")

                return len(notifications)

            except Exception as e:
                logger.error(f"[Worker] Error processing batch: {e}", exc_info=True)
                return 0

    async def run(self):
        """Main worker loop"""
        self.running = True
        logger.info("[Worker] 🚀 Starting notification worker...")

        logger.info(f"[Worker] Rate limit: {self.batch_size} messages per second")
        logger.info("[Worker] Press Ctrl+C to stop")

        iteration = 0

        while self.running:
            try:
                iteration += 1
                start_time = datetime.now()

                # Process batch
                processed_count = await self.process_batch()

                # Calculate sleep time to maintain rate limit (1 second per batch)
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, 1.0 - elapsed)

                if processed_count == 0:
                    # No messages in queue - sleep longer (5 seconds)
                    if iteration % 12 == 0:  # Log every minute when idle
                        logger.info("[Worker] 💤 Queue empty, waiting...")
                    await asyncio.sleep(5)
                else:
                    # Sleep to maintain rate limit
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)

            except KeyboardInterrupt:
                logger.info("[Worker] 🛑 Received stop signal")
                break

            except Exception as e:
                logger.error(f"[Worker] Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Sleep before retry

        logger.info("[Worker] ✓ Worker stopped")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("[Worker] Cleaning up...")
        await self.bot.session.close()
        logger.info("[Worker] ✓ Cleanup complete")


async def main():
    """Main entry point"""
    # Get bot token from environment
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        logger.error("[Worker] ❌ BOT_TOKEN not set in environment")
        logger.error("[Worker] Please set BOT_TOKEN environment variable")
        return

    # Create and run worker
    worker = NotificationWorker(bot_token=bot_token, batch_size=30)

    try:
        await worker.run()
    finally:
        await worker.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n[Worker] Goodbye!")
