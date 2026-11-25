from datetime import date

from app.models import Event, Match, Player, Pool, Team, User
from app.services.rankings import (
    compute_my_results,
    compute_rankings,
    parse_sets,
    player_team_ids,
)


def _make_team(db_session, number, player1, player2):
    # creating a team for a ranking scenario
    team = Team(
        company=f"Company {number}",
        player1=player1,
        player2=player2,
    )
    db_session.add(team)
    return team


def test_parse_sets_returns_tuples():
    # parsing a simple two-set score
    assert parse_sets("6-4, 6-3") == [(6, 4), (6, 3)]


def test_parse_sets_returns_empty_list_for_missing_score():
    # checking the empty-score behavior
    assert parse_sets(None) == []


def test_compute_rankings_gives_three_points_for_a_win(db_session):
    # creating two players and two teams
    player1 = Player(first_name="A", last_name="One", company="A", license_number="L000001", email="a@example.com")
    player2 = Player(first_name="B", last_name="Two", company="B", license_number="L000002", email="b@example.com")
    player3 = Player(first_name="C", last_name="Three", company="A", license_number="L000003", email="c@example.com")
    player4 = Player(first_name="D", last_name="Four", company="B", license_number="L000004", email="d@example.com")
    team1 = Team(company="Company A", player1=player1, player2=player3)
    team2 = Team(company="Company B", player1=player2, player2=player4)
    event = Event(event_date=date(2026, 11, 23), event_time="10:00")
    db_session.add_all([team1, team2, event])
    db_session.flush()

    # creating a finished match won by team 1
    match = Match(
        event_id=event.id,
        team1_id=team1.id,
        team2_id=team2.id,
        court_number=1,
        status="TERMINE",
        score_team1="6-4, 6-3",
        score_team2="4-6, 3-6",
    )
    db_session.add(match)
    db_session.commit()

    # checking that the ranking applies the specification's 3-point win
    ranking = compute_rankings(db_session)

    assert ranking[0]["company"] == "Company A"
    assert ranking[0]["wins"] == 1
    assert ranking[0]["points"] == 3


def test_player_team_ids_finds_player_memberships(db_session):
    # creating a player and a team
    player = Player(first_name="Alice", last_name="Test", company="A", license_number="L000010", email="alice@example.com")
    partner = Player(first_name="Bob", last_name="Test", company="A", license_number="L000011", email="bob@example.com")
    team = Team(company="A", player1=player, player2=partner)
    db_session.add(team)
    db_session.commit()

    # checking team membership
    assert player_team_ids(db_session, player.id) == [team.id]


def test_compute_my_results_reports_win_and_statistics(db_session):
    # creating player, opponent, team and finished match
    player = Player(first_name="Alice", last_name="Test", company="A", license_number="L000020", email="alice.results@example.com")
    partner = Player(first_name="Bob", last_name="Test", company="A", license_number="L000021", email="bob.results@example.com")
    opponent1 = Player(first_name="Charlie", last_name="Test", company="B", license_number="L000022", email="charlie@example.com")
    opponent2 = Player(first_name="Dana", last_name="Test", company="B", license_number="L000023", email="dana@example.com")
    user = User(email="alice.results@example.com", password_hash="hashed", role="JOUEUR")
    player.user = user
    team1 = Team(company="A", player1=player, player2=partner)
    team2 = Team(company="B", player1=opponent1, player2=opponent2)
    event = Event(event_date=date(2026, 11, 23), event_time="10:00")
    db_session.add_all([team1, team2, event])
    db_session.flush()
    match = Match(
        event_id=event.id,
        team1_id=team1.id,
        team2_id=team2.id,
        court_number=2,
        status="TERMINE",
        score_team1="6-4, 6-3",
        score_team2="4-6, 3-6",
    )
    db_session.add(match)
    db_session.commit()

    # checking personal result and statistics
    result = compute_my_results(db_session, player)

    assert result["statistics"] == {
        "total_matches": 1,
        "wins": 1,
        "losses": 0,
        "win_rate": 100.0,
    }
    assert result["results"][0]["result"] == "VICTOIRE"
