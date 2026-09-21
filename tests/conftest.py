"""Point every test at a throwaway database instead of the real one."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def temporary_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate each test with its own SQLite file."""
    from app import db

    database = tmp_path / "test_helpdesk.db"
    monkeypatch.setenv("HELPDESK_DB", str(database))
    db.init_db()
    yield database
    os.environ.pop("HELPDESK_DB", None)
