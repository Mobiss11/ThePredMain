"""Background scheduler for periodic tasks like mission resets"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import AsyncSessionLocal
from app.services.mission_service import MissionService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def reset_daily_missions_job():
    """Reset all daily missions at midnight UTC"""
    try:
        logger.info("Starting daily missions reset...")
        async with AsyncSessionLocal() as db:
            await MissionService.reset_daily_missions(db)
            logger.info("✓ Daily missions reset completed successfully")
    except Exception as e:
        logger.error(f"✗ Failed to reset daily missions: {e}", exc_info=True)


async def reset_weekly_missions_job():
    """Reset all weekly missions every Monday at midnight UTC"""
    try:
        logger.info("Starting weekly missions reset...")
        async with AsyncSessionLocal() as db:
            await MissionService.reset_weekly_missions(db)
            logger.info("✓ Weekly missions reset completed successfully")
    except Exception as e:
        logger.error(f"✗ Failed to reset weekly missions: {e}", exc_info=True)


def start_scheduler():
    """Start the background scheduler with all jobs"""
    # Daily missions reset - every day at 00:00 UTC
    scheduler.add_job(
        reset_daily_missions_job,
        trigger=CronTrigger(hour=0, minute=0, timezone='UTC'),
        id='reset_daily_missions',
        name='Reset Daily Missions',
        replace_existing=True
    )

    # Weekly missions reset - every Monday at 00:00 UTC
    scheduler.add_job(
        reset_weekly_missions_job,
        trigger=CronTrigger(day_of_week='mon', hour=0, minute=0, timezone='UTC'),
        id='reset_weekly_missions',
        name='Reset Weekly Missions',
        replace_existing=True
    )

    scheduler.start()
    logger.info("✓ Scheduler started successfully")
    logger.info(f"  - Daily missions reset: Every day at 00:00 UTC")
    logger.info(f"  - Weekly missions reset: Every Monday at 00:00 UTC")


def stop_scheduler():
    """Gracefully stop the scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


# For manual testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Starting scheduler...")
    start_scheduler()

    try:
        # Keep running
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("\nStopping scheduler...")
        stop_scheduler()
