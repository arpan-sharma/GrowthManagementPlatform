import os

os.environ["ENVIRONMENT"] = "development"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-use!!"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["COOKIE_SECURE"] = "false"
os.environ["ACCESS_TOKEN_TTL_SECONDS"] = "900"
os.environ["DATABASE_URL"] = ""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import reset_repositories
from app.core.config import get_settings
from app.main import create_app

BASE = "/api/v1/institutions/auth"
XHR = {"X-Requested-With": "XMLHttpRequest"}


@pytest.fixture
def client():
    reset_repositories()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    reset_repositories()


@pytest.fixture
def admin_login(client):
    return client.post(f"{BASE}/login", json={"email": "admin@gmail.com", "password": "admin"})
