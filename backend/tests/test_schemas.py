from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas import (
    AccountCreate,
    ChangePasswordRequest,
    EventCreate,
    EventUpdate,
    LoginRequest,
    MatchCreate,
    MatchUpdate,
    PlayerCreate,
    PlayerUpdate,
    PoolCreate,
    PoolUpdate,
    ProfileUpdate,
    TeamCreate,
    TeamUpdate,
)


def test_auth_schemas_accept_required_fields():
    assert LoginRequest(email="player@example.com", password="secret").email == (
        "player@example.com"
    )
    request = ChangePasswordRequest(
        current_password="old",
        new_password="new",
        confirm_password="new",
    )
    assert request.confirm_password == "new"


def test_player_create_normalizes_fields():
    player = PlayerCreate(
        first_name=" Alice ",
        last_name=" Dupont ",
        company=" Example Inc ",
        license_number=" L123456 ",
        email=" ALICE@EXAMPLE.COM ",
    )

    assert player.first_name == "Alice"
    assert player.last_name == "Dupont"
    assert player.company == "Example Inc"
    assert player.license_number == "L123456"
    assert player.email == "alice@example.com"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("first_name", "A"),
        ("last_name", "Dupont2"),
        ("company", "X"),
        ("license_number", "123456"),
        ("email", "not-an-email"),
    ],
)
def test_player_create_rejects_invalid_fields(field, value):
    data = {
        "first_name": "Alice",
        "last_name": "Dupont",
        "company": "Example Inc",
        "license_number": "L123456",
        "email": "alice@example.com",
    }
    data[field] = value

    with pytest.raises(ValidationError):
        PlayerCreate(**data)


def test_player_update_normalizes_fields():
    player = PlayerUpdate(
        first_name=" Alice ",
        last_name=" Dupont ",
        company=" Example Inc ",
    )

    assert (player.first_name, player.last_name, player.company) == (
        "Alice",
        "Dupont",
        "Example Inc",
    )


def test_team_schemas_validate_company_and_keep_optional_defaults():
    team = TeamCreate(company=" Example Inc ", player1_id=1, player2_id=2)
    update = TeamUpdate(player1_id=1, player2_id=2)

    assert team.company == "Example Inc"
    assert team.pool_id is None
    assert update.company is None
    assert update.pool_id is None

    with pytest.raises(ValidationError):
        TeamCreate(company="X", player1_id=1, player2_id=2)


def test_pool_schemas_normalize_name_and_default_update_name():
    pool = PoolCreate(name=" Pool A ", team_ids=[1, 2])
    update = PoolUpdate(team_ids=[1, 2])

    assert pool.name == "Pool A"
    assert update.name is None

    with pytest.raises(ValidationError):
        PoolCreate(name="   ", team_ids=[])


def test_event_schemas_validate_time_and_nested_matches():
    event = EventCreate(
        event_date="2026-11-23",
        event_time="09:30",
        matches=[{"court_number": 1, "team1_id": 1, "team2_id": 2}],
    )
    update = EventUpdate(event_date="2026-11-23", event_time="23:59")

    assert event.event_date == date(2026, 11, 23)
    assert event.matches[0].team2_id == 2
    assert update.event_time == "23:59"

    with pytest.raises(ValidationError):
        EventCreate(
            event_date="2026-11-23",
            event_time="24:00",
            matches=[],
        )


@pytest.mark.parametrize("court_number", [1, 10])
def test_match_create_accepts_court_boundaries(court_number):
    match = MatchCreate(
        event_date="2026-11-23",
        event_time="10:00",
        court_number=court_number,
        team1_id=1,
        team2_id=2,
    )

    assert match.court_number == court_number


@pytest.mark.parametrize("court_number", [0, 11])
def test_match_create_rejects_out_of_range_court(court_number):
    with pytest.raises(ValidationError):
        MatchCreate(
            event_date="2026-11-23",
            event_time="10:00",
            court_number=court_number,
            team1_id=1,
            team2_id=2,
        )


def test_match_update_validates_optional_fields_and_status():
    update = MatchUpdate(event_time="12:30", court_number=10, status="TERMINE")
    empty_update = MatchUpdate()

    assert update.status == "TERMINE"
    assert empty_update.event_time is None

    with pytest.raises(ValidationError):
        MatchUpdate(status="IN_PROGRESS")
    with pytest.raises(ValidationError):
        MatchUpdate(event_time="25:00")


def test_profile_update_normalizes_email_and_validates_birth_date():
    profile = ProfileUpdate(
        first_name=" Alice ",
        last_name=" Dupont ",
        email=" ALICE@EXAMPLE.COM ",
        birth_date="2000-01-01",
    )

    assert profile.first_name == "Alice"
    assert profile.last_name == "Dupont"
    assert profile.email == "alice@example.com"
    assert profile.birth_date == date(2000, 1, 1)

    with pytest.raises(ValidationError):
        ProfileUpdate(
            first_name="Alice",
            last_name="Dupont",
            email="alice@example.com",
            birth_date=date.today() + timedelta(days=1),
        )
    with pytest.raises(ValidationError):
        ProfileUpdate(
            first_name="Alice",
            last_name="Dupont",
            email="alice@example.com",
            birth_date=date.today() - timedelta(days=365 * 15),
        )


def test_account_create_defaults_and_validates_role():
    account = AccountCreate(player_id=1)
    admin = AccountCreate(player_id=2, role="ADMINISTRATEUR")

    assert account.role == "JOUEUR"
    assert admin.role == "ADMINISTRATEUR"

    with pytest.raises(ValidationError):
        AccountCreate(player_id=3, role="user")
