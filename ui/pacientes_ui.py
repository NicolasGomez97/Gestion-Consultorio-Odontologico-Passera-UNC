"""
pacientes_ui.py — Gestión completa de pacientes (CRUD + búsqueda avanzada).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import models
from ui.theme import COLORS, FONTS
from ui.app import app_state
from ui.turnos_ui import TurnoDialog
from ui.widgets import DateEntry


# ─────────────────────────────────────────────────────────────────────────────
# FRAME PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class PacientesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._selected_id: Optional[int] = None
        self._build()

    def _build(self):
        # Encabezado
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="👥  Gestión de Pacientes",
                 font=FONTS["title"], bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")

        # Cuerpo
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Búsqueda rápida ──────────────────────────────────────────────────
        search_row = tk.Frame(body, bg=COLORS["bg"])
        search_row.pack(fill="x", pady=(0, 8))

        tk.Label(search_row, text="Buscar:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._quick_search())
        entry = ttk.Entry(search_row, textvariable=self._search_var, width=28)
        entry.pack(side="left", padx=(4, 12))

        ttk.Button(search_row, text="🔍 Búsqueda Avanzada",
                   command=self._open_search).pack(side="left", padx=4)
        ttk.Button(search_row, text="↺ Mostrar todos",
                   command=self._load_all).pack(side="left", padx=4)
        ttk.Button(search_row, text="➕ Nuevo Paciente",
                   style="Accent.TButton",
                   command=self._new).pack(side="right", padx=4)

        # ── Tabla ────────────────────────────────────────────────────────────
        cols = ("ID", "Apellido", "Nombre", "DNI", "Fecha Nac.", "Obra Social", "Teléfono", "Estado")
        widths = (40, 130, 130, 90, 100, 140, 110, 80)
        self._tree = ttk.Treeview(body, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, widths):
            self._tree.heading(c, text=c, command=lambda _c=c: self._sort(_c))
            self._tree.column(c, width=w, minwidth=40)

        scroll_y = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_y.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="left", fill="y")

        self._tree.tag_configure("odd", background=COLORS["row_odd"])
        self._tree.bind("<Double-1>", lambda _: self._edit())
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Botones de acción ────────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=16, pady=8)
        ttk.Button(btn_bar, text="✏️ Editar",     command=self._edit).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🗑️ Dar de baja", style="Danger.TButton",
                   command=self._delete).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="📋 Ver Historial",
                   command=self._go_historial).pack(side="left", padx=20)
        ttk.Button(btn_bar, text="🦷 Ver Odontograma",
                   command=self._go_odontograma).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="💊 Ver Prestaciones",
                   command=self._go_prestaciones).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="📅 Nuevo Turno",
                   command=self._nuevo_turno).pack(side="left", padx=4)

        self._lbl_total = tk.Label(btn_bar, text="", font=FONTS["small"],
                                   bg=COLORS["bg"], fg=COLORS["text_light"])
        self._lbl_total.pack(side="right", padx=8)

        self._load_all()

    # ── Carga de datos ────────────────────────────────────────────────────────
    def _load_all(self):
        self._search_var.set("")
        self._populate(models.get_pacientes())

    def _quick_search(self):
        q = self._search_var.get().strip().lower()
        if not q:
            self._populate(models.get_pacientes())
            return
        # Búsqueda por nombre, apellido o DNI
        data = models.search_pacientes({"nombre": q}) + \
               models.search_pacientes({"apellido": q}) + \
               models.search_pacientes({"dni": q})
        # Deduplicar
        seen = set()
        unique = []
        for p in data:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique.append(p)
        self._populate(unique)

    def _populate(self, rows):
        self._tree.delete(*self._tree.get_children())
        for i, p in enumerate(rows):
            tag = "odd" if i % 2 else ""
            activo = "Activo" if p.get("activo", 1) else "Baja"
            self._tree.insert("", "end", iid=str(p["id"]), tags=(tag,), values=(
                p["id"], p["apellido"], p["nombre"],
                p.get("dni",""), p.get("fecha_nacimiento",""),
                p.get("obra_social_nombre",""),
                p.get("telefono",""), activo,
            ))
        self._lbl_total.configure(text=f"{len(rows)} paciente(s)")

    def _sort(self, col):
        items = [(self._tree.set(iid, col), iid) for iid in self._tree.get_children()]
        items.sort()
        for i, (_, iid) in enumerate(items):
            self._tree.move(iid, "", i)
            self._tree.item(iid, tags=("odd",) if i % 2 else ())

    def _on_select(self, _):
        sel = self._tree.selection()
        self._selected_id = int(sel[0]) if sel else None

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _new(self):
        dlg = PacienteDialog(self, None)
        self.wait_window(dlg)
        self._load_all()

    def _edit(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un paciente de la lista.")
            return
        dlg = PacienteDialog(self, self._selected_id)
        self.wait_window(dlg)
        self._load_all()

    def _delete(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un paciente.")
            return
        if messagebox.askyesno("Confirmar", "¿Dar de baja al paciente?"):
            models.delete_paciente(self._selected_id)
            self._load_all()

    def _open_search(self):
        dlg = BusquedaAvanzadaDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self._populate(dlg.result)

    def _go_historial(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un paciente.")
            return
        app_state.set_paciente(self._selected_id)
        self.winfo_toplevel().show_page("historial")

    def _go_odontograma(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un paciente.")
            return
        app_state.set_paciente(self._selected_id)
        self.winfo_toplevel().show_page("odontograma")

    def _go_prestaciones(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un paciente.")
            return
        app_state.set_paciente(self._selected_id)
        self.winfo_toplevel().show_page("prestaciones")

    def _nuevo_turno(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un paciente.")
            return
        dlg = TurnoDialog(self, None, paciente_id=self._selected_id)
        self.wait_window(dlg)

    def on_show(self):
        self._load_all()


# ─────────────────────────────────────────────────────────────────────────────
# DIÁLOGO NUEVO / EDITAR PACIENTE
# ─────────────────────────────────────────────────────────────────────────────

class PacienteDialog(tk.Toplevel):
    def __init__(self, parent, paciente_id: Optional[int]):
        super().__init__(parent)
        self._id = paciente_id
        self.title("Nuevo Paciente" if not paciente_id else "Editar Paciente")
        self.geometry("760x680")
        self.resizable(True, True)
        self.grab_set()
        self._data = models.get_paciente(paciente_id) if paciente_id else {}
        self._obras = models.get_obras_sociales()
        self._build()
        self._load_data()

    def _build(self):
        self.configure(bg=COLORS["bg"])

        # Notebook con pestañas
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=8)

        tab1 = tk.Frame(nb, bg=COLORS["bg"])
        tab2 = tk.Frame(nb, bg=COLORS["bg"])
        tab3 = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(tab1, text="  Datos Personales  ")
        nb.add(tab2, text="  Obra Social  ")
        nb.add(tab3, text="  Antecedentes Médicos  ")

        self._fields = {}
        self._build_tab1(tab1)
        self._build_tab2(tab2)
        self._build_tab3(tab3)

        # Botones
        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=12, pady=8)
        ttk.Button(btn_bar, text="💾 Guardar", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=4)

    def _lbl_entry(self, parent, row, col, label, key, required=False):
        lbl_text = label + (" *" if required else "")
        tk.Label(parent, text=lbl_text, font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=row, column=col*2, sticky="e", padx=6, pady=4)
        var = tk.StringVar()
        e = ttk.Entry(parent, textvariable=var, width=22)
        e.grid(row=row, column=col*2+1, sticky="w", padx=6, pady=4)
        self._fields[key] = var
        return var

    def _build_tab1(self, tab):
        tab.columnconfigure((1,3), weight=1)
        self._lbl_entry(tab, 0, 0, "Nombre",           "nombre",         True)
        self._lbl_entry(tab, 0, 1, "Apellido",          "apellido",       True)
        self._lbl_entry(tab, 1, 0, "DNI", "dni")
        # Fecha Nacimiento — selector con calendario
        tk.Label(tab, text="Fecha Nacimiento", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=1, column=2, sticky="e", padx=6, pady=4)
        self._fecha_nac = DateEntry(tab)
        self._fecha_nac.grid(row=1, column=3, sticky="w", padx=6, pady=4)
        tk.Label(tab, text="Sexo", font=FONTS["body"], bg=COLORS["bg"]
                 ).grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self._sex_var = tk.StringVar()
        ttk.Combobox(tab, textvariable=self._sex_var, values=["M", "F", "X"], width=8,
                     state="readonly").grid(row=2, column=1, sticky="w", padx=6, pady=4)
        self._fields["sexo"] = self._sex_var

        tk.Label(tab, text="Estado Civil", font=FONTS["body"], bg=COLORS["bg"]
                 ).grid(row=2, column=2, sticky="e", padx=6, pady=4)
        self._ecivil_var = tk.StringVar()
        ttk.Combobox(tab, textvariable=self._ecivil_var,
                     values=["Soltero","Casado","Divorciado","Viudo","Otro"],
                     width=14, state="readonly").grid(row=2, column=3, sticky="w", padx=6, pady=4)
        self._fields["estado_civil"] = self._ecivil_var

        self._lbl_entry(tab, 3, 0, "Dirección",         "direccion")
        self._lbl_entry(tab, 3, 1, "Teléfono",          "telefono")
        self._lbl_entry(tab, 4, 0, "Email",              "email")
        self._lbl_entry(tab, 4, 1, "Lugar de Trabajo",  "lugar_trabajo")
        self._lbl_entry(tab, 5, 0, "Jerarquía/Cargo",   "jerarquia")
        self._lbl_entry(tab, 5, 1, "Médico Clínico",    "medico_clinico")

        tk.Label(tab, text="Observaciones", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=6, column=0, sticky="ne", padx=6, pady=4)
        self._obs_text = tk.Text(tab, height=4, width=55, font=FONTS["body"])
        self._obs_text.grid(row=6, column=1, columnspan=3, sticky="ew", padx=6, pady=4)

    def _build_tab2(self, tab):
        tab.columnconfigure((1,3), weight=1)
        obras_names = [o["nombre"] for o in self._obras]
        tk.Label(tab, text="Obra Social", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=0, column=0, sticky="e", padx=6, pady=8)
        self._os_var = tk.StringVar()
        ttk.Combobox(tab, textvariable=self._os_var,
                     values=["(Particular)"] + obras_names,
                     width=28, state="readonly").grid(row=0, column=1, sticky="w", padx=6, pady=8)

        self._lbl_entry(tab, 1, 0, "N° Afiliado",   "num_afiliado")

        # Titular — Sí / No
        tk.Label(tab, text="Titular", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=1, column=2, sticky="e", padx=6, pady=4)
        self._titular_var = tk.StringVar(value="Sí")
        ttk.Combobox(tab, textvariable=self._titular_var,
                     values=["Sí", "No"], width=8,
                     state="readonly").grid(row=1, column=3, sticky="w", padx=6, pady=4)
        self._fields["titular"] = self._titular_var

        self._lbl_entry(tab, 2, 0, "Grupo Familiar", "grupo_familiar")

    def _build_tab3(self, tab):
        tab.columnconfigure(1, weight=1)

        def lbl_text_area(row, label, attr):
            tk.Label(tab, text=label, font=FONTS["body"],
                     bg=COLORS["bg"]).grid(row=row, column=0, sticky="ne", padx=6, pady=6)
            t = tk.Text(tab, height=4, width=60, font=FONTS["body"])
            t.grid(row=row, column=1, sticky="ew", padx=6, pady=6)
            setattr(self, f"_{attr}_text", t)

        lbl_text_area(0, "Alergias",       "alergias")
        lbl_text_area(1, "Enfermedades",   "enfermedades")

    # ── Carga y guardado ──────────────────────────────────────────────────────
    def _load_data(self):
        d = self._data
        for key, var in self._fields.items():
            var.set(d.get(key) or "")
        self._fecha_nac.set(d.get("fecha_nacimiento") or "")
        if d.get("observaciones"):
            self._obs_text.insert("1.0", d["observaciones"])
        if d.get("alergias"):
            self._alergias_text.insert("1.0", d["alergias"])
        if d.get("enfermedades"):
            self._enfermedades_text.insert("1.0", d["enfermedades"])
        # Obra social
        if d.get("obra_social_id"):
            os_map = {o["id"]: o["nombre"] for o in self._obras}
            self._os_var.set(os_map.get(d["obra_social_id"], "(Particular)"))
        else:
            self._os_var.set("(Particular)")

    def _save(self):
        data = {k: v.get().strip() for k, v in self._fields.items()}
        if not data.get("nombre") or not data.get("apellido"):
            messagebox.showerror("Validación", "Nombre y Apellido son obligatorios.")
            return
        data["fecha_nacimiento"] = self._fecha_nac.get()
        data["observaciones"] = self._obs_text.get("1.0", "end-1c").strip()
        data["alergias"]      = self._alergias_text.get("1.0", "end-1c").strip()
        data["enfermedades"]  = self._enfermedades_text.get("1.0", "end-1c").strip()

        # Mapear obra social
        os_name = self._os_var.get()
        data["obra_social_id"] = None
        for o in self._obras:
            if o["nombre"] == os_name:
                data["obra_social_id"] = o["id"]
                break

        if self._id:
            data["id"] = self._id
        if "activo" not in data or data["activo"] == "":
            data["activo"] = 1
        models.save_paciente(data)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# DIÁLOGO BÚSQUEDA AVANZADA
# ─────────────────────────────────────────────────────────────────────────────

class BusquedaAvanzadaDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Búsqueda Avanzada de Pacientes")
        self.geometry("640x560")
        self.grab_set()
        self.result = None
        self._obras = models.get_obras_sociales()
        self._odontologos = models.get_odontologos()
        self._build()

    def _build(self):
        self.configure(bg=COLORS["bg"])
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=8)

        tab1 = tk.Frame(nb, bg=COLORS["bg"])
        tab2 = tk.Frame(nb, bg=COLORS["bg"])
        nb.add(tab1, text="  Datos del Paciente  ")
        nb.add(tab2, text="  Criterios Clínicos  ")

        self._vars: dict = {}

        # ── Tab 1 ──
        def row(parent, r, label, key, width=20):
            tk.Label(parent, text=label, font=FONTS["body"],
                     bg=COLORS["bg"]).grid(row=r, column=0, sticky="e", padx=8, pady=6)
            v = tk.StringVar()
            ttk.Entry(parent, textvariable=v, width=width).grid(row=r, column=1, sticky="w", padx=8)
            self._vars[key] = v

        row(tab1, 0, "Nombre:",          "nombre")
        row(tab1, 1, "Apellido:",         "apellido")
        row(tab1, 2, "DNI:",              "dni")
        row(tab1, 3, "N° Afiliado:",      "num_afiliado")

        tk.Label(tab1, text="Obra Social:", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self._os_var = tk.StringVar()
        ttk.Combobox(tab1, textvariable=self._os_var,
                     values=["(Cualquiera)"] + [o["nombre"] for o in self._obras],
                     width=22, state="readonly").grid(row=4, column=1, sticky="w", padx=8)
        self._os_var.set("(Cualquiera)")

        tk.Label(tab1, text="Estado Civil:", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=5, column=0, sticky="e", padx=8, pady=6)
        self._ecivil_var = tk.StringVar()
        ttk.Combobox(tab1, textvariable=self._ecivil_var,
                     values=["(Cualquiera)","Soltero","Casado","Divorciado","Viudo","Otro"],
                     width=16, state="readonly").grid(row=5, column=1, sticky="w", padx=8)
        self._ecivil_var.set("(Cualquiera)")

        tk.Label(tab1, text="Odontólogo:", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=6, column=0, sticky="e", padx=8, pady=6)
        self._od_var = tk.StringVar()
        ttk.Combobox(tab1, textvariable=self._od_var,
                     values=["(Cualquiera)"] + [f"{o['apellido']}, {o['nombre']}" for o in self._odontologos],
                     width=28, state="readonly").grid(row=6, column=1, sticky="w", padx=8)
        self._od_var.set("(Cualquiera)")

        # ── Tab 2 ──
        row(tab2, 0, "Enfermedad:",         "enfermedades")
        row(tab2, 1, "Edad mínima:",        "edad_min", 8)
        row(tab2, 2, "Edad máxima:",        "edad_max", 8)
        row(tab2, 5, "Prof. bolsa ≥ (mm):", "profundidad_min", 8)

        # Fechas de nacimiento con selector calendario
        tk.Label(tab2, text="Nacido desde:", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self._fecha_desde = DateEntry(tab2)
        self._fecha_desde.grid(row=3, column=1, sticky="w", padx=8, pady=6)

        tk.Label(tab2, text="Nacido hasta:", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self._fecha_hasta = DateEntry(tab2)
        self._fecha_hasta.grid(row=4, column=1, sticky="w", padx=8, pady=6)

        # Botones
        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=12, pady=8)
        ttk.Button(btn_bar, text="🔍 Buscar", style="Accent.TButton",
                   command=self._search).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _search(self):
        criterios = {k: v.get().strip() for k, v in self._vars.items() if v.get().strip()}
        if self._fecha_desde.get():
            criterios["fecha_nacimiento_desde"] = self._fecha_desde.get()
        if self._fecha_hasta.get():
            criterios["fecha_nacimiento_hasta"] = self._fecha_hasta.get()
        os_name = self._os_var.get()
        if os_name != "(Cualquiera)":
            for o in self._obras:
                if o["nombre"] == os_name:
                    criterios["obra_social_id"] = o["id"]
                    break
        ec = self._ecivil_var.get()
        if ec != "(Cualquiera)":
            criterios["estado_civil"] = ec
        od_name = self._od_var.get()
        if od_name != "(Cualquiera)":
            for o in self._odontologos:
                if f"{o['apellido']}, {o['nombre']}" == od_name:
                    criterios["odontologo_id"] = o["id"]
                    break
        self.result = models.search_pacientes(criterios)
        self.destroy()
