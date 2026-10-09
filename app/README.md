# ClassLedger API (Backend)

FastAPI backend for ClassLedger. All routes live under `/api/v1/institutions`. Set `DATABASE_URL` to use PostgreSQL; without it, the API falls back to in-memory storage (tests use this mode).

## Requirements

- Python 3.11+ (3.14 works in this repo)
- `pip`

## Quick start

From the repository root:

```bash
# 1. Virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.example .env

# 4. Run the API
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: http://127.0.0.1:8000
- Health: http://127.0.0.1:8000/health
- Docs (development only): http://127.0.0.1:8000/docs

## Tests

```bash
pytest
```

## Environment variables

Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Purpose |
|---|---|---|
| `ENVIRONMENT` | `development` | `production` enforces secure JWT and cookies |
| `JWT_SECRET` | dev placeholder | Must be a strong secret in production |
| `JWT_ALGORITHM` | `HS256` | Pinned algorithm |
| `JWT_ISSUER` | `classledger` | JWT `iss` claim |
| `JWT_AUDIENCE` | `classledger-api` | JWT `aud` claim |
| `ACCESS_TOKEN_TTL_SECONDS` | `900` | Access token lifetime (15 min) |
| `COOKIE_SECURE` | `false` | Set `true` in production (HTTPS) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `DATABASE_URL` | _(unset)_ | PostgreSQL URL (`postgresql+psycopg://...`). Optional in development |

Production refuses to start with the default `JWT_SECRET`, `COOKIE_SECURE=false`, or a missing `DATABASE_URL`.

### Database check

When `DATABASE_URL` is set, startup will:

1. **Ping** the database (`SELECT 1`)
2. **Validate** that all expected tables exist (14 tables)

Check runtime status:

```http
GET /health
```

```json
{
  "status": "ok",
  "storage": "postgresql",
  "database": { "status": "ok", "tables": 14 }
}
```

Without `DATABASE_URL`, the API still runs with in-memory storage (`"storage": "memory"`).

When `DATABASE_URL` is set, **all auth and institute reads/writes go to PostgreSQL** via `SqlAuthRepository`. Development data (`admin@gmail.com` / `admin`, demo batch, demo student) is seeded automatically on first startup if the database is empty.

## Development logins

Seeded only when `ENVIRONMENT` is not `production`.

| Role | Login | Password |
|---|---|---|
| Head teacher | `admin@gmail.com` | `admin` |
| Student | institute code `DEMO01`, roll `24-018` | `student123` |

## Auth

### Head teacher login

```http
POST /api/v1/institutions/auth/login
Content-Type: application/json

{
  "email": "admin@gmail.com",
  "password": "admin"
}
```

Returns `access_token` in JSON and sets an httpOnly `refresh_token` cookie.

### Student login

```http
POST /api/v1/institutions/auth/student/login
Content-Type: application/json

{
  "institution_code": "DEMO01",
  "roll_number": "24-018",
  "password": "student123"
}
```

### Protected requests

Send the access token on every protected route:

```http
Authorization: Bearer <access_token>
```

The server reads the institute (`tid`), user (`sub`), and role from the JWT. Never pass `institution_id` in the body for scoping.

### Refresh

```http
POST /api/v1/institutions/auth/refresh
X-Requested-With: XMLHttpRequest
Cookie: refresh_token=...
```

## API overview

Base path: `/api/v1/institutions`

### Auth

| Method | Path | Access |
|---|---|---|
| POST | `/auth/signup` | public |
| POST | `/auth/login` | public |
| POST | `/auth/student/login` | public |
| POST | `/auth/refresh` | refresh cookie + `X-Requested-With` |
| POST | `/auth/logout` | Bearer |
| POST | `/auth/logout-all` | Bearer |
| GET | `/auth/me` | Bearer |
| POST | `/auth/change-password` | Bearer |

### Institute data

| Area | Paths | Write access |
|---|---|---|
| Dashboard | `GET /dashboard` | head teacher |
| Batches | `GET/POST /batches`, `GET/PATCH /batches/{id}` | teacher writes |
| Students | `GET/POST /students`, `GET/PATCH /students/{id}` | teacher writes; `GET /students/{id}` returns profile with subjects, chapters, fee |
| Subjects / chapters / topics | `GET/POST /subjects`, `/chapters`, `/topics` | teacher writes |
| Attendance | `GET/POST /attendance/session`, `GET /attendance` | session sheet for a batch + subject + date (defaults to today) |
| Tests | `GET/POST /tests`, `POST /tests/{id}/questions`, `PUT /tests/{id}/marks` | teacher writes |
| Fees | `GET /fees`, `PUT /fees/{student_id}`, `POST /fees/{student_id}/payments` | teacher writes; students see own fees |
| Notices | `GET/POST /notices` | teacher writes |

Students can read their own attendance, marks, fees, and notices. Test responses hide answer keys and other students' individual marks, but include batch averages where relevant.

## Frontend connection

Set the frontend API URL in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the frontend from `frontend/`:

```bash
npm install
npm run dev
```

## Project layout

```text
app/
  main.py                 FastAPI app, CORS, error handling
  core/
    config.py             settings and production guards
    security.py           JWT, bcrypt, refresh tokens
    errors.py             consistent API error shape
  schemas/
    auth.py               auth request/response models
    platform.py           institute resource models
  services/
    auth_service.py       signup, login, refresh, lockout
    platform_service.py   batches, students, tests, fees, etc.
  repositories/
    base.py               auth repository interface
    memory.py             in-memory auth store + dev seed
    academic.py           in-memory academic records
    models.py             domain models
  api/
    deps.py               DI, JWT principal, role guards
    v1/
      router.py           route registration
      institutions/
        auth.py           auth routes
        resources.py      institute routes
tests/
  test_auth.py
  test_platform.py
```

## Storage layer

| `DATABASE_URL` | Repository | Persistence |
|---|---|---|
| set | `SqlAuthRepository` + `SqlAcademicRepository` | PostgreSQL |
| unset | `InMemoryAuthRepository` | process memory (tests) |

Swap point: `app/api/deps.py::get_repo`.

## Security notes

- Access JWT: HS256, 15 minutes, required claims `sub`, `tid`, `role`, `iss`, `aud`, `exp`, `nbf`, `iat`.
- Refresh token: opaque, hashed at rest, httpOnly + SameSite=Strict cookie, rotated on use; reuse revokes the whole family.
- Failed logins lock the account after repeated attempts.
- Still to add: rate limiting, forgot/reset password, RS256 if other services must verify tokens independently.
