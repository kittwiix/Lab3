# -*- coding: utf-8 -*-
"""Пакет финансового трекера «Кошелёк».

Состав пакета:
    errors.py      — собственные исключения приложения;
    records.py     — модель расхода Expense и запись журнала JournalRecord;
    repository.py  — хранилище на SQLite и PostgreSQL;
    logic.py       — сервис TrackerService: операции и подсчёт статистики;
    window.py      — главное окно на Tkinter;
    web/server.py  — веб-версия на Litestar.
"""

__version__ = "1.1"
