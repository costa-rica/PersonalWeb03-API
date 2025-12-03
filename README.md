# PersonalWeb03

## Overview

PersonalWeb03 is a FastAPI-based backend that manages user authentication and a markdown-driven blog system. Blog content is stored on the server outside the repository, organized by post ID directories.

## Features

- User authentication with JWT (tokens never expire)
- Password hashing with bcrypt
- Blog post creation from ZIP files containing markdown and assets
- Blog post metadata updates (title, description, image)
- Static file serving for blog content
- SQLite database with SQLAlchemy ORM
- Comprehensive logging

## Installation

1. Clone the repository
2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the application:
   ```bash
   uvicorn src.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token

### Blog Posts

- `POST /create-post` - Create a new blog post (requires JWT)
- `PATCH /update-post/{post_id}` - Update blog post metadata (requires JWT)
- `GET /blog` - List all blog posts
- `GET /blog/{post_id}` - Get blog post details with markdown content

### Static Files

- `/posts/{directory_name}/` - Access static blog post files

## Environment Variables

See `.env.example` for required configuration:

- `NAME_APP` - Application name
- `PATH_BLOG` - Absolute path where blog files are stored
- `NAME_DB` - Database filename
- `PATH_DATABASE` - Database directory path
- `JWT_SECRET_KEY` - Secret key for JWT signing

## Project Structure

```
PersonalWeb03-API/
├── src/
│   ├── routers/
│   │   ├── auth.py       # Authentication endpoints
│   │   └── blog.py       # Blog endpoints
│   ├── models.py         # SQLAlchemy database models
│   ├── schemas.py        # Pydantic validation schemas
│   ├── auth.py           # Authentication utilities
│   ├── database.py       # Database configuration
│   └── main.py           # FastAPI application
├── docs/
│   └── REQUIREMENTS-API.md
├── requirements.txt
├── .env
├── .env.example
└── README.md
```
