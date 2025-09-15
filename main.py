import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.utils.i18n import I18n, FSMI18nMiddleware

from bot.handlers import dp
from bot.middlewares import DbSessionMiddleware, JoinChannelMiddleware, UserLanguageMiddleware, RateLimitMiddleware
from utils.env_data import Config as cf

from db import db
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

bot = Bot(token=cf.bot.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def set_bot_commands(bot: Bot, i18n: I18n) -> None:
    commands = [
        BotCommand(command="/start", description=i18n.gettext("Botni ishga tushirish")),
        BotCommand(command="/help", description=i18n.gettext("Yordam")),
    ]
    await bot.set_my_commands(commands=commands)


async def main() -> None:
    # Database initialization
    await db.create_all()

    async_session_maker = async_sessionmaker(
        db._engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Rate Limiting middleware qo'shish
    dp.message.middleware(RateLimitMiddleware(rate_limit=0.5))  # 0.5 soniya
    dp.callback_query.middleware(RateLimitMiddleware(rate_limit=0.3))  # 0.3 soniya

    i18n = I18n(path="locales", default_locale="uz", domain="messages")


    # 1. I18n middleware - ENG BIRINCHI (til funksiyalarini beradi)
    dp.message.outer_middleware(FSMI18nMiddleware(i18n))
    dp.callback_query.outer_middleware(FSMI18nMiddleware(i18n))

    # 2. Database session - ikkinchi
    dp.message.outer_middleware(DbSessionMiddleware(async_session_maker))
    dp.callback_query.outer_middleware(DbSessionMiddleware(async_session_maker))

    # 3. Channel check - uchinchi
    dp.message.outer_middleware(JoinChannelMiddleware(async_session_maker))
    dp.callback_query.outer_middleware(JoinChannelMiddleware(async_session_maker))

    # 4. User language loading - OXIRIDA (til o'rnatadi va override qiladi)
    dp.message.outer_middleware(UserLanguageMiddleware(async_session_maker, i18n))
    dp.callback_query.outer_middleware(UserLanguageMiddleware(async_session_maker, i18n))

    # 5. Group router'ga middleware qo'shish
    from bot.handlers.group_events import group_router
    group_router.chat_member.outer_middleware(DbSessionMiddleware(async_session_maker))


    await set_bot_commands(bot, i18n)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    asyncio.run(main())