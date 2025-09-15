from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.exceptions import TelegramBadRequest
import asyncio
import time
from collections import defaultdict, deque
from typing import Optional

from bot.states import MenuState
from bot.utils.user_helpers import update_user_language
from bot.buttons.reply import get_language_keyboard, get_main_menu_keyboard
from bot.utils.texts import (
    language_prompt_text,
    language_invalid_text,
    language_updated_text,
    language_error_text,
    get_main_text
)

language_router = Router()

# 🎯 CONSTANTS
MAX_MESSAGES_PER_USER = 5
CLEANUP_INTERVAL = 3600  # 1 soat
DELETE_CHUNK_SIZE = 10  # bir vaqtda o'chiriladigan xabarlar soni
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # sekund
SUCCESS_MESSAGE_DELAY = 1.5  # muvaffaqiyat xabari vaqti


# 🚀 OPTIMAL MESSAGE STORE
class OptimizedMessageStore:
    def __init__(self):
        # Har bir user uchun faqat oxirgi 5 ta xabar
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()

    def store_message(self, user_id: int, message_id: int, category: str = "language"):
        """Xabarni saqlash - avtomatik eski xabarlar o'chadi"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "language") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "language"):
        """User xabarlarini tozalash"""
        self.user_messages[user_id][category].clear()

    def _periodic_cleanup(self):
        """Har soatda bir marta eski userlarni tozalash"""
        current_time = time.time()
        if current_time - self.last_cleanup > CLEANUP_INTERVAL:
            # Bo'sh userlarni o'chirish
            empty_users = [
                user_id for user_id, categories in self.user_messages.items()
                if not any(messages for messages in categories.values())
            ]
            for user_id in empty_users:
                del self.user_messages[user_id]

            self.last_cleanup = current_time


# Global instance
message_store = OptimizedMessageStore()


# Komanda yangilash funksiyasi
async def update_bot_commands_for_user(bot, user_id: int, i18n):
    """User uchun komandalarni yangilash"""
    commands = [
        BotCommand(command="/start", description=i18n.gettext("Botni ishga tushirish")),
        BotCommand(command="/help", description=i18n.gettext("Yordam")),
    ]
    try:
        await bot.set_my_commands(commands=commands, scope={'type': 'chat', 'chat_id': user_id})
    except:
        pass


# 🎯 OPTIMIZED MESSAGE FUNCTIONS
async def store_message(user_id: int, category: str, message_id: int):
    """Xabar saqlash with error handling"""
    try:
        message_store.store_message(user_id, message_id, category)
    except Exception:
        pass  # Xatolikni yashirin handle qilish


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Xabarlarni parallel o'chirish with chunking"""
    msg_ids = message_store.get_messages(user_id, category)

    # Exclude qilingan IDlarni chiqarib tashlash
    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    # Chunking - katta ro'yxatlarni bo'laklarga bo'lish
    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

    # Store tozalash
    if not exclude_ids:
        message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    """Xavfsiz xabar o'chirish with retry"""
    for attempt in range(MAX_RETRIES):
        try:
            await bot.delete_message(chat_id, msg_id)
            return True
        except TelegramBadRequest:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False
        except Exception:
            return False


async def send_clean_message(message: Message, text: str, reply_markup=None, category="language"):
    """Tozalab xabar yuborish"""
    await delete_user_messages(message.bot, message.chat.id, category)
    sent = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await store_message(message.chat.id, category, sent.message_id)
    return sent


# 🌐 Tilni o'zgartirish menyu (OPTIMIZED)
@language_router.message(F.text == __("🌐 Tilni O'zgartirish"))
async def change_language_prompt(message: Message, state: FSMContext):
    # User xabarini saqlash
    await store_message(message.from_user.id, "language", message.message_id)

    # State o'rnatish
    await state.set_state(MenuState.language)

    # Til tanlash klaviaturasini darhol ko'rsatish
    kb = await get_language_keyboard()
    sent = await message.answer(
        language_prompt_text(),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await store_message(message.from_user.id, "language", sent.message_id)

    # Parallel ravishda eski xabarlarni o'chirish
    await asyncio.gather(
        delete_user_messages(message.bot, message.from_user.id, "menu"),
        delete_user_messages(message.bot, message.from_user.id, "language", exclude_ids=[sent.message_id])
    )


# 🔄 Tilni o'zgartirish (OPTIMIZED)
@language_router.message(MenuState.language)
async def set_language(message: Message, state: FSMContext, i18n):
    user_id = message.from_user.id

    # User xabarini saqlash
    await store_message(user_id, "language", message.message_id)

    # Dinamik til xaritasi - current locale asosida
    lang_map = {
        _("🇺🇿 Uzbek"): "uz",
        _("🇷🇺 Rus"): "ru",
        _("🇬🇧 Ingliz"): "en",
        _("🇺🇿 Qoraqalpoq"): "kk",
        _("↩️ Orqaga"): "back",
    }

    # Matn bo'yicha qidirish
    selected = lang_map.get(message.text)

    # Noto'g'ri tanlov
    if selected is None:
        kb = await get_language_keyboard()
        sent = await message.answer(
            language_invalid_text(),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await store_message(user_id, "language", sent.message_id)

        # Eski xabarlarni o'chirish
        await delete_user_messages(
            message.bot,
            user_id,
            "language",
            exclude_ids=[sent.message_id]
        )
        return

    # Orqaga qaytish (OPTIMIZED)
    if selected == "back":
        # Asosiy menyuga darhol qaytish
        kb = await get_main_menu_keyboard()
        sent = await message.answer(
            get_main_text(),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await store_message(user_id, "menu", sent.message_id)

        # Parallel o'chirish
        await asyncio.gather(
            delete_user_messages(message.bot, user_id, "language"),
            delete_user_messages(message.bot, user_id, "menu", exclude_ids=[sent.message_id])
        )

        await state.clear()
        return

    # 🔁 Tilni yangilash
    # 1. Database'da yangilash
    success = await update_user_language(user_id=user_id, language_code=selected)

    if not success:
        # Xatolik bo'lsa
        await message.answer(language_error_text())
        return

    # 2. Joriy session uchun til o'rnatish
    i18n.current_locale = selected

    # 3. Komandalarni yangi tilda o'rnatish
    await update_bot_commands_for_user(message.bot, user_id, i18n)

    # Til o'zgartirildi xabari va asosiy menyuni birga yuborish
    success_text = language_updated_text()
    kb = await get_main_menu_keyboard()

    # Bitta xabarda ikkalasini yuborish
    combined_msg = await message.answer(
        success_text,
        reply_markup=kb,
        parse_mode="HTML"
    )
    await store_message(user_id, "menu", combined_msg.message_id)

    # Barcha eski xabarlarni parallel o'chirish
    await asyncio.gather(
        delete_user_messages(message.bot, user_id, "language"),
        delete_user_messages(message.bot, user_id, "menu", exclude_ids=[combined_msg.message_id])
    )

    await state.clear()