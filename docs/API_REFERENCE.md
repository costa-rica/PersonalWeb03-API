# API Reference - MarkdownBlog01 API

Version: 1.0.0

Base URL: `http://localhost:8000`

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [General](#general)
  - [Authentication](#authentication-endpoints)
  - [Blog Posts](#blog-posts)
  - [Static Files](#static-files)
- [Data Models](#data-models)
- [Error Responses](#error-responses)

## Overview

The MarkdownBlog01 API is a FastAPI-based backend for managing user authentication and a markdown-driven blog system. Blog content is stored as markdown files with associated assets in a structured directory system.

### Key Features

- JWT-based authentication (tokens never expire)
- Password hashing with bcrypt
- Blog post creation from ZIP archives
- Markdown content management
- Static file serving for blog assets
- SQLite database with SQLAlchemy ORM

## Authentication

Most blog management endpoints require authentication using JWT (JSON Web Tokens).

### How to Authenticate

1. Register a new user account using `POST /auth/register`
2. Login using `POST /auth/login` to receive a JWT token
3. Include the token in subsequent requests using the Authorization header:

```
Authorization: Bearer <your_token_here>
```

### Protected Endpoints

The following endpoints require authentication:
- `POST /create-post`
- `PATCH /update-post/{post_id}`

## Endpoints

### General

#### Get Root Information

```http
GET /
```

Returns basic API information.

**Response** (200 OK):
```json
{
  "name": "MarkdownBlog01API",
  "version": "1.0.0",
  "status": "running"
}
```

#### Health Check

```http
GET /health
```

Checks if the API is healthy and running.

**Response** (200 OK):
```json
{
  "status": "healthy"
}
```

---

### Authentication Endpoints

#### Register User

```http
POST /auth/register
```

Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "your_secure_password"
}
```

**Response** (201 Created):
```json
{
  "message": "User registered successfully",
  "email": "user@example.com"
}
```

**Error Responses**:
- `400 Bad Request` - Email already registered
- `422 Unprocessable Entity` - Invalid email format or missing fields

**Example**:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

#### Login

```http
POST /auth/login
```

Authenticate and receive a JWT token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "your_secure_password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized` - Invalid credentials
- `422 Unprocessable Entity` - Invalid email format or missing fields

**Example**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

---

### Blog Posts

#### Create Blog Post

```http
POST /create-post
```

Create a new blog post by uploading a ZIP file containing `post.md` and any associated assets.

**Authentication**: Required

**Request**:
- Content-Type: `multipart/form-data`
- Form fields:
  - `title` (string, required): Blog post title
  - `zip_file` (file, required): ZIP archive containing post.md and assets

**ZIP File Requirements**:
- Must contain a `post.md` file in the root
- Can contain additional assets (images, etc.)
- Must be a valid ZIP archive

**Response** (201 Created):
```json
{
  "id": 1,
  "title": "My First Blog Post",
  "directory_name": "0001",
  "message": "Blog post created successfully"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid ZIP file or missing post.md
- `401 Unauthorized` - Missing or invalid authentication token
- `422 Unprocessable Entity` - Missing required fields

**Example**:
```bash
curl -X POST http://localhost:8000/create-post \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "title=My First Blog Post" \
  -F "zip_file=@/path/to/post.zip"
```

**Notes**:
- Post directories are created with zero-padded IDs (0001, 0002, etc.)
- The directory name is automatically generated based on the post ID
- If the ZIP is invalid or post.md is missing, the post record and directory are cleaned up

#### Update Blog Post

```http
PATCH /update-post/{post_id}
```

Update blog post metadata (title, description, or post_item_image).

**Authentication**: Required

**Path Parameters**:
- `post_id` (integer): Blog post ID

**Request Body** (all fields optional):
```json
{
  "title": "Updated Blog Post Title",
  "description": "A brief description of the blog post",
  "post_item_image": "thumbnail.jpg"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Updated Blog Post Title",
  "description": "A brief description of the blog post",
  "post_item_image": "thumbnail.jpg",
  "message": "Blog post updated successfully"
}
```

**Error Responses**:
- `404 Not Found` - Blog post not found
- `401 Unauthorized` - Missing or invalid authentication token
- `422 Unprocessable Entity` - Invalid request body

**Example**:
```bash
curl -X PATCH http://localhost:8000/update-post/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Updated Title",
    "description": "New description"
  }'
```

**Notes**:
- Only provided fields will be updated
- The `post_item_image` should reference an image file included in the original ZIP upload

#### List All Blog Posts

```http
GET /blog
```

Retrieve a list of all blog posts (ID and title only).

**Authentication**: Not required

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "title": "My First Blog Post"
  },
  {
    "id": 2,
    "title": "Another Great Post"
  }
]
```

**Example**:
```bash
curl -X GET http://localhost:8000/blog
```

#### Get Blog Post Details

```http
GET /blog/{post_id}
```

Get detailed information about a specific blog post, including the full markdown content.

**Authentication**: Not required

**Path Parameters**:
- `post_id` (integer): Blog post ID

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "My First Blog Post",
  "description": "A brief description of the post",
  "post_item_image": "thumbnail.jpg",
  "directory_name": "0001",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "markdown_content": "# Welcome\n\nThis is my first blog post..."
}
```

**Error Responses**:
- `404 Not Found` - Blog post not found or post.md file missing
- `500 Internal Server Error` - Error reading markdown file

**Example**:
```bash
curl -X GET http://localhost:8000/blog/1
```

---

### Static Files

#### Access Blog Post Assets

```http
GET /posts/{directory_name}/{file_path}
```

Serve static files from blog post directories (images, stylesheets, etc.).

**Authentication**: Not required

**Path Parameters**:
- `directory_name` (string): The post directory name (e.g., "0001")
- `file_path` (string): Relative path to the file within the post directory

**Example**:
```
http://localhost:8000/posts/0001/images/photo.jpg
http://localhost:8000/posts/0001/styles.css
```

**Notes**:
- Files are served directly from the filesystem
- This endpoint is mounted as a static file server
- All files within the post directory are accessible

---

## Data Models

### User

```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Fields**:
- `id` (integer): Unique user identifier
- `email` (string): User email address (unique)
- `created_at` (datetime): Account creation timestamp
- `updated_at` (datetime): Last update timestamp
- `password_hash` (string): Hashed password (never exposed in responses)

### Blog Post

```json
{
  "id": 1,
  "title": "My Blog Post",
  "description": "Post description",
  "post_item_image": "thumbnail.jpg",
  "directory_name": "0001",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Fields**:
- `id` (integer): Unique post identifier
- `title` (string): Blog post title
- `description` (string, nullable): Brief description of the post
- `post_item_image` (string, nullable): Thumbnail image filename
- `directory_name` (string): Zero-padded directory name (e.g., "0001")
- `created_at` (datetime): Post creation timestamp
- `updated_at` (datetime): Last update timestamp

### JWT Token

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Fields**:
- `access_token` (string): JWT token for authentication
- `token_type` (string): Always "bearer"

**Token Payload**:
```json
{
  "sub": "user@example.com"
}
```

**Note**: Tokens in this system never expire. Consider implementing token expiration for production use.

---

## Error Responses

The API uses standard HTTP status codes and returns error details in JSON format.

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data or malformed request
- `401 Unauthorized` - Authentication required or invalid credentials
- `404 Not Found` - Requested resource not found
- `422 Unprocessable Entity` - Validation error in request body
- `500 Internal Server Error` - Server-side error

### Example Error Responses

**400 Bad Request**:
```json
{
  "detail": "Email already registered"
}
```

**401 Unauthorized**:
```json
{
  "detail": "Invalid credentials"
}
```

**404 Not Found**:
```json
{
  "detail": "Blog post not found"
}
```

**422 Unprocessable Entity**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Interactive Documentation

The API provides interactive documentation through:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to explore and test API endpoints directly from your browser.

---

## Environment Configuration

The following environment variables are required:

```env
NAME_APP=MarkdownBlog01API
PATH_BLOG=/absolute/path/to/blog/storage
NAME_DB=markdownblog.db
PATH_DATABASE=/absolute/path/to/database
JWT_SECRET_KEY=your-secret-key-here
```

See `.env.example` for a complete configuration template.

---

## CORS Configuration

The API is configured with permissive CORS settings for development:

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

**Note**: Configure appropriate origins for production use.

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider adding rate limiting for production deployments.

---

## Versioning

Current API version: **1.0.0**

The version is included in the root endpoint response and API documentation.

---

## Support

For issues and questions:
- Check the main README.md for setup instructions
- Review the interactive documentation at `/docs`
- Examine application logs: `markdownblog01_api.log`
