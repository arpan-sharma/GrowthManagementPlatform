# ClassLedger API (FastAPI)

Auth first: signup, login (head teacher + student), refresh, logout, me, change-password.
Base path: `/api/v1/institutions`. Storage is **in-memory for now**; a relational DB comes later.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload        # docs at http://localhost:8000/docs
pytest
```

## Temporary dev login (development only)
`admin@gmail.com` / `admin` is seeded into the in-memory store on startup.
It is NOT created when `ENVIRONMENT=production`. Remove `seed_dev_data` once the DB exists.

## Endpoints (`/api/v1/institutions/auth`)
| Method | Path | Auth |
|---|---|---|
| POST | `/signup` | public |
| POST | `/login` | public (head teacher: email + password) |
| POST | `/student/login` | public (institution_code + roll_number + password) |
| POST | `/refresh` | refresh cookie + `X-Requested-With` header |
| POST | `/logout`, `/logout-all` | Bearer |
| GET | `/me` | Bearer |
| POST | `/change-password` | Bearer |

## Layout
```
app/
  main.py                      app factory, CORS, error shape, security headers
  core/        config.py  security.py (JWT, bcrypt, refresh tokens)  errors.py
  schemas/     auth.py           request/response models
  services/    auth_service.py   all auth rules (lockout, rotation, reuse detection)
  repositories/
      base.py                    AuthRepository interface
      memory.py                  in-memory implementation + dev seed
      models.py                  domain models (map 1:1 to future tables)
  api/
      deps.py                    get_repo (DB swap point), get_principal, require_role
      v1/router.py               register future routers here
      v1/institutions/auth.py    auth routes
tests/
```

## Moving to a relational database later
1. Add `SqlAuthRepository(AuthRepository)` (SQLAlchemy + PostgreSQL, Alembic migrations).
2. Change the single line in `app/api/deps.py::get_repo`.
3. Delete `memory.py` / the seed. Services, routes and tests' HTTP assertions stay as they are.

## Security notes
- Access JWT: 15 min, pinned algorithm, `iss`/`aud`/`exp` required. Claims: `sub`, `tid`, `role`, `sid` (students).
- Refresh token: opaque, hashed at rest, httpOnly + SameSite=Strict cookie, rotated every use, reuse revokes the family.
- Production refuses to start with the default `JWT_SECRET` or `COOKIE_SECURE=false`.
- Still to add: IP rate limiting (gateway / slowapi), forgot/reset password, RS256 keys if other services need to verify tokens.
