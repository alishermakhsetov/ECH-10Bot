import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from sqlalchemy import select
from datetime import datetime

try:
    from utils.env_data import Config as conf
except ImportError:
    import os
    from dotenv import load_dotenv

    load_dotenv()


    class MockConfig:
        class web:
            ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
            ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "$2b$12$hash")


    conf = MockConfig()

from db import db
from db.models import AdminUser as DBAdminUser


class ProfessionalAuthProvider(AuthProvider):
    """Professional authentication with error handling"""

    async def login(self, username: str, password: str, remember_me: bool, request: Request,
                    response: Response) -> Response:

        if len(username) < 3:
            raise FormValidationError({"username": "Login kamida 3 ta belgi bo'lishi kerak"})

        try:
            # 1. Super admin (.env dan)
            if username == conf.web.ADMIN_USERNAME:
                if bcrypt.checkpw(password.encode(), conf.web.ADMIN_PASSWORD.encode()):
                    request.session.update({
                        "username": username,
                        "role": "superuser",
                        "is_superuser": True,
                        "login_time": datetime.now().isoformat()
                    })
                    return response

            # 2. Database admin'lar
            async with db.get_session() as session:
                result = await session.execute(
                    select(DBAdminUser).where(
                        DBAdminUser.username == username,
                        DBAdminUser.is_active == True
                    )
                )
                admin = result.scalar_one_or_none()

                if admin and bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
                    request.session.update({
                        "username": username,
                        "role": admin.role.value,
                        "admin_id": admin.id,
                        "is_superuser": admin.role.value == "superuser",
                        "login_time": datetime.now().isoformat()
                    })

                    admin.last_login = datetime.utcnow()
                    await session.commit()
                    return response

        except Exception as e:
            print(f"Login error: {e}")

        raise LoginFailed("Noto'g'ri login yoki parol")

    async def is_authenticated(self, request) -> bool:
        username = request.session.get("username")
        role = request.session.get("role")
        login_time = request.session.get("login_time")

        if not username or not role or not login_time:
            return False

        # Session timeout (24 soat)
        try:
            login_dt = datetime.fromisoformat(login_time)
            if (datetime.now() - login_dt).total_seconds() > 86400:
                request.session.clear()
                return False
        except:
            request.session.clear()
            return False

        request.state.user = username
        request.state.role = role
        request.state.is_superuser = request.session.get("is_superuser", False)
        return True

    def get_admin_config(self, request: Request) -> AdminConfig:
        role = getattr(request.state, 'role', None)
        is_superuser = getattr(request.state, 'is_superuser', False)

        if is_superuser:
            title = "ECH-10 Super Admin Panel"
        else:
            titles = {
                "equipment_manager": "ECH-10 Himoya Vositalari",
                "safety_manager": "ECH-10 Mehnat Muhofazasi",
                "viewer": "ECH-10 Hisobotlar"
            }
            title = titles.get(role, "ECH-10 Admin Panel")

        return AdminConfig(app_title=title)

    def get_admin_user(self, request: Request) -> AdminUser:
        username = request.state.user
        role = request.state.role
        is_superuser = request.state.is_superuser

        if is_superuser:
            display_name = f"{username} (Super Admin)"
        else:
            role_names = {
                "equipment_manager": "Himoya Vositalari",
                "safety_manager": "Xavfsizlik",
                "viewer": "Hisobotlar"
            }
            display_name = f"{username} ({role_names.get(role, role)})"

        return AdminUser(username=display_name)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response