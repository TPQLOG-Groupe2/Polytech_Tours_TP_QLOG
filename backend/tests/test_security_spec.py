from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from app.auth import authenticate
from app.config import settings
from app.models import Player, User
from app.routers.admin import create_account
from app.schemas import AccountCreate
from app.security import create_access_token, decode_access_token, hash_password


def test_expired_access_token_must_be_rejected(db_session):
    # creating a user and an expired token
    user = User(
        email="expired@example.com",
        password_hash=hash_password("Password1!"),
        role="JOUEUR",
    )
    db_session.add(user)
    db_session.commit()
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    # the specification requires expiration verification
    with pytest.raises(Exception):
        decode_access_token(token)


def test_login_errors_must_not_distinguish_unknown_and_wrong_password(db_session):
    # unknown account
    with pytest.raises(HTTPException) as unknown:
        authenticate(db_session, "unknown@example.com", "WrongPassword1!")

    # known account with wrong password
    user = User(
        email="known@example.com",
        password_hash=hash_password("Password1!"),
        role="JOUEUR",
    )
    db_session.add(user)
    db_session.commit()
    with pytest.raises(HTTPException) as wrong_password:
        authenticate(db_session, "known@example.com", "WrongPassword1!")

    # account enumeration must not reveal whether the email exists
    assert unknown.value.detail == wrong_password.value.detail


def test_admin_route_rejects_player_role(db_session):
    # creating a player and a simulated player account
    player = Player(
        first_name="Alice",
        last_name="Test",
        company="A",
        license_number="L500001",
        email="alice.admin@example.com",
    )
    player_account = User(
        email="player.admin@example.com",
        password_hash="hashed",
        role="JOUEUR",
    )
    db_session.add_all([player, player_account])
    db_session.commit()

    # the route must return 403 for a player, instead of creating the account
    with pytest.raises(HTTPException) as exc_info:
        create_account(
            payload=AccountCreate(player_id=player.id),
            db=db_session,
            _=player_account,
        )

    assert exc_info.value.status_code == 403
