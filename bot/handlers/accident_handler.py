
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import asyncio
import time
import re
from collections import defaultdict, deque
from aiogram.utils.i18n import lazy_gettext as __

from db.models import User, AccidentYear, Accident, AccidentCategory, Role
from bot.buttons.inline import (
    accident_years_keyboard,
    accident_list_keyboard,
    accident_detail_keyboard,
    accident_statistics_main_keyboard,
    accident_statistics_year_keyboard,
    accident_empty_year_keyboard
)
from bot.utils.texts import (
    accident_main_text,
    accident_no_years_text,
    accident_year_header_text,
    accident_no_accidents_text,
    accident_detail_text,
    accident_statistics_main_text,
    accident_statistics_year_text,
    accident_no_statistics_text,
    accident_error_text,
    accident_file_error_text,
    accident_loading_text
)

accident_router = Router()

# Constants
ACCIDENTS_PER_PAGE = 15  # 3x5 grid
CACHE_TTL = 300  # 5 minutes
DELETE_CHUNK_SIZE = 10
EXCLUDED_CATEGORY = "Xisobat"  # Statistikadan chiqarib tashlanadigan kategoriya

# Cache
_accident_cache: Dict[str, Tuple[any, datetime]] = {}


# Message Store
class MessageStore:
    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=10))
        )
        self.last_cleanup = time.time()

    def store_message(self, user_id: int, message_id: int, category: str = "accident"):
        """Store message ID"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "accident") -> list[int]:
        """Get user messages"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "accident"):
        """Clear user messages"""
        self.user_messages[user_id][category].clear()

    def _periodic_cleanup(self):
        """Periodic cleanup of old data"""
        current_time = time.time()
        if current_time - self.last_cleanup > 3600:  # 1 hour
            empty_users = [
                user_id for user_id, categories in self.user_messages.items()
                if not any(messages for messages in categories.values())
            ]
            for user_id in empty_users:
                del self.user_messages[user_id]
            self.last_cleanup = current_time


# Global message store
message_store = MessageStore()


