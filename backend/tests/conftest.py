"""Shared test fixtures for the D&D Currency Manager backend."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.party import Party
from app.models.character import Character


@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with the test database session injected."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Create a test user in the database."""
    user = User(
        username="testplayer",
        hashed_password=hash_password("password123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_dm")
def test_dm_fixture(session: Session) -> User:
    """Create a test DM user in the database."""
    user = User(
        username="testdm",
        hashed_password=hash_password("password123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User) -> dict:
    """Create authorization headers for the test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="dm_headers")
def dm_headers_fixture(test_dm: User) -> dict:
    """Create authorization headers for the DM user."""
    token = create_access_token(test_dm.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="test_party")
def test_party_fixture(session: Session, test_dm: User) -> Party:
    """Create a test party with the DM."""
    party = Party(
        name="Test Party",
        code="TEST",
        dm_id=test_dm.id,
        use_gold=True,
        use_electrum=False,
        use_platinum=False,
    )
    session.add(party)
    session.commit()
    session.refresh(party)
    return party


@pytest.fixture(name="test_character")
def test_character_fixture(
    session: Session, test_user: User, test_party: Party
) -> Character:
    """Create a test character in the test party with some gold."""
    character = Character(
        name="Gandalf",
        character_class="Wizard",
        balance_cp=10000,  # 1 Gold = 100 CP, so 100 Gold
        user_id=test_user.id,
        party_id=test_party.id,
    )
    session.add(character)
    session.commit()
    session.refresh(character)
    return character


@pytest.fixture(name="second_user")
def second_user_fixture(session: Session) -> User:
    """Create a second test user."""
    user = User(
        username="player2",
        hashed_password=hash_password("password123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="second_character")
def second_character_fixture(
    session: Session, second_user: User, test_party: Party
) -> Character:
    """Create a second character in the test party."""
    character = Character(
        name="Aragorn",
        character_class="Ranger",
        balance_cp=5000,  # 50 Gold
        user_id=second_user.id,
        party_id=test_party.id,
    )
    session.add(character)
    session.commit()
    session.refresh(character)
    return character


@pytest.fixture(name="second_auth_headers")
def second_auth_headers_fixture(second_user: User) -> dict:
    """Create authorization headers for the second user."""
    token = create_access_token(second_user.id)
    return {"Authorization": f"Bearer {token}"}
