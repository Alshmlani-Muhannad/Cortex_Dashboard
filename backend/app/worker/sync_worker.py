"""Background sync worker using APScheduler.

Runs as a separate Docker service (see docker-compose.yml). Periodically syncs
Cortex XDR alerts and incidents into the local database.
"""
import logging
import signal
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.cortex_client import CortexXDRClient
from app.services.sync_service import run_full_sync

logger = logging.getLogger("app.worker")
scheduler = BackgroundScheduler()
running = True


def sync_job():
    db = SessionLocal()
    try:
        client = CortexXDRClient()
        if not client.is_configured and not settings.CORTEX_DEMO_MODE:
            logger.warning("Cortex XDR not configured; skipping automatic sync")
            return
        run_full_sync(client, db, job_type="automatic")
        logger.info("Automatic sync completed")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Automatic sync failed: %s", exc)
    finally:
        db.close()


def main():
    logger.info("Starting SOC sync worker")
    interval = settings.CORTEX_SYNC_INTERVAL_SECONDS
    if interval and interval > 0:
        scheduler.add_job(
            sync_job,
            IntervalTrigger(seconds=interval),
            id="cortex_sync",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Scheduled sync every %ds", interval)
    else:
        logger.info("Automatic sync disabled (CORTEX_SYNC_INTERVAL_SECONDS <= 0)")

    def handle_signal(signum, frame):
        global running
        running = False
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    while running:
        time.sleep(1)


if __name__ == "__main__":
    main()