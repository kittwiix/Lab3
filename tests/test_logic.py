# -*- coding: utf-8 -*-
from datetime import date, timedelta

import pytest

from money_tracker.errors import DuplicateExpense, ExpenseNotFound, ExportError


def add(service, title="Продукты", amount=100.0, spent_on=None, category="Продукты"):
    if spent_on is None:
        spent_on = date.today().strftime("%d.%m.%Y")
    return service.add_expense(title, category, amount, spent_on)


def test_add_and_list(service):
    saved = add(service)
    assert saved.expense_id == 1
    assert len(service.list_expenses()) == 1


def test_duplicate(service):
    add(service)
    with pytest.raises(DuplicateExpense):
        add(service)


def test_delete(service):
    saved = add(service)
    service.delete_expense(saved.expense_id)
    assert service.list_expenses() == []


def test_delete_missing(service):
    with pytest.raises(ExpenseNotFound):
        service.delete_expense(999)


def test_summary(service):
    add(service, "Продукты", 1000)
    add(service, "Автобус", 500, category="Транспорт")
    summary = service.summary()
    assert summary["count"] == 2
    assert summary["total"] == pytest.approx(1500)
    assert summary["average"] == pytest.approx(750)
    assert summary["by_category"][0]["percent"] == pytest.approx(66.7)


def test_daily_totals(service):
    today = date.today()
    add(service, "Продукты", 100, spent_on=today.strftime("%d.%m.%Y"))
    add(service, "Продукты", 50, spent_on=(today - timedelta(days=1)).strftime("%d.%m.%Y"),
        category="Другое")
    data = service.daily_totals(7)
    assert len(data) == 7
    assert data[-1]["sum"] == pytest.approx(100)
    assert data[-2]["sum"] == pytest.approx(50)


def test_export_csv(service, tmp_path):
    add(service, "Продукты", 100)
    path = tmp_path / "expenses.csv"
    service.export_csv(path)
    text = path.read_text(encoding="utf-8-sig")
    assert "Дата;Название;Категория;Сумма;Комментарий" in text
    assert "Продукты" in text


def test_export_error(service):
    with pytest.raises(ExportError):
        service.export_csv("Z:/no/such/folder/expenses.csv")
