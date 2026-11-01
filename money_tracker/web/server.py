# -*- coding: utf-8 -*-
"""Веб-версия трекера на Litestar.

Функция create_app() собирает приложение: подключает хранилище,
маршруты и шаблоны Jinja2. Хранилище можно передать снаружи — так
тесты подставляют временную SQLite вместо настоящего Postgres.
"""

import tempfile
from datetime import date
from pathlib import Path
from typing import Annotated

from litestar import Litestar, Request, get, post
from litestar.params import PathParameter
from litestar.plugins.jinja import JinjaTemplateEngine
from litestar.response import Redirect, Response, Template
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig

from ..errors import TrackerError
from ..logic import TrackerService
from ..records import CATEGORIES
from ..repository import create_repository

BASE_DIR = Path(__file__).resolve().parent

# цвета секторов круговой диаграммы, порядок повторяется по кругу
PIE_COLORS = ["#4285f4", "#ea4335", "#fbbc04", "#34a853",
              "#a142f4", "#24c1e0", "#f439a0", "#ff6d01"]


def pie_chart(by_category):
    """Подготовить данные для круговой диаграммы.

    Возвращает список категорий с цветом и готовую заливку для CSS:
    conic-gradient рисует сектора без графических библиотек.
    """
    items = []
    parts = []
    start = 0.0
    for index, item in enumerate(by_category):
        color = PIE_COLORS[index % len(PIE_COLORS)]
        # последний сектор всегда доходит до 100%, иначе останется щель
        end = 100.0 if index == len(by_category) - 1 else start + item["percent"]
        parts.append(f"{color} {start:.2f}% {end:.2f}%")
        items.append({**item, "color": color,
                      "percent_text": f"{item['percent']:.1f}".replace(".", ",")})
        start = end
    return items, "conic-gradient(" + ", ".join(parts) + ")"


def create_app(repository=None):
    """Создать приложение с указанным или выбранным хранилищем."""
    service = TrackerService(repository or create_repository())

    def page(request, error="", status_code=200, form=None):
        # одна общая функция сборки страницы: её вызывают и GET /,
        # и POST /expenses, когда форма заполнена с ошибкой
        category = request.query_params.get("category", "")
        search = request.query_params.get("search", "")
        expenses = service.list_expenses(category or None, search)
        summary = service.summary()
        daily = service.daily_totals(7)
        # горизонтальные полосы: ширина считается в процентах от
        # самого дорогого дня, делить на ноль не даём
        maximum = max((item["sum"] for item in daily), default=0) or 1
        for item in daily:
            item["height"] = round(item["sum"] / maximum * 100, 1)
            item["value_text"] = f"{item['sum']:,.0f}".replace(",", " ")
        pie, pie_gradient = pie_chart(summary["by_category"])
        return Template(
            "index.html",
            status_code=status_code,
            context={
                "expenses": expenses,
                "summary": summary,
                "daily": daily,
                "pie": pie,
                "pie_gradient": pie_gradient,
                "records": service.records(12),
                "category": category,
                "search": search,
                "error": error,
                "form": form or {},
                "categories": CATEGORIES,
                "today": date.today().strftime("%d.%m.%Y"),
            },
        )

    @get("/")
    async def index(request: Request) -> Template:
        return page(request)

    @post("/expenses")
    async def add_expense(request: Request) -> Template | Redirect:
        # данные приходят из HTML-формы, поэтому читаем их как строки,
        # а запятую в сумме меняем на точку до проверки
        form = await request.form()
        values = {
            "title": form.get("title", ""),
            "category": form.get("category", ""),
            "amount": form.get("amount", ""),
            "spent_on": form.get("spent_on", ""),
            "note": form.get("note", ""),
        }
        try:
            service.add_expense(
                values["title"],
                values["category"],
                values["amount"].replace(",", "."),
                values["spent_on"],
                values["note"],
            )
        except TrackerError as error:
            return page(request, str(error), status_code=400, form=values)
        return Redirect("/")

    @post("/expenses/{expense_id:int}/delete")
    async def delete_expense(
        expense_id: Annotated[int, PathParameter()],
    ) -> Redirect:
        try:
            service.delete_expense(expense_id)
        except TrackerError:
            pass
        return Redirect("/")

    @get("/export.csv")
    async def export_csv() -> Response:
        # сервис умеет писать только в файл, поэтому делаем временный
        # файл, отдаём его содержимое и сразу удаляем в finally
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as file:
            path = Path(file.name)
        try:
            service.export_csv(path)
            data = path.read_bytes()
        finally:
            path.unlink(missing_ok=True)
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=expenses.csv"},
        )

    # простой маршрут для проверки, что контейнер поднялся
    @get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return Litestar(
        route_handlers=[
            index,
            add_expense,
            delete_expense,
            export_csv,
            health,
            create_static_files_router(
                path="/static", directories=[BASE_DIR / "static"]
            ),
        ],
        template_config=TemplateConfig(
            directory=BASE_DIR / "templates",
            engine=JinjaTemplateEngine,
        ),
        on_shutdown=[service.close],
    )
