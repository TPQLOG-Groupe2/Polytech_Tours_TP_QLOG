from datetime import date

from app.models import Event, Match, Player, Pool, Team
from app.services.serializers import event_out, match_out, player_full, team_out


def test_player_full_includes_expected_profile_fields(db_session):
    # creating a player profile
    player = Player(
        first_name="Alice",
        last_name="Test",
        company="Example",
        license_number="L800001",
        email="alice.serial@example.com",
        birth_date=date(2000, 1, 1),
    )
    db_session.add(player)
    db_session.commit()

    # checking the serialized profile
    payload = player_full(player)

    assert payload["first_name"] == "Alice"
    assert payload["birth_date"] == "2000-01-01"
    assert payload["has_account"] is False


def test_team_and_match_serializers_include_nested_data(db_session):
    # creating teams and a match
    p1 = Player(first_name="A", last_name="One", company="A", license_number="L800002", email="a800@example.com")
    p2 = Player(first_name="B", last_name="Two", company="A", license_number="L800003", email="b800@example.com")
    p3 = Player(first_name="C", last_name="Three", company="B", license_number="L800004", email="c800@example.com")
    p4 = Player(first_name="D", last_name="Four", company="B", license_number="L800005", email="d800@example.com")
    pool = Pool(name="Pool A")
    t1 = Team(company="A", player1=p1, player2=p2, pool=pool)
    t2 = Team(company="B", player1=p3, player2=p4, pool=pool)
    event = Event(event_date=date(2026, 12, 1), event_time="10:00")
    db_session.add_all([t1, t2, event])
    db_session.flush()
    match = Match(
        event_id=event.id,
        team1_id=t1.id,
        team2_id=t2.id,
        court_number=1,
        status="A_VENIR",
    )
    db_session.add(match)
    db_session.commit()

    # checking nested serialization
    match_payload = match_out(match)
    event_payload = event_out(event)

    assert team_out(t1)["company"] == "A"
    assert match_payload["court_number"] == 1
    assert event_payload["matches"][0]["court_number"] == 1
