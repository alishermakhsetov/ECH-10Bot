from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin, ModelView

from db import db
from db.models import Category
from web.provider import UsernameAndPasswordProvider

app = Starlette()  # FastAPI()
# Create admin
admin = Admin(db._engine ,
            title= "P28_Admin",
            base_url= "/",
            auth_provider = UsernameAndPasswordProvider(),
            middlewares = [Middleware(SessionMiddleware, secret_key="qewrerthytju4")]
            )
# Add view
admin.add_view(ModelView(Category))
# Mount admin to your app
admin.mount_to(app)