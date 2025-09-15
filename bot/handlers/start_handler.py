from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Deque

from bot.middlewares import user_warn_messages
from bot.utils.name_helpers import validate_full_name, format_full_name
from db.models import User, Role, CompanyInfo
from bot.states import Registration
from bot.utils.texts import (
    full_name_example,
    full_name_error,
    phone_number_prompt,
    phone_number_error,
    get_main_menu_text_once,
    get_main_text, get_help_text
)
from bot.buttons.reply import (
    get_main_menu_keyboard,
    get_phone_request_keyboard
)


main_router = Router()


# 🚀 OPTIMAL MESSAGE CLEANER
MAX_MESSAGES_PER_USER = 5
CLEANUP_INTERVAL = 3600  # 1 soat


class OptimizedMessageStore:
    def __init__(self):
        # Har bir user uchun faqat oxirgi 5 ta xabar
        self.user_messages: Dict[int, Dict[str, Deque[int]]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()

    def store_message(self, user_id: int, message_id: int, category: str = "default"):
        """Xabarni saqlash - avtomatik eski xabarlar o'chadi"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "default") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "default"):
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
# Help xabarlarini kuzatish uchun
user_help_tasks = {}


# 🎯 SIMPLE MESSAGE FUNCTIONS
def store_message(user_id: int, message: Message, category: str = "default"):
    """Sodda xabar saqlash"""
    message_store.store_message(user_id, message.message_id, category)


async def clean_delete_messages(bot, chat_id: int, message_ids: list[int]):
    """Xabarlarni parallel o'chirish"""
    tasks = []
    for msg_id in message_ids:
        task = asyncio.create_task(_safe_delete(bot, chat_id, msg_id))
        tasks.append(task)

    # Barcha xabarlarni parallel o'chirish
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    """Xavfsiz xabar o'chirish"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass


async def delete_user_messages(message: Message, category: str = "default", except_msg_ids: list[int] = None):
    """User xabarlarini o'chirish"""
    user_id = message.from_user.id
    except_msg_ids = except_msg_ids or []

    # Faqat o'chiriladigan xabarlar
    all_msg_ids = message_store.get_messages(user_id, category)
    to_delete = [msg_id for msg_id in all_msg_ids if msg_id not in except_msg_ids]

    # Parallel o'chirish
    await clean_delete_messages(message.bot, message.chat.id, to_delete)

    # Store'ni yangilash
    message_store.clear_user_messages(user_id, category)
    for msg_id in except_msg_ids:
        message_store.store_message(user_id, msg_id, category)


# 🚀 /start command handler
@main_router.message(F.text.in_(["/start", "🚀 Boshlash"]))
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    # 1. User /start xabarini o'chirish
    await _safe_delete(bot, message.chat.id, message.message_id)

    # 2. YANGI: Welcome xabarni parallel o'chirish
    if message.from_user.id in user_warn_messages:
        # Parallel o'chirish
        tasks = []
        for msg_id in user_warn_messages[message.from_user.id]:
            task = asyncio.create_task(_safe_delete(bot, message.chat.id, msg_id))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        user_warn_messages[message.from_user.id].clear()

    # 2. User tekshirish
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()

    # 🚀 /start command handler da
    if user:
        # 3. Salomlashuv + keyboard (birinchi xabar)
        greeting_text = get_main_menu_text_once(user.full_name)
        msg_greeting_keyboard = await message.answer(
            greeting_text,
            reply_markup=await get_main_menu_keyboard()
        )

        # 4. Asosiy menyu text (ikkinchi xabar)
        msg_main_text = await message.answer(get_main_text())

        # 5. Yangi xabarlarni saqlash
        store_message(message.from_user.id, msg_greeting_keyboard, category="menu")
        store_message(message.from_user.id, msg_main_text, category="menu")

        # 6. Eski xabarlarni o'chirish
        await delete_user_messages(
            message,
            category="menu",
            except_msg_ids=[msg_greeting_keyboard.message_id, msg_main_text.message_id]
        )

        # 7. 3-4 sekunddan keyin faqat "Asosiy Menyu" textini o'chirish
        async def delete_main_text_only():
            await asyncio.sleep(3)
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=msg_main_text.message_id)
            except:
                pass

        asyncio.create_task(delete_main_text_only())

        await state.clear()

    else:
        # 6. Registration boshlanadi (YANGI USER)
        await delete_user_messages(message, category="menu")

        msg = await message.answer(full_name_example())
        store_message(message.from_user.id, msg, category="menu")
        await state.set_state(Registration.full_name)


