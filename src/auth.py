"""Authentication utilities for JWT and password hashing."""

import os
import logging
from typing import Optional
from datetime import datetime
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from src.database import get_db
from src.models import User

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in .env file")

ALGORITHM = "HS256"

# HTTP Bearer for JWT authentication
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Bcrypt has a maximum password length of 72 bytes. Passwords longer than
    this are truncated to prevent errors.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    logger.debug("Hashing password")
    # Bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password_truncated)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Bcrypt has a maximum password length of 72 bytes. Passwords longer than
    this are truncated to match the hashing behavior.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        bool: True if password matches, False otherwise
    """
    logger.debug("Verifying password")
    # Bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = plain_password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(password_truncated, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token that never expires.

    Args:
        data: Dictionary containing claims to encode in the token

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    # Add issued at timestamp
    to_encode.update({"iat": datetime.utcnow()})

    logger.info(f"Creating access token for user: {data.get('sub')}")
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Optional[dict]: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug("Token decoded successfully")
        return payload
    except JWTError as e:
        logger.warning(f"Token decode error: {e}")
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials containing JWT token
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        logger.warning("Invalid token received")
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        logger.warning("Token missing subject claim")
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"User not found: {email}")
        raise credentials_exception

    logger.info(f"User authenticated: {email}")
    return user
