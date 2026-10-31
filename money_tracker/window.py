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

# палитра окна: холодный светлый фон, тёмно-синяя шапка и медный акцент
BG = "#eff2f6"
CARD = "#ffffff"
HEADER = "#22304a"
HEADER_TEXT = "#ffffff"
HEADER_MUTED = "#a8b6cc"
INK = "#1d2733"
MUTED = "#6a7686"
ACCENT = "#3a6ea5"
ACCENT_DARK = "#2a5680"
COPPER = "#c2703a"
TRACK = "#e3e9f1"
BORDER = "#d6dde7"


class MainWindow(tk.Tk):
    """Окно с вкладками: таблица расходов, статистика и журнал действий."""

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.title("Кошелёк — финансовый трекер расходов")
        self.geometry("1180x600")
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
        style.configure("Kpi.TLabel", background=CARD, foreground=ACCENT_DARK,
                        font=("Segoe UI Semibold", 17))
        style.configure("KpiTitle.TLabel", background=CARD, foreground=MUTED,
                        font=("Segoe UI", 8))
        style.configure("TLabelframe", background=CARD, bordercolor=BORDER,
                        relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", background=CARD, foreground=ACCENT_DARK,
                        font=("Segoe UI Semibold", 10))
        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 6, 0, 0))
        style.configure("TNotebook.Tab", background="#dde3ec", foreground=INK,
                        font=("Segoe UI", 10), padding=(18, 8))
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", ACCENT_DARK)])
        style.configure("TButton", font=("Segoe UI", 9), padding=(10, 6))
        style.configure("Accent.TButton", background=COPPER, foreground="white",
                        borderwidth=0, padding=(12, 8))
        style.map("Accent.TButton",
                  background=[("active", "#b25f30"), ("pressed", "#b25f30")])
        style.configure("Danger.TButton", foreground="#a33a3a")
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=5)
        style.configure("Treeview", background=CARD, fieldbackground=CARD,
                        foreground=INK, rowheight=27, font=("Segoe UI", 9),
                        borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9),
                        background="#e6ebf3", foreground=ACCENT_DARK)
        style.map("Treeview", background=[("selected", "#d8e3f0")],
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
        # тёмная полоса сверху: слева название, справа итоговая сумма
        header = tk.Frame(self, bg=HEADER, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=HEADER)
        left.pack(side="left", padx=20, pady=10)
        tk.Label(left, text="Кошелёк", bg=HEADER, fg=HEADER_TEXT,
                 font=("Georgia", 20, "bold")).pack(anchor="w")
        tk.Label(left, text="учёт личных расходов, вариант 8", bg=HEADER,
                 fg=HEADER_MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        right = tk.Frame(header, bg=HEADER)
        right.pack(side="right", padx=20)
        self.header_total = tk.Label(right, text="0,00 руб.", bg=HEADER,
                                     fg=HEADER_TEXT,
                                     font=("Segoe UI Semibold", 18))
        self.header_total.pack(anchor="e")
        tk.Label(right, text="потрачено всего", bg=HEADER, fg=HEADER_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="e")

    def _build_status(self):
        self.status_var = tk.StringVar(value="Готово")
        bar = tk.Frame(self, bg=BG, height=26)
        bar.pack(side="bottom", fill="x")
        tk.Label(bar, textvariable=self.status_var, bg=BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="left", padx=18)

    # ---------- вкладки ----------

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(10, 4))
        self.tab_expenses = ttk.Frame(self.notebook, padding=12)
        self.tab_stats = ttk.Frame(self.notebook, padding=12)
        self.tab_journal = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_expenses, text="Расходы")
        self.notebook.add(self.tab_stats, text="Статистика")
        self.notebook.add(self.tab_journal, text="Журнал")
        self._build_expenses_tab()
        self._build_stats_tab()
        self._build_journal_tab()

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
            "date": ("Дата", 92),
            "title": ("Название", 260),
            "category": ("Категория", 120),
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

        side_card = ttk.LabelFrame(body, text="По категориям", padding=12)
        side_card.grid(row=0, column=1, sticky="ns")
        self.cat_box = ttk.Frame(side_card, style="Card.TFrame")
        self.cat_box.pack(fill="both", expand=True)

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
        self.notebook.select(self.tab_journal)
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
        if not summary["by_category"]:
            ttk.Label(self.cat_box, text="Пока нет расходов",
                      style="Muted.TLabel").pack(anchor="w")
            return
        for item in summary["by_category"]:
            row = ttk.Frame(self.cat_box, style="Card.TFrame")
            row.pack(fill="x", pady=(0, 8))
            top = ttk.Frame(row, style="Card.TFrame")
            top.pack(fill="x")
            ttk.Label(top, text=item["name"], style="Card.TLabel").pack(side="left")
            ttk.Label(top, text=item["sum_text"],
                      style="Card.TLabel").pack(side="right")
            ttk.Label(row, text=f"{item['percent']:.1f} % от всех расходов",
                      style="Muted.TLabel").pack(anchor="w")

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
        for index, item in enumerate(data):
            y = top + index * step + step / 2
            self.chart.create_text(10, y, text=item["label"], anchor="w",
                                   fill=MUTED, font=("Segoe UI", 8))
            self.chart.create_rectangle(left, y - 7, right, y + 7,
                                        fill=TRACK, outline="")
            bar = item["sum"] / maximum * track_width
            if bar > 0:
                self.chart.create_rectangle(left, y - 7, left + bar, y + 7,
                                            fill=ACCENT, outline="")
            self.chart.create_text(right + 8, y, text=f"{item['sum']:.0f}",
                                   anchor="w", fill=ACCENT_DARK,
                                   font=("Segoe UI", 8))

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

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "Кошелёк — финансовый трекер расходов\n"
            "Лабораторная работа № 3, вариант 8\n"
            "Дутикова Ксения Дмитриевна, Б.ПИН.РИС-24.06",
        )
