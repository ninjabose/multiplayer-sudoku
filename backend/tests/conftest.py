from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.game.global_chat import global_chat
from app.game.rooms import manager
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    init_db(f"sqlite:///{db_path}")
    manager.clear()
    global_chat.clear()
    with TestClient(app) as test_client:
        yield test_client
    manager.clear()
    global_chat.clear()
