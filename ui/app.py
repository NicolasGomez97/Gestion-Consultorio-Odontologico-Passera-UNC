"""
app.py — Ventana principal con sidebar de navegación y área de contenido.
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional
import models
from ui.theme import COLORS, FONTS, apply_theme


class AppState:
    """Bus de eventos centralizado y estado de contexto compartido."""
    def __init__(self):
        self._paciente_id: Optional[int] = None
        self._callbacks: Dict[str, List[Callable]] = {}
        self.current_user: Optional[Dict] = None   # asignado tras el login

    @property
    def paciente_id(self) -> Optional[int]:
        return self._paciente_id

    def set_paciente(self, id_: Optional[int]):
        self._paciente_id = id_
        self.emit("patient_changed", paciente_id=id_)

    def register(self, event: str, cb: Callable):
        self._callbacks.setdefault(event, []).append(cb)

    def emit(self, event: str, **kwargs):
        for cb in self._callbacks.get(event, []):
            try:
                cb(**kwargs)
            except Exception:
                pass


# Instancia global de estado (importada por los módulos de UI)
app_state = AppState()


class MainApp(tk.Tk):
    def __init__(self, current_user: Optional[Dict] = None):
        super().__init__()
        app_state.current_user = current_user
        self.title("Consultorio Odontológico Passera")
        self.geometry("1280x820")
        self.minsize(1024, 680)
        apply_theme(self)

        # Importaciones diferidas (evita importaciones circulares)
        from ui.pacientes_ui    import PacientesFrame
        from ui.odontologos_ui  import OdontologosFrame
        from ui.turnos_ui       import TurnosFrame
        from ui.historial_ui    import HistorialFrame
        from ui.odontograma_ui  import OdontogramaFrame
        from ui.periodontograma_ui import PeriodontogramaFrame
        from ui.prestaciones_ui import PrestacionesFrame
        from ui.usuarios_ui     import UsuariosFrame

        self._pages: Dict[str, tk.Frame] = {}
        self._current_page: Optional[str] = None

        # ── Layout raíz ──────────────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg=COLORS["sidebar_bg"], width=220)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        self._build_sidebar(sidebar)

        # ── Área de contenido ────────────────────────────────────────────────
        self._content = tk.Frame(self, bg=COLORS["bg"])
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        # ── Instanciar páginas ───────────────────────────────────────────────
        for name, cls in [
            ("dashboard",       DashboardFrame),
            ("pacientes",       PacientesFrame),
            ("turnos",          TurnosFrame),
            ("historial",       HistorialFrame),
            ("odontograma",     OdontogramaFrame),
            ("periodontal",     PeriodontogramaFrame),
            ("prestaciones",    PrestacionesFrame),
            ("odontologos",     OdontologosFrame),
            ("usuarios",        UsuariosFrame),
        ]:
            frame = cls(self._content)
            frame.grid(row=0, column=0, sticky="nsew")
            self._pages[name] = frame

        self.show_page("dashboard")

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent: tk.Frame):
        # Logo / título
        header = tk.Frame(parent, bg=COLORS["sidebar_bg"], pady=20)
        header.pack(fill="x")
        tk.Label(header, text="🦷", font=("Segoe UI", 28),
                 bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_fg"]).pack()
        tk.Label(header, text="Consultorio Passera",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_fg"]).pack()
        tk.Frame(parent, bg=COLORS["sidebar_sel"], height=1).pack(fill="x")

        nav_items = [
            ("🏠  Dashboard",        "dashboard"),
            ("👥  Pacientes",         "pacientes"),
            ("📅  Turnero",           "turnos"),
            ("📋  Historial Clínico", "historial"),
            ("🦷  Odontograma",       "odontograma"),
            ("🔬  Periodontal",       "periodontal"),
            ("💊  Prestaciones",      "prestaciones"),
            ("👨‍⚕️  Odontólogos",     "odontologos"),
            ("🔑  Usuarios",          "usuarios"),
        ]

        self._nav_buttons: Dict[str, tk.Button] = {}
        nav_frame = tk.Frame(parent, bg=COLORS["sidebar_bg"])
        nav_frame.pack(fill="both", expand=True, pady=8)

        for label, page_name in nav_items:
            btn = tk.Button(
                nav_frame, text=label,
                font=FONTS["sidebar"], anchor="w",
                bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_fg"],
                activebackground=COLORS["sidebar_sel"],
                activeforeground=COLORS["sidebar_fg"],
                relief="flat", bd=0, padx=16, pady=10,
                cursor="hand2",
                command=lambda p=page_name: self.show_page(p),
            )
            btn.pack(fill="x")
            self._nav_buttons[page_name] = btn

        # Versión y usuario logueado en el pie
        tk.Label(parent, text="Ramiro Nicolas Gomez",
                font=FONTS["small"],
                bg=COLORS["sidebar_bg"], fg=COLORS["text_light"]).pack(side="bottom", pady=(0, 2))
        tk.Label(parent, text="David Macías",
                font=FONTS["small"],
                bg=COLORS["sidebar_bg"], fg=COLORS["text_light"]).pack(side="bottom", pady=(0, 2))
        tk.Label(parent, text=" Matías Rodríguez",
                font=FONTS["small"],
                bg=COLORS["sidebar_bg"], fg=COLORS["text_light"]).pack(side="bottom", pady=(0, 2))
        tk.Label(parent, text="Desarrollado:",
                 font=FONTS["small"],
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_light"]).pack(side="bottom", pady=(0, 2))
        tk.Label(parent, text="v1.0 — UNC 2024",
                 font=FONTS["small"],
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_light"]).pack(side="bottom", pady=(8, 2))

        # Separador y sesión activa
        tk.Frame(parent, bg=COLORS["sidebar_sel"], height=1).pack(
            side="bottom", fill="x", pady=(4, 0))
        user = app_state.current_user
        if user:
            session_text = f"👤 {user['nombre']} ({user['rol']})"
        else:
            session_text = "👤 Sin sesión"
        tk.Label(parent, text=session_text,
                 font=FONTS["small"],
                 bg=COLORS["sidebar_bg"], fg="#90CDF4",
                 wraplength=190, justify="left").pack(
            side="bottom", anchor="w", padx=12, pady=(0, 4))

    def show_page(self, name: str):
        # Resaltar botón activo
        for pname, btn in self._nav_buttons.items():
            btn.configure(bg=COLORS["sidebar_sel"] if pname == name else COLORS["sidebar_bg"])
        self._pages[name].tkraise()
        self._current_page = name
        # Notificar a la página que se activó
        page = self._pages[name]
        if hasattr(page, "on_show"):
            page.on_show()


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

class DashboardFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build()

    def _build(self):
        # Encabezado
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Panel Principal",
                 font=FONTS["title"],
                 bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=24, anchor="w")
        tk.Label(hdr, text="Consultorio Odontológico Passera — Córdoba",
                 font=FONTS["body"],
                 bg=COLORS["header_bg"], fg="#BEE3F8").pack(padx=24, anchor="w")

        self._cards_frame = tk.Frame(self, bg=COLORS["bg"], pady=20, padx=20)
        self._cards_frame.pack(fill="x")
        self._info_frame = tk.Frame(self, bg=COLORS["bg"], padx=20)
        self._info_frame.pack(fill="both", expand=True)

    def on_show(self):
        # Limpiar y redibujar tarjetas
        for w in self._cards_frame.winfo_children():
            w.destroy()
        for w in self._info_frame.winfo_children():
            w.destroy()

        stats = models.get_stats()
        tarjetas = [
            ("Pacientes activos",           str(stats["total_pacientes"]),  COLORS["accent"],   "👥"),
            ("Turnos hoy",                  str(stats["turnos_hoy"]),        COLORS["success"],  "📅"),
            ("Turnos pendientes",           str(stats["turnos_pendientes"]), COLORS["warning"],  "⏳"),
            ("Prestaciones sin enviar\na Federación",
             str(stats["prestaciones_pendientes_fed"]),                       COLORS["danger"],   "📤"),
        ]
        for i, (titulo, valor, color, icono) in enumerate(tarjetas):
            card = tk.Frame(self._cards_frame, bg=color, padx=16, pady=12,
                            relief="flat", bd=0, cursor="hand2")
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            self._cards_frame.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=icono, font=("Segoe UI", 22),
                     bg=color, fg=COLORS["white"]).pack(anchor="w")
            tk.Label(card, text=valor, font=("Segoe UI", 28, "bold"),
                     bg=color, fg=COLORS["white"]).pack(anchor="w")
            tk.Label(card, text=titulo, font=FONTS["body"],
                     bg=color, fg=COLORS["white"], justify="left").pack(anchor="w")

        # Prestaciones del mes
        cnt, total = stats["prestaciones_mes"]
        info_lbl = tk.Label(self._info_frame,
                             text=f"📊  Mes actual: {cnt} prestaciones — Total: ${total:,.0f}",
                             font=FONTS["subtitle"], bg=COLORS["bg"], fg=COLORS["text"])
        info_lbl.pack(anchor="w", pady=(10, 4))

        # Próximos turnos de hoy
        from models import get_turnos
        import datetime
        hoy = datetime.date.today().isoformat()
        turnos = get_turnos(fecha=hoy)
        if turnos:
            lbl = tk.Label(self._info_frame, text="📅  Turnos de hoy:",
                           font=FONTS["subtitle"], bg=COLORS["bg"], fg=COLORS["text"])
            lbl.pack(anchor="w", pady=(16, 4))
            cols = ("Hora", "Paciente", "Odontólogo", "Motivo", "Estado")
            tree = ttk.Treeview(self._info_frame, columns=cols, show="headings", height=8)
            for c in cols:
                tree.heading(c, text=c)
                tree.column(c, width=160 if c not in ("Hora","Estado") else 90)
            for t in turnos:
                tree.insert("", "end", values=(
                    t["hora"], t["paciente_nombre"],
                    t["odontologo_nombre"], t.get("motivo",""), t["estado"].capitalize()
                ))
            tree.pack(fill="both", expand=True, pady=4)
        else:
            tk.Label(self._info_frame,
                     text="No hay turnos programados para hoy.",
                     font=FONTS["body"], bg=COLORS["bg"],
                     fg=COLORS["text_light"]).pack(anchor="w", pady=20)
