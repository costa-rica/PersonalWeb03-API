"""Database configuration and session management."""

import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.models import Base

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Get database configuration from environment
PATH_DATABASE = os.getenv("PATH_DATABASE")
NAME_DB = os.getenv("NAME_DB")

if not PATH_DATABASE or not NAME_DB:
    raise ValueError("PATH_DATABASE and NAME_DB must be set in .env file")

# Ensure database directory exists
db_dir = Path(PATH_DATABASE)
db_dir.mkdir(parents=True, exist_ok=True)

# Create database URL
database_path = db_dir / NAME_DB
DATABASE_URL = f"sqlite:///{database_path}"

logger.info(f"Database URL: {DATABASE_URL}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db():
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
