"""Hero section router for providing homepage data."""

import os
import csv
import logging
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from dotenv import load_dotenv

from src.schemas import HeroSectionData, UpToLately, TogglTableItem

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hero-section", tags=["Hero Section"])

# Get project resources path from environment
PATH_PROJECT_RESOURCES = os.getenv("PATH_PROJECT_RESOURCES")
if not PATH_PROJECT_RESOURCES:
    raise ValueError("PATH_PROJECT_RESOURCES must be set in .env file")

# GET /hero-section/data
@router.get("/data", response_model=HeroSectionData)
def get_hero_section_data():
    """
    Get hero section data including up_to_lately text and toggl table.

    Returns:
        HeroSectionData: Hero section data with text and project hours

    Raises:
        HTTPException: If files are not found or cannot be read
    """
    logger.info("Fetching hero section data")

    hero_section_dir = Path(PATH_PROJECT_RESOURCES) / "hero-section"

    # Read up_to_lately text from markdown file
    md_file_path = hero_section_dir / "last-7-days-activities-summary.md"
    if not md_file_path.exists():
        logger.error(f"Markdown file not found: {md_file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activities summary file not found"
        )

    try:
        up_to_lately_text = md_file_path.read_text(encoding='utf-8').strip()
        logger.debug(f"Read {len(up_to_lately_text)} characters from markdown file")
    except Exception as e:
        logger.error(f"Error reading markdown file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading activities summary"
        )

    # Read and parse CSV file for toggl table
    csv_file_path = hero_section_dir / "project_time_entries.csv"
    if not csv_file_path.exists():
        logger.error(f"CSV file not found: {csv_file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project time entries file not found"
        )

    try:
        toggl_items = []
        collection_date = None

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Parse project data
                toggl_items.append(TogglTableItem(
                    project_name=row['project_name'],
                    total_hours=float(row['total_hours'])
                ))

                # Extract date from first row (all rows have same datetime_collected)
                if collection_date is None and 'datetime_collected' in row:
                    # Parse datetime and extract just the date portion
                    datetime_str = row['datetime_collected']
                    dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                    collection_date = dt.strftime('%Y-%m-%d')

        logger.info(f"Parsed {len(toggl_items)} projects from CSV")

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading project time entries"
        )

    # Sort projects alphabetically by name
    toggl_items.sort(key=lambda x: x.project_name.lower())
    logger.debug("Sorted projects alphabetically")

    # Build response
    response = HeroSectionData(
        up_to_lately=UpToLately(
            text=up_to_lately_text,
            date=collection_date or ""
        ),
        toggl_table=toggl_items
    )

    logger.info("Hero section data retrieved successfully")
    return response
