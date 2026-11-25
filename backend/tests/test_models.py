from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Event, Match, Player, Pool, Team, User


def _make_player(db_session, number):
    # creating a valid player object
    player = Player(
        first_name=f"Player{number}",
        last_name="Test",
        company="Test company",
        license_number=f"L{number:06d}",
        email=f"player{number}@example.com",
    )
    db_session.add(player)
    return player


def _make_match_context(db_session):
    # creating players, a pool and an event
    players = [_make_player(db_session, number) for number in range(1, 5)]
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
    # creating a user with a supported role
    user = User(
        email=f"{role.lower()}@example.com",
        password_hash="hashed-password",
        role=role,
    )

    # persisting and checking the user
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert db_session.query(User).filter_by(email=user.email).one() is user


def test_user_rejects_unsupported_role(db_session):
    # creating a user with an unsupported role
    db_session.add(
        User(email="invalid@example.com", password_hash="hashed-password", role="USER")
    )

    # checking that the database constraint rejects it
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_player_is_linked_to_user_with_expected_defaults(db_session):
    # creating a user and linking a player
    user = User(
        email="player@example.com",
        password_hash="hashed-password",
        role="JOUEUR",
    )
    player = _make_player(db_session, 1)
    player.user = user
    # persisting the relationship
    db_session.commit()

    # checking the relationship and default values
    assert user.player is player
    assert player.user is user
    assert user.is_active is True
    assert user.must_change_password is False


def test_team_rejects_the_same_player_in_both_slots(db_session):
    # creating a player to use twice
    player = _make_player(db_session, 1)
    db_session.flush()
    # creating an invalid team
    db_session.add(Team(company="Test company", player1=player, player2=player))

    # checking that the database constraint rejects it
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("court_number", 0),
        ("court_number", 11),
        ("status", "IN_PROGRESS"),
    ],
)
def test_match_rejects_invalid_field_value(db_session, field, invalid_value):
    # creating a valid match context
    event, teams, _ = _make_match_context(db_session)
    match = Match(
        event_id=event.id,
        team1_id=teams[0].id,
        team2_id=teams[1].id,
        court_number=1,
        status="A_VENIR",
    )
    # adding an invalid field value
    setattr(match, field, invalid_value)
    db_session.add(match)

    # checking that the database constraint rejects it
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_match_rejects_the_same_team_in_both_slots(db_session):
    # creating a match context
    event, teams, _ = _make_match_context(db_session)
    # creating a match with the same team twice
    db_session.add(
        Match(
            event_id=event.id,
            team1_id=teams[0].id,
            team2_id=teams[0].id,
            court_number=1,
            status="A_VENIR",
        )
    )

    # checking that the database constraint rejects it
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_pool_exposes_assigned_teams(db_session):
    # creating a pool with assigned teams
    _, teams, pool = _make_match_context(db_session)

    # checking the pool relationship
    assert set(pool.teams) == set(teams)
