# -*- coding: utf-8 -*-
"""Тесты модели Expense: проверки полей, формулы и dunder-методы."""

import math
from datetime import date, timedelta

import pytest

from money_tracker.errors import ValidationError
from money_tracker.records import Expense, format_money, parse_date


def test_valid_expense():
    item = Expense("Продукты", "Продукты", 1293.1, "26.10.2026", "Пятёрочка")
    assert item.title == "Продукты"
    assert item.amount == pytest.approx(1293.1)
    assert item.spent_on == date(2026, 10, 26)
    assert item.amount_text == "1 293,10 руб."


def test_empty_title():
    with pytest.raises(ValidationError):
        Expense("   ", "Продукты", 100, "26.10.2026")


def test_long_title():
    with pytest.raises(ValidationError):
        Expense("а" * 81, "Продукты", 100, "26.10.2026")


def test_unknown_category():
    with pytest.raises(ValidationError):
        Expense("Обед", "Еда", 100, "26.10.2026")


@pytest.mark.parametrize("value", [-1, 0])
def test_bad_amount(value):
    with pytest.raises(ValidationError):
        Expense("Обед", "Продукты", value, "26.10.2026")


@pytest.mark.parametrize("value", [math.nan, math.inf, math.inf * -1])
def test_not_finite_amount(value):
    with pytest.raises(ValidationError):
        Expense("Обед", "Продукты", value, "26.10.2026")


def test_bool_amount():
    with pytest.raises(ValidationError):
        Expense("Обед", "Продукты", True, "26.10.2026")


def test_date_in_future():
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError):
        Expense("Обед", "Продукты", 100, tomorrow)


def test_bad_date():
    with pytest.raises(ValidationError):
        Expense("Обед", "Продукты", 100, "32.13.2026")


def test_parse_date_formats():
    assert parse_date("26.10.2026") == date(2026, 10, 26)
    assert parse_date("2026-10-26") == date(2026, 10, 26)


def test_format_money():
    assert format_money(0) == "0,00 руб."
    assert format_money(15517.2) == "15 517,20 руб."


def test_str_repr_eq():
    first = Expense("Обед", "Продукты", 500, "26.10.2026", "кафе")
    second = Expense("Обед", "Продукты", 500, "26.10.2026", "кафе")
    assert "26.10.2026" in str(first)
    assert "Expense(" in repr(first)
    assert first == second
