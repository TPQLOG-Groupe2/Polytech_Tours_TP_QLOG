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


def test_login_request_accepts_required_fields():
    # creating a valid login request
    request = LoginRequest(email="player@example.com", password="secret")

    # checking required fields
    assert request.email == "player@example.com"
    assert request.password == "secret"


def test_change_password_request_accepts_matching_fields():
    # creating a valid password-change request
    request = ChangePasswordRequest(
        current_password="old",
        new_password="NewPassword1!",
        confirm_password="NewPassword1!",
    )

    # checking confirmation password
    assert request.confirm_password == request.new_password


def test_player_create_normalizes_text_fields():
    # creating a player with unnormalized text
    player = PlayerCreate(
        first_name=" Alice ",
        last_name=" Dupont ",
        company=" Example Inc ",
        license_number=" L123456 ",
        email=" ALICE@EXAMPLE.COM ",
    )

    # checking normalized values
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
def test_player_create_rejects_invalid_field(field, value):
    # building valid player data
    data = {
        "first_name": "Alice",
        "last_name": "Dupont",
        "company": "Example Inc",
        "license_number": "L123456",
        "email": "alice@example.com",
    }
    # replacing one field with an invalid value
    data[field] = value

    # checking schema validation
    with pytest.raises(ValidationError):
        PlayerCreate(**data)


def test_player_update_normalizes_text_fields():
    # creating an update with unnormalized text
    player = PlayerUpdate(
        first_name=" Alice ",
        last_name=" Dupont ",
        company=" Example Inc ",
    )

    # checking normalized values
    assert (player.first_name, player.last_name, player.company) == (
        "Alice",
        "Dupont",
        "Example Inc",
    )


def test_team_create_normalizes_company_and_defaults_pool():
    # creating team schemas
    team = TeamCreate(company=" Example Inc ", player1_id=1, player2_id=2)
    update = TeamUpdate(player1_id=1, player2_id=2)

    # checking normalization and optional defaults
    assert team.company == "Example Inc"
    assert team.pool_id is None
    assert update.company is None
    assert update.pool_id is None


def test_team_create_rejects_short_company():
    # checking that a short company name is rejected
    with pytest.raises(ValidationError):
        TeamCreate(company="X", player1_id=1, player2_id=2)


def test_pool_create_normalizes_name():
    # creating a pool with an unnormalized name
    pool = PoolCreate(name=" Pool A ", team_ids=[1, 2])

    # checking normalization
    assert pool.name == "Pool A"
    assert pool.team_ids == [1, 2]


def test_pool_update_keeps_optional_name_default():
    # creating a pool update without name
    update = PoolUpdate(team_ids=[1, 2])

    # checking the optional default
    assert update.name is None


def test_pool_create_rejects_empty_name():
    # checking that an empty pool name is rejected
    with pytest.raises(ValidationError):
        PoolCreate(name="   ", team_ids=[1])


def test_event_create_accepts_valid_nested_match():
    # creating a valid event with one match
    event = EventCreate(
        event_date="2026-11-23",
        event_time="09:30",
        matches=[{"court_number": 1, "team1_id": 1, "team2_id": 2}],
    )

    # checking event and nested match values
    assert event.event_date == date(2026, 11, 23)
    assert event.event_time == "09:30"
    assert event.matches[0].team2_id == 2


@pytest.mark.parametrize("event_time", ["24:00", "9:30", "09-30"])
def test_event_create_rejects_invalid_time(event_time):
    # checking that an invalid event time is rejected
    with pytest.raises(ValidationError):
        EventCreate(event_date="2026-11-23", event_time=event_time, matches=[])


@pytest.mark.parametrize("court_number", [1, 10])
def test_match_create_accepts_court_boundaries(court_number):
    # creating a match on a valid court boundary
    match = MatchCreate(
        event_date="2026-11-23",
        event_time="10:00",
        court_number=court_number,
        team1_id=1,
        team2_id=2,
    )

    # checking the court number
    assert match.court_number == court_number


@pytest.mark.parametrize("court_number", [0, 11])
def test_match_create_rejects_court_outside_boundaries(court_number):
    # checking that an out-of-range court is rejected
    with pytest.raises(ValidationError):
        MatchCreate(
            event_date="2026-11-23",
            event_time="10:00",
            court_number=court_number,
            team1_id=1,
            team2_id=2,
        )


def test_match_update_accepts_optional_valid_fields():
    # creating a match update with valid optional fields
    update = MatchUpdate(event_time="12:30", court_number=10, status="TERMINE")

    # checking updated values
    assert update.event_time == "12:30"
    assert update.court_number == 10
    assert update.status == "TERMINE"


def test_match_update_has_empty_optional_fields():
    # checking default values for an empty update
    assert MatchUpdate().event_time is None


@pytest.mark.parametrize(
    "update",
    [
        {"status": "IN_PROGRESS"},
        {"event_time": "25:00"},
        {"court_number": 0},
    ],
)
def test_match_update_rejects_invalid_optional_field(update):
    # checking that an invalid optional field is rejected
    with pytest.raises(ValidationError):
        MatchUpdate(**update)


def test_profile_update_normalizes_valid_fields():
    # creating a profile update with unnormalized values
    profile = ProfileUpdate(
        first_name=" Alice ",
        last_name=" Dupont ",
        email=" ALICE@EXAMPLE.COM ",
        birth_date="2000-01-01",
    )

    # checking normalized values
    assert profile.first_name == "Alice"
    assert profile.last_name == "Dupont"
    assert profile.email == "alice@example.com"
    assert profile.birth_date == date(2000, 1, 1)


@pytest.mark.parametrize(
    "birth_date",
    [date.today() + timedelta(days=1), date.today() - timedelta(days=365 * 15)],
)
def test_profile_update_rejects_unacceptable_birth_date(birth_date):
    # checking that an invalid birth date is rejected
    with pytest.raises(ValidationError):
        ProfileUpdate(
            first_name="Alice",
            last_name="Dupont",
            email="alice@example.com",
            birth_date=birth_date,
        )


def test_account_create_uses_role_default_and_accepts_admin():
    # creating player and administrator accounts
    account = AccountCreate(player_id=1)
    admin = AccountCreate(player_id=2, role="ADMINISTRATEUR")

    # checking role defaults
    assert account.role == "JOUEUR"
    assert admin.role == "ADMINISTRATEUR"


def test_account_create_rejects_unknown_role():
    # checking that an unknown account role is rejected
    with pytest.raises(ValidationError):
        AccountCreate(player_id=3, role="USER")