# Helper functions
async def store_message(user_id: int, category: str, message_id: int):
    """Store message with error handling"""
    try:
        message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Delete user messages in chunks"""
    msg_ids = message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

    if not exclude_ids:
        message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    """Safe message deletion"""
    try:
        await bot.delete_message(chat_id, msg_id)
        return True
    except Exception:
        return False


async def send_clean_message(message: Message, text: str, reply_markup=None, parse_mode="HTML", category="accident"):
    """Send message after cleaning old ones"""
    await delete_user_messages(message.bot, message.chat.id, category)
    sent = await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    await store_message(message.chat.id, category, sent.message_id)
    return sent


async def get_cached_data(key: str, loader_func, *args) -> any:
    """Get data from cache or load"""
    now = datetime.now()

    if key in _accident_cache:
        data, timestamp = _accident_cache[key]
        if (now - timestamp).seconds < CACHE_TTL:
            return data

    # Load fresh data
    data = await loader_func(*args)
    _accident_cache[key] = (data, now)
    return data


def extract_number(title: str) -> int:
    """Extract number from title for proper sorting"""
    match = re.search(r'\d+', title)
    return int(match.group()) if match else 0


# Main handler
@accident_router.message(F.text == __("⚠️ Baxtsiz Hodisalar"))
async def show_accidents_main(message: Message, state: FSMContext, session: AsyncSession):
    """Main accident menu"""
    # Store user message
    await store_message(message.from_user.id, "accident", message.message_id)

    # Remove reply keyboard
    temp_msg = await message.answer(accident_loading_text(), reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    # Clear state
    await state.clear()

    # Get years with cache
    async def load_years(session):
        result = await session.execute(
            select(AccidentYear)
            .options(selectinload(AccidentYear.accidents))
        )
        years = result.scalars().all()
        return sorted(years, key=lambda y: y.year_number, reverse=True)

    years = await get_cached_data("accident_years", load_years, session)

    if not years:
        await send_clean_message(message, accident_no_years_text(), category="accident")
        return

    # Send with keyboard
    keyboard = accident_years_keyboard(years)
    await send_clean_message(
        message,
        accident_main_text(),
        reply_markup=keyboard,
        category="accident"
    )


@accident_router.callback_query(F.data.startswith("accident_year:"))
async def show_year_accidents(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show accidents by year"""
    await callback.answer()

    # Parse data
    data_parts = callback.data.split(":")
    year_id = int(data_parts[1])
    page = int(data_parts[2]) if len(data_parts) > 2 else 1

    # Check if we're coming from detail page (need to clean messages)
    if hasattr(callback, 'message') and callback.message:
        # Check if there are stored messages (indicates we're coming from detail)
        stored_messages = message_store.get_messages(callback.from_user.id, "accident")
        if len(stored_messages) > 1:  # More than 1 message means we have images/docs
            # Clean all previous messages when coming from detail
            await delete_user_messages(callback.bot, callback.from_user.id, "accident")

    # Get year with accidents
    async def load_year_accidents(session, year_id):
        result = await session.execute(
            select(AccidentYear)
            .options(selectinload(AccidentYear.accidents))
            .where(AccidentYear.id == year_id)
        )
        return result.scalar_one_or_none()

    year_obj = await get_cached_data(f"year_{year_id}", load_year_accidents, session, year_id)

    if not year_obj:
        await callback.answer(accident_error_text(), show_alert=True)
        return

    if not year_obj.accidents:
        text = accident_no_accidents_text(year_obj.name)
        keyboard = accident_empty_year_keyboard()

        # If messages were cleaned, send new message, otherwise edit
        if len(message_store.get_messages(callback.from_user.id, "accident")) == 0:
            new_msg = await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await store_message(callback.from_user.id, "accident", new_msg.message_id)
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Pagination with proper sorting
    accidents = sorted(year_obj.accidents, key=lambda x: extract_number(x.title))
    total_items = len(accidents)
    total_pages = (total_items + ACCIDENTS_PER_PAGE - 1) // ACCIDENTS_PER_PAGE

    # Validate page
    page = max(1, min(page, total_pages))

    # Current page items
    start_idx = (page - 1) * ACCIDENTS_PER_PAGE
    end_idx = min(start_idx + ACCIDENTS_PER_PAGE, total_items)
    current_accidents = accidents[start_idx:end_idx]

    # Text and keyboard
    text = accident_year_header_text(year_obj.name, total_items, page, total_pages)
    keyboard = accident_list_keyboard(
        accidents=current_accidents,
        year_id=year_id,
        current_page=page,
        total_pages=total_pages
    )

    # If messages were cleaned, send new message, otherwise edit
    if len(message_store.get_messages(callback.from_user.id, "accident")) == 0:
        new_msg = await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await store_message(callback.from_user.id, "accident", new_msg.message_id)
    else:
        # Use edit_text for pagination (tez ishlaydi)
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@accident_router.callback_query(F.data.startswith("accident_detail:"))
async def show_accident_detail(callback: CallbackQuery, session: AsyncSession):
    """Show accident details with image and document"""
    await callback.answer()

    accident_id = int(callback.data.split(":")[1])

    # Get accident with relations
    result = await session.execute(
        select(Accident)
        .options(
            selectinload(Accident.year),
            selectinload(Accident.category)
        )
        .where(Accident.id == accident_id)
    )
    accident = result.scalar_one_or_none()

    if not accident:
        await callback.answer(accident_error_text(), show_alert=True)
        return

    # Clean all previous messages for this user
    await delete_user_messages(callback.bot, callback.from_user.id, "accident")

    try:
        # 1. Send image if exists
        if accident.file_image:
            try:
                img_msg = await callback.message.answer_photo(
                    photo=accident.file_image
                )
                await store_message(callback.from_user.id, "accident", img_msg.message_id)
            except Exception:
                pass  # If image fails, continue

        # 2. Send document
        doc_msg = await callback.message.answer_document(
            document=accident.file_pdf
        )
        await store_message(callback.from_user.id, "accident", doc_msg.message_id)

        # 3. Send details with keyboard
        detail_text = accident_detail_text(
            accident.title,
            accident.year.name,
            accident.category.name,
            getattr(accident, 'description', None)  # Add description if exists
        )
        keyboard = accident_detail_keyboard(accident.year_id)

        detail_msg = await callback.message.answer(
            text=detail_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "accident", detail_msg.message_id)

    except Exception:
        # If document fails, send error message
        error_msg = await callback.message.answer(
            text=accident_file_error_text(),
            reply_markup=accident_detail_keyboard(accident.year_id),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "accident", error_msg.message_id)


