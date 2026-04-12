"""
widgets.py — Widgets reutilizables para la aplicación.
"""
import tkinter as tk
from tkinter import ttk
import calendar
import datetime
from ui.theme import COLORS, FONTS


# ─────────────────────────────────────────────────────────────────────────────
# CALENDAR POPUP
# ─────────────────────────────────────────────────────────────────────────────

class CalendarPopup(tk.Toplevel):
    """Popup calendario sin bordes, posicionado debajo del widget disparador."""

    MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    DIAS  = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]

    def __init__(self, anchor_widget: tk.Widget, callback):
        super().__init__(anchor_widget)
        self._callback = callback
        self.overrideredirect(True)
        self.configure(bg=COLORS["border"])
        self.resizable(False, False)

        today = datetime.date.today()
        self._year  = today.year
        self._month = today.month

        # Marco con borde visual
        self._inner = tk.Frame(self, bg=COLORS["bg"],
                               relief="flat", bd=0)
        self._inner.pack(padx=1, pady=1)

        self._draw()
        self._place(anchor_widget)
        self.grab_set()
        self.bind("<Escape>", lambda _: self.destroy())
        self.focus_set()

    # ── Posicionamiento ───────────────────────────────────────────────────────

    def _place(self, anchor: tk.Widget):
        self.update_idletasks()
        ax = anchor.winfo_rootx()
        ay = anchor.winfo_rooty() + anchor.winfo_height() + 2
        w  = self.winfo_reqwidth()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = min(ax, sw - w - 8)
        h  = self.winfo_reqheight()
        if ay + h > sh - 40:
            ay = anchor.winfo_rooty() - h - 2
        self.geometry(f"+{x}+{ay}")

    # ── Dibujo ────────────────────────────────────────────────────────────────

    def _draw(self):
        for w in self._inner.winfo_children():
            w.destroy()

        # Encabezado de navegación
        hdr = tk.Frame(self._inner, bg=COLORS["sidebar_bg"])
        hdr.pack(fill="x")

        tk.Button(
            hdr, text=" ◀ ", bg=COLORS["sidebar_bg"], fg=COLORS["white"],
            bd=0, cursor="hand2", font=FONTS["small"],
            activebackground=COLORS["sidebar_sel"],
            activeforeground=COLORS["white"],
            command=self._prev_month,
        ).pack(side="left", padx=4, pady=4)

        tk.Label(
            hdr,
            text=f"{self.MESES[self._month - 1]}  {self._year}",
            bg=COLORS["sidebar_bg"], fg=COLORS["white"],
            font=("Segoe UI", 10, "bold"), width=18,
        ).pack(side="left", expand=True)

        tk.Button(
            hdr, text=" ▶ ", bg=COLORS["sidebar_bg"], fg=COLORS["white"],
            bd=0, cursor="hand2", font=FONTS["small"],
            activebackground=COLORS["sidebar_sel"],
            activeforeground=COLORS["white"],
            command=self._next_month,
        ).pack(side="right", padx=4, pady=4)

        # Cuadrícula de días
        grid = tk.Frame(self._inner, bg=COLORS["bg"])
        grid.pack(padx=4, pady=4)

        # Cabeceras de día
        for col, day_lbl in enumerate(self.DIAS):
            weekend = col >= 5
            tk.Label(
                grid, text=day_lbl, width=3,
                font=("Segoe UI", 8, "bold"),
                bg=COLORS["header_bg"],
                fg="#FEB2B2" if weekend else COLORS["white"],
            ).grid(row=0, column=col, padx=1, pady=1)

        # Días del mes (lunes=0)
        today = datetime.date.today()
        for week_row, week in enumerate(calendar.monthcalendar(self._year, self._month)):
            for col, day in enumerate(week):
                if day == 0:
                    tk.Label(grid, text="", width=3,
                             bg=COLORS["bg"]).grid(
                        row=week_row + 1, column=col, padx=1, pady=1)
                    continue

                dt = datetime.date(self._year, self._month, day)
                is_today   = dt == today
                is_weekend = col >= 5

                if is_today:
                    bg, fg = COLORS["accent"], COLORS["white"]
                elif is_weekend:
                    bg, fg = "#FFF5F5", COLORS["danger"]
                else:
                    bg, fg = COLORS["white"], COLORS["text"]

                btn = tk.Button(
                    grid, text=str(day), width=3,
                    bg=bg, fg=fg, relief="flat", cursor="hand2",
                    font=FONTS["small"],
                    activebackground=COLORS["accent"],
                    activeforeground=COLORS["white"],
                    command=lambda d=dt: self._pick(d),
                )
                btn.grid(row=week_row + 1, column=col, padx=1, pady=1)

    def _prev_month(self):
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self._draw()

    def _next_month(self):
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self._draw()

    def _pick(self, date: datetime.date):
        self.destroy()
        self._callback(date)


