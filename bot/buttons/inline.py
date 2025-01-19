from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import Category


async def categories_list_inline():
    categories =  await Category.get_all()
    ikb = InlineKeyboardBuilder
    ikb.add(*[InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}") for category in categories])
    ikb.adjust(1, repeat=True)
    return ikb.as_markup()

