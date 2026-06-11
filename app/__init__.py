from flask import Flask, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from config import Config
import os

login_manager = LoginManager()
oauth = OAuth()


def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "frontend/templates"),
        static_folder=os.path.join(base_dir, "frontend/static"),
    )
    app.config.from_object(Config)
    CORS(app)

    # ── Flask-Login ───────────────────────────────────────────────────────
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.models.models import SessionLocal, User

    @login_manager.user_loader
    def load_user(user_id):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == int(user_id)).first()
        finally:
            db.close()

    # ── Google OAuth (Authlib) ────────────────────────────────────────────
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    # ── Blueprints ────────────────────────────────────────────────────────
    from app.routes.api import api
    from app.routes.auth import auth
    app.register_blueprint(api)
    app.register_blueprint(auth)

    # ── Ensure tables exist (safe to call repeatedly) ─────────────────────
    from app.models.models import init_db
    init_db()

    return app