"""Authentication router for user registration and login."""

import os
import logging
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError

from src.database import get_db
from src.models import User
from src.schemas import UserRegister, UserLogin, Token
from src.auth import hash_password, verify_password, create_access_token

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiting: Track reset email requests (email -> deque of timestamps)
reset_email_requests = {}

# Email configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_FROM", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", ""),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER_MSOFFICE", "smtp.gmail.com"),
    MAIL_STARTTLS=os.getenv("MAIL_TLS", "True").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL", "False").lower() == "true",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
)

fastmail = FastMail(mail_config)


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


# Pydantic schemas for password reset
class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Send password reset email to user.

    Args:
        request: Forgot password request with email
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If email not found or rate limit exceeded
    """
    logger.info(f"Password reset requested for: {request.email}")

    # Check rate limiting (max 3 emails per 5 minutes)
    now = datetime.now()
    email_lower = request.email.lower()

    if email_lower in reset_email_requests:
        # Remove timestamps older than 5 minutes
        reset_email_requests[email_lower] = deque(
            [ts for ts in reset_email_requests[email_lower] if now - ts < timedelta(minutes=5)],
            maxlen=3
        )

        # Check if limit exceeded
        if len(reset_email_requests[email_lower]) >= 3:
            logger.warning(f"Rate limit exceeded for: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many reset requests. Please try again in 5 minutes."
            )
    else:
        reset_email_requests[email_lower] = deque(maxlen=3)

    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.warning(f"Password reset failed: User not found - {request.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    # Generate reset token (JWT with 30 min expiration)
    reset_token_data = {
        "sub": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "type": "password_reset"
    }
    JWT_SECRET = os.getenv("JWT_SECRET_KEY")
    reset_token = jwt.encode(reset_token_data, JWT_SECRET, algorithm="HS256")

    # Build reset link
    base_url = os.getenv("URL_BASE_WEBSITE", "http://localhost:3000")
    reset_link = f"{base_url}/reset-password?token={reset_token}"

    # Send email
    try:
        message = MessageSchema(
            subject="Reset Your Password - PersonalWeb03",
            recipients=[request.email],
            template_body={"reset_link": reset_link},
            subtype=MessageType.html
        )

        await fastmail.send_message(message, template_name="password_reset.html")

        # Record this request
        reset_email_requests[email_lower].append(now)

        logger.info(f"Password reset email sent to: {request.email}")
        return {"message": "Password reset email sent successfully"}

    except Exception as e:
        logger.error(f"Failed to send password reset email to {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email. Please try again later."
        )


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset user password using token.

    Args:
        request: Reset password request with token and new password
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    logger.info("Password reset attempt with token")

    # Verify and decode token
    try:
        JWT_SECRET = os.getenv("JWT_SECRET_KEY")
        payload = jwt.decode(request.token, JWT_SECRET, algorithms=["HS256"])

        # Verify token type
        if payload.get("type") != "password_reset":
            logger.warning("Invalid token type for password reset")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        email = payload.get("sub")
        if not email:
            logger.warning("No email in reset token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning(f"Password reset failed: User not found - {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Hash and update password
    new_password_hash = hash_password(request.new_password)
    user.password_hash = new_password_hash
    db.commit()

    logger.info(f"Password reset successfully for: {email}")
    return {"message": "Password reset successfully"}
