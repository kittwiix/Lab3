# -*- coding: utf-8 -*-
import pytest

from money_tracker.logic import TrackerService
from money_tracker.repository import SqliteRepository


@pytest.fixture
def repo(tmp_path):
    return SqliteRepository(tmp_path / "test.db")


@pytest.fixture
def service(repo):
    tracker = TrackerService(repo)
    yield tracker
    tracker.close()
