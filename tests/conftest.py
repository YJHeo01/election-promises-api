from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app
from app.seed import seed_database


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    database_url = "sqlite+pysqlite:///:memory:"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )

    Base.metadata.create_all(bind=engine)
    with testing_session_local() as db:
        seed_database(db)
        yield db
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    database_url = "sqlite+pysqlite:///:memory:"

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    settings = Settings(custom_gpt_api_key="test-key", database_url=database_url)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-key"}


@pytest.fixture
def base_payload() -> dict[str, str]:
    return {
        "userQuestion": "제9회 지선 인천시장 후보 교통 공약 비교",
        "electionQuery": "제9회 전국동시지방선거",
        "regionQuery": "인천시장",
        "topic": "교통",
    }
