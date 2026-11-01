# -*- coding: utf-8 -*-
"""Тесты хранилища на SQLite: запись, чтение, фильтры и журнал."""

from money_tracker.records import Expense


def make_expense(title="Продукты", category="Продукты", amount=100.0,
                 spent_on="26.10.2026", note="", place="", payment="Карта"):
    return Expense(title, category, amount, spent_on, note, place, payment)


def test_add_and_get(repo):
    saved = repo.add(make_expense())
    assert saved.expense_id == 1
    assert repo.get(1).title == "Продукты"


def test_get_missing(repo):
    assert repo.get(999) is None


def test_new_columns_round_trip(repo):
    repo.add(make_expense(place="Лента", payment="Перевод"))
    saved = repo.get(1)
    assert saved.place == "Лента"
    assert saved.payment == "Перевод"


def test_list_and_filter(repo):
    repo.add(make_expense())
    repo.add(make_expense("Автобус", "Транспорт", 65))
    rows = repo.list_expenses(category="Транспорт")
    assert len(rows) == 1
    assert rows[0].title == "Автобус"


def test_search_casefold(repo):
    repo.add(make_expense("Продукты в Пятёрочке"))
    repo.add(make_expense("Аптека", "Здоровье", 780.4))
    assert len(repo.list_expenses(search="ПРОДУКТЫ")) == 1
    assert len(repo.list_expenses(search="аптек")) == 1


def test_delete(repo):
    saved = repo.add(make_expense())
    assert repo.delete(saved.expense_id) == 1
    assert repo.get(saved.expense_id) is None


def test_journal(repo):
    repo.add_record("добавление", "Продукты, 100,00 руб.")
    records = repo.list_records()
    assert len(records) == 1
    assert records[0].action == "добавление"
