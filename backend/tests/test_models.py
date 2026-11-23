from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Event, Match, Player, Pool, Team, User


def _create_player(db_session, number: int, user: User | None = None) -> Player:
    player = Player(
        first_name=f"Player{number}",
        last_name="Test",
        company="Test company",
        license_number=f"L{number:06d}",
        email=f"player{number}@example.com",
        user=user,
    )
    db_session.add(player)
    return player


def _create_match_context(db_session):
    players = [_create_player(db_session, number) for number in range(1, 5)]
    pool = Pool(name="Pool A")
    event = Event(event_date=date(2026, 11, 23), event_time="10:00")
    db_session.add_all([pool, event])
    db_session.flush()

    teams = [
        Team(
            company=f"Company {number}",
            player1=players[(number - 1) * 2],
            player2=players[(number - 1) * 2 + 1],
            pool=pool,
        )
        for number in (1, 2)
    ]
    db_session.add_all(teams)
    db_session.commit()
    return event, teams, pool


@pytest.mark.parametrize("role", ["JOUEUR", "ADMINISTRATEUR"])
def test_user_accepts_supported_roles(db_session, role):
    user = User(
        email=f"{role.lower()}@example.com",
        password_hash="hashed-password",
        role=role,
    )
    db_session.add(user)

    db_session.commit()

    assert user.id is not None


def test_user_rejects_unsupported_role(db_session):
    db_session.add(
        User(email="user@example.com", password_hash="hashed-password", role="user")
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_player_user_relationship_and_defaults(db_session):
    user = User(
        email="player@example.com",
        password_hash="hashed-password",
        role="JOUEUR",
    )
    player = _create_player(db_session, 1, user)
    db_session.commit()

    assert user.player is player
    assert player.user is user
    assert user.is_active is True
    assert user.must_change_password is False


def test_team_rejects_same_player_twice(db_session):
    player = _create_player(db_session, 1)
    db_session.flush()
    db_session.add(
        Team(company="Test company", player1=player, player2=player)
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize(
    "invalid_fields",
    [
        {"court_number": 0},
        {"court_number": 11},
        {"status": "IN_PROGRESS"},
        {"team2_id": 1},
    ],
)
def test_match_rejects_invalid_values(db_session, invalid_fields):
    event, teams, _ = _create_match_context(db_session)
    match = Match(
        event_id=event.id,
        team1_id=teams[0].id,
        team2_id=teams[1].id,
        court_number=1,
        status="A_VENIR",
    )
    for field, value in invalid_fields.items():
        setattr(match, field, value)
    db_session.add(match)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_pool_contains_assigned_teams(db_session):
    _, teams, pool = _create_match_context(db_session)

    assert set(pool.teams) == set(teams)
