from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Check for DATABASE_URL environment variable (Railway PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Railway provides postgresql:// but SQLAlchemy needs postgresql+psycopg2://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Create SQLAlchemy engine for PostgreSQL
    engine = create_engine(DATABASE_URL)
else:
    # Fallback to SQLite for local development
    BACKEND_DIR = Path(__file__).parent.parent
    DATABASE_PATH = BACKEND_DIR / "hedge_fund.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

    # Create SQLAlchemy engine for SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 