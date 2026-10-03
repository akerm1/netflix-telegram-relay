"""Verify bot token + send a test message to the admin."""

import asyncio

from aiogram import Bot
from aiogram.enums import ParseMode

from config import load_config

cfg = load_config()
bot = Bot(token=cfg.telegram_bot_token)


async def main():
    me = await bot.get_me()
    print(f"bot ok: @{me.username} ({me.id})")

    try:
        await bot.send_message(
            chat_id=cfg.admin_telegram_id,
            text="<b>Netflix Relay</b>\nTest message: admin delivery works.",
            parse_mode=ParseMode.HTML,
        )
        print("admin DM: OK")
    except Exception as e:
        print(f"admin DM FAILED: {e}")

    try:
        await bot.send_message(
            chat_id=cfg.telegram_group_id,
            text="Netflix Relay: group delivery test",
        )
        print("group: OK")
    except Exception as e:
        print(f"group FAILED: {e}")

    await bot.session.close()


asyncio.run(main())
