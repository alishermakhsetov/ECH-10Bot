
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import asyncio
from aiogram.utils.i18n import lazy_gettext as __, gettext as _
from collections import defaultdict, deque
import time

from db.models import CategoryVideo, Video
from bot.states import VideoStates
from bot.buttons.inline import (
    video_categories_keyboard,
    video_list_keyboard,
    video_detail_keyboard,
    video_statistics_keyboard,
    video_empty_category_keyboard
)
from bot.utils.texts import (
    video_main_text,
    video_no_categories_text,
    video_categories_text,
    video_no_videos_text,
    video_list_text,
    video_detail_text,
    video_statistics_text,
    video_no_statistics_text,
    video_error_text,
    video_file_error_text,
    get_main_text
)
from bot.buttons.reply import get_main_menu_keyboard

video_router = Router()

# Constants
CATEGORIES_PER_PAGE = 4
VIDEOS_PER_PAGE = 8
MAX_MESSAGES_PER_USER = 10
CLEANUP_INTERVAL = 3600  # 1 soat
DELETE_CHUNK_SIZE = 10


# 🚀 Message Store
class VideoMessageStore:
    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()
        self._cleanup_task = None

    def store_message(self, user_id: int, message_id: int, category: str = "video"):
        """Xabarni saqlash"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "video") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "video"):
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
video_message_store = VideoMessageStore()


# 🎯 Helper functions
async def store_message(user_id: int, category: str, message_id: int):
    """Xabar saqlash"""
    try:
        video_message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Xabarlarni parallel o'chirish"""
    msg_ids = video_message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    # Chunking
    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

    # Store tozalash
    if not exclude_ids:
        video_message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    """Xavfsiz xabar o'chirish"""
    try:
        await bot.delete_message(chat_id, msg_id)
        return True
    except Exception:
        return False


@video_router.message(F.text == __("🎥 Video Materiallar"))
async def show_video_main(message: Message, state: FSMContext, session: AsyncSession):
    """Main video menu"""

    # User xabarini saqlash
    await store_message(message.from_user.id, "video", message.message_id)

    # Clear state
    await state.clear()
    await state.set_state(VideoStates.viewing_categories)

    # Remove reply keyboard
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    # Get categories
    result = await session.execute(
        select(CategoryVideo)
        .options(selectinload(CategoryVideo.videos))
        .order_by(CategoryVideo.name)
    )
    categories = result.scalars().all()

    if not categories:
        text = video_no_categories_text()
        reply_markup = None
    else:
        text = video_main_text()
        keyboard = video_categories_keyboard(categories, 1, 1)
        reply_markup = keyboard

    # Send new message
    sent = await message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await store_message(message.from_user.id, "video", sent.message_id)

    # Parallel o'chirish - barcha eski xabarlarni
    await asyncio.gather(
        delete_user_messages(message.bot, message.from_user.id, "menu"),
        delete_user_messages(message.bot, message.from_user.id, "video", exclude_ids=[sent.message_id])
    )


@video_router.callback_query(F.data.startswith("video_category:"))
async def show_category_videos(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show videos in category"""
    await callback.answer()

    # Parse data
    data_parts = callback.data.split(":")
    category_id = int(data_parts[1])
    page = int(data_parts[2]) if len(data_parts) > 2 else 1

    # Set state
    await state.set_state(VideoStates.viewing_videos)

    # Get category with videos
    result = await session.execute(
        select(CategoryVideo)
        .options(selectinload(CategoryVideo.videos))
        .where(CategoryVideo.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        await callback.answer(video_error_text(), show_alert=True)
        return

    if not category.videos:
        text = video_no_videos_text(category.name)
        keyboard = video_empty_category_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Pagination - newest videos first
    videos = sorted(category.videos, key=lambda x: x.id, reverse=True)
    total_items = len(videos)
    total_pages = (total_items + VIDEOS_PER_PAGE - 1) // VIDEOS_PER_PAGE

    # Validate page
    page = max(1, min(page, total_pages))

    # Current page items
    start_idx = (page - 1) * VIDEOS_PER_PAGE
    end_idx = min(start_idx + VIDEOS_PER_PAGE, total_items)
    current_videos = videos[start_idx:end_idx]

    # Text and keyboard
    text = video_list_text(category.name, total_items, page, total_pages)
    keyboard = video_list_keyboard(
        videos=current_videos,
        category_id=category_id,
        current_page=page,
        total_pages=total_pages
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@video_router.callback_query(F.data.startswith("video_detail:"))
async def show_video_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show video details with file"""
    await callback.answer()

    video_id = int(callback.data.split(":")[1])

    # Set state
    await state.set_state(VideoStates.viewing_video_detail)

    # Get video with relations
    result = await session.execute(
        select(Video)
        .options(selectinload(Video.category))
        .where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        await callback.answer(video_error_text(), show_alert=True)
        return

    # Delete current message
    await callback.message.delete()

    try:
        # 1. Send video file
        video_msg = await callback.bot.send_video(
            chat_id=callback.from_user.id,
            video=video.file,
            caption=video_detail_text(
                video.name,
                video.category.name,
                video.description
            ),
            reply_markup=video_detail_keyboard(video.category_video_id),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "video", video_msg.message_id)

    except Exception:
        # If file fails, send error message
        error_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=video_file_error_text(),
            reply_markup=video_detail_keyboard(video.category_video_id),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "video", error_msg.message_id)

    # Update state with category id
    await state.update_data(category_id=video.category_video_id)


@video_router.callback_query(F.data == "video_statistics")
async def show_video_statistics(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show video statistics"""
    await callback.answer()

    # Set state
    await state.set_state(VideoStates.viewing_statistics)

    # Total videos count
    result = await session.execute(
        select(func.count(Video.id))
    )
    total_videos = result.scalar() or 0

    # Category statistics
    result = await session.execute(
        select(
            CategoryVideo.name,
            func.count(Video.id).label('count')
        )
        .join(Video, CategoryVideo.id == Video.category_video_id, isouter=True)
        .group_by(CategoryVideo.id, CategoryVideo.name)
        .order_by(func.count(Video.id).desc())
    )
    category_stats = result.all()

    # Check if there's any data
    if total_videos == 0:
        text = video_no_statistics_text()
    else:
        text = video_statistics_text(total_videos, category_stats)

    keyboard = video_statistics_keyboard()

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@video_router.callback_query(F.data == "video_back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back to categories list"""
    await callback.answer()

    # Set state
    await state.set_state(VideoStates.viewing_categories)

    # Delete current message
    await callback.message.delete()

    # Load categories
    result = await session.execute(
        select(CategoryVideo)
        .options(selectinload(CategoryVideo.videos))
        .order_by(CategoryVideo.name)
    )
    categories = result.scalars().all()

    if not categories:
        new_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=video_no_categories_text(),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "video", new_msg.message_id)
        return

    # Send new message
    text = video_main_text()
    keyboard = video_categories_keyboard(categories, 1, 1)

    new_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "video", new_msg.message_id)


