from datetime import datetime

import pytz

from app.config import get_settings

settings = get_settings()
APP_TIMEZONE = pytz.timezone(settings.timezone)


def now() -> datetime:
    """Current timezone-aware datetime in the app's configured timezone."""
    return datetime.now(APP_TIMEZONE)


def today():
    """Current date in the app's configured timezone (avoids UTC-boundary drift)."""
    return now().date()
