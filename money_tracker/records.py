# -*- coding: utf-8 -*-
"""Модель расхода и журнала действий."""

import math
from dataclasses import dataclass
from datetime import date, datetime

from .errors import ValidationError

CATEGORIES = (
    "Продукты",
    "Транспорт",
    "Жильё",
    "Здоровье",
    "Развлечения",
    "Одежда",
    "Другое",
)

MIN_DATE = date(2000, 1, 1)
MAX_AMOUNT = 1_000_000


def format_money(value):
    """Сумма в виде 1 293,10 руб."""
    text = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{text} руб."


def parse_date(value):
    """Разобрать дату из ДД.ММ.ГГГГ или ГГГГ-ММ-ДД."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValidationError("дата должна быть строкой")
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValidationError("дата должна быть в формате ДД.ММ.ГГГГ")


class Expense:
    """Одна запись о расходе."""

    def __init__(self, title, category, amount, spent_on, note="",
                 expense_id=None, created_at=None):
        self.expense_id = expense_id
        self.title = title
        self.category = category
        self.amount = amount
        self.spent_on = spent_on
        self.note = note
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = self._check_text(value, "название", 80)

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if not isinstance(value, str) or value not in CATEGORIES:
            raise ValidationError("неизвестная категория")
        self._category = value

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = self._check_amount(value)

    @property
    def spent_on(self):
        return self._spent_on

    @spent_on.setter
    def spent_on(self, value):
        self._spent_on = self._check_date(value)

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValidationError("комментарий должен быть строкой")
        value = value.strip()
        if len(value) > 200:
            raise ValidationError("комментарий длиннее 200 символов")
        self._note = value

    @property
    def amount_text(self):
        return format_money(self.amount)

    @property
    def date_text(self):
        return self.spent_on.strftime("%d.%m.%Y")

    @staticmethod
    def _check_text(value, field, limit):
        if not isinstance(value, str):
            raise ValidationError(f"{field} должно быть строкой")
        value = value.strip()
        if not value:
            raise ValidationError(f"{field} не может быть пустым")
        if len(value) > limit:
            raise ValidationError(f"{field} длиннее {limit} символов")
        return value

    @staticmethod
    def _check_amount(value):
        if isinstance(value, str):
            try:
                value = float(value.strip().replace(",", "."))
            except ValueError:
                raise ValidationError("сумма должна быть числом") from None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError("сумма должна быть числом")
        if not math.isfinite(value) or value <= 0:
            raise ValidationError("сумма должна быть положительной")
        if value > MAX_AMOUNT:
            raise ValidationError("сумма слишком большая")
        return round(float(value), 2)

    @staticmethod
    def _check_date(value):
        value = parse_date(value)
        if value < MIN_DATE:
            raise ValidationError("дата слишком ранняя")
        if value > date.today():
            raise ValidationError("дата не может быть в будущем")
        return value

    def __str__(self):
        return (f"{self.date_text} | {self.category} | {self.title} | "
                f"{self.amount_text}")

    def __repr__(self):
        return (f"Expense(id={self.expense_id!r}, title={self.title!r}, "
                f"category={self.category!r}, amount={self.amount!r}, "
                f"spent_on={self.spent_on!r})")

    def __eq__(self, other):
        if not isinstance(other, Expense):
            return NotImplemented
        return (self.title == other.title and self.category == other.category
                and self.amount == other.amount and self.spent_on == other.spent_on
                and self.note == other.note)


@dataclass
class JournalRecord:
    """Запись журнала действий."""

    action: str
    details: str
    created: str
    record_id: int | None = None

    def __str__(self):
        return f"{self.created} {self.action}: {self.details}"
