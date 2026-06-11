from flask import Flask
from flask_cors import CORS
from config import Config
import os


def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "frontend/templates"),
        static_folder=os.path.join(base_dir, "frontend/static"),
    )
    app.config.from_object(Config)
    CORS(app)

    from app.routes.api import api
    app.register_blueprint(api)

    return app
