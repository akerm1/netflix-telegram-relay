import asyncio
from unittest.mock import MagicMock, patch

from config import Config
from email_monitor import EmailMonitor
from parser import ParsedEmail

cfg = Config(
    telegram_bot_token="123:ABCDEFghijklmnop",
    telegram_group_id=-100123,
    admin_telegram_id=456,
    imap_server="imap.gmail.com",
    email_account="a@b.com",
    email_app_password="secret",
    poll_interval_seconds=1,
    dispatch_existing_on_start=True,
)

dispatched = []


async def cb(parsed: ParsedEmail):
    dispatched.append(parsed.category)


mon = EmailMonitor(cfg, cb)

# mock IMAP connection
mon.conn = MagicMock()
mon.conn.search.return_value = ("OK", [b"1 2"])

raw = (
    b"From: info@account.netflix.com\r\n"
    b"Subject: Your temporary verification code\r\n"
    b"\r\n"
    b"Your temporary code is 9081."
)
def fake_fetch(msg_id, spec):
    if msg_id == b"1":
        return ("OK", [(b"1 (RFC822 {n})", raw)])
    return ("OK", [None])


mon.conn.fetch.side_effect = fake_fetch

ids = mon._search_unseen()
assert ids == [b"1", b"2"], ids
print("search ok:", ids)

fetched = mon._fetch(b"1")
assert fetched == raw
mon._mark_seen(b"1")
mon.conn.store.assert_called_with(b"1", "+FLAGS", "\\Seen")
print("fetch+mark ok")

assert mon._filter_sender(raw) is True
assert mon._filter_sender(b"From: spam@x.com\r\n\r\nhi") is False
print("sender filter ok")


# run one full loop iteration of monitor.run (single poll) by patching sleep
async def one_loop():
    async def fake_sleep(_):
        mon.running = False
        raise asyncio.CancelledError

    with patch("email_monitor.asyncio.sleep", fake_sleep):
        try:
            await mon.run()
        except asyncio.CancelledError:
            pass


asyncio.run(one_loop())
assert dispatched == ["code"], dispatched
print("dispatch ok:", dispatched)

# ---- baseline: dispatch_existing_on_start=False marks backlog, no dispatch ----
cfg2 = Config(
    telegram_bot_token="123:ABCDEFghijklmnop",
    telegram_group_id=-100123,
    admin_telegram_id=456,
    imap_server="imap.gmail.com",
    email_account="a@b.com",
    email_app_password="secret",
    poll_interval_seconds=1,
    dispatch_existing_on_start=False,
)
dispatched2 = []


async def cb2(parsed: ParsedEmail):
    dispatched2.append(parsed.category)


mon2 = EmailMonitor(cfg2, cb2)
mon2.conn = MagicMock()
mon2.conn.search.return_value = ("OK", [b"1 2"])
mon2.conn.fetch.side_effect = fake_fetch


async def one_loop2():
    async def fake_sleep(_):
        mon2.running = False
        raise asyncio.CancelledError

    with patch("email_monitor.asyncio.sleep", fake_sleep):
        try:
            await mon2.run()
        except asyncio.CancelledError:
            pass


asyncio.run(one_loop2())
assert dispatched2 == [], dispatched2
mon2.conn.store.assert_not_called()
assert mon2.baseline_max == 2, mon2.baseline_max
assert mon2.first_cycle is False
print("baseline skip ok: no dispatch, no store, baseline_max=2")

# second cycle: only id > baseline_max is dispatched
mon2.running = True
mon2.conn.search.return_value = ("OK", [b"1 2 3"])


def fake_fetch_new(msg_id, spec):
    if msg_id == b"3":
        return ("OK", [(b"3 (RFC822 {n})", raw)])
    return ("OK", [None])


mon2.conn.fetch.side_effect = fake_fetch_new


async def two_loops2():
    calls = {"n": 0}

    async def fake_sleep(_):
        calls["n"] += 1
        if calls["n"] >= 1:
            mon2.running = False
            raise asyncio.CancelledError

    with patch("email_monitor.asyncio.sleep", fake_sleep):
        try:
            await mon2.run()
        except asyncio.CancelledError:
            pass


asyncio.run(two_loops2())
assert dispatched2 == ["code"], dispatched2
mon2.conn.store.assert_called_with(b"3", "+FLAGS", "\\Seen")
print("post-baseline dispatch ok:", dispatched2)

# dispatch failure -> email stays unread (store never called for it)
cfg3 = Config(
    telegram_bot_token="123:ABCDEFghijklmnop",
    telegram_group_id=-100123,
    admin_telegram_id=456,
    imap_server="imap.gmail.com",
    email_account="a@b.com",
    email_app_password="secret",
    poll_interval_seconds=1,
    dispatch_existing_on_start=True,
)


async def failing_cb(parsed: ParsedEmail):
    raise RuntimeError("telegram down")


mon3 = EmailMonitor(cfg3, failing_cb)
mon3.conn = MagicMock()
mon3.conn.search.return_value = ("OK", [b"1"])
mon3.conn.fetch.side_effect = fake_fetch


async def one_loop3():
    async def fake_sleep(_):
        mon3.running = False
        raise asyncio.CancelledError

    with patch("email_monitor.asyncio.sleep", fake_sleep):
        try:
            await mon3.run()
        except asyncio.CancelledError:
            pass


asyncio.run(one_loop3())
mon3.conn.store.assert_not_called()
print("failed dispatch keeps email unread: ok")

print("ALL EMAIL MONITOR TESTS PASSED")
