# tests/test_database.py
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base, SessionLocal, get_db, init_db


# Checks that Base inherits from DeclarativeBase (SQLAlchemy 2.0),
# the base class on which all models rely.
def test_base_is_declarative_base():
    assert issubclass(Base, DeclarativeBase)


# Checks that SessionLocal is a sessionmaker that produces Session instances bound to the correct engine and with autoflush disabled.
def test_session_local_configuration():
    session = SessionLocal()
    try:
        assert isinstance(session, Session)
        assert session.bind is database.engine
        assert session.autoflush is False
    finally:
        session.close()


# Checks that the SQLite foreign keys pragma is enabled, which is important for enforcing foreign key constraints.
def test_foreign_keys_pragma_enabled(db_engine):
    with db_engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1


# Checks that get_db yields a session and closes it after the generator is exhausted.
def test_get_db_yields_session_and_closes(monkeypatch):
    fake_session = MagicMock(spec=Session)
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    gen = get_db()
    assert next(gen) is fake_session
    fake_session.close.assert_not_called()

    with pytest.raises(StopIteration):
        next(gen)
    fake_session.close.assert_called_once()


# Checks that get_db closes the session even if an exception is raised in the generator.
def test_get_db_closes_session_on_exception(monkeypatch):
    fake_session = MagicMock(spec=Session)
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    gen = get_db()
    next(gen)
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("boom"))
    fake_session.close.assert_called_once()


# making a fixture to create an empty engine for testing init_db without affecting the real database
@pytest.fixture
def empty_engine(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", engine)
    yield engine
    engine.dispose()


# Checking that init_db creates all tables defined in Base.metadata.tables.
def test_init_db_creates_all_tables(empty_engine):
    assert inspect(empty_engine).get_table_names() == []

    init_db()

    tables = set(inspect(empty_engine).get_table_names())
    assert tables
    assert tables == set(Base.metadata.tables.keys())


# Checking that init_db can be called multiple times without error (idempotent).
def test_init_db_is_idempotent(empty_engine):
    init_db()
    init_db()