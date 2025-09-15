from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from typing import List, Tuple, Dict, Optional
import asyncio
import time
from collections import defaultdict, deque

from bot.utils.transliterate import normalize_text
from db.models import User, ExamSchedule, Role
from bot.utils.date_helpers import get_next_exam_friday
from bot.utils.constants import get_random_exam_image
from bot.states import ExamSearchState
from bot.buttons.inline import (
    exam_schedule_main_menu_keyboard,
    exam_viewer_categories_keyboard,
    exam_category_pagination_keyboard,
    exam_back_to_categories_keyboard,
    exam_search_keyboard,
    exam_search_pagination_keyboard
)
from bot.utils.texts import (
    exam_user_not_found_text, exam_no_data_text, exam_user_info_text,
    exam_no_users_found_text, exam_all_users_header_text, exam_statistics_text,
    get_category_header_text, get_category_empty_text, format_users_list,
    exam_search_prompt_text, exam_search_too_short_text, exam_search_no_results_text,
    exam_search_results_header_text, exam_search_pagination_text,
    exam_search_divider, format_search_user_result, exam_search_footer_text
)
from bot.utils.exam_helpers import get_exam_status

exam_schedule_router = Router()

# Constants
ITEMS_PER_PAGE = 6
SEARCH_ITEMS_PER_PAGE = 6
CACHE_TTL = 300  # 5 minutes
MAX_MESSAGES_PER_USER = 10
CLEANUP_INTERVAL = 3600  # 1 hour
DELETE_CHUNK_SIZE = 10

# Simple in-memory cache
_category_cache: Dict[str, Tuple[List[Dict], datetime]] = {}


# Message Store
class MessageStore:
    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()

    def store_message(self, user_id: int, message_id: int, category: str = "exam"):
        """Store message ID"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "exam") -> list[int]:
        """Get user messages"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "exam"):
        """Clear user messages"""
        self.user_messages[user_id][category].clear()

    def _periodic_cleanup(self):
        """Periodic cleanup of old data"""
        current_time = time.time()
        if current_time - self.last_cleanup > CLEANUP_INTERVAL:
            empty_users = [
                user_id for user_id, categories in self.user_messages.items()
                if not any(messages for messages in categories.values())
            ]
            for user_id in empty_users:
                del self.user_messages[user_id]
            self.last_cleanup = current_time


# Global message store instance
message_store = MessageStore()


# Helper functions for message management
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


async def send_clean_message(message: Message, text: str, reply_markup=None, parse_mode="HTML", category="exam"):
    """Send message after cleaning old ones"""
    await delete_user_messages(message.bot, message.chat.id, category)
    sent = await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    await store_message(message.chat.id, category, sent.message_id)
    return sent


def categorize_user(user: User, exam_schedule: Optional[ExamSchedule], today: datetime.date) -> Tuple[
    str, Optional[int], Optional[datetime]]:
    """Categorize a single user based on exam schedule"""
    if not exam_schedule:
        return "no_data", None, None

    next_exam = get_next_exam_friday(exam_schedule.last_exam)
    days_left = (next_exam.date() - today).days

    if days_left < 0:
        category = "overdue"
    elif days_left <= 5:
        category = "urgent"
    elif days_left <= 10:
        category = "warning"
    elif days_left <= 30:
        category = "normal"
    else:
        category = "safe"

    return category, days_left, next_exam


async def get_users_with_schedules(session: AsyncSession) -> List[Tuple[User, Optional[ExamSchedule]]]:
    """Get all users with their exam schedules in one query"""
    result = await session.execute(
        select(User, ExamSchedule)
        .outerjoin(ExamSchedule, User.id == ExamSchedule.user_id)
        .where(User.role == Role.user)
        .order_by(User.full_name)
    )
    return result.all()


def process_users_data(users_data: List[Tuple[User, Optional[ExamSchedule]]]) -> Dict[str, List[Dict]]:
    """Process all users and categorize them"""
    today = datetime.now().date()
    categorized_users = {
        "overdue": [],
        "urgent": [],
        "warning": [],
        "normal": [],
        "safe": [],
        "no_data": []
    }

    for user, exam_schedule in users_data:
        category, days_left, next_exam = categorize_user(user, exam_schedule, today)

        user_info = {
            'user': user,
            'days_left': days_left,
            'exam_schedule': exam_schedule,
            'next_exam': next_exam
        }

        categorized_users[category].append(user_info)

    # Sort each category
    for category, users in categorized_users.items():
        if category == "overdue":
            users.sort(key=lambda x: x['days_left'] if x['days_left'] is not None else 0)
        elif category != "no_data":
            users.sort(key=lambda x: x['days_left'] if x['days_left'] is not None else 999)

    return categorized_users


async def get_cached_category_data(category: str, session: AsyncSession) -> Optional[List[Dict]]:
    """Get category data from cache or database"""
    now = datetime.now()

    # Check cache
    if category in _category_cache:
        data, timestamp = _category_cache[category]
        if (now - timestamp).seconds < CACHE_TTL:
            return data

    # Load from database
    users_data = await get_users_with_schedules(session)
    categorized_users = process_users_data(users_data)

    # Update cache for all categories
    for cat, users in categorized_users.items():
        _category_cache[cat] = (users, now)

    return categorized_users.get(category, [])


