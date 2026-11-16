from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base


@pytest.fixture
def db_engine() -> Generator[Engine, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        Base.metadata.create_all(bind=engine)
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    import app.main as main

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)

    with TestClient(app) as test_client:
        yield test_client
