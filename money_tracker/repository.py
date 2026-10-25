# -*- coding: utf-8 -*-
"""Хранилище расходов: SQLite и PostgreSQL."""

import os
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .errors import RepositoryError
from .records import Expense, JournalRecord

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    title_key TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    spent_on TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

POSTGRES_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        title_key TEXT NOT NULL,
        category TEXT NOT NULL,
        amount NUMERIC(12, 2) NOT NULL,
        spent_on DATE NOT NULL,
        note TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS journal (
        id SERIAL PRIMARY KEY,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
)


class ExpenseRepository(ABC):
    """Общий интерфейс хранилища."""

    @abstractmethod
    def add(self, expense):
        ...

    @abstractmethod
    def get(self, expense_id):
        ...

    @abstractmethod
    def list_expenses(self, category=None, search=""):
        ...

    @abstractmethod
    def delete(self, expense_id):
        ...

    @abstractmethod
    def add_record(self, action, details):
        ...

    @abstractmethod
    def list_records(self, limit=50):
        ...

    @abstractmethod
    def close(self):
        ...


class SqliteRepository(ExpenseRepository):
    """Хранилище на sqlite3 для настольной версии."""

    def __init__(self, path="expenses.db"):
        self.path = str(path)
        folder = Path(self.path).parent
        if str(folder) not in ("", "."):
            folder.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as error:
            conn.rollback()
            raise RepositoryError(f"ошибка базы данных: {error}") from error
        finally:
            conn.close()

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(SQLITE_SCHEMA)

    @staticmethod
    def _row_to_expense(row):
        return Expense(
            row["title"],
            row["category"],
            float(row["amount"]),
            row["spent_on"],
            row["note"],
            expense_id=row["id"],
            created_at=row["created_at"],
        )

    def add(self, expense):
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO expenses "
                "(title, title_key, category, amount, spent_on, note, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    expense.title,
                    expense.title.casefold(),
                    expense.category,
                    expense.amount,
                    expense.spent_on.isoformat(),
                    expense.note,
                    expense.created_at,
                ),
            )
            expense_id = cursor.lastrowid
        return self.get(expense_id)

    def get(self, expense_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM expenses WHERE id = ?", (expense_id,)
            ).fetchone()
        return self._row_to_expense(row) if row else None

    def list_expenses(self, category=None, search=""):
        query = "SELECT * FROM expenses WHERE 1 = 1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        search_key = search.strip().casefold()
        if search_key:
            query += " AND title_key LIKE ?"
            params.append(f"%{search_key}%")
        query += " ORDER BY spent_on DESC, id DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_expense(row) for row in rows]

    def delete(self, expense_id):
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cursor.rowcount

    def add_record(self, action, details):
        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO journal (action, details, created_at) VALUES (?, ?, ?)",
                (action, details, created),
            )

    def list_records(self, limit=50):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM journal ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            JournalRecord(row["action"], row["details"], row["created_at"], row["id"])
            for row in rows
        ]

    def close(self):
        pass


class PostgresRepository(ExpenseRepository):
    """Хранилище на PostgreSQL для веб-версии."""

    def __init__(self, url):
        self.url = url
        self._init_db()

    @contextmanager
    def _connect(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(self.url, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except psycopg2.Error as error:
            conn.rollback()
            raise RepositoryError(f"ошибка базы данных: {error}") from error
        finally:
            conn.close()

    def _init_db(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            for statement in POSTGRES_SCHEMA:
                cursor.execute(statement)
            cursor.close()

    @staticmethod
    def _row_to_expense(row):
        return Expense(
            row["title"],
            row["category"],
            float(row["amount"]),
            row["spent_on"],
            row["note"],
            expense_id=row["id"],
            created_at=row["created_at"],
        )

    def add(self, expense):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses "
                "(title, title_key, category, amount, spent_on, note, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (
                    expense.title,
                    expense.title.casefold(),
                    expense.category,
                    expense.amount,
                    expense.spent_on,
                    expense.note,
                    expense.created_at,
                ),
            )
            expense_id = cursor.fetchone()["id"]
            cursor.close()
        return self.get(expense_id)

    def get(self, expense_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
            row = cursor.fetchone()
            cursor.close()
        return self._row_to_expense(row) if row else None

    def list_expenses(self, category=None, search=""):
        query = "SELECT * FROM expenses WHERE 1 = 1"
        params = []
        if category:
            query += " AND category = %s"
            params.append(category)
        search_key = search.strip().casefold()
        if search_key:
            query += " AND title_key LIKE %s"
            params.append(f"%{search_key}%")
        query += " ORDER BY spent_on DESC, id DESC"
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
        return [self._row_to_expense(row) for row in rows]

    def delete(self, expense_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
            count = cursor.rowcount
            cursor.close()
            return count

    def add_record(self, action, details):
        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO journal (action, details, created_at) VALUES (%s, %s, %s)",
                (action, details, created),
            )
            cursor.close()

    def list_records(self, limit=50):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM journal ORDER BY id DESC LIMIT %s", (limit,)
            )
            rows = cursor.fetchall()
            cursor.close()
        return [
            JournalRecord(row["action"], row["details"], row["created_at"], row["id"])
            for row in rows
        ]

    def close(self):
        pass


def create_repository():
    """Выбрать PostgreSQL или SQLite по переменным окружения."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return PostgresRepository(url)
    path = os.environ.get("TRACKER_DB", "expenses.db")
    return SqliteRepository(path)
