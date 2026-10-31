# -*- coding: utf-8 -*-
"""ЛР №3, вариант 8. Запуск настольного приложения.

Файл нужен только для старта: здесь создаётся хранилище, поверх него
сервис с бизнес-логикой и главное окно. Само окно ничего не знает про
базу, оно работает с сервисом.
"""

from money_tracker.logic import TrackerService
from money_tracker.repository import create_repository
from money_tracker.window import MainWindow


def main():
    # create_repository смотрит на переменные окружения: если задан
    # DATABASE_URL, будет PostgreSQL, иначе обычный файл SQLite
    repository = create_repository()
    service = TrackerService(repository)
    window = MainWindow(service)
    window.mainloop()
    # после закрытия окна соединение нужно отпустить
    service.close()


if __name__ == "__main__":
    main()
