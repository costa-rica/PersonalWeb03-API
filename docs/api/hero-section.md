# Hero Section Endpoints

## GET /hero-section/data

Get hero section data for homepage including recent activity summary and project time tracking.

**Authentication:** Not required

**Sample Request:**

```bash
curl -X GET http://localhost:8000/hero-section/data
```

**Response Examples:**

Success (200 OK):
```json
{
  "up_to_lately": {
    "text": "Working on PersonalWeb03 API development and documentation improvements. Implemented new hero section endpoint with Toggl integration.",
    "date": "2025-12-01"
  },
  "toggl_table": [
    {
      "project_name": "KM work",
      "total_hours": 4.39
    },
    {
      "project_name": "Search for work",
      "total_hours": 2.1
    },
    {
      "project_name": "Sharpening the Saw",
      "total_hours": 26.46
    }
  ]
}
```

Error - Files not found (404 Not Found):
```json
{
  "detail": "Activities summary file not found"
}
```

Error - Server error (500 Internal Server Error):
```json
{
  "detail": "Error reading project time entries"
}
```

**Response Fields:**

- `up_to_lately.text` - Content from `last-7-days-activities-summary.md`
- `up_to_lately.date` - Collection date from CSV data
- `toggl_table` - Array of project entries sorted alphabetically by project name
- `toggl_table[].project_name` - Name of the project
- `toggl_table[].total_hours` - Total hours spent on project

**Behavior:**
- Reads text from `{PATH_PROJECT_RESOURCES}/hero-section/last-7-days-activities-summary.md`
- Parses CSV from `{PATH_PROJECT_RESOURCES}/hero-section/project_time_entries.csv`
- Projects are automatically sorted alphabetically by name
- Date extracted from CSV's `datetime_collected` field (first row)