# ─────────────────────────────────────────────────────────────────────────────
# DATE ENTRY
# ─────────────────────────────────────────────────────────────────────────────

class DateEntry(tk.Frame):
    """Selector de fecha: spinboxes DD / MM / YYYY + botón calendario popup.

    Interfaz pública:
        get() -> str   — retorna 'YYYY-MM-DD' o '' si incompleto/inválido
        set(str)       — acepta 'YYYY-MM-DD' o vacío
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self._day   = tk.StringVar()
        self._month = tk.StringVar()
        self._year  = tk.StringVar()
        self._build()

    def _build(self):
        # Validadores: solo dígitos, tope por campo
        vcmd_d = (self.register(lambda v: v == "" or (v.isdigit() and 1 <= int(v) <= 31)), "%P")
        vcmd_m = (self.register(lambda v: v == "" or (v.isdigit() and 1 <= int(v) <= 12)), "%P")
        vcmd_y = (self.register(lambda v: v == "" or (v.isdigit() and len(v) <= 4)), "%P")

        sp_d = ttk.Spinbox(
            self, from_=1, to=31, textvariable=self._day,
            width=3, format="%02.0f",
            validate="key", validatecommand=vcmd_d,
        )
        sp_d.pack(side="left")

        tk.Label(self, text="/", bg=COLORS["bg"],
                 font=FONTS["body"]).pack(side="left")

        sp_m = ttk.Spinbox(
            self, from_=1, to=12, textvariable=self._month,
            width=3, format="%02.0f",
            validate="key", validatecommand=vcmd_m,
        )
        sp_m.pack(side="left")

        tk.Label(self, text="/", bg=COLORS["bg"],
                 font=FONTS["body"]).pack(side="left")

        sp_y = ttk.Spinbox(
            self, from_=1900, to=2100, textvariable=self._year,
            width=5,
            validate="key", validatecommand=vcmd_y,
        )
        sp_y.pack(side="left")

        self._cal_btn = ttk.Button(
            self, text="📅", width=3, command=self._open_calendar,
        )
        self._cal_btn.pack(side="left", padx=(4, 0))

    # ── API pública ───────────────────────────────────────────────────────────

    def get(self) -> str:
        """Retorna 'YYYY-MM-DD' o '' si el campo está incompleto o la fecha es inválida."""
        d = self._day.get().strip()
        m = self._month.get().strip()
        y = self._year.get().strip()
        if not d or not m or not y or len(y) < 4:
            return ""
        try:
            return datetime.date(int(y), int(m), int(d)).isoformat()
        except ValueError:
            return ""

    def set(self, date_str: str):
        """Acepta 'YYYY-MM-DD', 'DD/MM/YYYY' o cadena vacía."""
        if not date_str:
            self._day.set("")
            self._month.set("")
            self._year.set("")
            return
        try:
            if "-" in date_str:
                # Puede ser YYYY-MM-DD
                parts = date_str[:10].split("-")
                if len(parts[0]) == 4:
                    dt = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    dt = datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
            else:
                parts = date_str.split("/")
                dt = datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
            self._day.set(f"{dt.day:02d}")
            self._month.set(f"{dt.month:02d}")
            self._year.set(str(dt.year))
        except Exception:
            pass

    # ── Calendario ────────────────────────────────────────────────────────────

    def _open_calendar(self):
        # Pre-navegar al mes/año actual del campo si ya tiene valor
        popup = CalendarPopup(self._cal_btn, self._on_date_selected)
        current = self.get()
        if current:
            try:
                dt = datetime.date.fromisoformat(current)
                popup._year  = dt.year
                popup._month = dt.month
                popup._draw()
            except Exception:
                pass

    def _on_date_selected(self, date: datetime.date):
        self.set(date.isoformat())
