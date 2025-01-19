import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n import I18n

from bot.handlers import dp
from bot.middlewares import all_middleware
from utils.env_data import Config as cf



async def main() -> None:
    i18n = I18n(path="locales", default_locale="uz", domain="messages")
    bot = Bot(token=cf.bot.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await all_middleware(dp, i18n)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())