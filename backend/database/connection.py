"""
backend/database/connection.py
───────────────────────────────
SQLAlchemy async database connection for PostgreSQL.
Reads connection params from .env file.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost/sih1605"     # Default for local Mac setup
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Database connected: {DATABASE_URL}")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
