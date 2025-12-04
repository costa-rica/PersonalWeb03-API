"""Main FastAPI application for PersonalWeb03API."""

import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.database import init_db, seed_admin_user
from src.routers import auth, blog, hero_section, downloads, admin

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('personalweb03_api.log')
    ]
)

logger = logging.getLogger(__name__)

# Get configuration from environment
PATH_BLOG = os.getenv("PATH_BLOG")
PATH_PROJECT_RESOURCES = os.getenv("PATH_PROJECT_RESOURCES")
NAME_APP = os.getenv("NAME_APP", "PersonalWeb03API")

if not PATH_BLOG:
    raise ValueError("PATH_BLOG must be set in .env file")

if not PATH_PROJECT_RESOURCES:
    raise ValueError("PATH_PROJECT_RESOURCES must be set in .env file")

# Create FastAPI application
app = FastAPI(
    title=NAME_APP,
    description="API for managing markdown-based blog posts with user authentication",
    version="1.0.0"
)

# Configure CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(blog.router)
app.include_router(hero_section.router)
app.include_router(downloads.router)
app.include_router(admin.router)

# Ensure posts directory exists
posts_path = Path(PATH_BLOG) / "posts"
posts_path.mkdir(parents=True, exist_ok=True)
logger.info(f"Posts directory: {posts_path}")

# Ensure icons directory exists
icons_path = Path(PATH_BLOG) / "icons"
icons_path.mkdir(parents=True, exist_ok=True)
logger.info(f"Icons directory: {icons_path}")

# Ensure downloadable directory exists
downloadable_path = Path(PATH_PROJECT_RESOURCES) / "downloadable"
downloadable_path.mkdir(parents=True, exist_ok=True)
logger.info(f"Downloadable directory: {downloadable_path}")

# Mount static files for serving blog posts
app.mount("/posts", StaticFiles(directory=str(posts_path)), name="posts")
logger.info("Mounted static files at /posts")

# Mount static files for serving blog icons
app.mount("/blog/icons", StaticFiles(directory=str(icons_path)), name="blog-icons")
logger.info("Mounted static files at /blog/icons")


@app.on_event("startup")
def startup_event():
    """Initialize database and seed admin user on application startup."""
    logger.info("Starting PersonalWeb03API")
    init_db()
    logger.info("Database initialized successfully")
    seed_admin_user()
    logger.info("Admin user seed completed")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": NAME_APP,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
