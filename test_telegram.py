import asyncio

from config import Config
from telegram_handler import TelegramBot

cfg = Config(
    telegram_bot_token="123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw",
    telegram_group_id=-100123,
    admin_telegram_id=456,
    imap_server="imap.gmail.com",
    email_account="a@b.com",
    email_app_password="secret",
    poll_interval_seconds=1,
    dispatch_existing_on_start=False, lookback_minutes=15,
)

tg = TelegramBot(cfg)
print("TelegramBot constructed OK")

# _is_authorized: admin bypass (no API call needed)
class FakeMsg:
    from_user = None


async def check():
    m = FakeMsg()
    assert await tg._is_authorized(m) is False
    m.from_user = type("U", (), {"id": 456})()
    assert await tg._is_authorized(m) is True, "admin must be authorized"
    print("authorization: admin OK, no-user rejected OK")

    # send methods must not raise even when API fails (network offline in CI)
    await tg.send_code("1234")
    await tg.send_household_link("https://www.netflix.com/account/travel")
    await tg.send_password_reset("https://www.netflix.com/password")
    print("send methods handled API errors gracefully")


asyncio.run(check())
print("ALL TELEGRAM HANDLER TESTS PASSED")
