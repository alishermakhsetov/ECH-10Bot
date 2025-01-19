from aiogram import Router, html
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.buttons.inline import categories_list_inline

main = Router()

@main.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    markup = await categories_list_inline()
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=markup)
