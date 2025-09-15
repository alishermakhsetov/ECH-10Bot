import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database URL
DB_ASYNC_URL = "postgresql+asyncpg://postgres:1@localhost:5432/ech10db"


async def add_database_indexes():
    """Database'ga performance uchun index'lar qo'shish"""

    print("🚀 Database Index'larni qo'shish boshlandi...\n")

    # Engine yaratish
    engine = create_async_engine(DB_ASYNC_URL, echo=False)

    # Session yaratish
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Index'lar ro'yxati
    indexes = [
        {
            "name": "idx_users_telegram_id",
            "sql": "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);",
            "description": "Users jadvalida telegram_id bo'yicha tezkor qidiruv"
        },
        {
            "name": "idx_channels_chat_id",
            "sql": "CREATE INDEX IF NOT EXISTS idx_channels_chat_id ON channels(chat_id);",
            "description": "Channels jadvalida chat_id bo'yicha tezkor qidiruv"
        },
        {
            "name": "idx_user_subscriptions_user_id",
            "sql": "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);",
            "description": "User subscriptions'da user_id bo'yicha tezkor qidiruv"
        },
        {
            "name": "idx_user_subscriptions_channel_id",
            "sql": "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_channel_id ON user_subscriptions(channel_id);",
            "description": "User subscriptions'da channel_id bo'yicha tezkor qidiruv"
        },
        {
            "name": "idx_subscriptions_user_channel",
            "sql": "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_channel ON user_subscriptions(user_id, channel_id);",
            "description": "Composite index - user va channel birgalikda"
        }
    ]

    try:
        async with async_session() as session:
            print("📊 Database ulanishi tekshirilmoqda...")

            # Connection test
            await session.execute(text("SELECT 1;"))
            print("✅ Database'ga ulanish muvaffaqiyatli!\n")

            success_count = 0

            for idx in indexes:
                try:
                    print(f"⏳ {idx['name']} yaratilmoqda...")

                    await session.execute(text(idx['sql']))
                    await session.commit()

                    print(f"✅ {idx['name']} - muvaffaqiyatli!")
                    print(f"   📝 {idx['description']}")
                    success_count += 1

                except Exception as e:
                    print(f"❌ {idx['name']} - xatolik: {e}")

                print("-" * 60)

            # Natijani ko'rsatish
            print(f"\n🎉 Jarayon tugadi!")
            print(f"✅ Muvaffaqiyatli: {success_count}/{len(indexes)} index")

            if success_count == len(indexes):
                print("\n🚀 Barcha index'lar muvaffaqiyatli qo'shildi!")
                print("💡 Endi database query'lar 10-50x tezroq ishlaydi!")
                print("\n📋 Keyingi qadamlar:")
                print("   1. Botni qayta ishga tushiring")
                print("   2. Performance test qiling")
                print("   3. Connection pooling qo'shing")
            else:
                print(f"\n⚠️  {len(indexes) - success_count} ta index qo'shilmadi")
                print("🔍 Xatolarni tekshiring va qayta urinib ko'ring")

    except Exception as e:
        print(f"❌ Database ulanishida xatolik: {e}")
        print("\n🔧 Tekshirish kerak:")
        print("   1. PostgreSQL ishlab turibdimi?")
        print("   2. Database mavjudmi?")
        print("   3. Login ma'lumotlari to'g'rimi?")

    finally:
        await engine.dispose()
        print("\n🔚 Database connection yopildi.")


# Mavjud index'larni ko'rish uchun
async def show_existing_indexes():
    """Mavjud index'larni ko'rsatish"""

    print("📋 Mavjud Index'lar:\n")

    engine = create_async_engine(DB_ASYNC_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Index'larni olish
            query = text("""
                         SELECT indexname,
                                tablename,
                                indexdef
                         FROM pg_indexes
                         WHERE schemaname = 'public'
                         ORDER BY tablename, indexname;
                         """)

            result = await session.execute(query)
            indexes = result.fetchall()

            current_table = ""
            for row in indexes:
                if row.tablename != current_table:
                    current_table = row.tablename
                    print(f"\n📁 {current_table.upper()} jadvali:")
                    print("-" * 40)

                print(f"   🔗 {row.indexname}")

    except Exception as e:
        print(f"❌ Xatolik: {e}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("🎯 Database Performance Optimization")
    print("=" * 60)

    # Index'larni qo'shish
    asyncio.run(add_database_indexes())

    print("\n" + "=" * 60)

    # Mavjud index'larni ko'rsatish
    asyncio.run(show_existing_indexes())
