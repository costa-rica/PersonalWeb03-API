"""Pydantic schemas for request and response validation."""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, field_validator, Field


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


class BlogPostCreateLink(BaseModel):
    """Schema for creating a blog post link (external post)."""

    title: str
    url: str
    icon: Optional[str] = None
    description: Optional[str] = None
    date_shown_on_blog: Optional[date] = None


class BlogPostUpdate(BaseModel):
    """Schema for blog post update request."""

    title: Optional[str] = None
    description: Optional[str] = None
    post_item_image: Optional[str] = None
    date_shown_on_blog: Optional[date] = None
    link_to_external_post: Optional[str] = None


class BlogPostList(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    post_item_image: Optional[str] = None
    url: Optional[str] = Field(
        None,
        validation_alias='link_to_external_post',
        serialization_alias='url'
    )
    display_date: date = Field(
        validation_alias='date_shown_on_blog',
        serialization_alias='date'
    )

    class Config:
        from_attributes = True
        populate_by_name = True

class BlogPostDetail(BaseModel):
    """Schema for blog post detail response."""

    id: int
    title: str
    description: Optional[str]
    post_item_image: Optional[str]
    directory_name: Optional[str]
    date_shown_on_blog: date
    link_to_external_post: Optional[str]
    created_at: datetime
    updated_at: datetime
    markdown_content: Optional[str]

    class Config:
        from_attributes = True


# Hero Section Schemas
class TogglTableItem(BaseModel):
    """Schema for a single toggl table item."""

    project_name: str
    total_hours: float


class UpToLately(BaseModel):
    """Schema for up_to_lately section."""

    text: str
    date: str


class HeroSectionData(BaseModel):
    """Schema for hero section data response."""

    up_to_lately: UpToLately
    toggl_table: list[TogglTableItem]
