"""Shared test setup: lets tests import JARVIS modules and keeps your real
database and settings untouched."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import database  # noqa: E402


@pytest.fixture(autouse=True)
def temp_files(tmp_path, monkeypatch):
    """Every test gets its own empty database and settings file."""
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test_jarvis.db"))
    monkeypatch.setattr(config, "SETTINGS_FILE", str(tmp_path / "test_settings.json"))
    database.init_db()
