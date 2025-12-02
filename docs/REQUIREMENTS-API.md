# MarkdownBlog01API Requirements

## Overview

MarkdownBlog01API is a FastAPI-based backend that manages user
authentication and a markdown-driven blog system. Blog content is stored
on the server outside the repository, organized by post ID directories.

- Store all code in src folder
- use logging pacakge to log all actions
- use .env file to store environment variables

## Database Schema

### users Table

- id (integer, primary key, auto-increment)
- email (string, unique)
- password_hash (string)
- created_at (datetime)
- updated_at (datetime)

### blog_posts Table

- id (integer, primary key, auto-increment)
- title (string)
- description (string)
- post_item_image (string)
- directory_name (string) # zero-padded folder name (e.g., "0003")
- created_at (datetime)
- updated_at (datetime)

FastAPI with SQLAlchemy + Alembic will manage schema creation. Use SQLAlchemy event listeners or server_default timestamps for created_at and updated_at. If automation is not used, these timestamps will be manually set by the API.

## Environment Variables

- `PATH_BLOG`: Absolute path on the server where blog files are
  stored.
  - Must contain a `posts/` subdirectory.
- `NAME_DB`: Filename of the SQLite database.
- `PATH_DATABASE`: Full directory path where the database file will be created/stored.
- `JWT_SECRET`: Secret key for JWT authentication.

## Authentication

### Register

- **POST /auth/register**
- **Request:** `email`, `password`
- **Behavior:**
  - Hash password using bcrypt.\
  - Store new user in `Users` table.

### Login

- **POST /auth/login**
- **Request:** `email`, `password`
- **Behavior:**
  - Verify credentials.\
  - Return JWT access token.

## Blog Endpoints

### Create Post

- **POST /create-post**
- **Auth:** JWT required\
- **Request:**
  - `title` (string)\
  - `zip_file` (uploaded file) containing:
    - `post.md`\
    - Any images/assets\
- **Behavior:**
  - Insert new blog record in DB, receive numeric ID.\
  - Zero-pad ID to 4 digits (e.g., `0003`).\
  - Create directory: `${PATH_BLOG}/posts/0003/`.\
  - Extract ZIP contents into this directory.\
  - Store title and file path in database.

### List Blog Posts

- **GET /blog**
- **Response:**
  - List of `{id, title}` based on DB entries.

### Get Blog Post Content

- **GET /blog/{id}**
- **Response:**
  - Markdown and metadata for specified post.\
  - Files served statically at `/posts/{id}/`.

## Static File Serving

FastAPI will mount the posts directory:

    app.mount("/posts", StaticFiles(directory=f"{PATH_BLOG}/posts"), name="posts")

This exposes markdown and image assets as static URLs.
