"""Admin router for database backup and restore operations."""

import csv
import io
import logging
import zipfile
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, BlogPost
from src.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/database/backup")
def backup_database(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a backup of all database tables as a ZIP file containing CSV files.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse: ZIP file containing CSV files for each table

    Raises:
        HTTPException: If backup generation fails
    """
    logger.info(f"Database backup initiated by user: {current_user.email}")

    try:
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Backup User table
            users = db.query(User).all()
            logger.info(f"Backing up {len(users)} users")

            user_csv = io.StringIO()
            user_writer = csv.writer(user_csv)
            # Write header
            user_writer.writerow(['id', 'email', 'password_hash', 'created_at', 'updated_at'])
            # Write data
            for user in users:
                user_writer.writerow([
                    user.id,
                    user.email,
                    user.password_hash,
                    user.created_at.isoformat() if user.created_at else '',
                    user.updated_at.isoformat() if user.updated_at else ''
                ])

            zip_file.writestr('user.csv', user_csv.getvalue())
            logger.debug("User table backed up successfully")

            # Backup BlogPost table
            posts = db.query(BlogPost).all()
            logger.info(f"Backing up {len(posts)} blog posts")

            post_csv = io.StringIO()
            post_writer = csv.writer(post_csv)
            # Write header
            post_writer.writerow([
                'id', 'title', 'description', 'post_item_image',
                'directory_name', 'created_at', 'updated_at'
            ])
            # Write data
            for post in posts:
                post_writer.writerow([
                    post.id,
                    post.title,
                    post.description or '',
                    post.post_item_image or '',
                    post.directory_name,
                    post.created_at.isoformat() if post.created_at else '',
                    post.updated_at.isoformat() if post.updated_at else ''
                ])

            zip_file.writestr('blogpost.csv', post_csv.getvalue())
            logger.debug("BlogPost table backed up successfully")

        # Prepare ZIP for download
        zip_buffer.seek(0)

        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"db_backup_personalweb03_{timestamp}.zip"

        logger.info(f"Database backup completed successfully: {filename}")

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup generation failed: {str(e)}"
        )


@router.post("/database/restore")
def restore_database(
    zip_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore database from a backup ZIP file containing CSV files.

    Args:
        zip_file: ZIP file containing CSV backups
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: Summary of restore operation (imported and skipped records)

    Raises:
        HTTPException: If restore fails or invalid ZIP format
    """
    logger.info(f"Database restore initiated by user: {current_user.email}")

    # Validate ZIP file
    if not zip_file.filename.endswith('.zip'):
        logger.warning(f"Invalid file type uploaded: {zip_file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive"
        )

    summary = {
        "users_imported": 0,
        "users_skipped": 0,
        "posts_imported": 0,
        "posts_skipped": 0,
        "skipped_details": []
    }

    try:
        # Read ZIP file
        with zipfile.ZipFile(zip_file.file, 'r') as zip_ref:
            # Check for required CSV files
            zip_contents = zip_ref.namelist()
            logger.info(f"ZIP contents: {zip_contents}")

            # Restore User table if exists
            if 'user.csv' in zip_contents:
                logger.info("Restoring User table...")
                user_csv_data = zip_ref.read('user.csv').decode('utf-8')
                user_reader = csv.DictReader(io.StringIO(user_csv_data))

                for row in user_reader:
                    user_id = int(row['id'])
                    email = row['email']

                    # Check if ID exists
                    existing_by_id = db.query(User).filter(User.id == user_id).first()
                    if existing_by_id:
                        logger.warning(f"Skipping user ID {user_id}: ID already exists")
                        summary["users_skipped"] += 1
                        summary["skipped_details"].append(f"User ID {user_id}: ID exists")
                        continue

                    # Check if email exists
                    existing_by_email = db.query(User).filter(User.email == email).first()
                    if existing_by_email:
                        logger.warning(f"Skipping user {email}: email already exists")
                        summary["users_skipped"] += 1
                        summary["skipped_details"].append(f"User {email}: email exists")
                        continue

                    # Import user
                    new_user = User(
                        id=user_id,
                        email=email,
                        password_hash=row['password_hash']
                    )
                    # Set timestamps if available
                    if row.get('created_at'):
                        new_user.created_at = datetime.fromisoformat(row['created_at'])
                    if row.get('updated_at'):
                        new_user.updated_at = datetime.fromisoformat(row['updated_at'])

                    db.add(new_user)
                    summary["users_imported"] += 1
                    logger.debug(f"Imported user: {email}")

                db.commit()
                logger.info(f"User table restore complete: {summary['users_imported']} imported, {summary['users_skipped']} skipped")

            # Restore BlogPost table if exists
            if 'blogpost.csv' in zip_contents:
                logger.info("Restoring BlogPost table...")
                post_csv_data = zip_ref.read('blogpost.csv').decode('utf-8')
                post_reader = csv.DictReader(io.StringIO(post_csv_data))

                for row in post_reader:
                    post_id = int(row['id'])
                    directory_name = row['directory_name']

                    # Check if ID exists
                    existing_by_id = db.query(BlogPost).filter(BlogPost.id == post_id).first()
                    if existing_by_id:
                        logger.warning(f"Skipping blog post ID {post_id}: ID already exists")
                        summary["posts_skipped"] += 1
                        summary["skipped_details"].append(f"BlogPost ID {post_id}: ID exists")
                        continue

                    # Check if directory_name exists
                    existing_by_dir = db.query(BlogPost).filter(
                        BlogPost.directory_name == directory_name
                    ).first()
                    if existing_by_dir:
                        logger.warning(f"Skipping blog post {post_id}: directory {directory_name} exists")
                        summary["posts_skipped"] += 1
                        summary["skipped_details"].append(
                            f"BlogPost ID {post_id}: directory {directory_name} exists"
                        )
                        continue

                    # Import blog post
                    new_post = BlogPost(
                        id=post_id,
                        title=row['title'],
                        description=row['description'] if row['description'] else None,
                        post_item_image=row['post_item_image'] if row['post_item_image'] else None,
                        directory_name=directory_name
                    )
                    # Set timestamps if available
                    if row.get('created_at'):
                        new_post.created_at = datetime.fromisoformat(row['created_at'])
                    if row.get('updated_at'):
                        new_post.updated_at = datetime.fromisoformat(row['updated_at'])

                    db.add(new_post)
                    summary["posts_imported"] += 1
                    logger.debug(f"Imported blog post: {row['title']}")

                db.commit()
                logger.info(f"BlogPost table restore complete: {summary['posts_imported']} imported, {summary['posts_skipped']} skipped")

        logger.info(f"Database restore completed successfully: {summary}")
        return {
            "message": "Database restore completed",
            "summary": summary
        }

    except zipfile.BadZipFile:
        logger.error("Invalid ZIP file uploaded")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file"
        )
    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
        )
