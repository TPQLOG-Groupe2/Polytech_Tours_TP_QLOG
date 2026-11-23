from datetime import datetime, timedelta, timezone
from xmlrpc import client

from app.config import settings
from app.models import LoginAttempt, User
from app.security import hash_password

URL = "/auth/login"

def _login_attempt(client, email: str, password: str):
    return client.post(URL, json={"email": email, "password": password})


def _make_user(db_session, email: str, password: str):
    user = User(email=email, password_hash=hash_password(password))
    db_session.add(user)
    db_session.commit()
    return user


def test_login_success(client, db_session):
    user = _make_user(db_session, "test@example.com", "password")

    # testing conection
    response = _login_attempt(client, "test@example.com", "password")
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_wrong_password(client, db_session):
    user = _make_user(db_session, "test@example.com", "password")

    # testing wrong password
    response = _login_attempt(client, "test@example.com", "wrong_password")
    assert response.status_code == 401


def test_lockout_after_failed_attempts(client, db_session):
    user = _make_user(db_session, "test@example.com", "password")

    # making enough failed atteempts
    for _ in range(settings.max_login_attempts):
        response = _login_attempt(client, "test@example.com", "wrong_password")
        assert response.status_code == 401

    # declenching lockout
    response = _login_attempt(client, "test@example.com", "wrong_password")
    assert response.status_code == 423

    # testing that the user is not able to log anymore even w the right pword
    response = _login_attempt(client, "test@example.com", "password")
    assert response.status_code == 423


def test_lockout_expiration(client, db_session):
    user = _make_user(db_session, "test@example.com", "password")

    for _ in range(settings.max_login_attempts+1):
        _login_attempt(client, "test@example.com", "wrong_password")

    # manually setting the lockout expiration to a future time
    user.lockout_expiration = datetime.now(timezone.utc) - timedelta(minutes=30)
    db_session.commit()

    assert _login_attempt(client, "test@example.com", "password").status_code == 200