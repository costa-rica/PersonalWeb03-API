"""Authentication router for user registration and login."""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User
from src.schemas import UserRegister, UserLogin, Token
from src.auth import hash_password, verify_password, create_access_token

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user and return access token.

    Args:
        user_data: User registration data (email, password)
        db: Database session

    Returns:
        Token: JWT access token for the newly registered user

    Raises:
        HTTPException: If email is not authorized or already exists
    """
    logger.info(f"Registration attempt for email: {user_data.email}")

    # Check if email is in the authorized admin list
    admin_list_str = os.getenv("EMAIL_ADMIN_LIST", "")
    if not admin_list_str:
        # If EMAIL_ADMIN_LIST is not set or empty, block all registrations
        logger.warning(f"Registration blocked: EMAIL_ADMIN_LIST not configured - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration restricted to authorized email addresses"
        )

    # Parse comma-separated email list and convert to lowercase
    authorized_emails = [email.strip().lower() for email in admin_list_str.split(",")]

    # Check if the user's email (case-insensitive) is in the authorized list
    if user_data.email.lower() not in authorized_emails:
        logger.warning(f"Registration blocked: Unauthorized email - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration restricted to authorized email addresses"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration failed: Email already exists - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token for the newly registered user
    access_token = create_access_token(data={"sub": new_user.email})

    logger.info(f"User registered successfully and logged in: {user_data.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Args:
        user_data: User login data (email, password)
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    logger.info(f"Login attempt for email: {user_data.email}")

    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        logger.warning(f"Login failed: User not found - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        logger.warning(f"Login failed: Invalid password - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    logger.info(f"User logged in successfully: {user_data.email}")
    return {"access_token": access_token, "token_type": "bearer"}
