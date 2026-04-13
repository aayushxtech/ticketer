"""
Test configuration — shared fixtures for the entire test suite.

Key design decisions:
  • Uses a SEPARATE test database (test.db) so tests never touch production data.
  • Tables are recreated before EACH test for complete isolation.
  • The test DB file is cleaned up after the session ends.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Override DATABASE_URL BEFORE importing any app code so that `db.py`
# picks up the test database URL instead of the production one.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///./test.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.db import Base, get_db  # noqa: E402
from app.main import app         # noqa: E402

# ---------------------------------------------------------------------------
# Test engine and session factory
# ---------------------------------------------------------------------------
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# ---------------------------------------------------------------------------
# Per-test fixture: recreate all tables for complete isolation.
#
# We drop and recreate tables before each test so that every test starts
# with a perfectly clean database.  This is slightly slower than a
# transaction-rollback approach but avoids conflicts with the booking
# service's own commit/rollback calls.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_tables():
    """Drop and recreate all tables before each test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    # Optional post-test cleanup (tables are dropped at start of next test)


# ---------------------------------------------------------------------------
# Session-scoped: clean up the test.db file after all tests complete
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Remove the test.db file after the entire test session."""
    yield
    if os.path.exists("test.db"):
        os.remove("test.db")


# ---------------------------------------------------------------------------
# Per-test fixture: DB session
# ---------------------------------------------------------------------------
@pytest.fixture()
def db_session():
    """
    Yields a fresh database session for each test.
    Closed after the test completes.
    """
    session = TestSessionLocal()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Per-test fixture: FastAPI TestClient with overridden DB dependency
# ---------------------------------------------------------------------------
@pytest.fixture()
def client():
    """
    Provides a FastAPI TestClient.

    The app's `get_db` dependency is overridden to use the test engine's
    session factory, so every route handler gets a test DB session.
    """

    def _override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper fixture: create a show with seats (used by many tests)
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_show(client):
    """
    Creates a sample show with 10 seats via the admin API.
    Returns the response JSON dict.
    """
    response = client.post(
        "/admin/create-show",
        json={
            "name": "Test Show",
            "datetime": "2026-06-01T19:00:00",
            "total_seats": 10,
        },
    )
    assert response.status_code == 200
    return response.json()
