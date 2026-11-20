# tests/test_database.py
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base, SessionLocal, get_db, init_db


# Vérifie que Base hérite bien de DeclarativeBase (SQLAlchemy 2.0),
# la classe de base sur laquelle tous les modèles s'appuient.
def test_base_is_declarative_base():
    assert issubclass(Base, DeclarativeBase)


# Vérifie que SessionLocal fabrique une vraie session, liée à l'engine
# de database.py et avec autoflush désactivé comme dans la config.
def test_session_local_configuration():
    session = SessionLocal()
    try:
        assert isinstance(session, Session)
        assert session.bind is database.engine
        assert session.autoflush is False
    finally:
        session.close()


# Vérifie que le listener _set_sqlite_pragma active bien les clés
# étrangères (PRAGMA foreign_keys = 1) à chaque connexion SQLite.
def test_foreign_keys_pragma_enabled(db_engine):
    with db_engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1


# Vérifie que get_db fournit une session, puis la ferme une fois le
# générateur terminé (on espionne une fausse session avec un MagicMock).
def test_get_db_yields_session_and_closes(monkeypatch):
    fake_session = MagicMock(spec=Session)
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    gen = get_db()
    assert next(gen) is fake_session
    fake_session.close.assert_not_called()

    with pytest.raises(StopIteration):
        next(gen)
    fake_session.close.assert_called_once()


# Vérifie que get_db ferme quand même la session si une erreur survient
# pendant son utilisation.
def test_get_db_closes_session_on_exception(monkeypatch):
    fake_session = MagicMock(spec=Session)
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    gen = get_db()
    next(gen)
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("boom"))
    fake_session.close.assert_called_once()


# on fait une base vide qui va substituer database?engine
# comme ca init_db ne touche pas la vraie base.
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


# On verifie que init_db crée bien toutes les tables définies 
# sur Base.metadata.
def test_init_db_creates_all_tables(empty_engine):
    assert inspect(empty_engine).get_table_names() == []

    init_db()

    tables = set(inspect(empty_engine).get_table_names())
    assert tables
    assert tables == set(Base.metadata.tables.keys())


# Vérifie qu'appeler init_db deux fois ne plante pas
# le test réussi si on ne lève pas d'exception.
def test_init_db_is_idempotent(empty_engine):
    init_db()
    init_db()