# -*- coding: utf-8 -*-
"""Главное окно трекера: вкладки «Расходы», «Статистика» и «Журнал».

Окно ничего не знает про базу: оно получает готовый TrackerService и
вызывает только его методы. Поэтому одна и та же логика работает и в
окне, и в веб-версии. Все данные перечитываются в refresh().
"""

import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from .errors import TrackerError
from .records import CATEGORIES

# палитра в духе Google: светлый фон, синий акцент и мягкие подложки
BG = "#f8f9fa"
CARD = "#ffffff"
HEADER = "#e8f0fe"
HEADER_TEXT = "#174ea6"
HEADER_MUTED = "#5f6368"
INK = "#202124"
MUTED = "#5f6368"
ACCENT = "#1a73e8"
ACCENT_DARK = "#174ea6"
PRIMARY_ACTIVE = "#1765cc"
TRACK = "#e8f0fe"
BORDER = "#dadce0"
# цвета секторов круговой диаграммы
PIE_COLORS = ["#4285f4", "#ea4335", "#fbbc04", "#34a853",
              "#a142f4", "#24c1e0", "#f439a0", "#ff6d01"]


class MainWindow(tk.Tk):
    """Окно с вкладками: таблица расходов, статистика и журнал действий."""

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.title("Кошелёк — финансовый трекер расходов")
        self.geometry("1200x660")
        self.minsize(980, 560)
        self.configure(bg=BG)
        self._build_style()
        self._build_menu()
        self._build_header()
        self._build_tabs()
        self._build_status()
        self.refresh()

    # ---------- оформление ----------

    def _build_style(self):
        # тема clam лучше реагирует на настройку цветов, чем стандартная
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=INK,
                        font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=INK,
                        font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=CARD, foreground=MUTED,
                        font=("Segoe UI", 9))
        style.configure("Small.TLabel", background=CARD, foreground=MUTED,
                        font=("Segoe UI", 8))
        style.configure("Kpi.TLabel", background=CARD, foreground=ACCENT_DARK,
                        font=("Segoe UI Semibold", 18))
        style.configure("KpiTitle.TLabel", background=CARD, foreground=MUTED,
                        font=("Segoe UI", 8))
        style.configure("TLabelframe", background=CARD, bordercolor=BORDER,
                        relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", background=CARD, foreground=MUTED,
                        font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9), padding=(12, 7),
                        background=CARD, foreground=ACCENT, bordercolor=BORDER)
        style.map("TButton",
                  background=[("active", "#f1f3f4")],
                  foreground=[("active", ACCENT_DARK)])
        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                        borderwidth=0, padding=(14, 9),
                        font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton",
                  background=[("active", PRIMARY_ACTIVE), ("pressed", ACCENT_DARK)])
        style.configure("Danger.TButton", foreground="#d93025", background=CARD)
        style.map("Danger.TButton",
                  background=[("active", "#fce8e6")],
                  foreground=[("active", "#b3261e")])
        style.configure("TEntry", padding=6, fieldbackground=CARD,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        style.map("TEntry", bordercolor=[("focus", ACCENT)])
        style.configure("TCombobox", padding=6, fieldbackground=CARD,
                        bordercolor=BORDER, arrowcolor=MUTED)
        style.map("TCombobox",
                  bordercolor=[("focus", ACCENT)],
                  fieldbackground=[("readonly", CARD)])
        style.configure("Treeview", background=CARD, fieldbackground=CARD,
                        foreground=INK, rowheight=28, font=("Segoe UI", 9),
                        borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9),
                        background="#f1f3f4", foreground=MUTED, relief="flat")
        style.map("Treeview", background=[("selected", TRACK)],
                  foreground=[("selected", INK)])

    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт в CSV", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Обновить", command=self.refresh)
        view_menu.add_command(label="Журнал действий", command=self.show_journal_tab)
        menubar.add_cascade(label="Вид", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)
        self.config(menu=menubar)

    def _build_header(self):
        # светлая полоса сверху: знак приложения, название и итоговая сумма
        header = tk.Frame(self, bg=HEADER)
        header.pack(fill="x")

        left = tk.Frame(header, bg=HEADER)
        left.pack(side="left", padx=20, pady=18)
        mark = tk.Canvas(left, width=42, height=42, bg=HEADER,
                         highlightthickness=0)
        mark.create_oval(1, 1, 41, 41, fill=ACCENT, outline="")
        mark.create_text(21, 21, text="₽", fill="white",
                         font=("Segoe UI Semibold", 17))
        mark.pack(side="left", padx=(0, 12))
        titles = tk.Frame(left, bg=HEADER)
        titles.pack(side="left")
        tk.Label(titles, text="Кошелёк", bg=HEADER, fg=HEADER_TEXT,
                 font=("Segoe UI Semibold", 20)).pack(anchor="w")
        tk.Label(titles, text="учёт личных расходов, вариант 8", bg=HEADER,
                 fg=HEADER_MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        right = tk.Frame(header, bg=HEADER)
        right.pack(side="right", padx=20, pady=18)
        self.header_total = tk.Label(right, text="0,00 руб.", bg=HEADER,
                                     fg=HEADER_TEXT,
                                     font=("Segoe UI Semibold", 18))
        self.header_total.pack(anchor="e")
        tk.Label(right, text="потрачено всего", bg=HEADER, fg=HEADER_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="e")

        # кнопка справки стоит рядом с итогом, чтобы её было видно сразу
        help_button = tk.Button(header, text="Справка", command=self.show_help,
                                bg=HEADER, fg=ACCENT_DARK, relief="flat", bd=0,
                                activebackground="#d2e3fc",
                                activeforeground=ACCENT_DARK,
                                cursor="hand2", font=("Segoe UI", 9),
                                padx=14, pady=6)
        help_button.pack(side="right", padx=(0, 6))
        # тонкая линия отделяет шапку от содержимого, как в веб-версии
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _build_status(self):
        self.status_var = tk.StringVar(value="Готово")
        bar = tk.Frame(self, bg=BG, height=26)
        bar.pack(side="bottom", fill="x")
        tk.Label(bar, textvariable=self.status_var, bg=BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="left", padx=18)

    # ---------- вкладки ----------

    def _build_tabs(self):
        # своя полоса вкладок: синяя черта плавно переезжает к выбранной
        self._tab_bar = tk.Frame(self, bg=CARD)
        self._tab_bar.pack(fill="x")
        self._tab_buttons = {}
        self._tab_frames = {}
        self._current_tab = None
        for key, title in (("expenses", "Расходы"),
                           ("stats", "Статистика"),
                           ("journal", "Журнал")):
            label = tk.Label(self._tab_bar, text=title, bg=CARD, fg=MUTED,
                             cursor="hand2", font=("Segoe UI", 10),
                             padx=22, pady=14)
            label.pack(side="left")
            label.bind("<Button-1>",
                       lambda event, name=key: self._select_tab(name))
            self._tab_buttons[key] = label
        self._indicator = tk.Frame(self._tab_bar, bg=ACCENT, height=3)
        self._indicator.place(x=0, y=0, width=0, height=3)
        self._tab_bar.bind("<Configure>",
                           lambda event: self.after_idle(self._place_indicator))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        self._body = tk.Frame(self, bg=BG)
        self._body.pack(fill="both", expand=True)
        self.tab_expenses = tk.Frame(self._body, bg=BG, padx=12, pady=12)
        self.tab_stats = tk.Frame(self._body, bg=BG, padx=12, pady=12)
        self.tab_journal = tk.Frame(self._body, bg=BG, padx=12, pady=12)
        self._tab_frames = {"expenses": self.tab_expenses,
                            "stats": self.tab_stats,
                            "journal": self.tab_journal}
        self._build_expenses_tab()
        self._build_stats_tab()
        self._build_journal_tab()
        self._select_tab("expenses", animate=False)

    def _select_tab(self, key, animate=True):
        """Показать вкладку и перевести на неё подчёркивание."""
        if self._current_tab == key:
            return
        self._current_tab = key
        for name, frame in self._tab_frames.items():
            if name != key:
                frame.pack_forget()
        frame = self._tab_frames[key]
        frame.pack(fill="both", expand=True, pady=(10, 0))
        for name, label in self._tab_buttons.items():
            active = name == key
            label.configure(fg=ACCENT_DARK if active else MUTED,
                            font=("Segoe UI Semibold", 10) if active
                            else ("Segoe UI", 10))
        self._place_indicator()
        # содержимое новой вкладки чуть поднимается вверх, как панель в вебе
        if animate:
            self._grow_in(frame, 10)

    def _grow_in(self, frame, step):
        if self._tab_frames.get(self._current_tab) is not frame:
            return
        frame.pack_configure(pady=(step, 0))
        if step > 0:
            self.after(14, lambda: self._grow_in(frame, step - 1))

    def _place_indicator(self):
        if not self._current_tab:
            return
        label = self._tab_buttons[self._current_tab]
        start = self._indicator.winfo_x()
        self._indicator.place(x=start, width=label.winfo_width(), height=3,
                              y=self._tab_bar.winfo_height() - 3)
        self._slide_indicator(start, label.winfo_x(), 0)

    def _slide_indicator(self, start, goal, step):
        k = min(step / 10, 1)
        k = 1 - (1 - k) ** 3
        self._indicator.place_configure(x=int(start + (goal - start) * k))
        if k < 1 and self._current_tab:
            self.after(14, lambda: self._slide_indicator(start, goal, step + 1))

    def _build_expenses_tab(self):
        # слева форма, справа таблица — так форма не растягивается на всё окно
        self.tab_expenses.columnconfigure(1, weight=1)
        self.tab_expenses.rowconfigure(0, weight=1)

        form = ttk.LabelFrame(self.tab_expenses, text="Новая трата", padding=14)
        form.grid(row=0, column=0, sticky="nsw", padx=(0, 14))

        self.title_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        self.note_var = tk.StringVar()

        self.title_entry = self._field(form, "Название", self.title_var)
        block = ttk.Frame(form, style="Card.TFrame")
        block.pack(fill="x", pady=(0, 8))
        ttk.Label(block, text="Категория", style="Card.TLabel").pack(anchor="w")
        ttk.Combobox(block, textvariable=self.category_var, values=CATEGORIES,
                     state="readonly", width=24).pack(fill="x", pady=(2, 0))
        self._field(form, "Сумма, руб.", self.amount_var)
        self._field(form, "Дата", self.date_var)
        self._field(form, "Комментарий", self.note_var)

        ttk.Button(form, text="Записать", style="Accent.TButton",
                   command=self.on_add).pack(fill="x", pady=(6, 0))

        right = ttk.Frame(self.tab_expenses)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(right)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(toolbar, text="Поиск:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=26)
        search_entry.pack(side="left", padx=(4, 12))
        search_entry.bind("<Return>", lambda event: self.refresh())

        ttk.Label(toolbar, text="Категория:").pack(side="left")
        self.filter_var = tk.StringVar(value="Все")
        filter_box = ttk.Combobox(toolbar, textvariable=self.filter_var,
                                  values=("Все",) + CATEGORIES, state="readonly",
                                  width=13)
        filter_box.pack(side="left", padx=(4, 10))
        filter_box.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Button(toolbar, text="Найти", command=self.refresh).pack(side="left")
        ttk.Button(toolbar, text="Сбросить", command=self.reset_filters).pack(
            side="left", padx=(6, 0))

        # таблица расходов: комментарий сюда не выводим, чтобы не сжимать колонки
        table_frame = ttk.Frame(right, style="Card.TFrame")
        table_frame.grid(row=1, column=0, sticky="nsew")
        columns = ("id", "date", "title", "category", "amount")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                 selectmode="browse")
        headings = {
            "id": ("№", 46),
            "date": ("Дата", 104),
            "title": ("Название", 244),
            "category": ("Категория", 122),
            "amount": ("Сумма", 115),
        }
        for name, (text, width) in headings.items():
            self.tree.heading(name, text=text)
            anchor = "w" if name == "title" else "center"
            self.tree.column(name, width=width, anchor=anchor)
        self.tree.tag_configure("odd", background="#f7f9fc")
        self.tree.tag_configure("even", background=CARD)

        scroll = ttk.Scrollbar(table_frame, orient="vertical",
                               command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
        scroll.pack(side="right", fill="y")

        bottom = ttk.Frame(right)
        bottom.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(bottom, text="Удалить выбранную", style="Danger.TButton",
                   command=self.on_delete).pack(side="left")
        self.count_label = ttk.Label(bottom, text="", style="Muted.TLabel")
        self.count_label.configure(background=BG)
        self.count_label.pack(side="right")

    def _field(self, parent, label, variable):
        """Поле формы: подпись сверху и строка ввода под ней."""
        block = ttk.Frame(parent, style="Card.TFrame")
        block.pack(fill="x", pady=(0, 8))
        ttk.Label(block, text=label, style="Card.TLabel").pack(anchor="w")
        entry = ttk.Entry(block, textvariable=variable, width=24)
        entry.pack(fill="x", pady=(2, 0))
        return entry

    def _build_stats_tab(self):
        # верхний ряд — три короткие цифры, ниже график и разбивка по категориям
        kpi = ttk.Frame(self.tab_stats)
        kpi.pack(fill="x")
        self.kpi_total = self._kpi_card(kpi, "Потрачено")
        self.kpi_count = self._kpi_card(kpi, "Записей")
        self.kpi_average = self._kpi_card(kpi, "Средний расход")

        body = ttk.Frame(self.tab_stats)
        body.pack(fill="both", expand=True, pady=(12, 0))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        chart_card = ttk.LabelFrame(body, text="Активность за 7 дней", padding=10)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.chart = tk.Canvas(chart_card, height=250, bg=CARD,
                               highlightthickness=0)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda event: self._draw_chart())

        side_card = ttk.LabelFrame(body, text="По категориям", padding=10)
        side_card.grid(row=0, column=1, sticky="ns")
        # круговая диаграмма в тех же цветах, что и на веб-странице
        self.pie = tk.Canvas(side_card, width=120, height=120, bg=CARD,
                             highlightthickness=0)
        self.pie.pack(pady=(0, 6))
        # список категорий может быть длинным, поэтому он прокручивается
        self.cat_canvas = tk.Canvas(side_card, bg=CARD, highlightthickness=0,
                                    width=250)
        cat_scroll = ttk.Scrollbar(side_card, orient="vertical",
                                   command=self.cat_canvas.yview)
        self.cat_canvas.configure(yscrollcommand=cat_scroll.set)
        cat_scroll.pack(side="right", fill="y")
        self.cat_canvas.pack(side="left", fill="both", expand=True)
        self.cat_box = ttk.Frame(self.cat_canvas, style="Card.TFrame")
        self._cat_window = self.cat_canvas.create_window(
            (0, 0), window=self.cat_box, anchor="nw")
        self.cat_box.bind("<Configure>", lambda event: self.cat_canvas.configure(
            scrollregion=self.cat_canvas.bbox("all")))
        self.cat_canvas.bind("<Configure>", lambda event: self.cat_canvas.itemconfigure(
            self._cat_window, width=event.width))

    def _kpi_card(self, parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Label(card, text=title, style="KpiTitle.TLabel").pack(anchor="w")
        value = ttk.Label(card, text="—", style="Kpi.TLabel")
        value.pack(anchor="w", pady=(2, 0))
        return value

    def _build_journal_tab(self):
        toolbar = ttk.Frame(self.tab_journal)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Обновить журнал", command=self.refresh).pack(
            side="left")
        ttk.Button(toolbar, text="Экспорт в CSV", command=self.on_export).pack(
            side="left", padx=(8, 0))
        ttk.Label(toolbar, text="последние действия в приложении",
                  style="Muted.TLabel").pack(side="right")

        card = ttk.Frame(self.tab_journal, style="Card.TFrame")
        card.pack(fill="both", expand=True)
        self.journal = tk.Text(card, wrap="word", bd=0, bg=CARD, fg=INK,
                               font=("Consolas", 9), state="disabled", padx=10,
                               pady=8)
        scroll = ttk.Scrollbar(card, orient="vertical", command=self.journal.yview)
        self.journal.configure(yscrollcommand=scroll.set)
        self.journal.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def show_journal_tab(self):
        self._select_tab("journal")
        self.refresh()

    # ---------- обновление данных ----------

    def refresh(self):
        """Перечитать расходы и обновить все вкладки."""
        # «Все» — это отсутствие фильтра, в базу уходит None
        category = self.filter_var.get()
        if category == "Все":
            category = None
        expenses = self.service.list_expenses(category, self.search_var.get())
        self.tree.delete(*self.tree.get_children())
        for index, item in enumerate(expenses):
            tag = "odd" if index % 2 else "even"
            self.tree.insert(
                "", "end",
                values=(item.expense_id, item.date_text, item.title,
                        item.category, item.amount_text),
                tags=(tag,),
            )
        summary = self.service.summary()
        self.header_total.configure(text=summary["total_text"])
        self.kpi_total.configure(text=summary["total_text"])
        self.kpi_count.configure(text=str(summary["count"]))
        self.kpi_average.configure(text=summary["average_text"])
        self.count_label.configure(text=f"показано: {len(expenses)}")
        self.status_var.set(f"Записей в базе: {summary['count']} · "
                            f"показано: {len(expenses)}")
        self._fill_categories(summary)
        self._draw_chart()
        self._update_journal()

    def reset_filters(self):
        self.search_var.set("")
        self.filter_var.set("Все")
        self.refresh()

    def _fill_categories(self, summary):
        # список категорий пересобирается заново при каждом обновлении
        for child in self.cat_box.winfo_children():
            child.destroy()
        self._draw_pie(summary["by_category"], summary["total_text"])
        if not summary["by_category"]:
            ttk.Label(self.cat_box, text="Пока нет расходов",
                      style="Muted.TLabel").pack(anchor="w")
            return
        for index, item in enumerate(summary["by_category"]):
            row = ttk.Frame(self.cat_box, style="Card.TFrame")
            row.pack(fill="x", pady=(0, 6))
            # квадратик перед названием повторяет цвет сектора
            tk.Frame(row, bg=PIE_COLORS[index % len(PIE_COLORS)], width=8,
                     height=8).pack(side="left", padx=(0, 6))
            ttk.Label(row, text=item["sum_text"],
                      style="Card.TLabel").pack(side="right")
            ttk.Label(row, text=item["name"], style="Card.TLabel").pack(side="left")
            ttk.Label(row, text=f"{item['percent']:.1f} %",
                      style="Small.TLabel").pack(side="left", padx=(6, 0))

    def _draw_pie(self, items, total_text):
        """Круговая диаграмма: угол сектора равен доле категории."""
        self.pie.delete("all")
        size = 120
        if not items:
            self.pie.create_oval(8, 8, size - 8, size - 8, fill=TRACK, outline="")
            return
        start = 90.0
        for index, item in enumerate(items):
            extent = -item["percent"] * 3.6
            self.pie.create_arc(6, 6, size - 6, size - 6, start=start,
                                extent=extent, outline=CARD, width=2,
                                fill=PIE_COLORS[index % len(PIE_COLORS)])
            start += extent
        # белый круг в середине делает из диаграммы кольцо
        self.pie.create_oval(36, 36, size - 36, size - 36, fill=CARD, outline="")
        self.pie.create_text(size / 2, size / 2 - 6, text="всего", fill=MUTED,
                             font=("Segoe UI", 6))
        self.pie.create_text(size / 2, size / 2 + 5,
                             text=total_text.replace(" руб.", ""), fill=INK,
                             font=("Segoe UI", 7))

    def _draw_chart(self):
        # горизонтальные полосы: так подписи дат читаются без наклона
        self.chart.delete("all")
        width = max(self.chart.winfo_width(), 420)
        height = max(self.chart.winfo_height(), 220)
        data = self.service.daily_totals(7)
        maximum = max((item["sum"] for item in data), default=0) or 1

        left, right = 52, width - 88
        top = 16
        step = (height - 28) / 7
        track_width = right - left
        if track_width < 40:
            return
        self._bars = []
        for index, item in enumerate(data):
            y = top + index * step + step / 2
            self.chart.create_text(10, y, text=item["label"], anchor="w",
                                   fill=MUTED, font=("Segoe UI", 9))
            self.chart.create_rectangle(left, y - 7, right, y + 7,
                                        fill=TRACK, outline="")
            self.chart.create_text(right + 10, y,
                                   text=f"{item['sum']:,.0f}".replace(",", " "),
                                   anchor="w", fill=ACCENT_DARK,
                                   font=("Segoe UI", 9))
            self._bars.append((left, y, item["sum"] / maximum * track_width))
        # полосы дорисовываются плавно, как в веб-версии
        self._chart_token = getattr(self, "_chart_token", 0) + 1
        self._animate_bars(self._chart_token, 0)

    def _animate_bars(self, token, step):
        """Плавно «выращивает» полосы графика после обновления."""
        if token != getattr(self, "_chart_token", 0):
            return
        self.chart.delete("bar")
        k = min(step / 14, 1)
        k = 1 - (1 - k) ** 2
        for x0, y, width in self._bars:
            if width > 0:
                self.chart.create_rectangle(x0, y - 7, x0 + width * k, y + 7,
                                            fill=ACCENT, outline="", tags="bar")
        if k < 1:
            self.after(15, lambda: self._animate_bars(token, step + 1))

    def _update_journal(self):
        records = self.service.records(40)
        self.journal.configure(state="normal")
        self.journal.delete("1.0", "end")
        if not records:
            self.journal.insert("end", "Журнал пока пуст")
        for record in records:
            self.journal.insert("end", f"{record.created}   {record.action}: "
                                       f"{record.details}\n")
        self.journal.configure(state="disabled")

    # ---------- действия ----------

    def on_add(self):
        # всю проверку делает модель, здесь только показываем текст ошибки
        try:
            self.service.add_expense(
                self.title_var.get(),
                self.category_var.get(),
                self.amount_var.get().replace(",", "."),
                self.date_var.get(),
                self.note_var.get(),
            )
        except TrackerError as error:
            messagebox.showerror("Ошибка", str(error))
            return
        # после удачной записи очищаем поля, кроме даты и категории
        self.title_var.set("")
        self.amount_var.set("")
        self.note_var.set("")
        self.date_var.set(date.today().strftime("%d.%m.%Y"))
        self.refresh()
        self.title_entry.focus_set()

    def on_delete(self):
        # удаляем только выбранную строку и всегда с подтверждением
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Удаление", "Сначала выберите запись в таблице")
            return
        values = self.tree.item(selection[0], "values")
        if not messagebox.askyesno("Удаление", f"Удалить расход «{values[2]}»?"):
            return
        try:
            self.service.delete_expense(int(values[0]))
        except TrackerError as error:
            messagebox.showerror("Ошибка", str(error))
            return
        self.refresh()

    def on_export(self):
        path = filedialog.asksaveasfilename(
            title="Экспорт расходов",
            defaultextension=".csv",
            initialfile="expenses.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        try:
            self.service.export_csv(path)
        except TrackerError as error:
            messagebox.showerror("Ошибка", str(error))
            return
        messagebox.showinfo("Экспорт", f"Файл сохранён:\n{path}")

    def show_help(self):
        """Окно справки: короткая памятка по вкладкам и кнопкам."""
        window = tk.Toplevel(self)
        window.title("Справка")
        window.geometry("540x460")
        window.configure(bg=CARD)
        window.transient(self)
        window.resizable(False, False)

        tk.Label(window, text="Как работать с трекером", bg=CARD,
                 fg=HEADER_TEXT, font=("Segoe UI Semibold", 16)).pack(
            anchor="w", padx=22, pady=(18, 2))
        tk.Label(window, text="короткая памятка по вкладкам", bg=CARD,
                 fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=22)

        text = (
            "Расходы. Заполните название, категорию, сумму и дату, затем "
            "нажмите «Записать». Сумма принимается и с запятой, и с точкой.\n\n"
            "Поиск и фильтр. Строка поиска ищет по названию, список категорий "
            "ограничивает выдачу. Кнопка «Сбросить» возвращает полный список.\n\n"
            "Статистика. Сверху три карточки: сумма, число записей и средний "
            "расход. Ниже график за семь дней и разбивка по категориям.\n\n"
            "Журнал. Здесь видно, что и когда добавляли или удаляли. Кнопка "
            "«Экспорт в CSV» сохраняет весь каталог в файл.\n\n"
            "Записи лежат в базе SQLite, поэтому после закрытия окна они "
            "остаются на месте."
        )
        tk.Label(window, text=text, bg=CARD, fg=INK, justify="left",
                 wraplength=480, font=("Segoe UI", 10)).pack(
            anchor="w", padx=22, pady=(12, 0))

        tk.Button(window, text="Понятно", command=window.destroy, bg=ACCENT,
                  fg="white", activebackground=PRIMARY_ACTIVE,
                  activeforeground="white", relief="flat", bd=0,
                  cursor="hand2", font=("Segoe UI Semibold", 10),
                  padx=22, pady=8).pack(side="bottom", pady=16)

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "Кошелёк — финансовый трекер расходов\n"
            "Лабораторная работа № 3, вариант 8\n"
            "Дутикова Ксения Дмитриевна, Б.ПИН.РИС-24.06",
        )
