# -*- coding: utf-8 -*-
"""Собственные исключения приложения."""


class TrackerError(Exception):
    """Общая ошибка трекера."""


class ValidationError(TrackerError):
    """Некорректные данные расхода."""


class RepositoryError(TrackerError):
    """Ошибка при работе с базой данных."""


class ExpenseNotFound(TrackerError):
    """Расход не найден."""


class DuplicateExpense(TrackerError):
    """Такой расход уже добавлен."""


class ExportError(TrackerError):
    """Не удалось сохранить файл."""
