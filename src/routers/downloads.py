"""Downloads router for serving downloadable files."""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloads", tags=["Downloads"])

# Get project resources path from environment
PATH_PROJECT_RESOURCES = os.getenv("PATH_PROJECT_RESOURCES")
if not PATH_PROJECT_RESOURCES:
    raise ValueError("PATH_PROJECT_RESOURCES must be set in .env file")

# Path to downloadable files directory
DOWNLOADABLE_PATH = Path(PATH_PROJECT_RESOURCES) / "downloadable"


@router.get("/{filename}")
def download_file(filename: str):
    """
    Download a file from the downloadable directory.

    Args:
        filename: Name of the file to download

    Returns:
        FileResponse: The requested file

    Raises:
        HTTPException: If file not found or path traversal attempted
    """
    logger.info(f"Download request for file: {filename}")

    # Prevent directory traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        logger.warning(f"Potential directory traversal attempt: {filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    # Construct file path
    file_path = DOWNLOADABLE_PATH / filename

    # Check if file exists and is actually a file (not a directory)
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"File not found: {filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Ensure the resolved path is within the downloadable directory
    try:
        file_path.resolve().relative_to(DOWNLOADABLE_PATH.resolve())
    except ValueError:
        logger.warning(f"Path traversal attempt detected: {filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    logger.info(f"Serving file: {filename}")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )
