# handlers/train_safety_handler.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import asyncio
from aiogram.utils.i18n import lazy_gettext as __
from collections import defaultdict, deque
import time
from aiogram.exceptions import TelegramBadRequest

from db.models import TrainSafetyFolder, TrainSafetyFile
from bot.states import TrainSafetyStates
from bot.buttons.inline import (
    train_safety_folders_keyboard,
    train_safety_files_keyboard,
    train_safety_empty_folder_keyboard,
    train_safety_file_detail_keyboard
)
from bot.utils.texts import (
    train_safety_main_text,
    train_safety_no_folders_text,
    train_safety_folder_files_text,
    train_safety_file_info_text,
    train_safety_file_error_text,
    train_safety_error_text,
    main_menu_text
)
from bot.buttons.reply import get_main_menu_keyboard

train_safety_router = Router()

# Constants
FOLDERS_PER_PAGE = 10
FILES_PER_PAGE = 10
MAX_MESSAGES_PER_USER = 10
CLEANUP_INTERVAL = 3600  # 1 soat
DELETE_CHUNK_SIZE = 10


# Message Store - library handler kabi
class TrainSafetyMessageStore:
    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()
        self._cleanup_task = None

    def store_message(self, user_id: int, message_id: int, category: str = "train_safety"):
        """Xabarni saqlash"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "train_safety") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "train_safety"):
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


# Global instance
train_safety_message_store = TrainSafetyMessageStore()


# Helper functions
async def store_message(user_id: int, category: str, message_id: int):
    """Xabar saqlash"""
    try:
        train_safety_message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Xabarlarni parallel o'chirish"""
    msg_ids = train_safety_message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    # Chunking
    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

    # Store tozalash
    if not exclude_ids:
        train_safety_message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    """Xavfsiz xabar o'chirish"""
    try:
        await bot.delete_message(chat_id, msg_id)
        return True
    except Exception:
        return False


# Main handler
@train_safety_router.message(F.text == __("🚆 Poezdlar Harakat Xavfsizligi"))
async def show_train_safety_main(message: Message, state: FSMContext, session: AsyncSession):
    """Main train safety menu"""
    # User xabarini saqlash
    await store_message(message.from_user.id, "train_safety", message.message_id)

    # Clear state
    await state.clear()
    await state.set_state(TrainSafetyStates.viewing_folders)

    # Remove reply keyboard
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    # Get folders
    result = await session.execute(
        select(TrainSafetyFolder)
        .where(TrainSafetyFolder.is_active == True)
        .order_by(TrainSafetyFolder.order_index, TrainSafetyFolder.name)
    )
    folders = result.scalars().all()

    if not folders:
        text = train_safety_no_folders_text()
        reply_markup = None
    else:
        text = train_safety_main_text()
        keyboard = train_safety_folders_keyboard(folders, 1, FOLDERS_PER_PAGE)
        reply_markup = keyboard

    # Send new message
    sent = await message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await store_message(message.from_user.id, "train_safety", sent.message_id)

    # Parallel o'chirish - barcha eski xabarlarni
    await asyncio.gather(
        delete_user_messages(message.bot, message.from_user.id, "menu"),
        delete_user_messages(message.bot, message.from_user.id, "train_safety", exclude_ids=[sent.message_id])
    )


# Folders pagination handler
@train_safety_router.callback_query(F.data.startswith("train_safety_folders_page_"))
async def show_folders_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show folders pagination"""
    await callback.answer()

    page = int(callback.data.split("_")[-1])

    # Set state
    await state.set_state(TrainSafetyStates.viewing_folders)

    # Get folders
    result = await session.execute(
        select(TrainSafetyFolder)
        .where(TrainSafetyFolder.is_active == True)
        .order_by(TrainSafetyFolder.order_index, TrainSafetyFolder.name)
    )
    folders = result.scalars().all()

    if not folders:
        await callback.answer(train_safety_error_text(), show_alert=True)
        return

    # Text and keyboard
    text = train_safety_main_text()
    keyboard = train_safety_folders_keyboard(folders, page, FOLDERS_PER_PAGE)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Folder selected
@train_safety_router.callback_query(F.data.startswith("train_safety_folder_"))
async def show_folder_files(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show files in folder with pagination"""
    await callback.answer()

    # Parse data
    parts = callback.data.split("_")
    folder_id = int(parts[-1])
    page = 1  # Default page

    # Check if this is from pagination
    if len(parts) > 4 and parts[-2] == "page":
        folder_id = int(parts[-3])
        page = int(parts[-1])

    # Set state
    await state.set_state(TrainSafetyStates.viewing_files)
    await state.update_data(folder_id=folder_id)

    # Get folder with files
    result = await session.execute(
        select(TrainSafetyFolder)
        .options(selectinload(TrainSafetyFolder.files))
        .where(
            TrainSafetyFolder.id == folder_id,
            TrainSafetyFolder.is_active == True
        )
    )
    folder = result.scalar_one_or_none()

    if not folder:
        await callback.answer(train_safety_error_text(), show_alert=True)
        return

    # Active files only
    active_files = [
        file for file in folder.files
        if file.is_active
    ]
    active_files.sort(key=lambda x: (x.order_index, x.name))

    if not active_files:
        text = train_safety_folder_files_text(folder.name, folder.description, 0)
        keyboard = train_safety_empty_folder_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Text and keyboard
    text = train_safety_folder_files_text(
        folder.name,
        folder.description,
        len(active_files)
    )
    keyboard = train_safety_files_keyboard(active_files, folder_id, page, FILES_PER_PAGE)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Files pagination handler
