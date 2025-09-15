from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.types import ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest
import asyncio
from datetime import datetime, timezone
from typing import Optional
import time
from collections import defaultdict, deque

from db.models import (
    DepartmentSafety,
    AreaSafety,
    FacilitySafety,
    EquipmentSafety,
    EquipmentCatalog
)
from bot.states import EquipmentState
from bot.buttons.inline import (
    safety_department_keyboard,
    safety_area_keyboard,
    safety_facility_keyboard,
    safety_equipment_keyboard,
    safety_equipment_detail_keyboard,
    back_to_departments_keyboard,
    back_to_areas_keyboard,
    back_to_facilities_keyboard
)
from bot.utils.texts import (
    safety_no_departments_text,
    safety_departments_prompt,
    safety_no_areas_text,
    safety_areas_prompt,
    safety_area_with_image_caption,
    safety_no_facilities_text,
    safety_facility_with_image_caption,
    safety_no_equipment_text,
    safety_equipment_detail_text,
    safety_statistics_text,
    safety_error_text,
    safety_equipment_count_text,
    safety_equipment_count_with_dash_text,
    safety_equipment_page_info_text,
    safety_no_equipment_in_department_text,
    get_main_text
)

equipment_router = Router()

# 🎯 CONSTANTS - Test handler singari
MAX_MESSAGES_PER_USER = 5
CLEANUP_INTERVAL = 3600  # 1 soat
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # sekund
DELETE_CHUNK_SIZE = 10  # bir vaqtda o'chiriladigan xabarlar soni


# 🚀 OPTIMAL MESSAGE STORE - Test handlerdan copy
class OptimizedMessageStore:
    def __init__(self):
        # Har bir user uchun faqat oxirgi 5 ta xabar
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()
        self._cleanup_task = None

    def store_message(self, user_id: int, message_id: int, category: str = "equipment"):
        """Xabarni saqlash - avtomatik eski xabarlar o'chadi"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "equipment") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "equipment"):
        """User xabarlarini tozalash"""
        self.user_messages[user_id][category].clear()

    def _periodic_cleanup(self):
        """Har soatda bir marta eski userlarni tozalash"""
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
message_store = OptimizedMessageStore()


# 🎯 OPTIMIZED MESSAGE FUNCTIONS - Test handlerdan copy
async def store_message(user_id: int, category: str, message_id: int):
    """Xabar saqlash with error handling"""
    try:
        message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Xabarlarni parallel o'chirish with chunking"""
    msg_ids = message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    # Chunking
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
        except Exception:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False


async def send_clean_message(message: Message, text: str, reply_markup=None, category="equipment"):
    """Tozalab xabar yuborish"""
    await delete_user_messages(message.bot, message.chat.id, category)
    sent = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await store_message(message.chat.id, category, sent.message_id)
    return sent


# 🦺 Himoya vositalari - asosiy handler (OPTIMIZED)
@equipment_router.message(F.text == __("🦺 Himoya Vositalari"))
async def show_safety_departments(message: Message, state: FSMContext, session: AsyncSession):
    # User xabarini saqlash
    await store_message(message.from_user.id, "equipment", message.message_id)

    # Reply keyboard'ni o'chirish
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    # State'ni tozalash
    await state.clear()
    await state.update_data(user_telegram_id=message.from_user.id)

    # Department'larni olish
    result = await session.execute(select(DepartmentSafety))
    departments = result.scalars().all()

    if not departments:
        text = safety_no_departments_text()
        reply_markup = None
    else:
        text = safety_departments_prompt()
        reply_markup = safety_department_keyboard(departments)

    # Yangi xabar yuborish
    sent = await message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await store_message(message.chat.id, "equipment", sent.message_id)

    # Parallel ravishda eski xabarlarni o'chirish
    await asyncio.gather(
        delete_user_messages(message.bot, message.from_user.id, "menu"),
        delete_user_messages(message.bot, message.from_user.id, "equipment", exclude_ids=[sent.message_id])
    )

    await state.set_state(EquipmentState.choosing_department)


