# -*- coding: utf-8 -*-
"""Общие фикстуры: временная база на каждый тест."""

import pytest

from money_tracker.logic import TrackerService
from money_tracker.repository import SqliteRepository


@pytest.fixture
def repo(tmp_path):
    # tmp_path pytest создаёт сам и удаляет после теста,
    # поэтому рабочий файл expenses.db тесты не трогают
    return SqliteRepository(tmp_path / "test.db")


@pytest.fixture
def service(repo):
    tracker = TrackerService(repo)
    yield tracker
    tracker.close()
