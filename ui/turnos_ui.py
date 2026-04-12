"""
turnos_ui.py — Gestión del turnero (agenda de citas).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import datetime
import models
from ui.theme import COLORS, FONTS
from ui.app import app_state
from ui.widgets import DateEntry

ESTADOS = ["Pendiente", "Confirmado", "Presente", "Ausente", "Cancelado", "Reprogramado"]
ESTADO_COLORS = {
    "Pendiente":    "#7E95A2",
    "Confirmado":   "#0645F1",
    "Presente":     "#039336",
    "Ausente":      "#0C0000",
    "Cancelado":    "#F80303",
    "Reprogramado": "#FAFAFA",
}


class TurnosFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._selected_id: Optional[int] = None
        self._fecha_actual = datetime.date.today()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📅  Turnero",
                 font=FONTS["title"], bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")

        # ── Controles de fecha ────────────────────────────────────────────────
        ctrl = tk.Frame(self, bg=COLORS["bg"], pady=8, padx=16)
        ctrl.pack(fill="x")

        ttk.Button(ctrl, text="◀ Día ant.", command=self._prev_day).pack(side="left", padx=4)
        self._lbl_fecha = tk.Label(ctrl, text="", font=FONTS["subtitle"],
                                   bg=COLORS["bg"], fg=COLORS["text"])
        self._lbl_fecha.pack(side="left", padx=12)
        ttk.Button(ctrl, text="Día sig. ▶", command=self._next_day).pack(side="left", padx=4)
        ttk.Button(ctrl, text="Hoy", command=self._go_today).pack(side="left", padx=8)

        # Selector de fecha manual
        tk.Label(ctrl, text="Ir a fecha:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left", padx=(20, 4))
        self._fecha_ir = DateEntry(ctrl)
        self._fecha_ir.pack(side="left")
        ttk.Button(ctrl, text="Ir", command=self._go_date).pack(side="left", padx=4)

        # Filtro por odontólogo
        tk.Label(ctrl, text="Odontólogo:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left", padx=(16, 4))
        self._odontologo_var = tk.StringVar()
        self._odontologos = models.get_odontologos()
        od_names = ["(Todos)"] + [f"{o['apellido']}, {o['nombre']}" for o in self._odontologos]
        self._od_combo = ttk.Combobox(ctrl, textvariable=self._odontologo_var,
                                      values=od_names, width=22, state="readonly")
        self._od_combo.set("(Todos)")
        self._od_combo.pack(side="left", padx=4)
        self._od_combo.bind("<<ComboboxSelected>>", lambda _: self._load())

        ttk.Button(ctrl, text="➕ Nuevo Turno", style="Accent.TButton",
                   command=self._new).pack(side="right", padx=8)

        # ── Tabla de turnos ───────────────────────────────────────────────────
        body = tk.Frame(self, bg=COLORS["bg"], padx=16)
        body.pack(fill="both", expand=True)

        cols = ("ID", "Hora", "Duración", "Paciente", "Odontólogo", "Motivo", "Estado")
        widths = (40, 80, 80, 200, 180, 200, 110)
        self._tree = ttk.Treeview(body, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, widths):
            self._tree.heading(c, text=c)
            self._tree.column(c, width=w)

        # Tags de color por estado
        for estado, color in ESTADO_COLORS.items():
            self._tree.tag_configure(estado, background=color)

        scroll_y = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_y.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="left", fill="y")
        self._tree.bind("<Double-1>", lambda _: self._edit())
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Botones de acción
        btn_bar = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=8)
        btn_bar.pack(fill="x")
        ttk.Button(btn_bar, text="✏️ Editar",    command=self._edit).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="✅ Marcar presente",
                   style="Success.TButton",
                   command=lambda: self._cambiar_estado("presente")).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="❌ Cancelar turno",
                   style="Danger.TButton",
                   command=lambda: self._cambiar_estado("cancelado")).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="📋 Ver paciente",
                   command=self._ver_paciente).pack(side="left", padx=20)
        self._lbl_total = tk.Label(btn_bar, text="", font=FONTS["small"],
                                   bg=COLORS["bg"], fg=COLORS["text_light"])
        self._lbl_total.pack(side="right")

        self._go_today()

    def _go_today(self):
        self._fecha_actual = datetime.date.today()
        self._load()

    def _prev_day(self):
        self._fecha_actual -= datetime.timedelta(days=1)
        self._load()

    def _next_day(self):
        self._fecha_actual += datetime.timedelta(days=1)
        self._load()

    def _go_date(self):
        iso = self._fecha_ir.get()
        if not iso:
            messagebox.showerror("Fecha inválida", "Seleccione una fecha válida.")
            return
        self._fecha_actual = datetime.date.fromisoformat(iso)
        self._load()

    def _load(self):
        fecha_str = self._fecha_actual.isoformat()
        self._lbl_fecha.configure(
            text=self._fecha_actual.strftime("%A %d de %B de %Y").capitalize()
        )
        self._fecha_ir.set(fecha_str)

        od_name = self._odontologo_var.get()
        od_id = None
        if od_name != "(Todos)":
            for o in self._odontologos:
                if f"{o['apellido']}, {o['nombre']}" == od_name:
                    od_id = o["id"]
                    break

        turnos = models.get_turnos(fecha=fecha_str, odontologo_id=od_id)
        self._tree.delete(*self._tree.get_children())
        for t in turnos:
            estado = t.get("estado", "pendiente")
            self._tree.insert("", "end", iid=str(t["id"]),
                              tags=(estado,), values=(
                t["id"], t["hora"], f"{t.get('duracion_min',30)} min",
                t["paciente_nombre"], t["odontologo_nombre"],
                t.get("motivo",""), estado.capitalize(),
            ))
        self._lbl_total.configure(text=f"{len(turnos)} turno(s)")

    def _on_select(self, _):
        sel = self._tree.selection()
        self._selected_id = int(sel[0]) if sel else None

    def _new(self):
        dlg = TurnoDialog(self, None, fecha_default=self._fecha_actual.isoformat())
        self.wait_window(dlg)
        self._load()

    def _edit(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un turno.")
            return
        dlg = TurnoDialog(self, self._selected_id)
        self.wait_window(dlg)
        self._load()

    def _cambiar_estado(self, estado: str):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un turno.")
            return
        turno = models.get_turno(self._selected_id)
        if turno:
            turno["estado"] = estado
            models.save_turno(turno)
            self._load()

    def _ver_paciente(self):
        if not self._selected_id:
            return
        turno = models.get_turno(self._selected_id)
        if turno:
            app_state.set_paciente(turno["paciente_id"])
            self.winfo_toplevel().show_page("pacientes")

    def on_show(self):
        self._odontologos = models.get_odontologos()
        self._load()


class TurnoDialog(tk.Toplevel):
    def __init__(self, parent, turno_id: Optional[int], fecha_default: str = "",
                 paciente_id: Optional[int] = None):
        super().__init__(parent)
        self._id = turno_id
        self.title("Nuevo Turno" if not turno_id else "Editar Turno")
        self.geometry("500x480")
        self.grab_set()
        self.configure(bg=COLORS["bg"])
        self._data = models.get_turno(turno_id) if turno_id else {}
        if paciente_id and not self._data.get("paciente_id"):
            self._data["paciente_id"] = paciente_id
        self._fecha_default = fecha_default or datetime.date.today().isoformat()
        self._pacientes = models.get_pacientes()
        self._odontologos = models.get_odontologos()
        self._vars = {}
        self._build()
        self._load()

    def _build(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=20, pady=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Paciente
        tk.Label(frame, text="Paciente *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=0, column=0, sticky="e", padx=6, pady=8)
        self._pac_var = tk.StringVar()
        pac_names = [f"{p['apellido']}, {p['nombre']} (DNI: {p.get('dni','')})"
                     for p in self._pacientes]
        self._pac_combo = ttk.Combobox(frame, textvariable=self._pac_var,
                                       values=pac_names, width=36)
        self._pac_combo.grid(row=0, column=1, sticky="ew", padx=6)

        # Odontólogo
        tk.Label(frame, text="Odontólogo *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=1, column=0, sticky="e", padx=6, pady=8)
        self._od_var = tk.StringVar()
        od_names = [f"{o['apellido']}, {o['nombre']}" for o in self._odontologos]
        ttk.Combobox(frame, textvariable=self._od_var,
                     values=od_names, width=36, state="readonly"
                     ).grid(row=1, column=1, sticky="ew", padx=6)

        def row(r, label, key, width=18):
            tk.Label(frame, text=label, font=FONTS["body"],
                     bg=COLORS["bg"]).grid(row=r, column=0, sticky="e", padx=6, pady=8)
            v = tk.StringVar()
            ttk.Entry(frame, textvariable=v, width=width).grid(row=r, column=1, sticky="w", padx=6)
            self._vars[key] = v

        # Fecha — selector con calendario
        tk.Label(frame, text="Fecha *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=2, column=0, sticky="e", padx=6, pady=8)
        self._fecha = DateEntry(frame)
        self._fecha.grid(row=2, column=1, sticky="w", padx=6)

        # Hora — spinbox horas + combobox minutos (solo lectura)
        tk.Label(frame, text="Hora *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=3, column=0, sticky="e", padx=6, pady=8)
        hora_frame = tk.Frame(frame, bg=COLORS["bg"])
        hora_frame.grid(row=3, column=1, sticky="w", padx=6)
        self._hora_h = ttk.Spinbox(hora_frame, from_=0, to=23, width=3,
                                   format="%02.0f", state="readonly")
        self._hora_h.pack(side="left")
        tk.Label(hora_frame, text=":", bg=COLORS["bg"],
                 font=FONTS["body"]).pack(side="left")
        self._hora_m = ttk.Combobox(hora_frame,
                                    values=["00", "15", "30", "45"],
                                    width=4, state="readonly")
        self._hora_m.set("00")
        self._hora_m.pack(side="left")

        # Duración — combobox de solo lectura
        tk.Label(frame, text="Duración (min)", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=4, column=0, sticky="e", padx=6, pady=8)
        self._duracion_var = tk.StringVar(value="30")
        ttk.Combobox(frame, textvariable=self._duracion_var,
                     values=["15", "20", "30", "45", "60", "90", "120"],
                     width=6, state="readonly").grid(row=4, column=1, sticky="w", padx=6)

        row(5, "Motivo", "motivo", 36)

        # Estado
        tk.Label(frame, text="Estado", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=6, column=0, sticky="e", padx=6, pady=8)
        self._estado_var = tk.StringVar(value="Pendiente")
        ttk.Combobox(frame, textvariable=self._estado_var,
                     values=ESTADOS, width=18, state="readonly"
                     ).grid(row=6, column=1, sticky="w", padx=6)

        tk.Label(frame, text="Notas", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=7, column=0, sticky="ne", padx=6, pady=8)
        self._notas = tk.Text(frame, height=4, width=36, font=FONTS["body"])
        self._notas.grid(row=7, column=1, sticky="ew", padx=6)

        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=20, pady=8)
        ttk.Button(btn_bar, text="💾 Guardar", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _load(self):
        d = self._data
        self._fecha.set(d.get("fecha", self._fecha_default))
        # Hora
        raw_hora = d.get("hora", "09:00")
        try:
            hh, mm = raw_hora.split(":")
        except ValueError:
            hh, mm = "09", "00"
        self._hora_h.set(hh.zfill(2))
        # Redondear minutos al slot más cercano (00/15/30/45)
        mm_int = int(mm) if mm.isdigit() else 0
        mm_slot = min(["00", "15", "30", "45"], key=lambda s: abs(int(s) - mm_int))
        self._hora_m.set(mm_slot)
        # Duración
        self._duracion_var.set(str(d.get("duracion_min", 30)))
        self._vars["motivo"].set(d.get("motivo", "") or "")
        self._estado_var.set(d.get("estado", "pendiente").capitalize())
        if d.get("notas"):
            self._notas.insert("1.0", d["notas"])
        # Paciente
        if d.get("paciente_id"):
            for i, p in enumerate(self._pacientes):
                if p["id"] == d["paciente_id"]:
                    self._pac_var.set(
                        f"{p['apellido']}, {p['nombre']} (DNI: {p.get('dni','')})"
                    )
                    break
        # Odontólogo
        if d.get("odontologo_id"):
            for o in self._odontologos:
                if o["id"] == d["odontologo_id"]:
                    self._od_var.set(f"{o['apellido']}, {o['nombre']}")
                    break

    def _save(self):
        # Resolver paciente
        pac_str = self._pac_var.get()
        pac_id = None
        for p in self._pacientes:
            if pac_str.startswith(f"{p['apellido']}, {p['nombre']}"):
                pac_id = p["id"]
                break
        # Resolver odontólogo
        od_str = self._od_var.get()
        od_id = None
        for o in self._odontologos:
            if f"{o['apellido']}, {o['nombre']}" == od_str:
                od_id = o["id"]
                break
        if not pac_id or not od_id:
            messagebox.showerror("Validación", "Seleccione paciente y odontólogo.")
            return
        fecha = self._fecha.get()
        hora  = f"{self._hora_h.get()}:{self._hora_m.get()}"
        if not fecha:
            messagebox.showerror("Validación", "La fecha es obligatoria.")
            return

        data = {
            "paciente_id":   pac_id,
            "odontologo_id": od_id,
            "fecha":         fecha,
            "hora":          hora,
            "duracion_min":  int(self._duracion_var.get() or 30),
            "motivo":        self._vars["motivo"].get().strip(),
            "estado":        self._estado_var.get().lower(),
            "notas":         self._notas.get("1.0", "end-1c").strip(),
        }
        if self._id:
            data["id"] = self._id
        models.save_turno(data)
        self.destroy()
