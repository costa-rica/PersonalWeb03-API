# API Reference - PersonalWeb03 API

Version: 1.0.0
Base URL: `http://localhost:8000`

## Overview

The PersonalWeb03 API is a FastAPI-based backend for managing user authentication and a markdown-driven blog system. Blog content is stored as markdown files with associated assets in a structured directory system.

### Key Features

- JWT-based authentication (tokens never expire)
- Password hashing with bcrypt
- Blog post creation from ZIP archives
- Markdown content management
- Hero section data for homepage
- Static file serving for blog assets
- SQLite database with SQLAlchemy ORM

### Interactive Documentation

The API provides interactive documentation through:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## API Endpoints by Router

### Authentication
[Authentication Endpoints](./api/auth.md) - User registration and login

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token

### Blog
[Blog Endpoints](./api/blog.md) - Blog post management

- `POST /create-post` - Create a new blog post (requires JWT)
- `PATCH /update-post/{post_id}` - Update blog post metadata (requires JWT)
- `GET /blog` - List all blog posts
- `GET /blog/{post_id}` - Get blog post details with markdown content

### Hero Section
[Hero Section Endpoints](./api/hero-section.md) - Homepage data

- `GET /hero-section/data` - Get hero section data with activity summary and project hours

### Static Files

- `/posts/{directory_name}/{file_path}` - Access static blog post files (images, CSS, etc.)

---

## Authentication

Most blog management endpoints require authentication using JWT (JSON Web Tokens).

### How to Authenticate

1. Register a new user account using `POST /auth/register`
2. Login using `POST /auth/login` to receive a JWT token
3. Include the token in subsequent requests using the Authorization header:

```
Authorization: Bearer <your_token_here>
```

### Token Characteristics

- Tokens never expire in this system
- Token payload contains user email in the `sub` claim
- Algorithm: HS256

---

## Common Response Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data or malformed request
- `401 Unauthorized` - Authentication required or invalid credentials
- `404 Not Found` - Requested resource not found
- `422 Unprocessable Entity` - Validation error in request body
- `500 Internal Server Error` - Server-side error

---

## Environment Configuration

The following environment variables are required (see `.env.example`):

```env
NAME_APP=PersonalWeb03API
PATH_BLOG=/absolute/path/to/blog/storage
PATH_PROJECT_RESOURCES=/absolute/path/to/project/resources
NAME_DB=personalweb03.db
PATH_DATABASE=/absolute/path/to/database
JWT_SECRET_KEY=your-secret-key-here
```

---

## CORS Configuration

The API is configured with permissive CORS settings for development:

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

**Note:** Configure appropriate origins for production use.

---

## Documentation Guidelines

When documenting new endpoints in the individual router files, follow these guidelines:

### Required Sections

1. **Endpoint Heading** - HTTP method and path (e.g., `## POST /articles/endpoint-name`)
2. **Brief Description** - One sentence describing what the endpoint does
3. **Authentication** - `**Authentication:** Required (JWT token)` or `Not required`
4. **Sample Request** - curl example showing typical usage with headers and body
5. **Response Examples** - Success response (200) and relevant error responses (400, 404, 500)
6. **Behavior** (optional) - Key points about how the endpoint works, special logic, or important notes

### Optional Sections

- **Request Body Fields** - Table of parameters (if complex)
- **Response Fields** - Description of response structure (if complex)
- **URL Parameters** - For parameterized routes

### Format Guidelines

- Keep descriptions **concise** - avoid verbose explanations
- Use **code blocks** for all JSON examples
- Include **realistic data** in examples
- Use **tables** for parameter lists
- Keep **bullet points brief** in Behavior sections

### Anti-patterns to Avoid

- ❌ Long prose explanations
- ❌ Multiple redundant examples
- ❌ Excessive "Important Notes" sections
- ❌ Verbose field descriptions
- ❌ Integration code examples (unless truly necessary)

---

## Support

For issues and questions:
- Check the main README.md for setup instructions
- Review the interactive documentation at `/docs`
- Examine application logs: `personalweb03_api.log`
