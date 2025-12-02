"""Pydantic schemas for request and response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


# Auth Schemas
class UserRegister(BaseModel):
    """Schema for user registration request."""

    email: str
    password: str

    @field_validator('email')
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        """Validate that email is not empty."""
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        return v

    @field_validator('password')
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        """Validate that password is not empty."""
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v


class UserLogin(BaseModel):
    """Schema for user login request."""

    email: str
    password: str

    @field_validator('email')
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        """Validate that email is not empty."""
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        return v

    @field_validator('password')
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        """Validate that password is not empty."""
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str


# Blog Post Schemas
class BlogPostCreate(BaseModel):
    """Schema for blog post creation request."""

    title: str


class BlogPostUpdate(BaseModel):
    """Schema for blog post update request."""

    title: Optional[str] = None
    description: Optional[str] = None
    post_item_image: Optional[str] = None


class BlogPostList(BaseModel):
    """Schema for blog post list response."""

    id: int
    title: str

    class Config:
        from_attributes = True


class BlogPostDetail(BaseModel):
    """Schema for blog post detail response."""

    id: int
    title: str
    description: Optional[str]
    post_item_image: Optional[str]
    directory_name: str
    created_at: datetime
    updated_at: datetime
    markdown_content: str

    class Config:
        from_attributes = True
