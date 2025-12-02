"""Pydantic schemas for request and response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Auth Schemas
class UserRegister(BaseModel):
    """Schema for user registration request."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login request."""

    email: EmailStr
    password: str


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
