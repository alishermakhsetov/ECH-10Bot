from typing import Callable, Awaitable, Dict, Any, List
from aiogram import BaseMiddleware, Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.utils.i18n import I18n
from bot.utils.user_helpers import get_user_by_telegram_id

from db.models import Channel

MAX_STORED_MESSAGES = 2
user_warn_messages: Dict[int, list[int]] = {}  # user_id -> list of warning message_ids


def create_channel_join_keyboard(channels: List[Channel]) -> InlineKeyboardMarkup:
    """Guruh/kanallarga qo'shilish uchun inline tugmalar"""
    builder = InlineKeyboardBuilder()

    for channel in channels:
        if channel.link:  # Link mavjud bo'lsa
            # Emoji tanlash
            emoji = "👥" if channel.title and "guruh" in channel.title.lower() else "📢"

            builder.button(
                text=f"{emoji} {channel.title or 'Guruh/Kanal'}",
                url=channel.link
            )

    builder.adjust(1)  # Har qatorda 1 tadan tugma
    return builder.as_markup()


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


class JoinChannelMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session
            return await self.process(handler, event, data)

    async def process(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data.get("bot")
        session: AsyncSession = data.get("session")
        user = getattr(event, "from_user", None)

        if not user:
            return await handler(event, data)

        message: Message | None = None
        if isinstance(event, Message):
            message = event
        elif isinstance(event, CallbackQuery):
            message = event.message

        if not message:
            return await handler(event, data)

        # 🔥 MUHIM: Faqat private chatda tekshirish
        if message.chat.type != "private":
            return await handler(event, data)

        # Kanal va guruhlarni bazadan olish
        result = await session.execute(select(Channel).where(Channel.is_required == True))
        required_channels = result.scalars().all()

        # A'zo bo'lmagan kanallar ro'yxati
        not_joined_channels = []

        for channel in required_channels:
            try:
                member = await bot.get_chat_member(chat_id=channel.chat_id, user_id=user.id)

                if member.status == ChatMemberStatus.LEFT:
                    not_joined_channels.append(channel)

                elif member.status == ChatMemberStatus.KICKED:
                    await self.send_kicked_warning(bot, message, user.id)
                    return

            except TelegramBadRequest as e:
                await self.send_error_warning(bot, message, user.id)
                print(f"[JOIN CHECK ERROR] {e}")
                return

        # Agar a'zo bo'lmagan kanallar bo'lsa
        if not_joined_channels:
            await self.send_join_warning(bot, message, user.id, not_joined_channels)
            return

        # Foydalanuvchi barcha kanallarga a'zo — davom etadi
        return await handler(event, data)

    async def send_join_warning(self, bot: Bot, message: Message, user_id: int, channels: List[Channel]):
        """A'zo bo'lmagan kanallar uchun warning"""
        try:
            # User /start xabarini darhol o'chirish
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            except:
                pass

            # Avvalgi warning xabarlarini o'chirish
            if user_id in user_warn_messages:
                for old_msg_id in user_warn_messages[user_id]:
                    try:
                        await bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)
                    except:
                        pass
                user_warn_messages[user_id].clear()

            # Warning text
            text = (
                "🔒 Botdan foydalanish cheklangan!\n"
                "🏢 Bu Bot faqat ECH-10 korxonasi xodimlari uchun mo'ljallangan.\n\n"
                "📋 Botdan foydalanish uchun:\n"
                "• Quyidagi rasmiy guruh/kanalga qo'shiling\n"
                "• Administrator sizni tasdiqlaydi\n"
                "• Keyin Botdan to'liq foydalanishingiz mumkin\n\n"
                "👇 Qo'shilish uchun tugmani bosing:"
            )

            # Inline keyboard yaratish
            keyboard = create_channel_join_keyboard(channels)

            # Xabar yuborish
            sent_msg = await message.answer(text, reply_markup=keyboard)

            # Store qilish
            user_warn_messages.setdefault(user_id, []).append(sent_msg.message_id)

        except Exception as e:
            print(f"[SEND JOIN WARNING ERROR] {e}")

    async def send_kicked_warning(self, bot: Bot, message: Message, user_id: int):
        """Chetlashtirilgan foydalanuvchi uchun warning"""
        try:
            # User /start xabarini darhol o'chirish
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            except:
                pass

            # Avvalgi warning xabarlarini o'chirish
            if user_id in user_warn_messages:
                for old_msg_id in user_warn_messages[user_id]:
                    try:
                        await bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)
                    except:
                        pass
                user_warn_messages[user_id].clear()

            text = (
                "❌ Siz kerakli Guruh yoki Kanalga a'zo emassiz yoki chetlashtirilgansiz.\n"
                "🤖 Botdan foydalanish uchun administrator sizni guruhga qo'shishi kerak.\n"
                "📩 Iltimos, admin bilan bog'laning."
            )

            sent_msg = await message.answer(text)
            user_warn_messages.setdefault(user_id, []).append(sent_msg.message_id)

        except Exception as e:
            print(f"[SEND KICKED WARNING ERROR] {e}")

    async def send_error_warning(self, bot: Bot, message: Message, user_id: int):
        """Xatolik uchun warning"""
        try:
            # User /start xabarini darhol o'chirish
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            except:
                pass

            # Avvalgi warning xabarlarini o'chirish
            if user_id in user_warn_messages:
                for old_msg_id in user_warn_messages[user_id]:
                    try:
                        await bot.delete_message(chat_id=message.chat.id, message_id=old_msg_id)
                    except:
                        pass
                user_warn_messages[user_id].clear()

            text = "❌ Kanal yoki guruhga kirishda xatolik yuz berdi. Iltimos, admin bilan bog'laning."

            sent_msg = await message.answer(text)
            user_warn_messages.setdefault(user_id, []).append(sent_msg.message_id)

        except Exception as e:
            print(f"[SEND ERROR WARNING ERROR] {e}")


