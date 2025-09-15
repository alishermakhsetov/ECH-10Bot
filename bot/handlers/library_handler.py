
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import asyncio
from aiogram.utils.i18n import lazy_gettext as __
from collections import defaultdict, deque
import time

from db.models import CategoryBook, Book
from bot.states import LibraryStates
from bot.buttons.inline import (
    library_categories_keyboard,
    library_books_keyboard,
    library_book_detail_keyboard,
    library_statistics_keyboard,
    library_empty_category_keyboard
)
from bot.utils.texts import (
    library_main_text,
    library_no_categories_text,
    library_categories_text,
    library_no_books_text,
    library_books_text,
    library_book_detail_text,
    library_statistics_text,
    library_no_statistics_text,
    library_error_text,
    library_file_error_text,
    library_loading_text,
    main_menu_text
)
from bot.buttons.reply import get_main_menu_keyboard

library_router = Router()

# Constants
CATEGORIES_PER_PAGE = 4
BOOKS_PER_PAGE = 8
MAX_MESSAGES_PER_USER = 10
CLEANUP_INTERVAL = 3600  # 1 soat
DELETE_CHUNK_SIZE = 10


# 🚀 Message Store - equipment_handler kabi
class LibraryMessageStore:
    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()
        self._cleanup_task = None

    def store_message(self, user_id: int, message_id: int, category: str = "library"):
        """Xabarni saqlash"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "library") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "library"):
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
library_message_store = LibraryMessageStore()


# 🎯 Helper functions
async def store_message(user_id: int, category: str, message_id: int):
    """Xabar saqlash"""
    try:
        library_message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Xabarlarni parallel o'chirish"""
    msg_ids = library_message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    # Chunking
    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

    # Store tozalash
    if not exclude_ids:
        library_message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    """Xavfsiz xabar o'chirish"""
    try:
        await bot.delete_message(chat_id, msg_id)
        return True
    except Exception:
        return False


# Main handler - UPDATED
@library_router.message(F.text == __("📚 Kutubxona"))
async def show_library_main(message: Message, state: FSMContext, session: AsyncSession):
    """Main library menu"""
    # User xabarini saqlash
    await store_message(message.from_user.id, "library", message.message_id)

    # Clear state
    await state.clear()
    await state.set_state(LibraryStates.viewing_categories)

    # Remove reply keyboard
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    # Get categories
    result = await session.execute(
        select(CategoryBook)
        .options(selectinload(CategoryBook.books))
        .order_by(CategoryBook.name)
    )
    categories = result.scalars().all()

    if not categories:
        text = library_no_categories_text()
        reply_markup = None
    else:
        text = library_main_text()
        keyboard = library_categories_keyboard(categories, 1, 1)
        reply_markup = keyboard

    # Send new message
    sent = await message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await store_message(message.from_user.id, "library", sent.message_id)

    # Parallel o'chirish - barcha eski xabarlarni
    await asyncio.gather(
        delete_user_messages(message.bot, message.from_user.id, "menu"),
        delete_user_messages(message.bot, message.from_user.id, "library", exclude_ids=[sent.message_id])
    )


@library_router.callback_query(F.data.startswith("library_category:"))
async def show_category_books(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show books in category"""
    await callback.answer()

    # Parse data
    data_parts = callback.data.split(":")
    category_id = int(data_parts[1])
    page = int(data_parts[2]) if len(data_parts) > 2 else 1

    # Set state
    await state.set_state(LibraryStates.viewing_books)

    # Get category with books
    result = await session.execute(
        select(CategoryBook)
        .options(selectinload(CategoryBook.books))
        .where(CategoryBook.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        await callback.answer(library_error_text(), show_alert=True)
        return

    if not category.books:
        text = library_no_books_text(category.name)
        keyboard = library_empty_category_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Pagination - newest books first
    books = sorted(category.books, key=lambda x: x.id, reverse=True)
    total_items = len(books)
    total_pages = (total_items + BOOKS_PER_PAGE - 1) // BOOKS_PER_PAGE

    # Validate page
    page = max(1, min(page, total_pages))

    # Current page items
    start_idx = (page - 1) * BOOKS_PER_PAGE
    end_idx = min(start_idx + BOOKS_PER_PAGE, total_items)
    current_books = books[start_idx:end_idx]

    # Text and keyboard
    text = library_books_text(category.name, total_items, page, total_pages)
    keyboard = library_books_keyboard(
        books=current_books,
        category_id=category_id,
        current_page=page,
        total_pages=total_pages
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@library_router.callback_query(F.data.startswith("library_book:"))
async def show_book_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show book details with image and file"""
    await callback.answer()

    book_id = int(callback.data.split(":")[1])

    # Set state
    await state.set_state(LibraryStates.viewing_book_detail)

    # Get book with relations
    result = await session.execute(
        select(Book)
        .options(selectinload(Book.category))
        .where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()

    if not book:
        await callback.answer(library_error_text(), show_alert=True)
        return

    # Delete current message
    await callback.message.delete()

    try:
        # 1. Send image if exists
        if book.img:
            try:
                img_msg = await callback.bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=book.img
                )
                await store_message(callback.from_user.id, "library", img_msg.message_id)
            except:
                pass

        # 2. Send document
        doc_msg = await callback.bot.send_document(
            chat_id=callback.from_user.id,
            document=book.file
        )
        await store_message(callback.from_user.id, "library", doc_msg.message_id)

        # 3. Send details with keyboard
        detail_text = library_book_detail_text(
            book.name,
            book.category.name,
            book.description
        )
        keyboard = library_book_detail_keyboard(book.category_book_id)

        detail_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=detail_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "library", detail_msg.message_id)

    except Exception:
        # If file fails, send error message
        error_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=library_file_error_text(),
            reply_markup=library_book_detail_keyboard(book.category_book_id),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "library", error_msg.message_id)

    # Update state with category id
    await state.update_data(category_id=book.category_book_id)


