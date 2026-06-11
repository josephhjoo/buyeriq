from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class User(Base, UserMixin):
    """An account. Can sign in via password or Google OAuth."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    password_hash = Column(String(255))           # null if Google-only account
    google_id = Column(String(255), unique=True)  # null if password-only account
    avatar_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    searches = relationship("Search", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
        }


class Search(Base):
    """One buyer research run for a target company, owned by a user."""
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_name = Column(String(200))
    industry = Column(String(100))
    revenue_m = Column(Float)
    geography = Column(String(100))
    description = Column(Text)
    research_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="searches")
    buyers = relationship("Buyer", back_populates="search", cascade="all, delete-orphan")

    def to_dict(self, include_buyers=True):
        d = {
            "id": self.id,
            "target_name": self.target_name,
            "industry": self.industry,
            "revenue_m": self.revenue_m,
            "geography": self.geography,
            "description": self.description,
            "research_notes": self.research_notes,
            "created_at": str(self.created_at),
            "buyer_count": len(self.buyers),
        }
        if include_buyers:
            d["buyers"] = [b.to_dict() for b in self.buyers]
        return d


class Buyer(Base):
    """One potential buyer identified in a search."""
    __tablename__ = "buyers"
    id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey("searches.id"))
    firm_name = Column(String(200))
    buyer_type = Column(String(50))
    rationale = Column(Text)
    contact_name = Column(String(200))
    contact_title = Column(String(200))
    confidence = Column(Integer)
    confidence_reasoning = Column(Text)
    source_urls = Column(Text)

    search = relationship("Search", back_populates="buyers")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "firm_name": self.firm_name,
            "buyer_type": self.buyer_type,
            "rationale": self.rationale,
            "contact_name": self.contact_name,
            "contact_title": self.contact_title,
            "confidence": self.confidence,
            "confidence_reasoning": self.confidence_reasoning,
            "source_urls": json.loads(self.source_urls) if self.source_urls else [],
        }


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///buyeriq.db")
# Render (and some providers) hand out postgres:// — SQLAlchemy 2.x needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
    print("Database tables created!")