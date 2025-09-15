from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, String, ForeignKey, Text, Boolean, DateTime, Enum as SqlEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base
from db.utils import CreatedModel


class Role(Enum):
    superuser = "superuser"  # Tizimdagi barcha funksiyalarni boshqaradi (admin)
    equipment_manager = "equipment_manager"  # Himoya vositalarini kiritish, o'chirish, yangilash
    safety_manager = "safety_manager"  # Baxtsiz hodisalarni va Imtihon vatini boshqaradi
    viewer = "viewer"  # Boshliq: faqat ko'rish huquqiga ega
    user = "user"  # Oddiy foydalanuvchi: test va ma'lumotlardan foydalanadi


class User(CreatedModel):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), default=Role.user)
    username: Mapped[str | None] = mapped_column(String(56), nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    language_code: Mapped[str] = mapped_column(String(5), default="uz")
    last_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exam_schedule: Mapped["ExamSchedule"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __str__(self):
        return f"{self.full_name} - {self.phone_number}"

    def __repr__(self):
        return f"User(id={self.id}, name='{self.full_name}', phone='{self.phone_number}')"


class ExamSchedule(CreatedModel):
    __tablename__ = "exam_schedules"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    last_exam: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="exam_schedule")

    def __str__(self):
        return f"{self.user.full_name} - {self.last_exam.strftime('%d.%m.%Y')}"


class CategoryTest(CreatedModel):
    __tablename__ = "category_tests"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tests: Mapped[list["Test"]] = relationship(back_populates="category", cascade="all, delete-orphan")

    def __str__(self):
        return self.name


class Test(CreatedModel):
    __tablename__ = "tests"
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    category_test_id: Mapped[int] = mapped_column(ForeignKey("category_tests.id", ondelete='CASCADE'))
    category: Mapped["CategoryTest"] = relationship(back_populates="tests")
    answers: Mapped[list["AnswerTest"]] = relationship(back_populates="test", cascade="all, delete-orphan")

    def __str__(self):
        return self.text[:30] + "..." if len(self.text) > 30 else self.text


class AnswerTest(CreatedModel):
    __tablename__ = "answer_tests"
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete='CASCADE'))
    test: Mapped["Test"] = relationship(back_populates="answers")

    def __str__(self):
        return self.text


