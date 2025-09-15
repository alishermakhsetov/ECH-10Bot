import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

try:
    from utils.env_data import Config as cf
except ImportError:
    # Fallback - to'g'ridan-to'g'ri environment variable'lardan o'qish
    import os
    from dotenv import load_dotenv

    load_dotenv()


    class MockConfig:
        class db:
            DB_URL = os.getenv("DB_ASYNC_URL", "postgresql+asyncpg://postgres:1@localhost:5432/ech10db")

        class web:
            ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
            ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "$2b$12$hashed_password")


    cf = MockConfig()


class Base(AsyncAttrs, DeclarativeBase):
    pass


class AsyncDatabaseSession:
    def __init__(self):
        self._session_maker = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session_maker, name)

    def init(self):
        self._engine = create_async_engine(
            cf.db.DB_URL,
            future=True,
            echo=False,
            # Connection Pooling
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

        self._session_maker = async_sessionmaker(
            self._engine,
            expire_on_commit=False
        )

    def get_session(self):
        """Session olish"""
        return self._session_maker()

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


db = AsyncDatabaseSession()