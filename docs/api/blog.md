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

---

## Accessing Blog Post Assets (Images, CSS, etc.)

Blog post assets (images, stylesheets, etc.) are served as static files directly from the filesystem.

**Base URL Pattern:**
```
GET /posts/{directory_name}/{filename}
```

### How It Works

1. **Get the blog post details** to obtain the `directory_name`:
   ```bash
   curl -X GET http://localhost:8000/blog/1
   ```

   Response includes:
   ```json
   {
     "id": 1,
     "directory_name": "0001",
     ...
   }
   ```

2. **Construct asset URLs** using the `directory_name`:
   ```
   /posts/{directory_name}/{filename}
   ```

### Examples

**Accessing an image:**
```
GET /posts/0001/hero-image.png
```

**Accessing a thumbnail image (from post_item_image):**
```json
// From GET /blog/1 response:
{
  "post_item_image": "thumbnail.jpg",
  "directory_name": "0001"
}

// Access at:
GET /posts/0001/thumbnail.jpg
```

**Accessing a CSS file:**
```
GET /posts/0001/styles.css
```

**Accessing nested assets:**
```
GET /posts/0001/images/diagram.png
GET /posts/0001/assets/logo.svg
```

### Frontend Implementation Example

```javascript
// Fetch blog post details
const response = await fetch('http://localhost:8000/blog/1');
const post = await response.json();

// Construct image URL
const imageUrl = `/posts/${post.directory_name}/hero-image.png`;

// Use in img tag
<img src={imageUrl} alt="Hero" />

// Construct thumbnail URL from metadata
if (post.post_item_image) {
  const thumbnailUrl = `/posts/${post.directory_name}/${post.post_item_image}`;
}
```

### Important Notes

- **No authentication required** - all blog assets are publicly accessible
- **Directory name format** - Always zero-padded 4 digits (0001, 0002, 0143)
- **Case-sensitive** - File paths are case-sensitive on most servers
- **Direct filesystem access** - Assets are served directly without API processing (fast performance)
- **CORS enabled** - Assets can be accessed from any origin (configured in CORS settings)
- **All file types supported** - Images (PNG, JPG, GIF, SVG), CSS, JS, fonts, etc.

### Common Asset Patterns

| Asset Type | Example Path | Usage |
|------------|--------------|-------|
| Hero Image | `/posts/0001/hero.png` | Main post image |
| Thumbnail | `/posts/0001/thumbnail.jpg` | Post list preview (stored in `post_item_image`) |
| Content Image | `/posts/0001/diagram.png` | Inline markdown image |
| Stylesheet | `/posts/0001/custom.css` | Custom post styling |
| Nested Asset | `/posts/0001/images/photo.jpg` | Organized in subdirectories |
