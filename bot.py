import asyncio
import sys

from config import load_config
from email_monitor import EmailMonitor
from logger import setup_logger
from parser import ParsedEmail
from telegram_handler import TelegramBot

logger = setup_logger()


async def main():
    try:
        config = load_config()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    logger.info("Configuration loaded successfully")
    logger.info("IMAP server: %s", config.imap_server)
    logger.info("Poll interval: %ss", config.poll_interval_seconds)

    telegram = TelegramBot(config)

    async def dispatch(parsed: ParsedEmail):
        if parsed.is_password_reset:
            url = parsed.data.get("url", "")
            await telegram.send_password_reset(url)
        elif parsed.is_household_link:
            url = parsed.data.get("url", "")
            await telegram.send_household_link(url)
        elif parsed.is_code:
            code = parsed.data.get("value", "")
            await telegram.send_code(code)
        else:
            logger.warning("Unknown category, skipping dispatch")

    monitor = EmailMonitor(config, dispatch)

    monitor_task = asyncio.create_task(monitor.run())
    telegram_task = asyncio.create_task(telegram.start())

    logger.info("Netflix Email Relay Bot started")

    try:
        await asyncio.gather(monitor_task, telegram_task)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received")
    finally:
        monitor.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
