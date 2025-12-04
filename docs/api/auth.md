# Authentication Endpoints

## POST /auth/register

Register a new user account and receive a JWT access token.

**Authentication:** Not required

**Authorization:** Email must be in the `EMAIL_ADMIN_LIST` environment variable

**Sample Request:**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response Examples:**

Success (201 Created):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWF0IjoxNzAxNDUwMDAwfQ.signature",
  "token_type": "bearer"
}
```

Error - Unauthorized email (403 Forbidden):
```json
{
  "detail": "Registration restricted to authorized email addresses"
}
```

Error - Email already exists (400 Bad Request):
```json
{
  "detail": "Email already registered"
}
```

Error - Validation error (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Email cannot be empty",
      "type": "value_error"
    }
  ]
}
```

**Behavior:**
- Registration is restricted to emails listed in `EMAIL_ADMIN_LIST` (comma-separated)
- Email matching is case-insensitive
- If `EMAIL_ADMIN_LIST` is empty or not set, all registrations are blocked
- Upon successful registration, user is automatically logged in and receives a JWT token
- Email and password cannot be empty strings
- Passwords are hashed using bcrypt before storage
- Bcrypt has a 72-byte limit - longer passwords are truncated
- JWT tokens never expire in this system
- Use the token in subsequent requests: `Authorization: Bearer <token>`

---

## POST /auth/login

Authenticate and receive a JWT token.

**Authentication:** Not required

**Sample Request:**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response Examples:**

Success (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWF0IjoxNzAxNDUwMDAwfQ.signature",
  "token_type": "bearer"
}
```

Error - Invalid credentials (401 Unauthorized):
```json
{
  "detail": "Invalid credentials"
}
```

**Behavior:**
- JWT tokens never expire in this system
- Token contains user email in the `sub` claim
- Use the token in subsequent requests: `Authorization: Bearer <token>`

---

## POST /auth/forgot-password

Request a password reset email.

**Authentication:** Not required

**Sample Request:**

```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Response Examples:**

Success (200 OK):
```json
{
  "message": "Password reset email sent successfully"
}
```

Error - Email not found (404 Not Found):
```json
{
  "detail": "Email not found"
}
```

Error - Rate limit exceeded (429 Too Many Requests):
```json
{
  "detail": "Too many reset requests. Please try again in 5 minutes."
}
```

Error - Email sending failed (500 Internal Server Error):
```json
{
  "detail": "Failed to send reset email. Please try again later."
}
```

**Behavior:**
- Sends password reset email with time-limited token
- Token expires after 30 minutes
- Rate limited to 3 requests per 5 minutes per email address
- Reset link format: `{URL_BASE_WEBSITE}/reset-password?token=XXXXX`
- Email template follows project style guide (monospace, monochrome design)

**Email Configuration:**
Requires the following environment variables:
- `MAIL_SERVER_MSOFFICE` - SMTP server address
- `MAIL_PORT` - SMTP port (typically 587)
- `MAIL_TLS` - Enable TLS (True/False)
- `MAIL_SSL` - Enable SSL (True/False)
- `MAIL_FROM` - Sender email address
- `MAIL_PASSWORD` - Email account password or app password
- `URL_BASE_WEBSITE` - Frontend base URL for reset link

---

## POST /auth/reset-password

Reset password using token from email.

**Authentication:** Not required (uses reset token)

**Sample Request:**

```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "new_password": "newSecurePassword123"
  }'
```

**Response Examples:**

Success (200 OK):
```json
{
  "message": "Password reset successfully"
}
```

Error - Invalid/expired token (400 Bad Request):
```json
{
  "detail": "Invalid or expired reset token"
}
```

Error - User not found (404 Not Found):
```json
{
  "detail": "User not found"
}
```

**Behavior:**
- Validates JWT reset token
- Token must be of type "password_reset"
- Token expires after 30 minutes
- Updates password with new hashed value (bcrypt)
- No password complexity requirements enforced by backend
- Frontend should handle password validation
