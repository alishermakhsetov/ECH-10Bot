# bot/handlers/company_handler.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.i18n import lazy_gettext as __
from sqlalchemy import select
import asyncio
from typing import Optional
from collections import defaultdict, deque
import time

from db.models import CompanyInfo
from bot.states import CompanyStates
from bot.buttons.inline import (
    company_contact_keyboard,
    company_main_keyboard
)
from bot.utils.texts import (
    company_info_text,
    company_presentation_with_contact_text,
    company_no_data_text,
    company_no_contact_text,
    company_presentation_error_with_contact_text,
    get_main_text
)
from bot.buttons.reply import get_main_menu_keyboard

company_router = Router()

# Constants
MAX_MESSAGES_PER_USER = 10
CLEANUP_INTERVAL = 3600
DELETE_CHUNK_SIZE = 10


class CompanyMessageStore:
    """Xabarlarni boshqarish uchun store"""

    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()
        self._cleanup_task = None

    def store_message(self, user_id: int, message_id: int, category: str = "company"):
        """Xabarni saqlash"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "company") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "company"):
        """User xabarlarini tozalash"""
        self.user_messages[user_id][category].clear()

    def _periodic_cleanup(self):
        """Davriy tozalash"""
        current_time = time.time()
        if current_time - self.last_cleanup > CLEANUP_INTERVAL:
            empty_users = [
                user_id for user_id, categories in self.user_messages.items()
                if not any(messages for messages in categories.values())
            ]
            for user_id in empty_users:
                del self.user_messages[user_id]
            self.last_cleanup = current_time

    def start_periodic_cleanup(self):
        """Davriy tozalashni boshlash"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup())

    async def _auto_cleanup(self):
        """Avtomatik tozalash"""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            self._periodic_cleanup()


# Global instance
company_message_store = CompanyMessageStore()


async def store_message(user_id: int, category: str, message_id: int):
    """Xabar saqlash helper"""
    try:
        company_message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Xabarlarni parallel o'chirish"""
    msg_ids = company_message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    # Parallel o'chirish
    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

    if not exclude_ids:
        company_message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    """Xavfsiz xabar o'chirish"""
    try:
        await bot.delete_message(chat_id, msg_id)
        return True
    except Exception:
        return False


@company_router.message(F.text == __("🏢 Biz Haqimizda"))
async def show_company_info(message: Message, state: FSMContext, session: AsyncSession):
    """Kompaniya haqida ma'lumot ko'rsatish"""

    # User xabarini saqlash
    await store_message(message.from_user.id, "company", message.message_id)

    # State sozlash
    await state.clear()
    await state.set_state(CompanyStates.viewing_info)

    # Reply keyboard olib tashlash
    temp_msg = await message.answer(
        "...",
        reply_markup=ReplyKeyboardRemove()
    )
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    # Kompaniya ma'lumotlarini olish
    result = await session.execute(
        select(CompanyInfo).where(CompanyInfo.is_active == True)
    )
    company = result.scalar_one_or_none()

    # Ma'lumot yo'q holati
    if not company:
        sent = await message.answer(
            company_no_data_text(),
            reply_markup=company_main_keyboard(),
            parse_mode="HTML"
        )
        await store_message(message.from_user.id, "company", sent.message_id)

        # Eski xabarlarni o'chirish
        await asyncio.gather(
            delete_user_messages(message.bot, message.from_user.id, "menu"),
            delete_user_messages(message.bot, message.from_user.id, "company", exclude_ids=[sent.message_id])
        )
        return

    # Kompaniya ma'lumotlarini tayyorlash
    text = company_info_text(
        name=company.name,
        description=company.description
    )

    messages_to_keep = []

    # Asosiy kompaniya ma'lumotini yuborish (tugmalarsiz)
    if company.image:
        main_msg = await message.answer_photo(
            photo=company.image,
            caption=text,
            parse_mode="HTML"
        )
    else:
        main_msg = await message.answer(
            text,
            parse_mode="HTML"
        )

    await store_message(message.from_user.id, "company", main_msg.message_id)
    messages_to_keep.append(main_msg.message_id)

    # Prezentatsiya faylini kontakt ma'lumoti bilan yuborish
    if company.presentation_file:
        try:
            presentation_msg = await message.answer_document(
                document=company.presentation_file,
                caption=company_presentation_with_contact_text(),
                reply_markup=company_contact_keyboard(
                    admin_link=company.admin_link
                ),
                parse_mode="HTML"
            )
            await store_message(message.from_user.id, "company", presentation_msg.message_id)
            messages_to_keep.append(presentation_msg.message_id)

        except Exception:
            # Agar prezentatsiya yuklashda xatolik bo'lsa, kontakt ma'lumotini alohida yuborish
            contact_msg = await message.answer(
                company_presentation_error_with_contact_text(),
                reply_markup=company_contact_keyboard(
                    admin_link=company.admin_link
                ),
                parse_mode="HTML"
            )
            await store_message(message.from_user.id, "company", contact_msg.message_id)
            messages_to_keep.append(contact_msg.message_id)
    else:
        # Agar prezentatsiya fayli yo'q bo'lsa, faqat kontakt ma'lumotini yuborish
        contact_msg = await message.answer(
            company_no_contact_text(),
            reply_markup=company_contact_keyboard(
                admin_link=company.admin_link
            ),
            parse_mode="HTML"
        )
        await store_message(message.from_user.id, "company", contact_msg.message_id)
        messages_to_keep.append(contact_msg.message_id)

    # Eski xabarlarni o'chirish
    await asyncio.gather(
        delete_user_messages(message.bot, message.from_user.id, "menu"),
        delete_user_messages(message.bot, message.from_user.id, "company", exclude_ids=messages_to_keep)
    )


@company_router.callback_query(F.data == "company_main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await callback.answer()

    # Hozirgi xabarni o'chirish
    await callback.message.delete()

    # BARCHA company va menu xabarlarini o'chirish
    await asyncio.gather(
        delete_user_messages(callback.bot, callback.from_user.id, "company"),
        delete_user_messages(callback.bot, callback.from_user.id, "menu")
    )

    # Store'ni majburiy tozalash (hech narsa qolmasligi uchun)
    company_message_store.clear_user_messages(callback.from_user.id, "company")
    company_message_store.clear_user_messages(callback.from_user.id, "menu")

    # State tozalash
    await state.clear()

    # Yangi asosiy menyu yuborish
    kb = await get_main_menu_keyboard()
    main_menu_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=get_main_text(),
        reply_markup=kb,
        parse_mode="HTML"
    )

    # Yangi xabarni saqlash
    await store_message(callback.from_user.id, "menu", main_menu_msg.message_id)


async def start_company_message_store_cleanup():
    """Bot start bo'lganda cleanup'ni ishga tushirish"""
    company_message_store.start_periodic_cleanup()