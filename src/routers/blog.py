"""Blog router for managing blog posts."""

import os
import logging
import zipfile
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from src.database import get_db
from src.models import BlogPost, User
from src.schemas import BlogPostList, BlogPostDetail, BlogPostUpdate
from src.auth import get_current_user

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Blog"])

# Get blog path from environment
PATH_BLOG = os.getenv("PATH_BLOG")
if not PATH_BLOG:
    raise ValueError("PATH_BLOG must be set in .env file")


@router.post("/create-post", status_code=status.HTTP_201_CREATED)
def create_post(
    title: str = Form(...),
    zip_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new blog post by uploading a ZIP file.

    Args:
        title: Blog post title
        zip_file: ZIP file containing post.md and assets
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: Created blog post information

    Raises:
        HTTPException: If ZIP extraction fails or post.md is missing
    """
    logger.info(f"Creating new blog post: {title}")

    # Validate ZIP file
    if not zip_file.filename.endswith('.zip'):
        logger.warning(f"Invalid file type uploaded: {zip_file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive"
        )

    # Create new blog post record
    new_post = BlogPost(
        title=title,
        directory_name=""  # Will be updated after getting ID
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Generate zero-padded directory name
    directory_name = f"{new_post.id:04d}"
    new_post.directory_name = directory_name
    db.commit()

    logger.info(f"Created blog post with ID: {new_post.id}, directory: {directory_name}")

    # Create posts directory if it doesn't exist
    posts_dir = Path(PATH_BLOG) / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    # Create post directory
    post_dir = posts_dir / directory_name
    post_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Created directory: {post_dir}")

    # Extract ZIP contents
    try:
        with zipfile.ZipFile(zip_file.file, 'r') as zip_ref:
            zip_ref.extractall(post_dir)
        logger.info(f"Extracted ZIP contents to {post_dir}")
    except zipfile.BadZipFile:
        logger.error(f"Invalid ZIP file uploaded for post {new_post.id}")
        # Clean up: delete post record and directory
        db.delete(new_post)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file"
        )

    # Clean up macOS metadata folder if it exists
    macosx_dir = post_dir / "__MACOSX"
    if macosx_dir.exists():
        shutil.rmtree(macosx_dir)
        logger.info(f"Removed __MACOSX metadata folder")

    # Find post.md (might be in a subdirectory)
    post_md_path = post_dir / "post.md"
    if not post_md_path.exists():
        # Search for post.md in subdirectories
        post_md_files = list(post_dir.rglob("post.md"))
        if not post_md_files:
            logger.error(f"post.md not found in ZIP for post {new_post.id}")
            # Clean up: delete post record and directory
            db.delete(new_post)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP file must contain post.md"
            )

        # Found post.md in a subdirectory - move all contents to root
        post_md_path = post_md_files[0]
        source_dir = post_md_path.parent
        logger.info(f"Found post.md in subdirectory: {source_dir}")

        # Move all files from subdirectory to post_dir root
        for item in source_dir.iterdir():
            dest = post_dir / item.name
            if dest.exists():
                # Skip if destination already exists (shouldn't happen normally)
                logger.warning(f"Skipping {item.name}, already exists in destination")
                continue
            shutil.move(str(item), str(dest))
            logger.debug(f"Moved {item.name} to post directory root")

        # Remove the now-empty subdirectory
        if source_dir.exists() and source_dir != post_dir:
            shutil.rmtree(source_dir)
            logger.info(f"Removed empty subdirectory: {source_dir.name}")

        # Update post_md_path to the new location
        post_md_path = post_dir / "post.md"

    logger.info(f"Blog post created successfully: {new_post.id}")
    return {
        "id": new_post.id,
        "title": new_post.title,
        "directory_name": directory_name,
        "message": "Blog post created successfully"
    }


@router.patch("/update-post/{post_id}")
def update_post(
    post_id: int,
    update_data: BlogPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update blog post metadata (title, description, post_item_image).

    Args:
        post_id: Blog post ID
        update_data: Fields to update
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: Updated blog post information

    Raises:
        HTTPException: If post not found
    """
    logger.info(f"Updating blog post {post_id}")

    # Find post
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        logger.warning(f"Blog post not found: {post_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Update fields if provided
    if update_data.title is not None:
        post.title = update_data.title
        logger.debug(f"Updated title for post {post_id}")

    if update_data.description is not None:
        post.description = update_data.description
        logger.debug(f"Updated description for post {post_id}")

    if update_data.post_item_image is not None:
        post.post_item_image = update_data.post_item_image
        logger.debug(f"Updated post_item_image for post {post_id}")

    db.commit()
    db.refresh(post)

    logger.info(f"Blog post {post_id} updated successfully")
    return {
        "id": post.id,
        "title": post.title,
        "description": post.description,
        "post_item_image": post.post_item_image,
        "message": "Blog post updated successfully"
    }


@router.get("/blog", response_model=List[BlogPostList])
def list_posts(db: Session = Depends(get_db)):
    """
    List all blog posts (id and title only).

    Args:
        db: Database session

    Returns:
        List[BlogPostList]: List of blog posts with id and title
    """
    logger.info("Fetching all blog posts")
    posts = db.query(BlogPost).all()
    logger.info(f"Found {len(posts)} blog posts")
    return posts

# GET /blog/{post_id}
@router.get("/blog/{post_id}", response_model=BlogPostDetail)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    Get detailed blog post information including markdown content.

    Args:
        post_id: Blog post ID
        db: Database session

    Returns:
        BlogPostDetail: Blog post metadata and markdown content

    Raises:
        HTTPException: If post not found or post.md missing
    """
    logger.info(f"Fetching blog post {post_id}")

    # Find post
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        logger.warning(f"Blog post not found: {post_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Read markdown content
    posts_dir = Path(PATH_BLOG) / "posts"
    post_md_path = posts_dir / post.directory_name / "post.md"

    if not post_md_path.exists():
        logger.error(f"post.md not found for post {post_id} at {post_md_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post markdown file not found"
        )

    try:
        markdown_content = post_md_path.read_text(encoding='utf-8')
        logger.info(f"Read markdown content for post {post_id}")
    except Exception as e:
        logger.error(f"Error reading markdown file for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading post content"
        )

    # Return post with markdown content
    return BlogPostDetail(
        id=post.id,
        title=post.title,
        description=post.description,
        post_item_image=post.post_item_image,
        directory_name=post.directory_name,
        created_at=post.created_at,
        updated_at=post.updated_at,
        markdown_content=markdown_content
    )
