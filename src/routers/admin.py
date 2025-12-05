"""Admin router for database backup and restore operations."""

import csv
import io
import logging
import zipfile
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User, BlogPost
from src.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


def parse_flexible_date(date_string: str) -> Optional[date]:
    """
    Parse a date string in various common formats and return a date object.

    Supports formats like:
    - ISO: YYYY-MM-DD (2025-12-04)
    - US: MM/DD/YY (12/4/25)
    - US: MM/DD/YYYY (12/04/2025)
    - US: M/D/YY (1/5/25)
    - US: M/D/YYYY (1/5/2025)
    - Hyphenated: MM-DD-YYYY (12-04-2025)

    Args:
        date_string: Date string to parse

    Returns:
        date object if parsing successful, None if empty string

    Raises:
        ValueError: If date string cannot be parsed in any known format
    """
    if not date_string or not date_string.strip():
        return None

    date_string = date_string.strip()

    # List of date formats to try
    formats = [
        '%Y-%m-%d',      # ISO: 2025-12-04
        '%m/%d/%y',      # US: 12/4/25
        '%m/%d/%Y',      # US: 12/04/2025
        '%m-%d-%Y',      # Hyphenated: 12-04-2025
        '%m-%d-%y',      # Hyphenated: 12-04-25
        '%Y/%m/%d',      # Alternative ISO: 2025/12/04
        '%d/%m/%Y',      # European: 04/12/2025
        '%d-%m-%Y',      # European: 04-12-2025
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_string, fmt).date()
            logger.debug(f"Successfully parsed '{date_string}' using format '{fmt}' -> {parsed_date}")
            return parsed_date
        except ValueError:
            continue

    # If no format worked, raise an error
    raise ValueError(f"Could not parse date string '{date_string}' in any known format")


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

            zip_file.writestr('db_backup/user.csv', user_csv.getvalue())
            logger.debug("User table backed up successfully")

            # Backup BlogPost table
            posts = db.query(BlogPost).all()
            logger.info(f"Backing up {len(posts)} blog posts")

            post_csv = io.StringIO()
            post_writer = csv.writer(post_csv)
            # Write header
            post_writer.writerow([
                'id', 'title', 'description', 'post_item_image',
                'directory_name', 'date_shown_on_blog', 'link_to_external_post',
                'created_at', 'updated_at'
            ])
            # Write data
            for post in posts:
                post_writer.writerow([
                    post.id,
                    post.title,
                    post.description or '',
                    post.post_item_image or '',
                    post.directory_name or '',
                    post.date_shown_on_blog.isoformat() if post.date_shown_on_blog else '',
                    post.link_to_external_post or '',
                    post.created_at.isoformat() if post.created_at else '',
                    post.updated_at.isoformat() if post.updated_at else ''
                ])

            zip_file.writestr('db_backup/blogpost.csv', post_csv.getvalue())
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

            # Filter out __MACOSX and find CSV files in db_backup* folders
            def find_csv_file(csv_name):
                """Find CSV file in db_backup* or database_backup* folder, ignoring __MACOSX."""
                logger.debug(f"Looking for: {csv_name}")
                candidates = []

                for path in zip_contents:
                    # Skip __MACOSX folders
                    if '__MACOSX' in path:
                        logger.debug(f"Skipping __MACOSX: {path}")
                        continue

                    # Look for csv files in folders starting with db_backup or database_backup
                    if path.endswith(f'/{csv_name}'):
                        if path.startswith('db_backup') or path.startswith('database_backup'):
                            logger.debug(f"Found candidate: {path}")
                            candidates.append(path)

                    # Also check root level for backwards compatibility
                    if path == csv_name:
                        logger.debug(f"Found at root level: {path}")
                        return path

                if candidates:
                    selected = candidates[0]
                    logger.info(f"Selected CSV path: {selected}")
                    return selected

                logger.warning(f"Could not find {csv_name} in ZIP. Searched for files ending with '/{csv_name}' in folders starting with 'db_backup' or 'database_backup'")
                return None

            # Find user.csv
            user_csv_path = find_csv_file('user.csv')
            if user_csv_path:
                logger.info(f"Restoring User table from: {user_csv_path}")
                user_csv_data = zip_ref.read(user_csv_path).decode('utf-8')
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
            blogpost_csv_path = find_csv_file('blogpost.csv')
            if blogpost_csv_path:
                logger.info(f"Restoring BlogPost table from: {blogpost_csv_path}")
                post_csv_data = zip_ref.read(blogpost_csv_path).decode('utf-8')
                post_reader = csv.DictReader(io.StringIO(post_csv_data))

                for row in post_reader:
                    post_id = int(row['id'])
                    directory_name = row['directory_name'] if row['directory_name'] else None

                    # Check if ID exists
                    existing_by_id = db.query(BlogPost).filter(BlogPost.id == post_id).first()
                    if existing_by_id:
                        logger.warning(f"Skipping blog post ID {post_id}: ID already exists")
                        summary["posts_skipped"] += 1
                        summary["skipped_details"].append(f"BlogPost ID {post_id}: ID exists")
                        continue

                    # Check if directory_name exists (only if not null)
                    if directory_name:
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
                        directory_name=directory_name,
                        link_to_external_post=row.get('link_to_external_post') if row.get('link_to_external_post') else None
                    )
                    # Set date_shown_on_blog if available, otherwise use default
                    if row.get('date_shown_on_blog'):
                        parsed_date = parse_flexible_date(row['date_shown_on_blog'])
                        if parsed_date:
                            new_post.date_shown_on_blog = parsed_date
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
