from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Search(Base):
    """One buyer research run for a target company."""
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True)
    target_name = Column(String(200))
    industry = Column(String(100))
    revenue_m = Column(Float)
    geography = Column(String(100))
    description = Column(Text)
    research_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    buyer_type = Column(String(50))          # "strategic" or "financial"
    rationale = Column(Text)
    contact_name = Column(String(200))
    contact_title = Column(String(200))
    confidence = Column(Integer)             # 0-100
    confidence_reasoning = Column(Text)
    source_urls = Column(Text)               # JSON-encoded list

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


# SQLite by default for easy local dev — set DATABASE_URL for Postgres in prod
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///buyeriq.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
    print("Database tables created!")
