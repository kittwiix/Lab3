# -*- coding: utf-8 -*-
"""Тесты веб-маршрутов: страница, добавление, удаление, CSV и /health."""

from datetime import date

import pytest
from litestar.testing import TestClient

from money_tracker.records import Expense
from money_tracker.web.server import create_app


@pytest.fixture
def client(repo):
    app = create_app(repo)
    with TestClient(app=app) as test_client:
        yield test_client


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Финансовый трекер расходов" in response.text


def test_pie_chart(client, repo):
    repo.add(Expense("Обед", "Продукты", 100, date.today()))
    response = client.get("/")
    assert "conic-gradient" in response.text
    assert "Расходы по категориям" in response.text


def test_add_expense(client, repo):
    response = client.post(
        "/expenses",
        data={
            "title": "Обед",
            "category": "Продукты",
            "amount": "100,50",
            "spent_on": date.today().strftime("%d.%m.%Y"),
            "note": "кафе",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert len(repo.list_expenses()) == 1
    assert repo.list_expenses()[0].amount == 100.5


def test_invalid_expense(client):
    response = client.post(
        "/expenses",
        data={
            "title": "",
            "category": "Продукты",
            "amount": "100",
            "spent_on": date.today().strftime("%d.%m.%Y"),
            "note": "",
        },
    )
    assert response.status_code == 400
    assert "название не может быть пустым" in response.text


def test_delete_expense(client, repo):
    saved = repo.add(Expense("Обед", "Продукты", 100, date.today()))
    response = client.post(f"/expenses/{saved.expense_id}/delete",
                           follow_redirects=False)
    assert response.status_code == 302
    assert repo.list_expenses() == []


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_export_csv(client, repo):
    repo.add(Expense("Обед", "Продукты", 100, date.today()))
    response = client.get("/export.csv")
    assert response.status_code == 200
    assert "Обед" in response.text
    assert "attachment" in response.headers["content-disposition"]
