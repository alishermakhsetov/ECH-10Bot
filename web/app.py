import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.exceptions import FormValidationError
from starlette.requests import Request
from typing import Any, Dict
import bcrypt

from db import db
from db.models import (
    User, ExamSchedule, AdminUser, Role,
    CategoryTest, Test, AnswerTest,
    DepartmentSafety, AreaSafety, FacilitySafety,
    EquipmentCatalog, EquipmentSafety,
    CategoryBook, Book, CategoryVideo, Video,
    AccidentCategory, AccidentYear, Accident,
    Channel, CompanyInfo, TrainSafetyFolder, TrainSafetyFile
)
from web.provider import ProfessionalAuthProvider


class BaseModelView(ModelView):
    """Asosiy ModelView - umumiy sozlamalar"""

    exclude_fields_from_create = ["id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "created_at", "updated_at"]
    exclude_fields_from_list = ["created_at", "updated_at"]
    exclude_fields_from_detail = ["created_at", "updated_at"]

    page_size = 25
    page_size_options = [10, 25, 50, 100]

    def label_for_field_name(self, field_name: str) -> str:
        """Field'lar uchun O'zbek nomlari"""
        labels = {
            "username": "Login", "password_hash": "Parol", "role": "Lavozim",
            "is_active": "Faol", "last_login": "Oxirgi kirish",
            "full_name": "Ism-familiya", "phone_number": "Telefon",
            "telegram_id": "Telegram ID", "language_code": "Til",
            "name": "Nomi", "title": "Sarlavha", "description": "Tavsif",
            "text": "Matn", "image": "Rasm", "file": "Fayl", "img": "Rasm",
            "user": "Xodim", "last_exam": "Imtihon sanasi", "comment": "Izoh",
            "catalog": "Katalog", "serial_number": "Seriya raqami",
            "expire_at": "Yaroqlilik muddati", "facility_safety": "Inshoot",
            "file_image": "Rasm fayli", "category": "Kategoriya", "is_correct": "To'g'ri javob",
            "test": "Savol", "year": "Yil", "file_pdf": "PDF fayl",
            "chat_id": "Chat ID", "link": "Havola", "is_required": "Majburiy",
            "department_safety": "Bo'lim", "area_safety": "Hudud",
            "folder": "Papka", "file_id": "Fayl ID", "order_index": "Tartib raqami"
        }
        return labels.get(field_name, field_name.replace('_', ' ').title())

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        """Yangi yozuv yaratish"""
        try:
            errors = self._validate_data(data, is_create=True)
            if errors:
                raise FormValidationError(errors)

            if self.model.__name__ == "AdminUser" and data.get("password_hash"):
                data["password_hash"] = bcrypt.hashpw(
                    data["password_hash"].encode(), bcrypt.gensalt()
                ).decode()

            return await super().create(request, data)
        except FormValidationError:
            raise
        except Exception as e:
            raise FormValidationError({"error": f"Xatolik: {str(e)}"})

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        """Yozuvni tahrirlash"""
        try:
            errors = self._validate_data(data, is_create=False)
            if errors:
                raise FormValidationError(errors)

            if self.model.__name__ == "AdminUser" and data.get("password_hash"):
                data["password_hash"] = bcrypt.hashpw(
                    data["password_hash"].encode(), bcrypt.gensalt()
                ).decode()

            return await super().edit(request, pk, data)
        except FormValidationError:
            raise
        except Exception as e:
            raise FormValidationError({"error": f"Xatolik: {str(e)}"})

    def _validate_data(self, data: Dict[str, Any], is_create: bool = True) -> Dict[str, str]:
        """Barcha modellar uchun validation"""
        errors = {}
        model_name = self.model.__name__

        if model_name == "AdminUser":
            if not data.get("username", "").strip():
                errors["username"] = "Login kiritish majburiy"
            if is_create and not data.get("password_hash", "").strip():
                errors["password_hash"] = "Parol kiritish majburiy"
            if not data.get("role"):
                errors["role"] = "Lavozimni tanlash majburiy"

        elif model_name == "User":
            if not data.get("full_name", "").strip():
                errors["full_name"] = "Ism-familiya kiritish majburiy"
            if not data.get("phone_number", "").strip():
                errors["phone_number"] = "Telefon raqam kiritish majburiy"

        return errors


class EquipmentManagerView(BaseModelView):
    """Equipment manager uchun"""

    def is_accessible(self, request: Request) -> bool:
        if not hasattr(request.state, 'role'):
            return False

        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        if is_superuser:
            return True

        return role == 'equipment_manager'


class SafetyManagerView(BaseModelView):
    """Safety manager uchun"""

    def is_accessible(self, request: Request) -> bool:
        if not hasattr(request.state, 'role'):
            return False

        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        if is_superuser:
            return True

        return role == 'safety_manager'


class ViewerView(BaseModelView):
    """Viewer uchun - faqat ko'rish"""

    def is_accessible(self, request: Request) -> bool:
        if not hasattr(request.state, 'role'):
            return False

        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        if is_superuser:
            return True

        return role == 'viewer'

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class SuperuserOnlyView(BaseModelView):
    """Faqat superuser uchun"""

    def is_accessible(self, request: Request) -> bool:
        return getattr(request.state, 'is_superuser', False)


# App va Admin yaratish
app = Starlette()
db.init()

admin = Admin(
    db._engine,
    title="ECH-10 Boshqaruv Markazi",
    base_url="/",
    auth_provider=ProfessionalAuthProvider(),
    middlewares=[
        Middleware(SessionMiddleware, secret_key="ech10-professional-secret-key-32-chars-min")
    ]
)

# Admin panel menu'lari
# 1. Tizim boshqaruvi (faqat superuser)
admin.add_view(SuperuserOnlyView(AdminUser,
                                 name="1.1 Adminlar",
                                 icon="fas fa-user-shield",
                                 label="1.1 Adminlar"))

# 2. Imtihonlar (Safety Manager + Superuser)
admin.add_view(SafetyManagerView(User,
                                 name="2.1 Xodimlar",
                                 icon="fas fa-users",
                                 label="2.1 Xodimlar"))

admin.add_view(SafetyManagerView(ExamSchedule,
                                 name="2.2 Imtihonlar",
                                 icon="fas fa-calendar-check",
                                 label="2.2 Imtihonlar"))

# 3. Test tizimi (faqat superuser)
admin.add_view(SuperuserOnlyView(CategoryTest,
                                 name="3.1 Test Kategoriyalari",
                                 icon="fas fa-tags",
                                 label="3.1 Test Kategoriyalari"))

admin.add_view(SuperuserOnlyView(Test,
                                 name="3.2 Test Savollari",
                                 icon="fas fa-question-circle",
                                 label="3.2 Test Savollari"))

admin.add_view(SuperuserOnlyView(AnswerTest,
                                 name="3.3 Test Javoblari",
                                 icon="fas fa-check-circle",
                                 label="3.3 Test Javoblari"))

# 4. Kitoblar (faqat superuser)
admin.add_view(SuperuserOnlyView(CategoryBook,
                                 name="4.1 Kitob Kategoriyalari",
                                 icon="fas fa-bookmark",
                                 label="4.1 Kitob Kategoriyalari"))

admin.add_view(SuperuserOnlyView(Book,
                                 name="4.2 Kitoblar",
                                 icon="fas fa-book",
                                 label="4.2 Kitoblar"))

# 5. Videolar (faqat superuser)
admin.add_view(SuperuserOnlyView(CategoryVideo,
                                 name="5.1 Video Kategoriyalari",
                                 icon="fas fa-folder-open",
                                 label="5.1 Video Kategoriyalari"))

admin.add_view(SuperuserOnlyView(Video,
                                 name="5.2 Videolar",
                                 icon="fas fa-play-circle",
                                 label="5.2 Videolar"))

# 6. Kompaniya ma'lumotlari (faqat superuser)
admin.add_view(SuperuserOnlyView(CompanyInfo,
                                 name="6.1 Korxona",
                                 icon="fas fa-building",
                                 label="6.1 Korxona"))

admin.add_view(SuperuserOnlyView(Channel,
                                 name="6.2 Kanallar",
                                 icon="fas fa-broadcast-tower",
                                 label="6.2 Kanallar"))

# 7. Himoya vositalari (Equipment Manager + Superuser)
admin.add_view(EquipmentManagerView(DepartmentSafety,
                                    name="7.1 HV Bo'limlari",
                                    icon="fas fa-building",
                                    label="7.1 HV Bo'limlari"))

admin.add_view(EquipmentManagerView(AreaSafety,
                                    name="7.2 HV Hududlari",
                                    icon="fas fa-map-marker-alt",
                                    label="7.2 HV Hududlari"))

admin.add_view(EquipmentManagerView(FacilitySafety,
                                    name="7.3 HV Inshootlari",
                                    icon="fas fa-warehouse",
                                    label="7.3 HV Inshootlari"))

admin.add_view(EquipmentManagerView(EquipmentCatalog,
                                    name="7.4 HV Katalogi",
                                    icon="fas fa-list-alt",
                                    label="7.4 HV Katalogi"))

admin.add_view(EquipmentManagerView(EquipmentSafety,
                                    name="7.5 Himoya Vositalari",
                                    icon="fas fa-hard-hat",
                                    label="7.5 Himoya Vositalari"))

# 8. Baxtsiz hodisalar (Safety Manager + Superuser)
admin.add_view(SafetyManagerView(AccidentCategory,
                                 name="8.1 BH Kategoriyalari",
                                 icon="fas fa-exclamation-triangle",
                                 label="8.1 BH Kategoriyalari"))

admin.add_view(SafetyManagerView(AccidentYear,
                                 name="8.2 BH Yillari",
                                 icon="fas fa-calendar",
                                 label="8.2 BH Yillari"))

admin.add_view(SafetyManagerView(Accident,
                                 name="8.3 Baxtsiz Hodisalar",
                                 icon="fas fa-file-medical",
                                 label="8.3 Baxtsiz Hodisalar"))

# 9. Poezdlar harakat xavfsizligi (faqat superuser)
admin.add_view(SuperuserOnlyView(TrainSafetyFolder,
                                 name="9.1 PHX Papkalari",
                                 icon="fas fa-folder",
                                 label="9.1 PHX Papkalari"))

admin.add_view(SuperuserOnlyView(TrainSafetyFile,
                                 name="9.2 PHX Fayllari",
                                 icon="fas fa-file-pdf",
                                 label="9.2 PHX Fayllari"))


class UserReportView(ViewerView):
    """Xodimlar hisoboti - tozalangan fields"""
    fields = ["full_name", "phone_number", "role", "language_code"]

    def is_accessible(self, request: Request) -> bool:
        if not hasattr(request.state, 'role'):
            return False

        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        # Superuser uchun ko'rinmasin
        if is_superuser:
            return False

        return role == 'viewer'


class ExamReportView(ViewerView):
    """Imtihon hisoboti - tozalangan fields"""
    fields = ["user", "last_exam", "comment"]

    def is_accessible(self, request: Request) -> bool:
        if not hasattr(request.state, 'role'):
            return False

        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        # Superuser uchun ko'rinmasin
        if is_superuser:
            return False

        return role == 'viewer'


class AccidentReportView(ViewerView):
    """BH hisoboti - tozalangan fields"""
    fields = ["title", "year", "category", "description"]

    def is_accessible(self, request: Request) -> bool:
        if not hasattr(request.state, 'role'):
            return False

        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        # Superuser uchun ko'rinmasin
        if is_superuser:
            return False

        return role == 'viewer'


class EquipmentReportView(ViewerView):
    """HV hisoboti - tozalangan fields"""
    fields = ["catalog", "serial_number", "expire_at", "is_active", "facility_safety"]

    def is_accessible(self, request: Request) -> bool:
        if not hasattr(request.state, 'role'):
            return False

        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        # Superuser uchun ko'rinmasin
        if is_superuser:
            return False

        return role == 'viewer'


admin.add_view(UserReportView(User,
                              name="10.1 Xodimlar Hisoboti",
                              identity="user_report",
                              icon="fas fa-chart-bar",
                              label="10.1 Xodimlar Hisoboti"))

admin.add_view(ExamReportView(ExamSchedule,
                              name="10.2 Imtihon Hisoboti",
                              identity="exam_report",
                              icon="fas fa-chart-line",
                              label="10.2 Imtihon Hisoboti"))

admin.add_view(AccidentReportView(Accident,
                                  name="10.3 BH Hisoboti",
                                  identity="accident_report",
                                  icon="fas fa-chart-pie",
                                  label="10.3 BH Hisoboti"))

admin.add_view(EquipmentReportView(EquipmentSafety,
                                   name="10.4 HV Hisoboti",
                                   identity="equipment_report",
                                   icon="fas fa-chart-area",
                                   label="10.4 HV Hisoboti"))

admin.mount_to(app)

if __name__ == '__main__':
    print("ECH-10 Boshqaruv Markazi ishga tushmoqda...")
    print("URL: http://localhost:8000")
    print("Super Admin: admin / Admin@2024!")
    print("ViewerView qo'shildi - 4 ta hisobot bo'limi")
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=False)