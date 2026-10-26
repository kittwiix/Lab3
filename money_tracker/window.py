# -*- coding: utf-8 -*-
"""Главное окно финансового трекера на Tkinter."""

import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from .errors import TrackerError
from .records import CATEGORIES

BG = "#eef4fb"
CARD = "#ffffff"
ACCENT = "#2f5d8a"
ACCENT_DARK = "#244866"
TEXT = "#1f2d3d"
MUTED = "#6b7c93"
BORDER = "#c9d8e8"


class MainWindow(tk.Tk):
    """Окно с таблицей, формой, графиком и журналом."""

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.title("Финансовый трекер расходов — вариант 8")
        self.geometry("1260x780")
        self.minsize(1100, 700)
        self.configure(bg=BG)
        self._build_style()
        self._build_menu()
        self._build_header()
        self._build_form()
        self._build_toolbar()
        self._build_status()
        self._build_table()
        self._build_side()
        self.refresh()

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=TEXT,
                        font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=CARD, foreground=MUTED,
                        font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=ACCENT_DARK,
                        font=("Segoe UI Semibold", 18))
        style.configure("Subtitle.TLabel", background=BG, foreground=MUTED,
                        font=("Segoe UI", 10))
        style.configure("TLabelframe", background=CARD, bordercolor=BORDER,
                        relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", background=CARD, foreground=ACCENT_DARK,
                        font=("Segoe UI Semibold", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 6))
        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                        borderwidth=0, padding=(16, 7))
        style.map("Accent.TButton",
                  background=[("active", ACCENT_DARK), ("pressed", ACCENT_DARK)])
        style.configure("Danger.TButton", foreground="#a33a3a")
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=5)
        style.configure("Treeview", background=CARD, fieldbackground=CARD,
                        foreground=TEXT, rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9),
                        background="#dce8f5", foreground=ACCENT_DARK)
        style.map("Treeview", background=[("selected", "#cfe0f2")],
                  foreground=[("selected", TEXT)])

    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт CSV", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Обновить", command=self.refresh)
        menubar.add_cascade(label="Вид", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)
        self.config(menu=menubar)

    def _build_header(self):
        header = ttk.Frame(self, padding=(18, 14, 18, 6))
        header.pack(fill="x")
        ttk.Label(header, text="Финансовый трекер расходов",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Лабораторная работа № 3, вариант 8",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))

    def _build_form(self):
        frame = ttk.LabelFrame(self, text="Новый расход", padding=12)
        frame.pack(fill="x", padx=18, pady=(6, 8))

        self.title_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        self.note_var = tk.StringVar()

        fields = [
            ("Название", self.title_var, 22),
            ("Категория", self.category_var, 14),
            ("Сумма, руб.", self.amount_var, 12),
            ("Дата", self.date_var, 12),
            ("Комментарий", self.note_var, 24),
        ]
        for column, (label, variable, width) in enumerate(fields):
            block = ttk.Frame(frame, style="Card.TFrame")
            block.grid(row=0, column=column, sticky="ew", padx=(0, 10))
            ttk.Label(block, text=label, style="Card.TLabel").pack(anchor="w")
            if label == "Категория":
                widget = ttk.Combobox(block, textvariable=variable, values=CATEGORIES,
                                      state="readonly", width=width)
            else:
                widget = ttk.Entry(block, textvariable=variable, width=width)
            widget.pack(fill="x", pady=(3, 0))

        ttk.Button(frame, text="Добавить", style="Accent.TButton",
                   command=self.on_add).grid(row=0, column=len(fields),
                                             sticky="s", padx=(6, 0))
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(4, weight=2)
        self.title_entry = frame.winfo_children()[0].winfo_children()[1]

    def _build_toolbar(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=18, pady=(0, 6))

        ttk.Label(toolbar, text="Категория:").pack(side="left")
        self.filter_var = tk.StringVar(value="Все")
        filter_box = ttk.Combobox(toolbar, textvariable=self.filter_var,
                                  values=("Все",) + CATEGORIES, state="readonly",
                                  width=14)
        filter_box.pack(side="left", padx=(4, 14))
        filter_box.bind("<<ComboboxSelected>>", lambda event: self.refresh())

        ttk.Label(toolbar, text="Поиск:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=28)
        search_entry.pack(side="left", padx=(4, 8))
        search_entry.bind("<Return>", lambda event: self.refresh())

        ttk.Button(toolbar, text="Обновить", command=self.refresh).pack(side="left")
        ttk.Button(toolbar, text="Удалить", style="Danger.TButton",
                   command=self.on_delete).pack(side="right")

    def _build_table(self):
        container = ttk.Frame(self)
        container.pack(side="left", fill="both", expand=True, padx=(18, 8), pady=(0, 8))

        columns = ("id", "date", "title", "category", "amount", "note")
        self.tree = ttk.Treeview(container, columns=columns, show="headings",
                                 selectmode="browse")
        headings = {
            "id": ("ID", 48),
            "date": ("Дата", 92),
            "title": ("Название", 220),
            "category": ("Категория", 115),
            "amount": ("Сумма", 110),
            "note": ("Комментарий", 190),
        }
        for name, (text, width) in headings.items():
            self.tree.heading(name, text=text)
            self.tree.column(name, width=width, anchor="w" if name in ("title", "note") else "center")
        self.tree.tag_configure("odd", background="#f7fbff")
        self.tree.tag_configure("even", background=CARD)

        scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _build_side(self):
        side = ttk.Frame(self, width=330)
        side.pack(side="right", fill="y", padx=(0, 18), pady=(0, 8))
        side.pack_propagate(False)

        summary_card = ttk.LabelFrame(side, text="Сводка", padding=12)
        summary_card.pack(fill="x")
        self.summary_total = ttk.Label(summary_card, text="0,00 руб.",
                                       style="Card.TLabel",
                                       font=("Segoe UI Semibold", 16))
        self.summary_total.pack(anchor="w")
        ttk.Label(summary_card, text="Всего расходов",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        row = ttk.Frame(summary_card, style="Card.TFrame")
        row.pack(fill="x")
        self.summary_count = ttk.Label(row, text="0", style="Card.TLabel",
                                       font=("Segoe UI Semibold", 13))
        self.summary_count.pack(side="left")
        ttk.Label(row, text="записей", style="Muted.TLabel").pack(side="left", padx=(4, 18))
        self.summary_average = ttk.Label(row, text="0,00 руб.", style="Card.TLabel",
                                         font=("Segoe UI Semibold", 11))
        self.summary_average.pack(side="left")
        ttk.Label(row, text="в среднем", style="Muted.TLabel").pack(side="left", padx=(4, 0))

        chart_card = ttk.LabelFrame(side, text="Расходы за 7 дней", padding=8)
        chart_card.pack(fill="x", pady=(8, 0))
        self.chart = tk.Canvas(chart_card, height=210, bg=CARD,
                               highlightthickness=0)
        self.chart.pack(fill="x")

        journal_card = ttk.LabelFrame(side, text="Последние действия", padding=8)
        journal_card.pack(fill="both", expand=True, pady=(8, 0))
        self.journal = tk.Text(journal_card, height=9, wrap="word", bd=0,
                               bg=CARD, fg=TEXT, font=("Segoe UI", 8),
                               state="disabled")
        self.journal.pack(fill="both", expand=True)

    def _build_status(self):
        self.status_var = tk.StringVar(value="Готово")
        ttk.Label(self, textvariable=self.status_var, style="Subtitle.TLabel",
                  padding=(18, 0, 18, 8)).pack(side="bottom", fill="x")

    def refresh(self):
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
                        item.category, item.amount_text, item.note),
                tags=(tag,),
            )
        summary = self.service.summary()
        self.summary_total.configure(text=summary["total_text"])
        self.summary_count.configure(text=str(summary["count"]))
        self.summary_average.configure(text=summary["average_text"])
        self._draw_chart()
        self._update_journal()
        self.status_var.set(f"Показано записей: {len(expenses)}")

    def _draw_chart(self):
        self.chart.delete("all")
        self.chart.update_idletasks()
        width = max(self.chart.winfo_width(), 300)
        height = max(self.chart.winfo_height(), 190)
        data = self.service.daily_totals(7)
        maximum = max((item["sum"] for item in data), default=0) or 1
        left, right = 34, width - 8
        top, bottom = 12, height - 30
        plot_width = right - left
        plot_height = bottom - top

        for step in range(4):
            y = top + plot_height * step / 3
            self.chart.create_line(left, y, right, y, fill="#e3edf7")
            value = maximum * (3 - step) / 3
            self.chart.create_text(left - 4, y, text=f"{value:.0f}", anchor="e",
                                   fill=MUTED, font=("Segoe UI", 7))

        slot = plot_width / len(data)
        bar_width = slot * 0.55
        for index, item in enumerate(data):
            x = left + slot * index + (slot - bar_width) / 2
            bar_height = item["sum"] / maximum * plot_height
            y = bottom - bar_height
            self.chart.create_rectangle(x, y, x + bar_width, bottom,
                                        fill=ACCENT, outline="")
            self.chart.create_text(x + bar_width / 2, bottom + 10,
                                   text=item["label"], fill=MUTED,
                                   font=("Segoe UI", 7))
            if item["sum"]:
                self.chart.create_text(x + bar_width / 2, y - 6,
                                       text=f"{item['sum']:.0f}", fill=ACCENT_DARK,
                                       font=("Segoe UI", 7))

    def _update_journal(self):
        records = self.service.records(15)
        self.journal.configure(state="normal")
        self.journal.delete("1.0", "end")
        for record in records:
            self.journal.insert("end", f"{record.created}  {record.action}: "
                                       f"{record.details}\n")
        self.journal.configure(state="disabled")

    def on_add(self):
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
        self.title_var.set("")
        self.amount_var.set("")
        self.note_var.set("")
        self.date_var.set(date.today().strftime("%d.%m.%Y"))
        self.refresh()
        self.title_entry.focus_set()

    def on_delete(self):
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
            "Финансовый трекер расходов\n"
            "Лабораторная работа № 3, вариант 8\n"
            "Дутикова Ксения Дмитриевна, Б.ПИН.РИС-24.06",
        )
