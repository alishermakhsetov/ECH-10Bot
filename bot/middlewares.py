from aiogram.utils.i18n import FSMI18nMiddleware


async def all_middleware(dp, i18n):

    dp.update.middleware.register(FSMI18nMiddleware(i18n))