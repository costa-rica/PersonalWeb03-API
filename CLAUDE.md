# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PersonalWeb03-API is a FastAPI-based backend for managing user authentication and a markdown-driven blog system. Blog content is stored as markdown files with associated assets outside the repository in a configured directory.

## Development Commands

### Running the Application

```bash
# Start development server with auto-reload
uvicorn src.main:app --reload

# Run on specific host/port
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (required before running)
cp .env.example .env
# Edit .env with actual paths and secret key
```

### Dependencies

Core dependencies (see requirements.txt):
- fastapi==0.104.1
- uvicorn==0.24.0
- sqlalchemy==2.0.23
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4

## Architecture

### Application Structure

```
src/
├── main.py              # FastAPI app initialization, CORS, static files mounting
├── database.py          # SQLAlchemy engine, session management, init_db()
├── models.py            # SQLAlchemy ORM models (User, BlogPost)
├── schemas.py           # Pydantic validation schemas
├── auth.py              # JWT utilities, password hashing, get_current_user dependency
└── routers/
    ├── auth.py          # /auth/register, /auth/login endpoints
    ├── blog.py          # Blog CRUD endpoints
    ├── hero_section.py  # /hero-section endpoint for homepage data
    └── downloads.py     # /downloads/{filename} endpoint for downloadable files
```

### Database Models

**User** (src/models.py:10)
- Authentication with email/password_hash
- Timestamps: created_at, updated_at

**BlogPost** (src/models.py:22)
- Fields: id, title, description, post_item_image, directory_name
- Directory naming: Zero-padded 4-digit format (0001, 0002, etc.)
- Timestamps: created_at, updated_at

### Authentication System

**JWT Configuration** (src/auth.py:27)
- Tokens never expire (by design)
- Algorithm: HS256
- Subject claim: user email
- HTTPBearer security scheme

**Password Hashing** (src/auth.py:37)
- Bcrypt with 72-byte truncation limit
- Important: Passwords are truncated to 72 bytes before hashing/verification

**Protected Endpoints**
- POST /create-post
- PATCH /update-post/{post_id}
- DELETE /blog/{post_id}

Use `get_current_user` dependency for authentication.

### Blog Post System

**File Storage Architecture**
- Blog posts stored in `PATH_BLOG/posts/{directory_name}/`
- Each post requires `post.md` file
- Static assets (images, etc.) stored alongside markdown
- Static files served via FastAPI StaticFiles at `/posts`

**ZIP Upload Processing** (src/routers/blog.py:32)
1. Validates ZIP file format
2. Creates BlogPost record (gets auto-incremented ID)
3. Generates zero-padded directory name from ID
4. Extracts ZIP to `posts/{directory_name}/`
5. Removes `__MACOSX` metadata folders
6. Handles nested directories: if post.md is in a subdirectory, moves all contents to root
7. On failure: cleans up database record and filesystem directory

**Directory Name Format**
- Generated from post ID with zero-padding: `f"{post.id:04d}"`
- Examples: 0001, 0002, 0143

### Downloads System

**File Storage Architecture**
- Downloadable files stored in `PATH_PROJECT_RESOURCES/downloadable/`
- Files served via GET endpoint: `/downloads/{filename}`
- No authentication required (public downloads)

**Security Features** (src/routers/downloads.py)
- Directory traversal prevention: blocks `..`, `/`, `\` in filenames
- Path validation: ensures resolved path stays within downloadable directory
- File existence check: returns 404 if file not found
- File type check: only serves actual files (not directories)

**Behavior:**
- Returns files with `application/octet-stream` MIME type
- Original filename preserved in response
- Comprehensive logging of download requests and security violations

### Environment Variables

Required in `.env`:
- `NAME_APP` - Application name (default: PersonalWeb03API)
- `PATH_BLOG` - Absolute path to blog storage directory (must contain posts/ subdirectory)
- `PATH_PROJECT_RESOURCES` - Absolute path to project resources directory (must contain downloadable/ and hero-section/ subdirectories)
- `NAME_DB` - SQLite database filename
- `PATH_DATABASE` - Absolute path to database directory
- `JWT_SECRET_KEY` - Secret key for JWT signing (use long random string)
- `EMAIL_ADMIN_LIST` - Comma-separated list of authorized email addresses for registration (e.g., "admin@example.com,user@example.com")

### Database Initialization

Database tables are created automatically on application startup via the `@app.on_event("startup")` decorator in src/main.py:66, which calls `init_db()`.

### Logging

Comprehensive logging throughout application:
- Log level: INFO
- Outputs to: console + `personalweb03_api.log`
- Format: timestamp - name - level - message

### API Documentation

Interactive documentation available when running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### CORS Configuration

Currently configured for development with permissive settings (allow_origins=["*"]). Adjust for production use in src/main.py:44.

## Key Implementation Notes

- **JWT Tokens**: Never expire by design. Only issued_at (iat) claim is added.
- **Password Security**: Bcrypt has 72-byte limit - passwords are truncated in both hash_password() and verify_password()
- **Registration Restriction**: Only emails in EMAIL_ADMIN_LIST can register. Matching is case-insensitive. Returns JWT token upon successful registration.
- **Blog Post Deletion**: Deletes both database record and filesystem directory. Completes successfully even if filesystem deletion fails (logs warning).
- **Static File Serving**: Mounted at `/posts` path, serves directly from filesystem for blog content
- **Downloads**: Separate endpoint with security checks for downloadable files (resume, PDFs, etc.)
- **SQLite**: Uses check_same_thread=False for FastAPI compatibility
- **ZIP Handling**: Automatically flattens nested directory structures if post.md is not in root
