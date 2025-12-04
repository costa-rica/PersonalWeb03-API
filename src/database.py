"""Database configuration and session management."""

import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.models import Base, User

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


def seed_admin_user():
    """
    Create default admin user from environment variables on startup.

    Creates a user with:
    - Email: First email from EMAIL_ADMIN_LIST
    - Password: PASSWORD_ADMIN

    Only creates if user doesn't already exist.
    """
    # Import here to avoid circular import
    from src.auth import hash_password

    logger.info("Checking admin user seed...")

    # Get admin credentials from environment
    admin_list_str = os.getenv("EMAIL_ADMIN_LIST", "")
    admin_password = os.getenv("PASSWORD_ADMIN", "")

    if not admin_list_str:
        logger.warning("EMAIL_ADMIN_LIST not configured, skipping admin user seed")
        return

    if not admin_password:
        logger.warning("PASSWORD_ADMIN not configured, skipping admin user seed")
        return

    # Get first email from comma-separated list
    admin_emails = [email.strip() for email in admin_list_str.split(",")]
    admin_email = admin_emails[0]

    logger.info(f"Attempting to seed admin user: {admin_email}")

    # Create database session
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == admin_email).first()

        if existing_user:
            logger.info(f"Admin user already exists: {admin_email}")
            return

        # Create admin user
        hashed_password = hash_password(admin_password)
        admin_user = User(
            email=admin_email,
            password_hash=hashed_password
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info(f"Admin user created successfully: {admin_email}")

    except Exception as e:
        logger.error(f"Failed to seed admin user: {e}")
        db.rollback()
    finally:
        db.close()


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
