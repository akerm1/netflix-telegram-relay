"""Single relay cycle for scheduled environments (GitHub Actions cron).

Connects to IMAP, considers only the newest unread Netflix emails, relays those
received within LOOKBACK_MINUTES, and marks each as read after successful
dispatch. Old backlog is never touched, so there is no flood on first run.
"""

import asyncio
import email.utils
import re
import sys
import time

from config import load_config
from email_monitor import EmailMonitor
from logger import setup_logger
from telegram_handler import TelegramBot

logger = setup_logger()

NEWEST_IDS = 40  # bound per-run work to the newest unread messages
_INTERNALDATE_RE = re.compile(rb'INTERNALDATE "([^"]+)"')


def parse_internaldate(raw: bytes) -> float | None:
    """Return epoch seconds from an IMAP FETCH INTERNALDATE response, else None."""
    m = _INTERNALDATE_RE.search(raw)
    if not m:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(m.group(1).decode("ascii", "replace"))
    except Exception:
        return None
    return dt.timestamp()


def select_window(ages_newest_first, max_age_seconds):
    """Pick message ids to relay.

    ages_newest_first: [(msg_id, age_seconds)] sorted newest first; age None
    means the date could not be read (skip it). Stop at the first old message
    because everything after it is older too. Returns ids oldest-first.
    """
    window = []
    for msg_id, age in ages_newest_first:
        if age is None:
            continue
        if age > max_age_seconds:
            break
        window.append(msg_id)
    window.reverse()
    return window


async def main() -> int:
    config = load_config()
    telegram = TelegramBot(config)
    monitor = EmailMonitor(config, telegram.dispatch)

    try:
        monitor._connect()
        try:
            ids = monitor._search_unseen()
            newest = ids[-NEWEST_IDS:]
            now = time.time()
            cutoff = config.lookback_minutes * 60

            ages_newest_first = []
            for msg_id in reversed(newest):
                typ, data = monitor.conn.fetch(msg_id, "(INTERNALDATE)")
                age = None
                if typ == "OK" and data and data[0] is not None:
                    item = data[0]
                    raw = item[0] if isinstance(item, tuple) else item
                    ts = parse_internaldate(raw)
                    if ts is not None:
                        age = now - ts
                ages_newest_first.append((msg_id, age))

            window = select_window(ages_newest_first, cutoff)
            logger.info(
                "Relay cycle: %d unread, %d newest checked, %d within %d min",
                len(ids),
                len(newest),
                len(window),
                config.lookback_minutes,
            )

            if window:
                await monitor._process_ids(window)
        finally:
            monitor._disconnect()
    except Exception as e:
        logger.error("Relay cycle failed: %s", e)
        await telegram.bot.session.close()
        return 1

    await telegram.bot.session.close()
    logger.info("Relay cycle complete")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
