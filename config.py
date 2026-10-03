import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Config:
    telegram_bot_token: str
    telegram_group_id: int
    admin_telegram_id: int
    imap_server: str
    email_account: str
    email_app_password: str
    poll_interval_seconds: int
    dispatch_existing_on_start: bool
    lookback_minutes: int


def load_config() -> Config:
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_bot_token:
        raise ValueError('TELEGRAM_BOT_TOKEN is required')

    telegram_group_id_str = os.getenv('TELEGRAM_GROUP_ID')
    if not telegram_group_id_str:
        raise ValueError('TELEGRAM_GROUP_ID is required')
    try:
        telegram_group_id = int(telegram_group_id_str)
    except ValueError:
        raise ValueError('TELEGRAM_GROUP_ID must be an integer')

    admin_telegram_id_str = os.getenv('ADMIN_TELEGRAM_ID')
    if not admin_telegram_id_str:
        raise ValueError('ADMIN_TELEGRAM_ID is required')
    try:
        admin_telegram_id = int(admin_telegram_id_str)
    except ValueError:
        raise ValueError('ADMIN_TELEGRAM_ID must be an integer')

    imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')

    email_account = os.getenv('EMAIL_ACCOUNT')
    if not email_account:
        raise ValueError('EMAIL_ACCOUNT is required')

    email_app_password = os.getenv('EMAIL_APP_PASSWORD')
    if not email_app_password:
        raise ValueError('EMAIL_APP_PASSWORD is required')

    poll_interval_seconds_str = os.getenv('POLL_INTERVAL_SECONDS', '10')
    try:
        poll_interval_seconds = int(poll_interval_seconds_str)
    except ValueError:
        raise ValueError('POLL_INTERVAL_SECONDS must be an integer')

    dispatch_existing_on_start = _env_bool('DISPATCH_EXISTING_ON_START', False)

    lookback_minutes_str = os.getenv('LOOKBACK_MINUTES', '15')
    try:
        lookback_minutes = int(lookback_minutes_str)
    except ValueError:
        raise ValueError('LOOKBACK_MINUTES must be an integer')

    return Config(
        telegram_bot_token=telegram_bot_token,
        telegram_group_id=telegram_group_id,
        admin_telegram_id=admin_telegram_id,
        imap_server=imap_server,
        email_account=email_account,
        email_app_password=email_app_password,
        poll_interval_seconds=poll_interval_seconds,
        dispatch_existing_on_start=dispatch_existing_on_start,
        lookback_minutes=lookback_minutes,
    )

