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

## POST /blog/create-post-link

Create a new blog post link (external post) without uploading files. This is used for linking to external blog posts (e.g., Medium, Dev.to).

**Authentication:** Required (JWT token)

**Sample Request:**

```bash
curl -X POST http://localhost:8000/blog/create-post-link \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Medium Blog Post",
    "url": "https://medium.com/@user/my-post",
    "icon": "medium-icon.svg",
    "description": "Check out my latest post on Medium",
    "date_shown_on_blog": "2025-12-04"
  }'
```

**Request Body Fields:**

Required:
- `title` (string) - Blog post title
- `url` (string) - URL to the external post

Optional:
- `icon` (string) - Icon filename (from `/blog/icons` directory)
- `description` (string) - Brief description
- `date_shown_on_blog` (date) - Date to show on blog (defaults to today)

**Response Examples:**

Success (201 Created):
```json
{
  "id": 5,
  "title": "My Medium Blog Post",
  "link_to_external_post": "https://medium.com/@user/my-post",
  "post_item_image": "medium-icon.svg",
  "message": "Blog post link created successfully"
}
```

Error - Unauthorized (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

**Behavior:**
- Post ID is auto-generated
- `directory_name` is set to `null` (no files stored on server)
- `url` parameter maps to `link_to_external_post` field
- `icon` parameter maps to `post_item_image` field
- Icon file should exist in the icons directory (no validation performed)
- If `date_shown_on_blog` is not provided, today's date is used
- No ZIP file or markdown content required

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
- `post_item_image` (string) - Filename of thumbnail image or icon
- `date_shown_on_blog` (date) - Date to display on blog (format: YYYY-MM-DD)
- `link_to_external_post` (string) - URL to external blog post

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

Retrieve a list of all blog posts with metadata.

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
    "title": "My First Blog Post",
    "description": "A brief description of the post",
    "post_item_image": "thumbnail.jpg",
    "url": null,
    "date": "2024-01-15"
  },
  {
    "id": 2,
    "title": "Another Great Post",
    "description": "Another post description",
    "post_item_image": null,
    "url": null,
    "date": "2024-01-20"
  },
  {
    "id": 5,
    "title": "My Medium Article",
    "description": "Check out my post on Medium",
    "post_item_image": "medium-icon.svg",
    "url": "https://medium.com/@user/article",
    "date": "2024-12-04"
  }
]
```

**Response Fields:**
- `id` (integer) - Blog post ID
- `title` (string) - Blog post title
- `description` (string, nullable) - Brief description
- `post_item_image` (string, nullable) - Thumbnail image or icon filename
- `url` (string, nullable) - URL to external post (null for local posts)
- `date` (date) - Date to display on blog (format: YYYY-MM-DD)

**Behavior:**
- Returns all blog posts (both local and external link posts)
- Local posts have `url` as `null`
- External link posts have `url` populated with the external URL
- All fields except `id`, `title`, and `date` are nullable

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

Success (200 OK) - Regular blog post:
```json
{
  "id": 1,
  "title": "My First Blog Post",
  "description": "A brief description of the post",
  "post_item_image": "thumbnail.jpg",
  "directory_name": "0001",
  "date_shown_on_blog": "2024-01-15",
  "link_to_external_post": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "markdown_content": "# Welcome\n\nThis is my first blog post..."
}
```

Success (200 OK) - External link post:
```json
{
  "id": 5,
  "title": "My Medium Article",
  "description": "Check out my post on Medium",
  "post_item_image": "medium-icon.svg",
  "directory_name": null,
  "date_shown_on_blog": "2024-12-04",
  "link_to_external_post": "https://medium.com/@user/article",
  "created_at": "2024-12-04T10:30:00",
  "updated_at": "2024-12-04T10:30:00",
  "markdown_content": null
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
- For link posts (where `directory_name` is null), `markdown_content` will be null

---

## GET /blog/icons

Get a list of all available icon files in the icons directory.

**Authentication:** Required (JWT token)

**Sample Request:**

```bash
curl -X GET http://localhost:8000/blog/icons \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response Examples:**

Success (200 OK):
```json
{
  "icons": [
    "dev-to-icon.svg",
    "github-icon.svg",
    "medium-icon.svg",
    "twitter-icon.png"
  ]
}
```

Empty directory (200 OK):
```json
{
  "icons": []
}
```

Error - Unauthorized (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

**Behavior:**
- Returns only image files (png, jpg, jpeg, gif, svg, webp, ico, bmp)
- Results are sorted alphabetically
- Icon files should be placed in `PATH_BLOG/icons/` directory
- Used for selecting icons when creating link posts with POST `/blog/create-post-link`
- Icons are publicly accessible at `/blog/icons/{filename}` once uploaded

**Usage Example:**

1. Get list of available icons:
   ```bash
   GET /blog/icons
   ```

2. Use an icon when creating a link post:
   ```bash
   POST /blog/create-post-link
   {
     "title": "My External Post",
     "url": "https://example.com/post",
     "icon": "medium-icon.svg"  // from the icons list
   }
   ```

3. Icon will be accessible at:
   ```
   GET /blog/icons/medium-icon.svg
   ```

---

## DELETE /blog/{post_id}

Delete a blog post and all its associated files.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `post_id` (integer) - Blog post ID

**Sample Request:**

```bash
curl -X DELETE http://localhost:8000/blog/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response Examples:**

Success (200 OK):
```json
{
  "message": "Blog post deleted successfully",
  "id": 1
}
```

Error - Not found (404 Not Found):
```json
{
  "detail": "Blog post not found"
}
```

Error - Unauthorized (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

**Behavior:**
- Deletes blog post record from database
- Removes the entire post directory and all its files from filesystem
- If directory doesn't exist but database record exists, still deletes the database record (cleanup)
- If filesystem deletion fails but database deletion succeeds, operation completes successfully (logs warning)
- Cannot be undone - deleted posts and files are permanently removed

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

---

## Accessing Blog Icons

Blog icons are served as static files directly from the icons directory. These are typically used for external blog post links.

**Base URL Pattern:**
```
GET /blog/icons/{filename}
```

### How It Works

1. **Upload icon files** to the `PATH_BLOG/icons/` directory on the server
2. **Get list of available icons** using the API:
   ```bash
   GET /blog/icons  # Requires authentication
   ```

3. **Access icons** directly via static URL:
   ```
   GET /blog/icons/{filename}  # No authentication required
   ```

### Examples

**Accessing a Medium icon:**
```
GET /blog/icons/medium-icon.svg
```

**Accessing a GitHub icon:**
```
GET /blog/icons/github-icon.png
```

**Using in link posts:**
```json
// Create a link post with an icon
POST /blog/create-post-link
{
  "title": "My Medium Article",
  "url": "https://medium.com/@user/article",
  "icon": "medium-icon.svg"
}

// Icon is accessible at:
GET /blog/icons/medium-icon.svg
```

### Frontend Implementation Example

```javascript
// Fetch available icons (requires auth)
const response = await fetch('http://localhost:8000/blog/icons', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const { icons } = await response.json();
// ["medium-icon.svg", "github-icon.svg", ...]

// Use icon in img tag (no auth needed for display)
const iconUrl = `/blog/icons/${icons[0]}`;
<img src={iconUrl} alt="Icon" />

// Or display icon from blog post metadata
const post = await fetch('/blog/5').then(r => r.json());
if (post.post_item_image) {
  const iconUrl = `/blog/icons/${post.post_item_image}`;
}
```

### Important Notes

- **No authentication required for display** - icons are publicly accessible at `/blog/icons/{filename}`
- **Authentication required for listing** - `GET /blog/icons` requires JWT token
- **Supported formats** - PNG, JPG, JPEG, GIF, SVG, WEBP, ICO, BMP
- **Icon directory** - All icons stored in `PATH_BLOG/icons/` directory
- **CORS enabled** - Icons can be accessed from any origin
- **Use case** - Primarily for external blog post links created via `POST /blog/create-post-link`

### Comparison: Blog Icons vs Blog Post Assets

| Feature | Blog Icons | Blog Post Assets |
|---------|-----------|------------------|
| **Location** | `/blog/icons/` | `/posts/{directory_name}/` |
| **Purpose** | Icons for external posts | Content for local posts |
| **Upload Method** | Manual upload to server | ZIP upload via API |
| **URL Pattern** | `/blog/icons/{filename}` | `/posts/{directory_name}/{filename}` |
| **Listing API** | `GET /blog/icons` (auth required) | No listing endpoint |
| **Access** | Public (no auth) | Public (no auth) |