@accident_router.callback_query(F.data == "accident_statistics_main")
async def show_main_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show main statistics (excluding 'Xisobat' category)"""
    await callback.answer()

    # Total count (excluding 'Xisobat')
    result = await session.execute(
        select(func.count(Accident.id))
        .join(AccidentCategory)
        .where(AccidentCategory.name != EXCLUDED_CATEGORY)
    )
    total_count = result.scalar() or 0

    # Year statistics (excluding 'Xisobat' category)
    result = await session.execute(
        select(
            AccidentYear.name,
            func.count(Accident.id).label('count')
        )
        .join(Accident)
        .join(AccidentCategory)
        .where(AccidentCategory.name != EXCLUDED_CATEGORY)
        .group_by(AccidentYear.id, AccidentYear.name)
        .order_by(AccidentYear.name.desc())
        .limit(10)  # Increased to get more years for comparison
    )
    year_stats = result.all()

    # Check if there's any data
    if total_count == 0:
        text = accident_no_statistics_text()
    else:
        # Create dummy category_stats for total calculation
        dummy_category_stats = [type('obj', (object,), {'count': total_count})]
        text = accident_statistics_main_text(dummy_category_stats, year_stats)

    keyboard = accident_statistics_main_keyboard()

    # Use edit_text for statistics (tez ishlaydi)
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@accident_router.callback_query(F.data.startswith("accident_statistics_year:"))
async def show_year_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show year statistics (excluding 'Xisobat' category)"""
    await callback.answer()

    year_id = int(callback.data.split(":")[1])

    # Get year
    result = await session.execute(
        select(AccidentYear).where(AccidentYear.id == year_id)
    )
    year_obj = result.scalar_one_or_none()

    if not year_obj:
        await callback.answer(accident_error_text(), show_alert=True)
        return

    # Category statistics for this year (excluding 'Xisobat')
    result = await session.execute(
        select(
            AccidentCategory.name,
            func.count(Accident.id).label('count')
        )
        .join(Accident)
        .where(
            and_(
                Accident.year_id == year_id,
                AccidentCategory.name != EXCLUDED_CATEGORY
            )
        )
        .group_by(AccidentCategory.id)
        .order_by(func.count(Accident.id).desc())
    )
    category_stats = result.all()

    # Total count (excluding 'Xisobat')
    total = sum(stat.count for stat in category_stats)

    # Text and keyboard
    text = accident_statistics_year_text(year_obj.name, total, category_stats)
    keyboard = accident_statistics_year_keyboard(year_id)

    # Use edit_text for statistics (tez ishlaydi)
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@accident_router.callback_query(F.data == "accident_back_to_years")
async def back_to_years(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back to years list"""
    await callback.answer()

    # Clean all accident messages first
    await delete_user_messages(callback.bot, callback.from_user.id, "accident")

    # Clear cache to get fresh data
    if "accident_years" in _accident_cache:
        del _accident_cache["accident_years"]

    # Get years
    result = await session.execute(
        select(AccidentYear)
        .options(selectinload(AccidentYear.accidents))
    )
    years = result.scalars().all()
    years = sorted(years, key=lambda y: y.year_number, reverse=True)

    # Send new message
    text = accident_main_text()
    keyboard = accident_years_keyboard(years)

    new_msg = await callback.message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "accident", new_msg.message_id)


@accident_router.callback_query(F.data == "accident_back_from_stats")
async def back_from_statistics(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back from statistics"""
    await back_to_years(callback, state, session)


@accident_router.callback_query(F.data == "accident_back_from_detail")
async def back_from_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back from detail to year list"""
    year_id = int(callback.data.split(":")[1]) if ":" in callback.data else None

    if year_id:
        # Go back to specific year
        callback.data = f"accident_year:{year_id}:1"
        await show_year_accidents(callback, state, session)
    else:
        # Go back to years
        await back_to_years(callback, state, session)