@video_router.callback_query(F.data == "video_back_from_stats")
async def back_from_statistics(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back from statistics"""
    await back_to_categories(callback, state, session)


@video_router.callback_query(F.data.startswith("video_back_from_detail:"))
async def back_from_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back from detail to category videos"""
    await callback.answer()

    category_id = int(callback.data.split(":")[1])

    # Set state
    await state.set_state(VideoStates.viewing_videos)

    # Delete all current messages
    await delete_user_messages(callback.bot, callback.from_user.id, "video")

    # Load category
    result = await session.execute(
        select(CategoryVideo)
        .options(selectinload(CategoryVideo.videos))
        .where(CategoryVideo.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        await callback.answer(video_error_text(), show_alert=True)
        return

    if not category.videos:
        text = video_no_videos_text(category.name)
        keyboard = video_empty_category_keyboard()

        new_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "video", new_msg.message_id)
        return

    # Pagination - newest videos first
    videos = sorted(category.videos, key=lambda x: x.id, reverse=True)
    total_items = len(videos)
    total_pages = (total_items + VIDEOS_PER_PAGE - 1) // VIDEOS_PER_PAGE

    # Current page items (page 1)
    start_idx = 0
    end_idx = min(VIDEOS_PER_PAGE, total_items)
    current_videos = videos[start_idx:end_idx]

    # Text and keyboard
    text = video_list_text(category.name, total_items, 1, total_pages)
    keyboard = video_list_keyboard(
        videos=current_videos,
        category_id=category_id,
        current_page=1,
        total_pages=total_pages
    )

    # Send new message
    new_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "video", new_msg.message_id)


# Main menu callback handler
@video_router.callback_query(F.data == "video_main_menu")
async def handle_video_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handle video main menu button"""

    await callback.answer()

    # Delete current message
    await callback.message.delete()

    # Parallel o'chirish - barcha video va menu xabarlarini
    await asyncio.gather(
        delete_user_messages(callback.bot, callback.from_user.id, "video"),
        delete_user_messages(callback.bot, callback.from_user.id, "menu")
    )

    # Clear state
    await state.clear()

    # Send main menu with reply keyboard
    kb = await get_main_menu_keyboard()
    main_menu_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=get_main_text(),
        reply_markup=kb,
        parse_mode="HTML"
    )

    # Store main menu message
    await store_message(callback.from_user.id, "menu", main_menu_msg.message_id)


# Categories pagination handler
@video_router.callback_query(F.data.startswith("video_categories_page:"))
async def show_categories_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show categories pagination"""
    await callback.answer()

    page = int(callback.data.split(":")[1])

    # Get categories
    result = await session.execute(
        select(CategoryVideo)
        .options(selectinload(CategoryVideo.videos))
        .order_by(CategoryVideo.name)
    )
    categories = result.scalars().all()

    if not categories:
        await callback.answer(video_error_text(), show_alert=True)
        return

    # Pagination
    total_items = len(categories)
    total_pages = (total_items + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE

    # Validate page
    page = max(1, min(page, total_pages))

    # Current page items
    start_idx = (page - 1) * CATEGORIES_PER_PAGE
    end_idx = min(start_idx + CATEGORIES_PER_PAGE, total_items)
    current_categories = categories[start_idx:end_idx]

    # Text and keyboard
    text = video_categories_text(page, total_pages)
    keyboard = video_categories_keyboard(current_categories, page, total_pages)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Bot ishga tushganda cleanup'ni boshlash
async def start_video_message_store_cleanup():
    """Bot start bo'lganda cleanup'ni ishga tushirish"""
    video_message_store.start_periodic_cleanup()