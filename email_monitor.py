import asyncio
import email
import imaplib
from collections.abc import Awaitable, Callable

from config import Config
from logger import setup_logger
from parser import NETFLIX_SENDERS, ParsedEmail, parse_email_message
from utils import compute_backoff_delay

logger = setup_logger(__name__)


class EmailMonitor:
    def __init__(self, config: Config, dispatch_callback: Callable[[ParsedEmail], Awaitable[None]]):
        self.config = config
        self.dispatch_callback = dispatch_callback
        self.conn: imaplib.IMAP4_SSL | None = None
        self.running = True
        self.backoff_attempt = 0
        self.last_error: str | None = None
        self.first_cycle = True
        self.baseline_max = 0  # messages with seq <= this are pre-existing backlog

    def _connect(self):
        logger.info("Connecting to IMAP server %s", self.config.imap_server)
        self.conn = imaplib.IMAP4_SSL(self.config.imap_server, timeout=30)
        self.conn.login(self.config.email_account, self.config.email_app_password)
        self.conn.select("INBOX")
        logger.info("IMAP connection established and INBOX selected")
        self.backoff_attempt = 0
        self.last_error = None

    def _disconnect(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            try:
                self.conn.logout()
            except Exception:
                pass
            self.conn = None

    def _search_unseen(self):
        typ, data = self.conn.search(None, "UNSEEN", '(FROM "netflix.com")')
        if typ != "OK":
            return []
        return data[0].split()

    def _fetch(self, msg_id: bytes) -> bytes | None:
        typ, data = self.conn.fetch(msg_id, "(RFC822)")
        if typ != "OK" or not data or data[0] is None:
            return None
        return data[0][1]

    def _mark_seen(self, msg_id: bytes):
        try:
            self.conn.store(msg_id, "+FLAGS", "\\Seen")
        except Exception as e:
            logger.warning("Failed to mark message %s as seen: %s", msg_id, e)

    def _filter_sender(self, raw_bytes: bytes) -> bool:
        msg = email.message_from_bytes(raw_bytes)
        from_header = msg.get("From", "") or ""
        from_l = from_header.lower()
        return any(sender in from_l for sender in NETFLIX_SENDERS) or "netflix.com" in from_l

    async def _process_ids(self, msg_ids):
        for msg_id in msg_ids:
            raw = await asyncio.to_thread(self._fetch, msg_id)
            if not raw:
                continue

            if not self._filter_sender(raw):
                logger.info("Skipping non-Netflix email id=%s", msg_id)
                await asyncio.to_thread(self._mark_seen, msg_id)
                continue

            parsed = parse_email_message(raw)
            if not parsed.category:
                logger.info("No category matched for email id=%s", msg_id)
                await asyncio.to_thread(self._mark_seen, msg_id)
                continue

            logger.info("Parsed email id=%s category=%s", msg_id, parsed.category)
            try:
                await self.dispatch_callback(parsed)
            except Exception as e:
                logger.error(
                    "Failed to dispatch email id=%s (kept unread for retry): %s",
                    msg_id,
                    e,
                )
                continue
            logger.info("Dispatched email id=%s category=%s", msg_id, parsed.category)
            await asyncio.to_thread(self._mark_seen, msg_id)

    async def run(self):
        logger.info(
            "Email monitor started (poll every %ss)", self.config.poll_interval_seconds
        )
        while self.running:
            try:
                if self.conn is None:
                    await asyncio.to_thread(self._connect)

                msg_ids = await asyncio.to_thread(self._search_unseen)

                if self.first_cycle:
                    self.first_cycle = False
                    if msg_ids and not self.config.dispatch_existing_on_start:
                        self.baseline_max = max(int(i) for i in msg_ids)
                        logger.info(
                            "Startup baseline set: %d pre-existing unread emails will be "
                            "skipped (set DISPATCH_EXISTING_ON_START=true to relay them)",
                            len(msg_ids),
                        )

                new_ids = [i for i in msg_ids if int(i) > self.baseline_max]

                if new_ids:
                    logger.info(
                        "Found %d new unseen Netflix email(s)", len(new_ids)
                    )
                    await self._process_ids(new_ids)

                self.backoff_attempt = 0
                self.last_error = None
                await asyncio.sleep(self.config.poll_interval_seconds)

            except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError, TimeoutError) as e:
                self.last_error = str(e)
                logger.warning("IMAP error: %s", e)
                self._disconnect()
                delay = compute_backoff_delay(self.backoff_attempt)
                self.backoff_attempt += 1
                logger.info(
                    "Reconnecting in %.1fs (attempt %d)", delay, self.backoff_attempt
                )
                await asyncio.sleep(delay)
            except Exception as e:
                self.last_error = str(e)
                logger.error("Unexpected error in email monitor: %s", e)
                self._disconnect()
                delay = compute_backoff_delay(self.backoff_attempt)
                self.backoff_attempt += 1
                await asyncio.sleep(delay)

    def stop(self):
        self.running = False
        self._disconnect()
        logger.info("Email monitor stopped")