# 📋 /help command handler
@main_router.message(F.text == "/help")
async def cmd_help(message: Message, bot: Bot, session: AsyncSession):
    user_id = message.from_user.id

    # Admin link olish
    result = await session.execute(
        select(CompanyInfo).where(CompanyInfo.is_active == True)
    )
    company_info = result.scalar_one_or_none()

    # Admin link formatlash
    if company_info and company_info.admin_link:
        admin_link = company_info.admin_link

        # Link formatini tekshirish va to'g'rilash
        if not admin_link.startswith('@') and not admin_link.startswith('http'):
            admin_link = f"@{admin_link}"

        # @ bilan boshlansa, telegram linkiga aylantirish
        if admin_link.startswith('@'):
            admin_link = f"https://t.me/{admin_link[1:]}"
    else:
        admin_link = "https://t.me/support"  # default link

    # User /help xabarini o'chirish
    await _safe_delete(bot, message.chat.id, message.message_id)

    # Eski help task'ni bekor qilish
    if user_id in user_help_tasks:
        user_help_tasks[user_id].cancel()

    # Eski help xabarlarini o'chirish
    old_help_msgs = message_store.get_messages(user_id, "help")
    await clean_delete_messages(bot, message.chat.id, old_help_msgs)
    message_store.clear_user_messages(user_id, "help")

    # Yangi help xabarini yuborish
    help_msg = await message.answer(
        get_help_text(admin_link),
        parse_mode="HTML",
        disable_web_page_preview = True
    )

    # Yangi help xabarini saqlash
    message_store.store_message(user_id, help_msg.message_id, category="help")

    # 15 sekunddan keyin o'chirish
    async def delete_help():
        await asyncio.sleep(15)
        await _safe_delete(bot, message.chat.id, help_msg.message_id)
        # Task'ni tozalash
        if user_id in user_help_tasks:
            del user_help_tasks[user_id]

    # Task'ni saqlash va ishga tushirish
    user_help_tasks[user_id] = asyncio.create_task(delete_help())


# full_name_handler ni yangilang:
@main_router.message(Registration.full_name)
async def full_name_handler(message: Message, state: FSMContext):
    # User xabarini saqlash
    store_message(message.from_user.id, message, category="menu")

    # Ism-familyani tekshirish
    is_valid = validate_full_name(message.text)

    if not is_valid:
        # Xato bo'lsa, xato xabarini ko'rsatish (texts.py dan)
        msg = await message.answer(full_name_error(), parse_mode="HTML")
        store_message(message.from_user.id, msg, category="menu")
        return

    # Ism-familyani to'g'ri formatlash
    formatted_name = format_full_name(message.text)

    # State'ga saqlash
    await state.update_data(full_name=formatted_name)

    # Eski xabarlarni o'chirish
    await delete_user_messages(message, category="menu", except_msg_ids=[])

    # Telefon raqam so'rash
    msg = await message.answer(
        phone_number_prompt(),
        reply_markup=await get_phone_request_keyboard()
    )
    store_message(message.from_user.id, msg, category="menu")

    await state.set_state(Registration.phone_number)


# ☎️ Phone number handler
@main_router.message(Registration.phone_number, F.contact)
async def phone_handler(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    full_name = data.get("full_name")
    phone = message.contact.phone_number

    # User xabarini saqlash
    store_message(message.from_user.id, message, category="menu")

    # User yaratish
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        new_user = User(
            telegram_id=message.from_user.id,
            full_name=full_name,
            phone_number=phone,
            username=message.from_user.username,
            language_code="uz",
            role=Role.user,
            last_update=datetime.utcnow(),
        )
        session.add(new_user)
        await session.commit()

    await state.clear()

    # Salomlashuv va menyu
    msg1 = await message.answer(get_main_menu_text_once(full_name))
    msg2 = await message.answer(get_main_text(), reply_markup=await get_main_menu_keyboard())

    # Eski xabarlarni o'chirish va yangilarini saqlash
    await delete_user_messages(message, category="menu", except_msg_ids=[msg1.message_id, msg2.message_id])
    store_message(message.from_user.id, msg1, category="menu")
    store_message(message.from_user.id, msg2, category="menu")


# ❌ Manual phone error
@main_router.message(Registration.phone_number)
async def phone_manual_error(message: Message):
    store_message(message.from_user.id, message, category="menu")
    msg = await message.answer(phone_number_error())
    store_message(message.from_user.id, msg, category="menu")