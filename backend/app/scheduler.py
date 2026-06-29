from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db import SessionLocal
from app.services.refresh import refresh_trending
from app.services.settings import get_or_create_settings

logger = logging.getLogger(__name__)
LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo
_scheduler = BackgroundScheduler(timezone=LOCAL_TIMEZONE)
JOB_ID = "github-trending-refresh"
DEFAULT_REFRESH_TIME = "09:00"


def start_scheduler() -> None:
    if not _scheduler.running:
        _scheduler.start()
    reschedule_refresh_job()


def shutdown_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


def reschedule_refresh_job() -> None:
    with SessionLocal() as db:
        settings = get_or_create_settings(db)
        if _scheduler.get_job(JOB_ID):
            _scheduler.remove_job(JOB_ID)
        if not settings.auto_refresh_enabled:
            return
        hour, minute = _parse_refresh_time(settings.refresh_time_of_day)
        _scheduler.add_job(
            _run_scheduled_refresh,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=LOCAL_TIMEZONE),
            id=JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )


def _run_scheduled_refresh() -> None:
    with SessionLocal() as db:
        try:
            refresh_trending(db)
        except Exception:
            logger.exception("Scheduled GitHub Trending refresh failed")


def _parse_refresh_time(value: str | None) -> tuple[int, int]:
    raw = value or DEFAULT_REFRESH_TIME
    try:
        hour_text, minute_text = raw.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (ValueError, AttributeError):
        return 9, 0
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    return 9, 0