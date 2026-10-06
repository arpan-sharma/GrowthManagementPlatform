from tests.conftest import BASE, XHR

SIGNUP = {
    "institute": {"name": "Sharma Classes", "city": "Mumbai", "phone": "+919876543210", "email": "contact@sharmaclasses.in"},
    "head_teacher": {"full_name": "R Sharma", "email": "rsharma@sharmaclasses.in", "phone": "+919876543210", "password": "S3cure-pass-77"},
    "consent": {"terms_accepted": True, "privacy_accepted": True},
}


def test_seed_admin_login(admin_login):
    assert admin_login.status_code == 200
    body = admin_login.json()
    assert body["token_type"] == "Bearer" and body["expires_in"] == 900
    assert body["user"]["role"] == "head_teacher"
    cookie = admin_login.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie


def test_wrong_password_and_unknown_user_look_identical(client):
    a = client.post(f"{BASE}/login", json={"email": "admin@gmail.com", "password": "nope"})
    b = client.post(f"{BASE}/login", json={"email": "ghost@gmail.com", "password": "nope"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_lockout_after_failures(client):
    for _ in range(5):
        client.post(f"{BASE}/login", json={"email": "admin@gmail.com", "password": "bad"})
    r = client.post(f"{BASE}/login", json={"email": "admin@gmail.com", "password": "admin"})
    assert r.status_code == 423 and "retry-after" in r.headers


def test_access_token_claims_and_rejects_tampering(client, admin_login):
    import jwt

    from app.core.config import get_settings

    settings = get_settings()
    tok = admin_login.json()["access_token"]
    claims = jwt.decode(
        tok,
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
    user = admin_login.json()["user"]
    assert claims["sub"] == user["id"]
    assert claims["tid"] == user["institution_id"]
    assert claims["role"] == "head_teacher"
    tampered = tok[:-2] + ("aa" if not tok.endswith("aa") else "bb")
    assert client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401
    wrong_secret = jwt.encode(
        {"sub": user["id"], "tid": user["institution_id"], "role": "head_teacher", "exp": 9_999_999_999, "iat": 1, "nbf": 1, "iss": settings.jwt_issuer, "aud": settings.jwt_audience},
        "another-secret-that-is-not-the-server-key",
        algorithm="HS256",
    )
    assert client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {wrong_secret}"}).status_code == 401


def test_me_requires_and_accepts_token(client, admin_login):
    assert client.get(f"{BASE}/me").status_code == 401
    tok = admin_login.json()["access_token"]
    r = client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200 and r.json()["email"] == "admin@gmail.com"
    assert client.get(f"{BASE}/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_refresh_rotates_and_detects_reuse(client, admin_login):
    old = client.cookies.get("refresh_token")
    r = client.post(f"{BASE}/refresh", headers=XHR)
    assert r.status_code == 200
    new = client.cookies.get("refresh_token")
    assert new and new != old
    # replay the rotated-out token -> whole family revoked
    client.cookies.clear()
    r2 = client.post(f"{BASE}/refresh", headers={**XHR, "Cookie": f"refresh_token={old}"})
    assert r2.status_code == 401 and r2.json()["error"]["code"] == "token_reuse_detected"
    # the legit newest token is now dead too
    client.cookies.clear()
    r3 = client.post(f"{BASE}/refresh", headers={**XHR, "Cookie": f"refresh_token={new}"})
    assert r3.status_code == 401


def test_refresh_needs_csrf_header(client, admin_login):
    assert client.post(f"{BASE}/refresh").status_code == 403


def test_logout_revokes_refresh(client, admin_login):
    tok = admin_login.json()["access_token"]
    raw = client.cookies.get("refresh_token")
    assert client.post(f"{BASE}/logout", headers={"Authorization": f"Bearer {tok}"}).status_code == 204
    client.cookies.clear()
    r = client.post(f"{BASE}/refresh", headers={**XHR, "Cookie": f"refresh_token={raw}"})
    assert r.status_code == 401


def test_signup_then_pending_login_blocked(client):
    r = client.post(f"{BASE}/signup", json=SIGNUP)
    assert r.status_code == 201 and r.json()["status"] == "pending_review"
    assert client.post(f"{BASE}/signup", json=SIGNUP).status_code == 409
    login = client.post(f"{BASE}/login", json={"email": "rsharma@sharmaclasses.in", "password": "S3cure-pass-77"})
    assert login.status_code == 403 and login.json()["error"]["code"] == "account_pending"


def test_signup_validation(client):
    bad = {**SIGNUP, "consent": {"terms_accepted": False, "privacy_accepted": True}}
    r = client.post(f"{BASE}/signup", json=bad)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    weak = {**SIGNUP, "head_teacher": {**SIGNUP["head_teacher"], "password": "short"}}
    assert client.post(f"{BASE}/signup", json=weak).status_code == 422


def test_student_login_unknown_is_generic(client):
    r = client.post(f"{BASE}/student/login", json={"institution_code": "DEMO01", "roll_number": "1", "password": "x"})
    assert r.status_code == 401


def test_change_password(client, admin_login):
    tok = admin_login.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    assert client.post(f"{BASE}/change-password", headers=h, json={"current_password": "wrong", "new_password": "N3w-strong-pass"}).status_code == 400
    assert client.post(f"{BASE}/change-password", headers=h, json={"current_password": "admin", "new_password": "N3w-strong-pass"}).status_code == 204
    assert client.post(f"{BASE}/login", json={"email": "admin@gmail.com", "password": "N3w-strong-pass"}).status_code == 200
