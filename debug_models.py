# debug_models.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from db import db
from db.models import User, CategoryBook, CategoryVideo


async def test_model_display():
    """Model'larning __str__ metodini tekshirish"""
    db.init()

    async with db.get_session() as session:
        print("🔍 DEBUG: Model'larning __str__ metodini tekshirish...")
        print("=" * 60)

        # User test
        user_result = await session.execute(text("SELECT * FROM users LIMIT 1"))
        user_row = user_result.fetchone()

        if user_row:
            print("=== USER TEST ===")
            print(f"Database'dan: {user_row}")

            # User obyektini yaratish
            user = User()
            user.id = user_row.id
            user.full_name = user_row.full_name
            user.phone_number = user_row.phone_number
            user.telegram_id = user_row.telegram_id
            user.role = user_row.role
            user.username = user_row.username
            user.language_code = user_row.language_code

            print(f"__str__ result: '{str(user)}'")
            print(f"__repr__ result: '{repr(user)}'")

            # Actual database'dan User obyektini olish
            actual_user = await session.get(User, user_row.id)
            if actual_user:
                print(f"Actual User __str__: '{str(actual_user)}'")
                print(f"Actual User __repr__: '{repr(actual_user)}'")
        else:
            print("❌ User topilmadi database'da")

        print()

        # CategoryBook test
        cat_result = await session.execute(text("SELECT * FROM category_books LIMIT 1"))
        cat_row = cat_result.fetchone()

        if cat_row:
            print("=== CATEGORY BOOK TEST ===")
            print(f"Database'dan: {cat_row}")

            cat = CategoryBook()
            cat.id = cat_row.id
            cat.name = cat_row.name

            print(f"__str__ result: '{str(cat)}'")
            print(f"__repr__ result: '{repr(cat)}'")

            # Actual database'dan
            actual_cat = await session.get(CategoryBook, cat_row.id)
            if actual_cat:
                print(f"Actual Category __str__: '{str(actual_cat)}'")
        else:
            print("❌ CategoryBook topilmadi")

        print()
        print("🔍 STARLETTE ADMIN INTEGRATION TEST...")

        # Starlette admin qanday ko'rsatishini tekshirish
        if user_row:
            actual_user = await session.get(User, user_row.id)
            print(f"User object: {actual_user}")
            print(f"User object type: {type(actual_user)}")
            print(f"User object __class__.__name__: {actual_user.__class__.__name__}")
            print(f"hasattr full_name: {hasattr(actual_user, 'full_name')}")
            print(f"hasattr phone_number: {hasattr(actual_user, 'phone_number')}")

            # Manual formatting test
            if hasattr(actual_user, 'full_name') and hasattr(actual_user, 'phone_number'):
                manual_format = f"{actual_user.full_name} - {actual_user.phone_number}"
                print(f"Manual format: '{manual_format}'")


if __name__ == "__main__":
    asyncio.run(test_model_display())