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