@train_safety_router.callback_query(F.data.startswith("train_safety_files_page_"))
async def show_files_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show files pagination"""
    await callback.answer()

    # Parse data: train_safety_files_page_{folder_id}_{page}
    parts = callback.data.split("_")
    folder_id = int(parts[-2])
    page = int(parts[-1])

    # Get folder with files
    result = await session.execute(
        select(TrainSafetyFolder)
        .options(selectinload(TrainSafetyFolder.files))
        .where(
            TrainSafetyFolder.id == folder_id,
            TrainSafetyFolder.is_active == True
        )
    )
    folder = result.scalar_one_or_none()

    if not folder:
        await callback.answer(train_safety_error_text(), show_alert=True)
        return

    # Active files only
    active_files = [
        file for file in folder.files
        if file.is_active
    ]
    active_files.sort(key=lambda x: (x.order_index, x.name))

    # Text and keyboard
    text = train_safety_folder_files_text(
        folder.name,
        folder.description,
        len(active_files)
    )
    keyboard = train_safety_files_keyboard(active_files, folder_id, page, FILES_PER_PAGE)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# File selected
@train_safety_router.callback_query(F.data.startswith("train_safety_file_"))
async def show_file_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show file details and send document"""
    await callback.answer()

    file_id = int(callback.data.split("_")[-1])

    # Get file with relations
    result = await session.execute(
        select(TrainSafetyFile)
        .options(selectinload(TrainSafetyFile.folder))
        .where(
            TrainSafetyFile.id == file_id,
            TrainSafetyFile.is_active == True
        )
    )
    file = result.scalar_one_or_none()

    if not file:
        await callback.answer(train_safety_error_text(), show_alert=True)
        return

    # Delete current message
    await callback.message.delete()

    # Delete all old messages
    await delete_user_messages(callback.bot, callback.from_user.id, "train_safety")

    try:
        # File info text
        file_info = train_safety_file_info_text(
            folder_name=file.folder.name,
            file_name=file.name,
            description=file.description
        )

        # Send document with caption and keyboard
        keyboard = train_safety_file_detail_keyboard(file.folder_id)
        doc_msg = await callback.bot.send_document(
            chat_id=callback.from_user.id,
            document=file.file_id,
            caption=file_info,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "train_safety", doc_msg.message_id)

    except TelegramBadRequest:
        # Error message
        error_text = train_safety_file_error_text(
            file_name=file.name,
            folder_name=file.folder.name
        )

        error_msg = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=error_text,
            reply_markup=train_safety_file_detail_keyboard(file.folder_id),
            parse_mode="HTML"
        )
        await store_message(callback.from_user.id, "train_safety", error_msg.message_id)

    # Update state with folder id
    await state.update_data(folder_id=file.folder_id)


# Back to folders
@train_safety_router.callback_query(F.data == "train_safety_back_to_folders")
async def back_to_folders(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back to folders list"""
    await callback.answer()

    # Set state
    await state.set_state(TrainSafetyStates.viewing_folders)

    # Delete all messages
    await delete_user_messages(callback.bot, callback.from_user.id, "train_safety")

    # Get folders
    result = await session.execute(
        select(TrainSafetyFolder)
        .where(TrainSafetyFolder.is_active == True)
        .order_by(TrainSafetyFolder.order_index, TrainSafetyFolder.name)
    )
    folders = result.scalars().all()

    if not folders:
        text = train_safety_no_folders_text()
        keyboard = None
    else:
        text = train_safety_main_text()
        keyboard = train_safety_folders_keyboard(folders, 1, FOLDERS_PER_PAGE)

    # Send new message
    new_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "train_safety", new_msg.message_id)


# Back from file detail
@train_safety_router.callback_query(F.data.startswith("train_safety_back_from_detail:"))
async def back_from_detail(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Back from file detail to files list"""
    await callback.answer()

    folder_id = int(callback.data.split(":")[1])

    # Set state
    await state.set_state(TrainSafetyStates.viewing_files)

    # Delete all messages
    await delete_user_messages(callback.bot, callback.from_user.id, "train_safety")

    # Get folder with files
    result = await session.execute(
        select(TrainSafetyFolder)
        .options(selectinload(TrainSafetyFolder.files))
        .where(
            TrainSafetyFolder.id == folder_id,
            TrainSafetyFolder.is_active == True
        )
    )
    folder = result.scalar_one_or_none()

    if not folder:
        await callback.answer(train_safety_error_text(), show_alert=True)
        return

    # Active files only
    active_files = [
        file for file in folder.files
        if file.is_active
    ]
    active_files.sort(key=lambda x: (x.order_index, x.name))

    if not active_files:
        text = train_safety_folder_files_text(folder.name, folder.description, 0)
        keyboard = train_safety_empty_folder_keyboard()
    else:
        text = train_safety_folder_files_text(
            folder.name,
            folder.description,
            len(active_files)
        )
        keyboard = train_safety_files_keyboard(active_files, folder_id, 1, FILES_PER_PAGE)

    # Send new message
    new_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "train_safety", new_msg.message_id)


# Main menu callback handler
@train_safety_router.callback_query(F.data == "train_safety_main_menu")
async def handle_train_safety_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handle main menu button - delete all messages first"""
    from bot.utils.texts import get_main_text

    await callback.answer()

    # First delete all train_safety messages (including current document)
    await delete_user_messages(callback.bot, callback.from_user.id, "train_safety")

    # Then delete current message if it still exists
    try:
        await callback.message.delete()
    except:
        pass

    # Delete menu messages too
    await delete_user_messages(callback.bot, callback.from_user.id, "menu")

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