from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base, SessionLocal, get_db, init_db


def test_base_is_declarative_base():
    # checking the SQLAlchemy base class
    assert issubclass(Base, DeclarativeBase)


def test_session_local_uses_application_engine_without_autoflush():
    # creating a database session
    session = SessionLocal()
    try:
        # checking session type, engine binding and autoflush
        assert isinstance(session, Session)
        assert session.bind is database.engine
        assert session.autoflush is False
    finally:
        session.close()


def test_sqlite_engine_enables_foreign_keys(db_engine):
    # querying the SQLite foreign-key pragma
    with db_engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_get_db_yields_session_and_closes_it(monkeypatch):
    # replacing SessionLocal with a fake session
    session = MagicMock(spec=Session)
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    # creating the dependency generator
    generator = get_db()

    # checking that the session is yielded and not closed yet
    assert next(generator) is session
    session.close.assert_not_called()
    # checking cleanup after generator exhaustion
    with pytest.raises(StopIteration):
        next(generator)
    session.close.assert_called_once_with()


def test_get_db_closes_session_when_generator_is_abandoned(monkeypatch):
    # replacing SessionLocal with a fake session
    session = MagicMock(spec=Session)
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    # starting the dependency generator
    generator = get_db()
    next(generator)

    # simulating an exception and checking cleanup
    with pytest.raises(RuntimeError, match="failure"):
        generator.throw(RuntimeError("failure"))
    session.close.assert_called_once_with()


@pytest.fixture
def empty_engine(monkeypatch):
    # creating an isolated in-memory engine
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", engine)
    yield engine
    engine.dispose()


def test_init_db_creates_registered_tables(empty_engine):
    # checking that the empty engine has no tables
    assert inspect(empty_engine).get_table_names() == []

    # initializing database tables
    init_db()

    # checking that all registered tables were created
    assert set(inspect(empty_engine).get_table_names()) == set(Base.metadata.tables)


def test_init_db_is_idempotent(empty_engine):
    # initializing tables twice
    init_db()
    init_db()

    assert set(inspect(empty_engine).get_table_names()) == set(Base.metadata.tables)
