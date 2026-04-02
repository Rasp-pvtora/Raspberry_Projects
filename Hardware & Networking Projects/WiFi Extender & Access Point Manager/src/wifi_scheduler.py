"""WiFi scheduler — time-based AP on/off using APScheduler."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


class WiFiScheduler:
    def __init__(self, ap_manager, db):
        self.ap = ap_manager
        self.db = db
        self.scheduler = BackgroundScheduler()
        self.override_active = False

    def load_schedule(self):
        """Load schedule entries from database and create cron jobs."""
        # Remove existing schedule jobs
        for job in self.scheduler.get_jobs():
            if job.id.startswith('wifi_'):
                job.remove()

        schedules = self.db.get_wifi_schedules()
        for sched in schedules:
            if not sched['enabled']:
                continue

            day = sched['day_of_week']
            on_parts = sched['on_time'].split(':')
            off_parts = sched['off_time'].split(':')

            # Schedule WiFi ON
            self.scheduler.add_job(
                self._turn_on,
                'cron',
                day_of_week=day,
                hour=int(on_parts[0]),
                minute=int(on_parts[1]),
                id=f"wifi_on_{day}",
                replace_existing=True,
            )
            # Schedule WiFi OFF
            self.scheduler.add_job(
                self._turn_off,
                'cron',
                day_of_week=day,
                hour=int(off_parts[0]),
                minute=int(off_parts[1]),
                id=f"wifi_off_{day}",
                replace_existing=True,
            )
        logger.info("WiFi schedule loaded with %d entries", len(schedules))

    def _turn_on(self):
        if not self.override_active:
            try:
                self.ap.start()
                logger.info("WiFi turned ON by schedule")
            except Exception:
                logger.exception("Failed to start AP via schedule")

    def _turn_off(self):
        if not self.override_active:
            try:
                self.ap.stop()
                logger.info("WiFi turned OFF by schedule")
            except Exception:
                logger.exception("Failed to stop AP via schedule")

    def force_on(self):
        """Override schedule and force WiFi on."""
        self.override_active = True
        self.ap.start()
        logger.info("WiFi forced ON (override)")

    def force_off(self):
        """Override schedule and force WiFi off."""
        self.override_active = True
        self.ap.stop()
        logger.info("WiFi forced OFF (override)")

    def clear_override(self):
        """Clear manual override — resume schedule."""
        self.override_active = False
        logger.info("WiFi schedule override cleared")

    def start(self):
        self.load_schedule()
        self.scheduler.start()
        logger.info("WiFi scheduler started")

    def stop(self):
        self.scheduler.shutdown(wait=False)
        logger.info("WiFi scheduler stopped")
