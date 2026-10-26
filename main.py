# -*- coding: utf-8 -*-
"""ЛР №3, вариант 8. Запуск настольного приложения."""

from money_tracker.logic import TrackerService
from money_tracker.repository import create_repository
from money_tracker.window import MainWindow


def main():
    service = TrackerService(create_repository())
    window = MainWindow(service)
    window.mainloop()


if __name__ == "__main__":
    main()