class DepartmentSafety(CreatedModel):
    """Sex/Bo'lim - Korxonadagi asosiy bo'limlar"""
    __tablename__ = "department_safeties"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    area_safeties: Mapped[list["AreaSafety"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="department_safety"
    )

    def __str__(self):
        return self.name


class AreaSafety(CreatedModel):
    """Hudud - Sex ichidagi maydonlar"""
    __tablename__ = "area_safeties"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str | None] = mapped_column(String, nullable=True)

    department_safety_id: Mapped[int] = mapped_column(
        ForeignKey("department_safeties.id", ondelete='RESTRICT')
    )

    department_safety: Mapped["DepartmentSafety"] = relationship(back_populates="area_safeties")
    facility_safeties: Mapped[list["FacilitySafety"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="area_safety"
    )

    def __str__(self):
        return self.name


class FacilitySafety(CreatedModel):
    """Inshoot - Hudud ichidagi binolar/inshootlar"""
    __tablename__ = "facility_safeties"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image: Mapped[str | None] = mapped_column(String, nullable=True)

    area_safety_id: Mapped[int] = mapped_column(
        ForeignKey("area_safeties.id", ondelete='RESTRICT')
    )

    area_safety: Mapped["AreaSafety"] = relationship(back_populates="facility_safeties")
    equipment_safeties: Mapped[list["EquipmentSafety"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="facility_safety"
    )

    def __str__(self):
        return self.name


class EquipmentCatalog(CreatedModel):
    """Himoya vositalari katalogi - shablon"""
    __tablename__ = "equipment_catalogs"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str] = mapped_column(Text)

    equipment_items: Mapped[list["EquipmentSafety"]] = relationship(back_populates="catalog")

    def __str__(self):
        return self.name


class EquipmentSafety(CreatedModel):
    """Himoya vositalari - Inshootdagi himoya uskunalari"""
    __tablename__ = "equipment_safeties"

    catalog_id: Mapped[int] = mapped_column(
        ForeignKey("equipment_catalogs.id", ondelete='RESTRICT')
    )
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    file_image: Mapped[str] = mapped_column(String, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    facility_safety_id: Mapped[int] = mapped_column(
        ForeignKey("facility_safeties.id", ondelete='RESTRICT')
    )

    facility_safety: Mapped["FacilitySafety"] = relationship(back_populates="equipment_safeties")
    catalog: Mapped["EquipmentCatalog"] = relationship(back_populates="equipment_items")

    def __str__(self):
        return f"{self.catalog.name} - {self.serial_number}"


class CategoryBook(CreatedModel):
    __tablename__ = "category_books"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    books: Mapped[list["Book"]] = relationship(back_populates="category", cascade="all, delete-orphan")

    def __str__(self):
        return self.name


class Book(CreatedModel):
    __tablename__ = "books"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    img: Mapped[str] = mapped_column(String(255), nullable=True)
    file: Mapped[str] = mapped_column(String)
    category_book_id: Mapped[int] = mapped_column(ForeignKey("category_books.id", ondelete='CASCADE'))
    category: Mapped["CategoryBook"] = relationship(back_populates="books")

    def __str__(self):
        return self.name


class CategoryVideo(CreatedModel):
    __tablename__ = "category_videos"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    videos: Mapped[list["Video"]] = relationship(back_populates="category", cascade="all, delete-orphan")

    def __str__(self):
        return self.name


class Video(CreatedModel):
    __tablename__ = "videos"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    file: Mapped[str] = mapped_column(String)
    category_video_id: Mapped[int] = mapped_column(ForeignKey("category_videos.id", ondelete='CASCADE'))
    category: Mapped["CategoryVideo"] = relationship(back_populates="videos")

    def __str__(self):
        return self.name


class AccidentCategory(CreatedModel):
    """Baxtsiz hodisa kategoriyalari (admin uchun)"""
    __tablename__ = "accident_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    accidents: Mapped[list["Accident"]] = relationship(back_populates="category")

    def __str__(self):
        return self.name


class AccidentYear(CreatedModel):
    """Baxtsiz hodisa yillari"""
    __tablename__ = "accident_years"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    accidents: Mapped[list["Accident"]] = relationship(back_populates="year")

    @property
    def year_number(self) -> int:
        """Yil raqamini olish (tartiblash uchun)"""
        import re
        match = re.search(r'(\d{4})', self.name)
        return int(match.group(1)) if match else 0

    @property
    def has_accidents(self) -> bool:
        """Bu yilda baxtsiz hodisalar bormi?"""
        return len(self.accidents) > 0

    def __str__(self):
        return self.name


class Accident(CreatedModel):
    """Baxtsiz hodisalar"""
    __tablename__ = "accidents"

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    file_pdf: Mapped[str] = mapped_column(String, nullable=False)
    file_image: Mapped[str | None] = mapped_column(String, nullable=True)
    year_id: Mapped[int] = mapped_column(ForeignKey("accident_years.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("accident_categories.id"))

    year: Mapped["AccidentYear"] = relationship(back_populates="accidents")
    category: Mapped["AccidentCategory"] = relationship(back_populates="accidents")

    description: Mapped[str] = mapped_column(Text)

    def __str__(self):
        return self.title


class Channel(CreatedModel):
    __tablename__ = "channels"

    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    link: Mapped[str | None] = mapped_column(String, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __str__(self):
        return self.title or "Kanal"


class CompanyInfo(CreatedModel):
    __tablename__ = "company_info"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=True)
    presentation_file: Mapped[str] = mapped_column(String, nullable=True)
    group_link: Mapped[str] = mapped_column(String, nullable=False)
    admin_link: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str] = mapped_column(String, nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __str__(self):
        return self.name


class TrainSafetyFolder(CreatedModel):
    """Poezdlar harakat xavfsizligi papkalari"""
    __tablename__ = "train_safety_folders"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    files: Mapped[list["TrainSafetyFile"]] = relationship(
        back_populates="folder",
        order_by="TrainSafetyFile.order_index"
    )

    def __str__(self):
        return self.name


class TrainSafetyFile(CreatedModel):
    """Poezdlar harakat xavfsizligi fayllari"""
    __tablename__ = "train_safety_files"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    folder_id: Mapped[int] = mapped_column(ForeignKey("train_safety_folders.id"))

    folder: Mapped["TrainSafetyFolder"] = relationship(back_populates="files")

    def __str__(self):
        return self.name


class AdminUser(CreatedModel):
    __tablename__ = "admin_users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __str__(self):
        return self.username


metadata = Base.metadata