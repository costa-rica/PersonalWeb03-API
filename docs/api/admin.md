# Admin Endpoints

Administrative endpoints for database backup and restore operations.

**Important:** All admin endpoints require JWT authentication.

---

## POST /admin/database/backup

Generate a backup of all database tables as a ZIP file containing CSV files.

**Authentication:** Required (JWT token)

**Sample Request:**

```bash
curl -X POST http://localhost:8000/admin/database/backup \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -O -J
```

**Response:**

Success (200 OK):
- Returns a ZIP file download
- Filename format: `db_backup_personalweb03_YYYYMMDD_HHMMSS.zip`
- Contains CSV files:
  - `user.csv` - All user records
  - `blogpost.csv` - All blog post records

**ZIP Contents:**

Each CSV file contains all fields from the respective table:

**user.csv:**
- id, email, password_hash, created_at, updated_at

**blogpost.csv:**
- id, title, description, post_item_image, directory_name, created_at, updated_at

**Error Responses:**

Error - Unauthorized (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

Error - Backup failed (500 Internal Server Error):
```json
{
  "detail": "Backup generation failed: <error details>"
}
```

**Behavior:**
- Queries all records from User and BlogPost tables
- Generates CSV files in memory
- Creates ZIP file containing all CSVs
- Returns ZIP as direct download (not saved to server)
- Includes timestamp in filename for version tracking
- Comprehensive logging of backup process

---

## POST /admin/database/restore

Restore database from a backup ZIP file containing CSV files.

**Authentication:** Required (JWT token)

**Sample Request:**

```bash
curl -X POST http://localhost:8000/admin/database/restore \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "zip_file=@db_backup_personalweb03_20250101_120000.zip"
```

**Response Examples:**

Success (200 OK):
```json
{
  "message": "Database restore completed",
  "summary": {
    "users_imported": 5,
    "users_skipped": 2,
    "posts_imported": 10,
    "posts_skipped": 1,
    "skipped_details": [
      "User ID 1: ID exists",
      "User admin@example.com: email exists",
      "BlogPost ID 3: directory 0003 exists"
    ]
  }
}
```

Error - Invalid file type (400 Bad Request):
```json
{
  "detail": "File must be a ZIP archive"
}
```

Error - Invalid ZIP (400 Bad Request):
```json
{
  "detail": "Invalid ZIP file"
}
```

Error - Unauthorized (401 Unauthorized):
```json
{
  "detail": "Could not validate credentials"
}
```

Error - Restore failed (500 Internal Server Error):
```json
{
  "detail": "Restore failed: <error details>"
}
```

**Behavior:**
- **Appends data** to existing tables (does not clear existing data)
- **ID preservation:** Uses IDs from CSV files
- **Conflict handling:**
  - Skips record if ID already exists in database
  - For User table: Skips if email already exists
  - For BlogPost table: Skips if directory_name already exists
- **Detailed logging:** All skipped records are logged with reasons
- **Transaction safety:** Commits each table separately, rollback on error
- **Summary report:** Returns counts of imported and skipped records

**Important Notes:**
- This is an **append** operation, not a replacement
- Existing data is preserved
- Duplicate IDs, emails, or directory names will be skipped
- Review `skipped_details` to understand what was not imported
- Ensure blog post directories exist on filesystem if importing posts

**Use Cases:**
1. **Migration:** Moving data from one instance to another
2. **Disaster recovery:** Restoring from backup after data loss
3. **Data synchronization:** Importing new records from another system
4. **Development/Testing:** Populating test environments with production-like data

---

## Backup/Restore Workflow Example

### Creating a Backup

```bash
# 1. Create backup
curl -X POST http://localhost:8000/admin/database/backup \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -O -J

# Downloads: db_backup_personalweb03_20250304_153000.zip
```

### Restoring from Backup

```bash
# 1. Restore from backup
curl -X POST http://localhost:8000/admin/database/restore \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "zip_file=@db_backup_personalweb03_20250304_153000.zip"

# 2. Review the summary to see what was imported/skipped
```

### Best Practices

1. **Regular backups:** Schedule periodic backups of your database
2. **Timestamp tracking:** Backup filenames include timestamps for easy identification
3. **Verify before restore:** Check backup contents before restoring
4. **Test restores:** Periodically test restore process in non-production environment
5. **Monitor skipped records:** Review `skipped_details` to ensure expected behavior
6. **Coordinate with filesystem:** Ensure blog post directories exist when restoring BlogPost records
