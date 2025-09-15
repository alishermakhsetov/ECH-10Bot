from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.orm import sessionmaker
from db.models import User
from db import db
import logging

logger = logging.getLogger(__name__)


async def update_user_language(user_id: int, language_code: str):
    """
    Foydalanuvchi tilini yangilash - TELEGRAM_ID bo'yicha
    """
    try:
        # 🔄 FIXED: Har safar yangi session yaratish
        session_factory = sessionmaker(db._engine, expire_on_commit=False, class_=AsyncSession)

        async with session_factory() as session:
            # MUHIM: User.telegram_id ishlatish (User.id emas!)
            query = (
                update(User)
                .where(User.telegram_id == user_id)
                .values(language_code=language_code)
            )

            result = await session.execute(query)
            await session.commit()  # Commit qilish muhim!

            if result.rowcount > 0:
                logger.info(f"User telegram_id={user_id} language updated to {language_code}")
                return True
            else:
                logger.warning(f"No user found with telegram_id={user_id}")
                return False

    except Exception as e:
        logger.error(f"Error updating user language: {e}")
        return False


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """
    Telegram ID bo'yicha foydalanuvchini olish
    """
    try:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by telegram_id: {e}")
        return None


async def get_user_info(session: AsyncSession, telegram_id: int) -> tuple[str, str]:
    """
    Foydalanuvchi ma'lumotlarini olish - telegram_id bo'yicha
    """
    try:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user:
            return user.full_name or "Foydalanuvchi", user.language_code or "uz"
        return "Foydalanuvchi", "uz"
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return "Foydalanuvchi", "uz"


def validate_language_code(language_code: str) -> bool:
    """
    Til kodini tekshirish
    """
    SUPPORTED_LANGUAGES = ["uz", "ru", "en", "kk"]  # Sizning tillaringiz
    return language_code in SUPPORTED_LANGUAGES