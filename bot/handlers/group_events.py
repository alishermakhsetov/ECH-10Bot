# group_events.py

from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ChatMemberStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from bot.middlewares import user_warn_messages
from db.models import Channel

group_router = Router()


@group_router.chat_member()
async def user_joined_group(update: ChatMemberUpdated, bot: Bot, session: AsyncSession):
    """User guruhga qo'shilganda avtomatik warning o'chirish va start tugmasi"""
    try:
        # Database'dan required guruhlarni olish
        result = await session.execute(select(Channel).where(Channel.is_required == True))
        required_channels = result.scalars().all()

        # Bu guruh required guruhlardan birimi?
        is_required_group = any(channel.chat_id == update.chat.id for channel in required_channels)
        if not is_required_group:
            return

        user_id = update.new_chat_member.user.id
        old_status = update.old_chat_member.status
        new_status = update.new_chat_member.status

        # User guruhga qo'shildi
        if (old_status == ChatMemberStatus.LEFT and
                new_status == ChatMemberStatus.MEMBER):
            # Parallel ravishda eski xabarlarni o'chirish
            await clear_user_warnings(bot, user_id)

            # Reply button bilan start tugmasi yuborish
            await send_start_button(bot, user_id)

    except Exception as e:
        print(f"Error in user_joined_group: {e}")


async def clear_user_warnings(bot: Bot, user_id: int):
    """Parallel ravishda warning xabarlarni o'chirish"""
    if user_id in user_warn_messages:
        # Parallel o'chirish
        tasks = []
        for msg_id in user_warn_messages[user_id]:
            task = asyncio.create_task(safe_delete_message(bot, user_id, msg_id))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        user_warn_messages[user_id].clear()


async def safe_delete_message(bot: Bot, chat_id: int, message_id: int):
    """Xavfsiz xabar o'chirish"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass  # Silent ignore


async def send_start_button(bot: Bot, user_id: int):
    """Reply keyboard bilan start tugmasi yuborish"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Boshlash")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    welcome_msg = await bot.send_message(
        user_id,
        "🎉 Siz muvaffaqiyatli qo'shildingiz!\n"
        "🤖 Botdan foydalanish uchun\n🚀 Boshlash tugmasini bosing.",
        reply_markup=keyboard
    )

    # Welcome xabarni store qilish
    user_warn_messages.setdefault(user_id, []).append(welcome_msg.message_id)