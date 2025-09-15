
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _


async def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("🧠 Test")),
        KeyboardButton(text=_("🦺 Himoya Vositalari")),
        KeyboardButton(text=_("⚠️ Baxtsiz Hodisalar")),
        KeyboardButton(text=_("📅 Davriy Imtixon Vaqti")),
        KeyboardButton(text=_("🤖 AI Yordamchi")),
        KeyboardButton(text=_("📚 Kutubxona")),
        KeyboardButton(text=_("🎥 Video Materiallar")),
        KeyboardButton(text=_("🚆 Poezdlar Harakat Xavfsizligi")),
        KeyboardButton(text=_("🏢 Biz Haqimizda")),
        KeyboardButton(text=_("🌐 Tilni O'zgartirish")),
    ]
    builder.add(*buttons)
    builder.adjust(1, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


async def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=_("📱 Telefon raqamimni yuborish"), request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def get_language_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("🇺🇿 Uzbek")),
        KeyboardButton(text=_("🇷🇺 Rus")),
        KeyboardButton(text=_("🇬🇧 Ingliz")),
        KeyboardButton(text=_("🇺🇿 Qoraqalpoq")),
        KeyboardButton(text=_("↩️ Orqaga")),
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


# ------------------- ai handler ----------------------------

def ai_menu_keyboard() -> ReplyKeyboardMarkup:
    """AI assistant reply keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("📊 Limitni ko'rish")),
                KeyboardButton(text=_("🗑 Chatni tozalash"))
            ],
            [
                KeyboardButton(text=_("🏠 Asosiy Menyu"))
            ]
        ],
        resize_keyboard=True
    )