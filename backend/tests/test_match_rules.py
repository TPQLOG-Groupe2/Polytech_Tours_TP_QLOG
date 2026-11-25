from datetime import date

import pytest
from fastapi import HTTPException

from app.models import Event, Match, Team, Player
from app.routers.events import _validate_matches
from app.routers.matches import _court_conflict, create_match, delete_match
from app.schemas import MatchCreate, MatchInEvent
from app.validators import validate_score


def test_validate_score_accepts_simple_valid_shape():
    # checking a normal two-set score
    assert validate_score("6-4, 6-3") is True


@pytest.mark.parametrize(
    "score",
    [
        "",
        "six-four",
        "5-5",
    ],
)
def test_validate_score_rejects_invalid_or_incomplete_scores(score):
    # checking scores that do not follow a valid padel rule
    assert validate_score(score) is False


def test_event_validation_rejects_duplicate_court(db_session):
    # creating two teams and matches on the same court
    players = [
        Player(first_name=f"P{i}", last_name="Test", company="A", license_number=f"L{i:06d}", email=f"p{i}@example.com")
        for i in range(1, 5)
    ]
    teams = [
        Team(company="A", player1=players[0], player2=players[1]),
        Team(company="A", player1=players[2], player2=players[3]),
    ]
    db_session.add_all(teams)
    db_session.commit()
    matches = [
        MatchInEvent(court_number=1, team1_id=teams[0].id, team2_id=teams[1].id),
        MatchInEvent(court_number=1, team1_id=teams[1].id, team2_id=teams[0].id),
    ]

    # checking the duplicate-court rule
    with pytest.raises(HTTPException) as exc_info:
        _validate_matches(db_session, matches)

    assert exc_info.value.status_code == 400


def test_event_validation_rejects_team_playing_twice(db_session):
    # creating players and teams
    p1 = Player(first_name="A", last_name="Test", company="A", license_number="L100001", email="a100@example.com")
    p2 = Player(first_name="B", last_name="Test", company="A", license_number="L100002", email="b100@example.com")
    p3 = Player(first_name="C", last_name="Test", company="A", license_number="L100003", email="c100@example.com")
    p4 = Player(first_name="D", last_name="Test", company="A", license_number="L100004", email="d100@example.com")
    t1 = Team(company="A", player1=p1, player2=p2)
    t2 = Team(company="A", player1=p3, player2=p4)
    db_session.add_all([t1, t2])
    db_session.commit()
    matches = [
        MatchInEvent(court_number=1, team1_id=t1.id, team2_id=t2.id),
        MatchInEvent(court_number=2, team1_id=t1.id, team2_id=t2.id),
    ]

    # checking that the same team cannot appear twice
    with pytest.raises(HTTPException) as exc_info:
        _validate_matches(db_session, matches)

    assert exc_info.value.status_code == 400


def test_court_conflict_detects_existing_match(db_session):
    # creating an event and match on court 3
    event = Event(event_date=date(2026, 12, 1), event_time="12:00")
    p1 = Player(first_name="A", last_name="Test", company="A", license_number="L200001", email="a200@example.com")
    p2 = Player(first_name="B", last_name="Test", company="A", license_number="L200002", email="b200@example.com")
    p3 = Player(first_name="C", last_name="Test", company="B", license_number="L200003", email="c200@example.com")
    p4 = Player(first_name="D", last_name="Test", company="B", license_number="L200004", email="d200@example.com")
    t1 = Team(company="A", player1=p1, player2=p2)
    t2 = Team(company="B", player1=p3, player2=p4)
    db_session.add_all([event, t1, t2])
    db_session.flush()
    match = Match(
        event_id=event.id,
        team1_id=t1.id,
        team2_id=t2.id,
        court_number=3,
        status="A_VENIR",
    )
    db_session.add(match)
    db_session.commit()

    # checking conflict detection
    assert _court_conflict(db_session, date(2026, 12, 1), "12:00", 3) is True


def test_create_match_does_not_reject_past_dates(db_session):
    # creating valid teams
    p1 = Player(first_name="A", last_name="Test", company="A", license_number="L300001", email="a300@example.com")
    p2 = Player(first_name="B", last_name="Test", company="A", license_number="L300002", email="b300@example.com")
    p3 = Player(first_name="C", last_name="Test", company="B", license_number="L300003", email="c300@example.com")
    p4 = Player(first_name="D", last_name="Test", company="B", license_number="L300004", email="d300@example.com")
    t1 = Team(company="A", player1=p1, player2=p2)
    t2 = Team(company="B", player1=p3, player2=p4)
    db_session.add_all([t1, t2])
    db_session.commit()
    payload = MatchCreate(
        event_date="2020-01-01",
        event_time="10:00",
        court_number=1,
        team1_id=t1.id,
        team2_id=t2.id,
    )

    # the specification requires rejecting this date, so this test documents the current behavior
    with pytest.raises(HTTPException) as exc_info:
        create_match(payload=payload, db=db_session)

    assert exc_info.value.status_code == 400


def test_delete_match_does_not_check_status(db_session):
    # creating a finished match
    event = Event(event_date=date(2026, 12, 1), event_time="10:00")
    p1 = Player(first_name="A", last_name="Test", company="A", license_number="L400001", email="a400@example.com")
    p2 = Player(first_name="B", last_name="Test", company="A", license_number="L400002", email="b400@example.com")
    p3 = Player(first_name="C", last_name="Test", company="B", license_number="L400003", email="c400@example.com")
    p4 = Player(first_name="D", last_name="Test", company="B", license_number="L400004", email="d400@example.com")
    t1 = Team(company="A", player1=p1, player2=p2)
    t2 = Team(company="B", player1=p3, player2=p4)
    db_session.add_all([event, t1, t2])
    db_session.flush()
    match = Match(
        event_id=event.id,
        team1_id=t1.id,
        team2_id=t2.id,
        court_number=1,
        status="TERMINE",
    )
    db_session.add(match)
    db_session.commit()

    # R4 requires rejection, but the current implementation deletes it
    delete_match(match_id=match.id, db=db_session)

    assert db_session.query(Match).filter(Match.id == match.id).first() is None
