from sqlalchemy import select
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.suite.test_reflection import metadata

from db import Base, db
from db.utils import CreatedModel


class Category(CreatedModel):
    __tablename__ = 'categories'
    name: Mapped[str]

    @classmethod
    async def get_by_name(cls, name):
        query = select(cls).where(cls.name.ilike(f"%{name}%"))
        objects = await db.execute(query)
        objects = objects.skalar()
        if objects:
            return objects
        else:
            return []


metadata = Base.metadata