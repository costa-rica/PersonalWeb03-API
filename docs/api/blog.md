# Blog Endpoints

## POST /create-post

Create a new blog post by uploading a ZIP file containing markdown and assets.

**Authentication:** Required (JWT token)

**Sample Request:**

```bash
curl -X POST http://localhost:8000/create-post \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "title=My First Blog Post" \
  -F "zip_file=@/path/to/post.zip"
```

**ZIP File Requirements:**
- Must contain `post.md` in root or subdirectory
- Can include assets (images, CSS, etc.)
- Must be valid ZIP format

**Response Examples:**

Success (201 Created):
```json
{
  "id": 1,
  "title": "My First Blog Post",
  "directory_name": "0001",
  "message": "Blog post created successfully"
}
```

Error - Invalid ZIP (400 Bad Request):
```json
{
  "detail": "Invalid ZIP file"
}
```

Error - Missing post.md (400 Bad Request):
```json
{
  "detail": "ZIP file must contain post.md"
}
```

Error - Unauthorized (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

**Behavior:**
- Post ID is auto-generated and used to create zero-padded directory (0001, 0002, etc.)
- If post.md is in a subdirectory, all contents are moved to root level
- `__MACOSX` metadata folders are automatically removed
- On failure, database record and directory are cleaned up
- Static files are accessible at `/posts/{directory_name}/{file_path}`

---

## PATCH /update-post/{post_id}

Update blog post metadata (title, description, or thumbnail image).

**Authentication:** Required (JWT token)

**URL Parameters:**
- `post_id` (integer) - Blog post ID

**Sample Request:**

```bash
curl -X PATCH http://localhost:8000/update-post/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Updated Title",
    "description": "A brief description of this post",
    "post_item_image": "thumbnail.jpg"
  }'
```

**Request Body Fields:**

All fields are optional:
- `title` (string) - Blog post title
- `description` (string) - Brief description
- `post_item_image` (string) - Filename of thumbnail image

**Response Examples:**

Success (200 OK):
```json
{
  "id": 1,
  "title": "My Updated Title",
  "description": "A brief description of this post",
  "post_item_image": "thumbnail.jpg",
  "message": "Blog post updated successfully"
}
```

Error - Not found (404 Not Found):
```json
{
  "detail": "Blog post not found"
}
```

**Behavior:**
- Only provided fields are updated
- `post_item_image` should reference a file in the post's ZIP upload

---

## GET /blog

Retrieve a list of all blog posts (ID and title only).

**Authentication:** Not required

**Sample Request:**

```bash
curl -X GET http://localhost:8000/blog
```

**Response Examples:**

Success (200 OK):
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

---

## GET /blog/{post_id}

Get detailed blog post information including full markdown content.

**Authentication:** Not required

**URL Parameters:**
- `post_id` (integer) - Blog post ID

**Sample Request:**

```bash
curl -X GET http://localhost:8000/blog/1
```

**Response Examples:**

Success (200 OK):
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

Error - Not found (404 Not Found):
```json
{
  "detail": "Blog post not found"
}
```

Error - Missing markdown file (404 Not Found):
```json
{
  "detail": "Post markdown file not found"
}
```

**Behavior:**
- Returns complete post metadata plus markdown file contents
- Reads `post.md` from filesystem at request time