@library_router.callback_query(F.data == "library_statistics")
async def show_library_statistics(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show library statistics"""
    await callback.answer()

    # Set state
    await state.set_state(LibraryStates.viewing_statistics)

    # Total books count
    result = await session.execute(
        select(func.count(Book.id))
    )
    total_books = result.scalar() or 0

    # Category statistics
    result = await session.execute(
        select(
            CategoryBook.name,
            func.count(Book.id).label('count')
        )
        .join(Book, CategoryBook.id == Book.category_book_id, isouter=True)
        .group_by(CategoryBook.id, CategoryBook.name)
        .order_by(func.count(Book.id).desc())
    )
    category_stats = result.all()

    # Check if there's any data
    if total_books == 0:
        text = library_no_statistics_text()
    else:
        text = library_statistics_text(total_books, category_stats)

    keyboard = library_statistics_keyboard()

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@library_router.callback_query(F.data == "library_back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back to categories list"""
    await callback.answer()

    # Set state
    await state.set_state(LibraryStates.viewing_categories)

    # Delete current message
    await callback.message.delete()

    # Load categories
    result = await session.execute(
        select(CategoryBook)
        .options(selectinload(CategoryBook.books))
        .order_by(CategoryBook.name)
    )
    categories = result.scalars().all()

    if not categories:
        new_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=library_no_categories_text(),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "library", new_msg.message_id)
        return

    # Send new message
    text = library_main_text()
    keyboard = library_categories_keyboard(categories, 1, 1)

    new_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "library", new_msg.message_id)


@library_router.callback_query(F.data == "library_back_from_stats")
async def back_from_statistics(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back from statistics"""
    await back_to_categories(callback, state, session)


@library_router.callback_query(F.data.startswith("library_back_from_detail:"))
async def back_from_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back from detail to category books"""
    await callback.answer()

    category_id = int(callback.data.split(":")[1])

    # Set state
    await state.set_state(LibraryStates.viewing_books)

    # Delete all current messages
    await delete_user_messages(callback.bot, callback.from_user.id, "library")

    # Load category
    result = await session.execute(
        select(CategoryBook)
        .options(selectinload(CategoryBook.books))
        .where(CategoryBook.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        await callback.answer(library_error_text(), show_alert=True)
        return

    if not category.books:
        text = library_no_books_text(category.name)
        keyboard = library_empty_category_keyboard()

        new_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "library", new_msg.message_id)
        return

    # Pagination - newest books first
    books = sorted(category.books, key=lambda x: x.id, reverse=True)
    total_items = len(books)
    total_pages = (total_items + BOOKS_PER_PAGE - 1) // BOOKS_PER_PAGE

    # Current page items (page 1)
    start_idx = 0
    end_idx = min(BOOKS_PER_PAGE, total_items)
    current_books = books[start_idx:end_idx]

    # Text and keyboard
    text = library_books_text(category.name, total_items, 1, total_pages)
    keyboard = library_books_keyboard(
        books=current_books,
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
    await store_message(callback.from_user.id, "library", new_msg.message_id)


# Main menu callback handler - MUHIM! - UPDATED
@library_router.callback_query(F.data == "library_main_menu")
async def handle_library_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handle library main menu button"""
    from bot.utils.texts import get_main_text

    await callback.answer()

    # Delete current message
    await callback.message.delete()

    # Parallel o'chirish - barcha library va menu xabarlarini
    await asyncio.gather(
        delete_user_messages(callback.bot, callback.from_user.id, "library"),
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
@library_router.callback_query(F.data.startswith("library_categories_page:"))
async def show_categories_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show categories pagination"""
    await callback.answer()

    page = int(callback.data.split(":")[1])

    # Get categories
    result = await session.execute(
        select(CategoryBook)
        .options(selectinload(CategoryBook.books))
        .order_by(CategoryBook.name)
    )
    categories = result.scalars().all()

    if not categories:
        await callback.answer(library_error_text(), show_alert=True)
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
    text = library_categories_text(page, total_pages)
    keyboard = library_categories_keyboard(current_categories, page, total_pages)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Bot ishga tushganda cleanup'ni boshlash
async def start_library_message_store_cleanup():
    """Bot start bo'lganda cleanup'ni ishga tushirish"""
    library_message_store.start_periodic_cleanup()