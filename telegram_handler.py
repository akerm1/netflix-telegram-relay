from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from logger import setup_logger

logger = setup_logger(__name__)


class TelegramBot:
    def __init__(self, config):
        self.config = config
        self.bot = Bot(
            token=config.telegram_bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.dp = Dispatcher()
        self._setup_handlers()

    def _setup_handlers(self):
        @self.dp.message(CommandStart())
        async def start_handler(message: Message):
            if not await self._is_authorized(message):
                return
            await message.answer(
                "<b>Netflix Email Relay Bot</b>\n\nStatus: Active\nCommands: /status, /check",
                parse_mode=ParseMode.HTML,
            )

        @self.dp.message(Command("status"))
        async def status_handler(message: Message):
            if not await self._is_authorized(message):
                return
            await message.answer("<b>Status:</b> Running and monitoring emails", parse_mode=ParseMode.HTML)

        @self.dp.message(Command("check"))
        async def check_handler(message: Message):
            if not await self._is_authorized(message):
                return
            await message.answer("<b>Check:</b> Bot is operational", parse_mode=ParseMode.HTML)

    async def _is_authorized(self, message: Message) -> bool:
        if not message.from_user:
            return False
        user_id = message.from_user.id
        if user_id == self.config.admin_telegram_id:
            return True
        try:
            chat_member = await self.bot.get_chat_member(
                chat_id=self.config.telegram_group_id, user_id=user_id
            )
            if chat_member.status in ("member", "administrator", "creator"):
                return True
        except Exception as e:
            logger.debug("Authorization check failed: %s", e)
        return False

    async def send_code(self, code: str):
        text = "<b>Netflix Verification Code</b>\n<code>" + str(code) + "</code>"
        try:
            await self.bot.send_message(
                chat_id=self.config.telegram_group_id, text=text, parse_mode=ParseMode.HTML
            )
            logger.info("Sent verification code to group")
        except Exception as e:
            logger.error("Failed to send code to group: %s", e)

    async def send_household_link(self, url: str):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Open Link", url=url)]]
        )
        text = '<b>Netflix Household Update</b>\n<a href="' + url + '">Update Household</a>'
        try:
            await self.bot.send_message(
                chat_id=self.config.telegram_group_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
            logger.info("Sent household update link to group")
        except Exception as e:
            logger.error("Failed to send household link to group: %s", e)

    async def send_password_reset(self, url: str):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Open Link", url=url)]]
        )
        text = '<b>Netflix Password Reset</b>\n<a href="' + url + '">Reset Password</a>'
        try:
            await self.bot.send_message(
                chat_id=self.config.admin_telegram_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
            logger.info("Sent password reset link to admin (admin-only)")
        except Exception as e:
            logger.error("Failed to send password reset to admin: %s", e)

    async def dispatch(self, parsed):
        """Route a parsed email to the correct destination (shared by bot.py and run_once.py)."""
        if parsed.is_password_reset:
            await self.send_password_reset(parsed.data.get("url", ""))
        elif parsed.is_household_link:
            await self.send_household_link(parsed.data.get("url", ""))
        elif parsed.is_code:
            await self.send_code(parsed.data.get("value", ""))
        else:
            logger.warning("Unknown category, skipping dispatch")

    async def start(self):
        logger.info("Starting Telegram bot polling")
        await self.dp.start_polling(self.bot)