# 🏢 Department tanlash - Area'larni ko'rsatish
@equipment_router.callback_query(F.data.startswith("safety_dept:"))
async def show_department_areas(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        department_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    department = await session.get(DepartmentSafety, department_id)
    if not department:
        await callback.answer(safety_error_text())
        return

    result = await session.execute(
        select(AreaSafety).where(AreaSafety.department_safety_id == department_id)
    )
    areas = result.scalars().all()

    await state.update_data(
        department_id=department_id,
        department_name=department.name
    )

    if not areas:
        text = safety_no_areas_text(department.name)
        reply_markup = back_to_departments_keyboard()
    else:
        text = safety_areas_prompt(department.name)
        reply_markup = safety_area_keyboard(areas, department_id)

    await callback.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    await state.set_state(EquipmentState.choosing_area)


# 📍 Area tanlash - Rasm bor/yo'qligini tekshirish
@equipment_router.callback_query(F.data.startswith("safety_area:"))
async def show_area_facilities(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        parts = callback.data.split(":")
        department_id = int(parts[1])
        area_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    area = await session.get(AreaSafety, area_id)
    if not area:
        await callback.answer(safety_error_text())
        return

    result = await session.execute(
        select(FacilitySafety).where(FacilitySafety.area_safety_id == area_id)
    )
    facilities = result.scalars().all()

    data = await state.get_data()
    department_name = data.get("department_name", "")

    await state.update_data(
        area_id=area_id,
        area_name=area.name
    )

    caption = safety_area_with_image_caption(department_name, area.name)

    if not facilities:
        caption += "\n\n" + safety_no_facilities_text(area.name)
        reply_markup = safety_facility_keyboard([], department_id, area_id)
    else:
        reply_markup = safety_facility_keyboard(facilities, department_id, area_id)

    # Eski xabarni o'chirish
    await callback.message.delete()

    # Rasm bor/yo'qligini tekshirish
    if area.image:
        try:
            sent = await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=area.image,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            sent = await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    else:
        sent = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    await store_message(callback.from_user.id, "equipment", sent.message_id)
    await state.set_state(EquipmentState.choosing_facility)


# 🏛️ Facility tanlash - Equipment'larni ko'rsatish
@equipment_router.callback_query(F.data.startswith("safety_facility:"))
async def show_facility_equipment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        parts = callback.data.split(":")
        department_id = int(parts[1])
        area_id = int(parts[2])
        facility_id = int(parts[3])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    facility = await session.get(FacilitySafety, facility_id)
    if not facility:
        await callback.answer(safety_error_text())
        return

    result = await session.execute(
        select(EquipmentSafety)
        .options(selectinload(EquipmentSafety.catalog))
        .where(EquipmentSafety.facility_safety_id == facility_id)
        .where(EquipmentSafety.is_active == True)
        .order_by(EquipmentSafety.expire_at)
    )
    equipment_items = result.scalars().all()

    data = await state.get_data()
    department_name = data.get("department_name", "")
    area_name = data.get("area_name", "")

    await state.update_data(
        facility_id=facility_id,
        facility_name=facility.name
    )

    caption = safety_facility_with_image_caption(department_name, area_name, facility.name)

    if not equipment_items:
        caption += "\n" + safety_no_equipment_text(facility.name)
        reply_markup = back_to_facilities_keyboard(department_id, area_id)
    else:
        caption += "\n" + safety_equipment_count_text(len(equipment_items))
        reply_markup = safety_equipment_keyboard(equipment_items, department_id, area_id, facility_id, page=1)

    # Eski xabarni o'chirish
    await callback.message.delete()

    # Rasm bor/yo'qligini tekshirish
    if facility.image:
        try:
            sent = await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=facility.image,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            sent = await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    else:
        sent = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    await store_message(callback.from_user.id, "equipment", sent.message_id)
    await state.set_state(EquipmentState.choosing_equipment)


# 🛡️ Equipment detail ko'rish
@equipment_router.callback_query(F.data.startswith("safety_equipment:"))
async def show_equipment_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        parts = callback.data.split(":")
        department_id = int(parts[1])
        area_id = int(parts[2])
        facility_id = int(parts[3])
        equipment_id = int(parts[4])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    result = await session.execute(
        select(EquipmentSafety)
        .options(selectinload(EquipmentSafety.catalog))
        .where(EquipmentSafety.id == equipment_id)
    )
    equipment = result.scalar_one_or_none()

    if not equipment:
        await callback.answer(safety_error_text())
        return

    data = await state.get_data()
    department_name = data.get("department_name", "")
    area_name = data.get("area_name", "")
    facility_name = data.get("facility_name", "")

    caption = safety_equipment_detail_text(
        department_name=department_name,
        area_name=area_name,
        facility_name=facility_name,
        catalog_name=equipment.catalog.name,
        catalog_description=equipment.catalog.description,
        serial_number=equipment.serial_number,
        expire_date=equipment.expire_at
    )

    # Eski xabarni o'chirish
    await callback.message.delete()

    # Rasm yuborish
    sent = await callback.bot.send_photo(
        chat_id=callback.from_user.id,
        photo=equipment.file_image,
        caption=caption,
        reply_markup=safety_equipment_detail_keyboard(
            equipment_id, department_id, area_id, facility_id
        ),
        parse_mode="HTML"
    )

    await store_message(callback.from_user.id, "equipment", sent.message_id)
    await state.set_state(EquipmentState.viewing_detail)


# 📄 Equipment sahifasini o'zgartirish
@equipment_router.callback_query(F.data.startswith("equipment_page:"))
async def change_equipment_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        parts = callback.data.split(":")
        department_id = int(parts[1])
        area_id = int(parts[2])
        facility_id = int(parts[3])
        page = int(parts[4])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    result = await session.execute(
        select(EquipmentSafety)
        .options(selectinload(EquipmentSafety.catalog))
        .where(EquipmentSafety.facility_safety_id == facility_id)
        .where(EquipmentSafety.is_active == True)
        .order_by(EquipmentSafety.expire_at)
    )
    equipment_items = result.scalars().all()

    data = await state.get_data()
    department_name = data.get("department_name", "")
    area_name = data.get("area_name", "")
    facility_name = data.get("facility_name", "")

    caption = safety_facility_with_image_caption(department_name, area_name, facility_name)

    items_per_page = 10
    total_items = len(equipment_items)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    caption += "\n" + safety_equipment_page_info_text(total_items, page, total_pages)

    reply_markup = safety_equipment_keyboard(equipment_items, department_id, area_id, facility_id, page)

    try:
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.message.edit_reply_markup(reply_markup=reply_markup)


# 📊 Department statistika
@equipment_router.callback_query(F.data.startswith("safety_statistics:"))
async def show_department_statistics(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        department_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    result = await session.execute(
        select(
            EquipmentCatalog.name,
            func.count(EquipmentSafety.id).label('count')
        )
        .select_from(EquipmentSafety)
        .join(EquipmentCatalog)
        .join(FacilitySafety)
        .join(AreaSafety)
        .where(AreaSafety.department_safety_id == department_id)
        .where(EquipmentSafety.is_active == True)
        .group_by(EquipmentCatalog.id, EquipmentCatalog.name)
        .order_by(func.count(EquipmentSafety.id).desc())
    )

    statistics = result.all()
    department = await session.get(DepartmentSafety, department_id)

    if not statistics:
        text = safety_no_equipment_in_department_text()
    else:
        text = safety_statistics_text(department.name, statistics)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=back_to_areas_keyboard(department_id),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.message.delete()
        sent = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            reply_markup=back_to_areas_keyboard(department_id),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "equipment", sent.message_id)


# 🔙 Navigation handlerlari
@equipment_router.callback_query(F.data.startswith("back_to_facilities:"))
async def back_to_facilities(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        parts = callback.data.split(":")
        department_id = int(parts[1])
        area_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    area = await session.get(AreaSafety, area_id)
    result = await session.execute(
        select(FacilitySafety).where(FacilitySafety.area_safety_id == area_id)
    )
    facilities = result.scalars().all()

    data = await state.get_data()
    department_name = data.get("department_name", "")

    caption = safety_area_with_image_caption(department_name, area.name)

    if not facilities:
        caption += "\n\n" + safety_no_facilities_text(area.name)
        reply_markup = safety_facility_keyboard([], department_id, area_id)
    else:
        reply_markup = safety_facility_keyboard(facilities, department_id, area_id)

    await callback.message.delete()

    if area.image:
        try:
            sent = await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=area.image,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            sent = await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    else:
        sent = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    await store_message(callback.from_user.id, "equipment", sent.message_id)
    await state.set_state(EquipmentState.choosing_facility)


@equipment_router.callback_query(F.data.startswith("back_to_equipment:"))
async def back_to_equipment_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        parts = callback.data.split(":")
        department_id = int(parts[1])
        area_id = int(parts[2])
        facility_id = int(parts[3])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    facility = await session.get(FacilitySafety, facility_id)
    result = await session.execute(
        select(EquipmentSafety)
        .options(selectinload(EquipmentSafety.catalog))
        .where(EquipmentSafety.facility_safety_id == facility_id)
        .where(EquipmentSafety.is_active == True)
        .order_by(EquipmentSafety.expire_at)
    )
    equipment_items = result.scalars().all()

    data = await state.get_data()
    department_name = data.get("department_name", "")
    area_name = data.get("area_name", "")

    caption = safety_facility_with_image_caption(department_name, area_name, facility.name)

    if not equipment_items:
        caption += "\n" + safety_no_equipment_text(facility.name)
        reply_markup = back_to_facilities_keyboard(department_id, area_id)
    else:
        caption += "\n" + safety_equipment_count_with_dash_text(len(equipment_items))
        reply_markup = safety_equipment_keyboard(equipment_items, department_id, area_id, facility_id)

    await callback.message.delete()

    if facility.image:
        try:
            sent = await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=facility.image,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            sent = await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    else:
        sent = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    await store_message(callback.from_user.id, "equipment", sent.message_id)
    await state.set_state(EquipmentState.choosing_equipment)


@equipment_router.callback_query(F.data.startswith("back_to_areas:"))
async def back_to_areas(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    try:
        department_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(safety_error_text())
        return

    department = await session.get(DepartmentSafety, department_id)
    result = await session.execute(
        select(AreaSafety).where(AreaSafety.department_safety_id == department_id)
    )
    areas = result.scalars().all()

    if not areas:
        text = safety_no_areas_text(department.name)
        reply_markup = back_to_departments_keyboard()
    else:
        text = safety_areas_prompt(department.name)
        reply_markup = safety_area_keyboard(areas, department_id)

    await callback.message.delete()
    sent = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "equipment", sent.message_id)

    await state.set_state(EquipmentState.choosing_area)


@equipment_router.callback_query(F.data == "back_to_departments")
async def back_to_departments(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    result = await session.execute(select(DepartmentSafety))
    departments = result.scalars().all()

    if not departments:
        text = safety_no_departments_text()
        reply_markup = None
    else:
        text = safety_departments_prompt()
        reply_markup = safety_department_keyboard(departments)

    await callback.message.delete()
    sent = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "equipment", sent.message_id)

    await state.set_state(EquipmentState.choosing_department)


# 🏠 Asosiy menyu (OPTIMIZED - Test handler singari)
@equipment_router.callback_query(F.data == "safety_main_menu")
async def back_to_main_menu_from_safety(callback: CallbackQuery, state: FSMContext):
    from bot.buttons.reply import get_main_menu_keyboard

    await callback.answer()
    await callback.message.delete()

    # Parallel o'chirish - Test handler singari
    await asyncio.gather(
        delete_user_messages(callback.bot, callback.from_user.id, "equipment"),
        delete_user_messages(callback.bot, callback.from_user.id, "menu")
    )

    await state.clear()

    # Yangi xabar yuborish
    kb = await get_main_menu_keyboard()
    sent = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=get_main_text(),
        reply_markup=kb,
        parse_mode="HTML"
    )

    await store_message(callback.from_user.id, "menu", sent.message_id)


# Bot ishga tushganda cleanup'ni boshlash
async def start_equipment_message_store_cleanup():
    """Bot start bo'lganda cleanup'ni ishga tushirish"""
    message_store.start_periodic_cleanup()