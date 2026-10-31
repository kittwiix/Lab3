# -*- coding: utf-8 -*-
"""Сервисный слой: операции над расходами и подсчёт статистики.

Окно Tkinter и веб-страница вызывают только методы TrackerService,
поэтому проверка дублей, запись в журнал и все формулы живут в одном
месте и не расходятся между двумя интерфейсами.
"""

import csv
from datetime import date, timedelta

from .errors import DuplicateExpense, ExpenseNotFound, ExportError
from .records import CATEGORIES, Expense, format_money


class TrackerService:
    """Операции над каталогом расходов."""

    def __init__(self, repository):
        self.repository = repository

    def add_expense(self, title, category, amount, spent_on, note=""):
        # сначала создаём объект: если поля неверные, дальше не пойдём
        expense = Expense(title, category, amount, spent_on, note)
        # ищем такую же трату: совпали название, дата и сумма
        for item in self.repository.list_expenses():
            same_title = item.title.casefold() == expense.title.casefold()
            same_date = item.spent_on == expense.spent_on
            same_amount = abs(item.amount - expense.amount) < 0.005
            if same_title and same_date and same_amount:
                raise DuplicateExpense("такая трата уже есть")
        saved = self.repository.add(expense)
        self.repository.add_record(
            "добавление",
            f"{saved.title}, {saved.amount_text}",
        )
        return saved

    def delete_expense(self, expense_id):
        # сначала читаем запись, чтобы было что написать в журнал
        expense = self.repository.get(expense_id)
        if expense is None:
            raise ExpenseNotFound("расход не найден")
        if self.repository.delete(expense_id) == 0:
            raise ExpenseNotFound("расход не найден")
        self.repository.add_record(
            "удаление",
            f"{expense.title}, {expense.amount_text}",
        )

    def list_expenses(self, category=None, search=""):
        return self.repository.list_expenses(category, search)

    def summary(self):
        """Итог, количество, средний расход и доли категорий."""
        expenses = self.repository.list_expenses()
        total = sum(item.amount for item in expenses)
        count = len(expenses)
        average = total / count if count else 0.0
        # категории идём по справочнику, чтобы порядок был всегда одинаковым
        by_category = []
        for category in CATEGORIES:
            category_sum = sum(
                item.amount for item in expenses if item.category == category
            )
            if category_sum:
                percent = category_sum / total * 100 if total else 0.0
                by_category.append({
                    "name": category,
                    "sum": round(category_sum, 2),
                    "sum_text": format_money(category_sum),
                    "percent": round(percent, 1),
                })
        return {
            "count": count,
            "total": round(total, 2),
            "total_text": format_money(total),
            "average": round(average, 2),
            "average_text": format_money(average),
            "by_category": by_category,
        }

    def daily_totals(self, days=7):
        """Суммы по дням за последние days дней, включая сегодня.

        Дни без трат тоже попадают в результат с нулём, иначе
        на графике пропадали бы пустые столбцы.
        """
        today = date.today()
        start = today - timedelta(days=days - 1)
        totals = {
            start + timedelta(days=index): 0.0
            for index in range(days)
        }
        for expense in self.repository.list_expenses():
            if start <= expense.spent_on <= today:
                totals[expense.spent_on] += expense.amount
        result = []
        for day in sorted(totals):
            value = round(totals[day], 2)
            result.append({
                "date": day,
                "label": day.strftime("%d.%m"),
                "sum": value,
                "sum_text": format_money(value),
            })
        return result

    def export_csv(self, path):
        # utf-8-sig нужен, чтобы Excel не ломал русские буквы
        expenses = self.repository.list_expenses()
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(["Дата", "Название", "Категория", "Сумма", "Комментарий"])
                for item in expenses:
                    writer.writerow([
                        item.date_text,
                        item.title,
                        item.category,
                        f"{item.amount:.2f}".replace(".", ","),
                        item.note,
                    ])
        except OSError as error:
            raise ExportError(f"не удалось сохранить файл: {error}") from error
        self.repository.add_record("экспорт", f"CSV, записей: {len(expenses)}")

    def records(self, limit=20):
        return self.repository.list_records(limit)

    def close(self):
        self.repository.close()