class UserLanguageMiddleware(BaseMiddleware):
    """
    Har requestda user tilini database'dan yuklaydi va i18n'ga o'rnatadi
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession], i18n: I18n):
        self.session_pool = session_pool
        self.i18n = i18n
        self.default_locale = "uz"

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        # User telegram_id olish
        user_obj = getattr(event, 'from_user', None)
        if not user_obj:
            self.i18n.current_locale = self.default_locale
            return await handler(event, data)

        telegram_id = user_obj.id

        # Database'dan user tilini olish
        try:
            async with self.session_pool() as session:
                user = await get_user_by_telegram_id(session, telegram_id)

                if user and user.language_code:
                    self.i18n.current_locale = user.language_code
                else:
                    self.i18n.current_locale = self.default_locale

        except Exception as e:
            print(f"Error loading user language: {e}")
            self.i18n.current_locale = self.default_locale

        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """Spam oldini olish uchun rate limiting middleware"""

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit  # Soniya
        self.user_requests = {}  # user_id: timestamp

        # Admin user IDs (spam limit yo'q)
        self.admin_ids = {
            900172087,  # Sizning telegram ID
        }

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        # User ID olish
        user = getattr(event, 'from_user', None)
        if not user:
            return await handler(event, data)

        user_id = user.id

        # Admin'lar uchun rate limit yo'q
        if user_id in self.admin_ids:
            return await handler(event, data)

        # Rate limit tekshiruvi
        import time
        now = time.time()

        if user_id in self.user_requests:
            time_passed = now - self.user_requests[user_id]
            if time_passed < self.rate_limit:
                # Spam - ignore qilish
                print(f"🚫 Rate limit: User {user_id}")
                return

        # Request'ni record qilish
        self.user_requests[user_id] = now

        # Memory cleanup (1000+ user bo'lganda)
        if len(self.user_requests) > 1000:
            cleanup_threshold = 3600  # 1 soat
            users_to_remove = [
                uid for uid, timestamp in self.user_requests.items()
                if now - timestamp > cleanup_threshold
            ]
            for uid in users_to_remove:
                del self.user_requests[uid]

        return await handler(event, data)