# Main handler
@exam_schedule_router.message(F.text == __("📅 Davriy Imtixon Vaqti"))
async def show_exam_schedule(message: Message, state: FSMContext, session: AsyncSession):
    """Main exam schedule handler - optimized"""
    # Store user message
    await store_message(message.from_user.id, "exam", message.message_id)

    # Remove reply keyboard
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    # Clear state first
    await state.clear()

    # Get current user with single query
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    current_user = result.scalar_one_or_none()

    if not current_user:
        sent = await send_clean_message(message, exam_user_not_found_text())
        return

    # Route based on role
    if current_user.role == Role.viewer:
        await show_viewer_interface(message, session)
    else:
        await show_user_interface(message, current_user, session)


async def show_user_interface(message: Message, user: User, session: AsyncSession):
    """Show personal exam info for regular users"""
    # Get exam schedule
    result = await session.execute(
        select(ExamSchedule).where(ExamSchedule.user_id == user.id)
    )
    exam_schedule = result.scalar_one_or_none()

    keyboard = exam_schedule_main_menu_keyboard()

    if not exam_schedule:
        text = exam_no_data_text(user.full_name, user.phone_number)
        await send_clean_message(message, text, reply_markup=keyboard, category="exam")
        return

    # Calculate dates and status
    next_exam_friday = get_next_exam_friday(exam_schedule.last_exam)
    days_left = (next_exam_friday.date() - datetime.now().date()).days
    status_icon, status_text = get_exam_status(days_left)

    # Format text
    text = exam_user_info_text(
        user.full_name,
        user.phone_number,
        exam_schedule.last_exam.strftime('%d.%m.%Y'),
        next_exam_friday.strftime('%d.%m.%Y'),
        status_icon,
        status_text
    )

    # Send with image if available
    random_image = get_random_exam_image()
    if random_image:
        try:
            # Delete old messages first
            await delete_user_messages(message.bot, message.chat.id, "exam")
            sent = await message.answer_photo(
                photo=random_image,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await store_message(message.chat.id, "exam", sent.message_id)
            return
        except Exception:
            pass  # Fallback to text

    await send_clean_message(message, text, reply_markup=keyboard, category="exam")


async def show_viewer_interface(message: Message, session: AsyncSession):
    """Show categories menu for viewers"""
    # Get all users data
    users_data = await get_users_with_schedules(session)

    if not users_data:
        await send_clean_message(message, exam_no_users_found_text(), category="exam")
        return

    # Process and count categories
    categorized_users = process_users_data(users_data)
    counts = {cat: len(users) for cat, users in categorized_users.items()}

    # Build text
    total_users = len(users_data)
    text = exam_all_users_header_text()
    text += exam_statistics_text(
        total_users,
        counts['overdue'],
        counts['urgent'],
        counts['warning'],
        counts['normal'],
        counts['safe'],
        counts['no_data']
    )

    keyboard = exam_viewer_categories_keyboard(
        counts['overdue'],
        counts['urgent'],
        counts['warning'],
        counts['normal'],
        counts['safe'],
        counts['no_data']
    )

    await send_clean_message(message, text, reply_markup=keyboard, category="exam")


@exam_schedule_router.callback_query(F.data.startswith("exam_category:"))
async def show_category_users(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show users in specific category - optimized with caching"""
    await callback.answer()

    # Parse callback data
    try:
        parts = callback.data.split(":")
        category = parts[1]
        page = int(parts[2]) if len(parts) > 2 else 1
    except (ValueError, IndexError):
        await callback.answer(_("❌ Xatolik yuz berdi"))
        return

    # Get category data (with caching)
    filtered_users = await get_cached_category_data(category, session)

    if not filtered_users:
        text = get_category_empty_text(category)
        keyboard = exam_back_to_categories_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Pagination calculations
    total_items = len(filtered_users)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    # Validate page number
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
    current_users = filtered_users[start_idx:end_idx]

    # Build response
    text = get_category_header_text(category, total_items, page, total_pages)
    text += format_users_list(current_users, category)

    keyboard = exam_category_pagination_keyboard(category, page, total_pages)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@exam_schedule_router.callback_query(F.data == "back_to_exam_categories")
async def back_to_exam_categories(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Return to categories view"""
    await callback.answer()
    # Clear cache to ensure fresh data
    _category_cache.clear()

    # Delete current message and show fresh categories
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Show categories interface again
    await show_viewer_interface(callback.message, session)


@exam_schedule_router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main menu"""
    from bot.buttons.reply import get_main_menu_keyboard
    from bot.utils.texts import get_main_text

    await callback.answer()

    # Clear state and cache
    await state.clear()
    _category_cache.clear()

    # Delete all exam messages
    await asyncio.gather(
        delete_user_messages(callback.bot, callback.from_user.id, "exam"),
        delete_user_messages(callback.bot, callback.from_user.id, "menu")
    )

    # Delete current message
    try:
        await callback.message.delete()
    except Exception:
        pass

    keyboard = await get_main_menu_keyboard()
    sent = await callback.message.answer(
        get_main_text(),
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    # Store as menu message
    await store_message(callback.from_user.id, "menu", sent.message_id)


# Search functionality
@exam_schedule_router.callback_query(F.data == "exam_search")
async def start_exam_search(callback: CallbackQuery, state: FSMContext):
    """Start search mode"""
    await callback.answer()

    # Set search state
    await state.set_state(ExamSearchState.waiting_for_name)

    text = exam_search_prompt_text()
    keyboard = exam_search_keyboard()

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.delete()
        sent = await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await store_message(callback.from_user.id, "exam", sent.message_id)


@exam_schedule_router.callback_query(F.data.startswith("exam_search_page:"))
async def handle_search_pagination(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle search pagination via callback"""
    await callback.answer()

    # Parse page number
    try:
        page = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(_("❌ Xatolik yuz berdi"))
        return

    # Get search data from state
    data = await state.get_data()
    search_query = data.get("search_query")
    search_results = data.get("search_results")

    if not search_query or not search_results:
        # If no search data, redirect to search start
        text = exam_search_prompt_text()
        keyboard = exam_search_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(ExamSearchState.waiting_for_name)
        return

    # Display search results for the requested page
    await display_search_results(callback.message, search_query, search_results, page, state, edit_message=True)


@exam_schedule_router.message(ExamSearchState.waiting_for_name)
async def search_users(message: Message, state: FSMContext, session: AsyncSession):
    """Search users by name"""
    search_query = message.text.strip()

    # Store user message
    await store_message(message.from_user.id, "exam", message.message_id)

    # Validate search query
    if len(search_query) < 2:
        text = exam_search_too_short_text()
        await send_clean_message(message, text, reply_markup=exam_search_keyboard(), category="exam")
        return

    # Normalize search query (YANGI)
    search_term = normalize_text(search_query)

    # Get all users with exam schedules
    result = await session.execute(
        select(User, ExamSchedule)
        .outerjoin(ExamSchedule, User.id == ExamSchedule.user_id)
        .where(User.role == Role.user)
    )
    all_users = result.all()

    # Filter in Python (YANGI USUL)
    search_results = [
        (user, exam_schedule)
        for user, exam_schedule in all_users
        if search_term in normalize_text(user.full_name)
    ]

    # Sort by name
    search_results.sort(key=lambda x: x[0].full_name)

    if not search_results:
        text = exam_search_no_results_text(search_query)
        await send_clean_message(message, text, reply_markup=exam_search_keyboard(), category="exam")
        await state.clear()
        return

    # Store search results in state for pagination
    await state.update_data(search_query=search_query, search_results=search_results)

    # Display first page
    await display_search_results(message, search_query, search_results, 1, state)


async def display_search_results(message, search_query: str, search_results: list, page: int, state: FSMContext,
                                 edit_message: bool = False):
    """Display search results with pagination"""
    # Pagination logic
    total_items = len(search_results)
    total_pages = (total_items + SEARCH_ITEMS_PER_PAGE - 1) // SEARCH_ITEMS_PER_PAGE

    # Validate page
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * SEARCH_ITEMS_PER_PAGE
    end_idx = min(start_idx + SEARCH_ITEMS_PER_PAGE, total_items)
    current_page_results = search_results[start_idx:end_idx]

    # Build text
    today = datetime.now().date()

    # Tepasidagi header
    text = exam_search_results_header_text(search_query, total_items)

    if total_pages > 1:
        text += exam_search_pagination_text(page, total_pages)

    text += exam_search_divider()

    # Display results using the format function
    for i, (user, exam_schedule) in enumerate(current_page_results, start_idx + 1):
        text += format_search_user_result(i, user, exam_schedule, today)

    # Pastdagi statistika (faqat soni va sahifa)
    text += exam_search_footer_text(total_items)

    if total_pages > 1:
        text += exam_search_pagination_text(page, total_pages)

    # Choose keyboard based on pagination
    if total_pages > 1:
        keyboard = exam_search_pagination_keyboard(page, total_pages)
        # Keep search state active for pagination
    else:
        keyboard = exam_search_keyboard()
        await state.clear()

    # Send or edit message
    if edit_message:
        try:
            await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            # If edit fails, send new message
            await message.delete()
            sent = await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await store_message(message.chat.id, "exam", sent.message_id)
    else:
        await send_clean_message(message, text, reply_markup=keyboard, category="exam")


# Cancel search state on navigation
@exam_schedule_router.callback_query(ExamSearchState.waiting_for_name)
async def cancel_search_on_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel search state when any callback is pressed"""
    # Only clear state for non-search related callbacks
    if not callback.data.startswith("exam_search"):
        await state.clear()
    # Let the actual callback handler process the request


# Optional: Periodic cache cleanup
async def cleanup_cache():
    """Cleanup expired cache entries"""
    now = datetime.now()
    expired_keys = [
        key for key, (_, timestamp) in _category_cache.items()
        if (now - timestamp).seconds > CACHE_TTL
    ]
    for key in expired_keys:
        _category_cache.pop(key, None)