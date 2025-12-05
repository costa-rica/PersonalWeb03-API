"""Database models for PersonalWeb03API."""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BlogPost(Base):
    """Blog post model."""

    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    post_item_image = Column(String, nullable=True)
    directory_name = Column(String, nullable=True)
    date_shown_on_blog = Column(Date, default=date.today, nullable=False)
    link_to_external_post = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
