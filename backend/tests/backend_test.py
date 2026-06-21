"""
Backend pytest suite for Everstead.
Tests: auth (signup/login/me/forgot/oauth) and retrofits CRUD (scoped to user).
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://retrofit-assess.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

DEMO_EMAIL = "demo@everstead.app"
DEMO_PASSWORD = "Everstead123!"


def _uniq_email():
    # use example.com - widely accepted by email-validator
    return f"test_{uuid.uuid4().hex[:10]}@example.com"


SAMPLE_ASSESSMENT = {
    "site": {"resolvedAddress": "123 Main St, Winnipeg, MB"},
    "currency": "CAD",
    "technologies": [
        {"type": "solar_pv", "displayName": "Rooftop Solar", "yearlySavings": 1280, "rank": 1},
        {"type": "battery", "displayName": "Home Battery", "yearlySavings": 420, "rank": 2},
        {"type": "wind", "displayName": "Small Wind", "yearlySavings": 220, "rank": 3},
        {"type": "geothermal", "displayName": "Geothermal HP", "yearlySavings": 900, "rank": 4},
    ],
    "rebates": [{"name": "Federal solar credit", "amount": 5000}],
}


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def demo_token(session):
    r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, f"Demo login failed: {r.status_code} {r.text}"
    return r.json()["token"]


# ---------- Health ----------
def test_api_root(session):
    r = session.get(f"{API}/")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# ---------- Auth: signup ----------
class TestSignup:
    def test_signup_success(self, session):
        email = _uniq_email()
        r = session.post(f"{API}/auth/signup", json={"name": "Test User", "email": email, "password": "secret6"})
        assert r.status_code == 201, r.text
        data = r.json()
        assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 10
        assert data["user"]["email"] == email
        assert data["user"]["name"] == "Test User"
        assert "id" in data["user"]

    def test_signup_duplicate_email(self, session):
        email = _uniq_email()
        session.post(f"{API}/auth/signup", json={"name": "A", "email": email, "password": "secret6"})
        r = session.post(f"{API}/auth/signup", json={"name": "A", "email": email, "password": "secret6"})
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "EMAIL_IN_USE"

    def test_signup_short_password(self, session):
        r = session.post(f"{API}/auth/signup", json={"name": "A", "email": _uniq_email(), "password": "abc"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_signup_invalid_email(self, session):
        r = session.post(f"{API}/auth/signup", json={"name": "A", "email": "not-an-email", "password": "secret6"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------- Auth: login ----------
class TestLogin:
    def test_demo_login_success(self, session):
        r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert data["user"]["email"] == DEMO_EMAIL
        assert "token" in data

    def test_login_wrong_password(self, session):
        r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": "wrong-password"})
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_unknown_email(self, session):
        r = session.post(f"{API}/auth/login", json={"email": "no-such-user@example.com", "password": "anything"})
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


# ---------- Auth: /me ----------
class TestMe:
    def test_me_with_token(self, session, demo_token):
        r = session.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {demo_token}"})
        assert r.status_code == 200
        assert r.json()["user"]["email"] == DEMO_EMAIL

    def test_me_no_token(self, session):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "UNAUTHORIZED"

    def test_me_invalid_token(self, session):
        r = requests.get(f"{API}/auth/me", headers={"Authorization": "Bearer not.a.token"})
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "UNAUTHORIZED"


# ---------- Auth: forgot + oauth ----------
class TestForgotOauth:
    def test_forgot_existing(self, session):
        r = session.post(f"{API}/auth/forgot-password", json={"email": DEMO_EMAIL})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert "message" in body

    def test_forgot_nonexistent(self, session):
        r = session.post(f"{API}/auth/forgot-password", json={"email": "ghost@example.com"})
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_oauth_not_implemented(self, session):
        r = session.post(f"{API}/auth/oauth", json={"provider": "google"})
        assert r.status_code == 501
        assert r.json()["error"]["code"] == "NOT_IMPLEMENTED"


# ---------- Retrofits CRUD (scoped) ----------
class TestRetrofits:
    @pytest.fixture(scope="class")
    def user_a(self, session):
        email = _uniq_email()
        r = session.post(f"{API}/auth/signup", json={"name": "User A", "email": email, "password": "secret6"})
        assert r.status_code == 201
        return r.json()

    @pytest.fixture(scope="class")
    def user_b(self, session):
        email = _uniq_email()
        r = session.post(f"{API}/auth/signup", json={"name": "User B", "email": email, "password": "secret6"})
        assert r.status_code == 201
        return r.json()

    def test_unauth_list(self, session):
        r = requests.get(f"{API}/retrofits")
        assert r.status_code == 401

    def test_create_get_list_delete(self, session, user_a):
        token = user_a["token"]
        h = {"Authorization": f"Bearer {token}"}

        # CREATE
        r = session.post(f"{API}/retrofits", json={"assessment": SAMPLE_ASSESSMENT, "label": "Our house"}, headers=h)
        assert r.status_code == 201, r.text
        created = r.json()
        assert "id" in created
        assert created["label"] == "Our house"
        assert "createdAt" in created
        rid = created["id"]

        # LIST
        r = session.get(f"{API}/retrofits", headers=h)
        assert r.status_code == 200
        retros = r.json()["retrofits"]
        assert any(x["id"] == rid for x in retros)
        item = next(x for x in retros if x["id"] == rid)
        assert item["label"] == "Our house"
        assert item["topRecommendation"] == "solar_pv"

        # GET full
        r = session.get(f"{API}/retrofits/{rid}", headers=h)
        assert r.status_code == 200
        full = r.json()
        assert full["id"] == rid
        assert full["label"] == "Our house"
        assert "assessment" in full
        assert full["assessment"]["technologies"][0]["type"] == "solar_pv"

        # DELETE
        r = session.delete(f"{API}/retrofits/{rid}", headers=h)
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # GET should now 404
        r = session.get(f"{API}/retrofits/{rid}", headers=h)
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOT_FOUND"

    def test_cross_user_isolation(self, session, user_a, user_b):
        ha = {"Authorization": f"Bearer {user_a['token']}"}
        hb = {"Authorization": f"Bearer {user_b['token']}"}

        r = session.post(f"{API}/retrofits", json={"assessment": SAMPLE_ASSESSMENT, "label": "A-house"}, headers=ha)
        assert r.status_code == 201
        rid = r.json()["id"]

        # User B cannot read User A's retrofit
        r = session.get(f"{API}/retrofits/{rid}", headers=hb)
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOT_FOUND"

        # User B cannot delete User A's retrofit
        r = session.delete(f"{API}/retrofits/{rid}", headers=hb)
        assert r.status_code == 404

        # User B's list should not include it
        r = session.get(f"{API}/retrofits", headers=hb)
        assert r.status_code == 200
        assert not any(x["id"] == rid for x in r.json()["retrofits"])

        # cleanup
        session.delete(f"{API}/retrofits/{rid}", headers=ha)

    def test_unknown_id_404(self, session, user_a):
        h = {"Authorization": f"Bearer {user_a['token']}"}
        # valid ObjectId format but not present
        r = session.get(f"{API}/retrofits/507f1f77bcf86cd799439011", headers=h)
        assert r.status_code == 404
        # malformed id
        r = session.get(f"{API}/retrofits/not-an-id", headers=h)
        assert r.status_code == 404

    def test_create_missing_assessment(self, session, user_a):
        h = {"Authorization": f"Bearer {user_a['token']}"}
        r = session.post(f"{API}/retrofits", json={"label": "x"}, headers=h)
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"
