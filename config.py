import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///buyeriq.db")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
