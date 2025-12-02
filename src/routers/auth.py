"""Authentication router for user registration and login."""

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


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_data: User registration data (email, password)
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If email already exists
    """
    logger.info(f"Registration attempt for email: {user_data.email}")

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

    logger.info(f"User registered successfully: {user_data.email}")
    return {"message": "User registered successfully", "email": user_data.email}


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
