# Финансовый трекер расходов (ЛР №3, вариант 8)

Приложение для учёта личных расходов. Позволяет добавлять траты, удалять их,
фильтровать по категории, искать по названию и смотреть суммы за последние
семь дней. Есть настольная версия на Tkinter и веб-версия на Litestar.

Работа выполнена по всем уровням: Rare — графический интерфейс и собственные
исключения, Medium — база данных и тесты, Well-done — веб-версия и PostgreSQL
в Docker.

## Состав проекта

- `money_tracker/records.py` — классы `Expense` и `JournalRecord`, проверка полей;
- `money_tracker/errors.py` — собственные исключения приложения;
- `money_tracker/repository.py` — интерфейс `ExpenseRepository`, реализации
  `SqliteRepository` и `PostgresRepository`;
- `money_tracker/logic.py` — операции над расходами, статистика и экспорт в CSV;
- `money_tracker/window.py` — главное окно Tkinter с вкладками «Расходы», «Статистика» и «Журнал»;
- `money_tracker/web/server.py` — веб-приложение Litestar;
- `main.py` — запуск настольной версии;
- `tests/` — тесты pytest.

## Запуск настольной версии

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

На Linux или macOS активация окружения выполняется командой
`source .venv/bin/activate`. Настольная версия хранит данные в файле
`expenses.db` рядом с `main.py`.

## Веб-версия

```bash
pip install -r requirements-web.txt
uvicorn money_tracker.web.server:create_app --factory --reload
```

После запуска страница доступна по адресу `http://127.0.0.1:8000`. Если
переменная `DATABASE_URL` не задана, веб-версия использует SQLite. Для
PostgreSQL нужно указать строку подключения:

```bash
set DATABASE_URL=postgresql://finance:finance@localhost:5432/finance
```

## Docker

В Docker поднимаются два контейнера: PostgreSQL и веб-приложение.

```bash
docker compose up --build
```

Сайт открывается по адресу `http://localhost:8000`. Данные базы сохраняются
в томе `finance_data`.

## Тесты

```bash
pytest tests -v
```

Тесты проверяют валидацию полей, работу хранилища, операции сервиса и
веб-маршруты.

## Краткая справка

Категории: продукты, транспорт, жильё, здоровье, развлечения, одежда и
другое. В настольной версии три вкладки: на «Расходах» слева стоит форма
новой траты, а справа таблица с поиском, на «Статистике» — карточки с итогами,
график за неделю и разбивка по категориям, на «Журнале» — последние действия
и экспорт в CSV. В веб-версии те же действия выполняются через формы на
странице.

## Автор

Дутикова Ксения Дмитриевна, группа Б.ПИН.РИС-24.06, ТвГТУ, 2026.
