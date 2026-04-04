"""
Shared test fixtures.

All tests use an in-memory SQLite database so they are fast and isolated.
External APIs (AgNet, CIS) are always mocked — tests must never hit the
real servers.
"""

import pytest
from app import create_app
from repository.db import close_db


@pytest.fixture()
def app():
    """Create a Flask app backed by an in-memory DB."""
    application = create_app(db_path=":memory:")
    application.config["TESTING"] = True
    yield application
    close_db()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()
