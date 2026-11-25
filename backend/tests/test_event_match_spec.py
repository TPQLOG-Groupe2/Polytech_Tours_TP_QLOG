from datetime import date

import pytest
from fastapi import HTTPException

from app.models import Event, Match, Player, Team
from app.routers.events import create_event
from app.routers.matches import create_match
from app.schemas import EventCreate, MatchCreate, MatchInEvent


def test_create_event_rejects_past_date(db_session):
    # creating teams
    p1 = Player(first_name="A", last_name="Test", company="A", license_number="L600001", email="a600@example.com")
    p2 = Player(first_name="B", last_name="Test", company="A", license_number="L600002", email="b600@example.com")
    p3 = Player(first_name="C", last_name="Test", company="B", license_number="L600003", email="c600@example.com")
    p4 = Player(first_name="D", last_name="Test", company="B", license_number="L600004", email="d600@example.com")
    t1 = Team(company="A", player1=p1, player2=p2)
    t2 = Team(company="B", player1=p3, player2=p4)
    db_session.add_all([t1, t2])
    db_session.commit()
    payload = EventCreate(
        event_date="2020-01-01",
        event_time="10:00",
        matches=[
            MatchInEvent(court_number=1, team1_id=t1.id, team2_id=t2.id)
        ],
    )

    # R1 requires rejecting past dates
    with pytest.raises(HTTPException) as exc_info:
        create_event(payload=payload, db=db_session)

    assert exc_info.value.status_code == 400


def test_create_match_rejects_court_conflict(db_session):
    # creating an occupied court
    event = Event(event_date=date(2026, 12, 1), event_time="10:00")
    p1 = Player(first_name="A", last_name="Test", company="A", license_number="L700001", email="a700@example.com")
    p2 = Player(first_name="B", last_name="Test", company="A", license_number="L700002", email="b700@example.com")
    p3 = Player(first_name="C", last_name="Test", company="B", license_number="L700003", email="c700@example.com")
    p4 = Player(first_name="D", last_name="Test", company="B", license_number="L700004", email="d700@example.com")
    t1 = Team(company="A", player1=p1, player2=p2)
    t2 = Team(company="B", player1=p3, player2=p4)
    db_session.add_all([event, t1, t2])
    db_session.flush()
    db_session.add(
        Match(
            event_id=event.id,
            team1_id=t1.id,
            team2_id=t2.id,
            court_number=1,
            status="A_VENIR",
        )
    )
    db_session.commit()
    payload = MatchCreate(
        event_date="2026-12-01",
        event_time="10:00",
        court_number=1,
        team1_id=t1.id,
        team2_id=t2.id,
    )

    # R2 requires a 409 conflict
    with pytest.raises(HTTPException) as exc_info:
        create_match(payload=payload, db=db_session)

    assert exc_info.value.status_code == 409
