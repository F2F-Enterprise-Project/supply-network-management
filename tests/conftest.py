import os
import pytest
from starlette.testclient import TestClient

os.environ["DB_PATH"] = "test_snm.db"

import app as app_module  # noqa: E402

_asgi_app = app_module.app.build_app()


@pytest.fixture(scope="session")
def client():
    with TestClient(_asgi_app) as c:
        yield c
