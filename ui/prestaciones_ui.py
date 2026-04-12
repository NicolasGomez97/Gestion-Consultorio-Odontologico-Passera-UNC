"""
prestaciones_ui.py — Registro de prestaciones odontológicas y envío a Federación.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
import datetime
import models
from ui.theme import COLORS, FONTS
from ui.app import app_state
from ui.widgets import DateEntry


class PrestacionesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._selected_id: Optional[int] = None
        self._pac_id: Optional[int] = None
        self._build()
        app_state.register("patient_changed", lambda **kw: self._on_patient_change(**kw))
        app_state.register("nueva_prestacion", lambda **kw: self._on_nueva_prestacion(**kw))

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="💊  Registro de Prestaciones",
                 font=FONTS["title"], bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")
        self._lbl_pac = tk.Label(hdr, text="Sin paciente seleccionado",
                                  font=FONTS["body"], bg=COLORS["header_bg"], fg="#BEE3F8")
        self._lbl_pac.pack(padx=20, anchor="w")

        # Controles
        ctrl = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=8)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Paciente:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left")
        self._pac_var = tk.StringVar()
        self._pac_combo = ttk.Combobox(ctrl, textvariable=self._pac_var, width=34)
        self._pac_combo.pack(side="left", padx=6)
        ttk.Button(ctrl, text="Cargar", command=self._cargar_combo).pack(side="left")

        # Filtros de fecha
        tk.Label(ctrl, text="  Desde:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left")
        self._desde = DateEntry(ctrl)
        self._desde.pack(side="left", padx=2)
        tk.Label(ctrl, text="Hasta:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left", padx=(6, 0))
        self._hasta = DateEntry(ctrl)
        self._hasta.pack(side="left", padx=2)
        ttk.Button(ctrl, text="Filtrar", command=self._load).pack(side="left", padx=4)

        ttk.Button(ctrl, text="➕ Nueva Prestación", style="Accent.TButton",
                   command=self._new).pack(side="right", padx=8)

        # Tabla
        body = tk.Frame(self, bg=COLORS["bg"], padx=16)
        body.pack(fill="both", expand=True)

        cols = ("ID", "Fecha", "Paciente", "Odontólogo", "Cód.", "Prestación",
                "Diente", "Sup.", "Monto", "Obra Social", "Enviado")
        widths = (40, 95, 160, 150, 55, 200, 60, 50, 80, 120, 70)
        self._tree = ttk.Treeview(body, columns=cols, show="headings", selectmode="extended")
        for c, w in zip(cols, widths):
            self._tree.heading(c, text=c)
            self._tree.column(c, width=w)
        scroll_y = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        scroll_x = ttk.Scrollbar(body, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_x.pack(side="bottom", fill="x")
        self._tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="left", fill="y")
        self._tree.tag_configure("odd", background=COLORS["row_odd"])
        self._tree.tag_configure("enviado", background="#C6F6D5")
        self._tree.tag_configure("pendiente_fed", background="#FED7D7")
        self._tree.bind("<Double-1>", lambda _: self._edit())
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Botones de acción
        btn_bar = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=8)
        btn_bar.pack(fill="x")
        ttk.Button(btn_bar, text="✏️ Editar",        command=self._edit).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🗑️ Eliminar", style="Danger.TButton",
                   command=self._delete).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="📤 Marcar enviado a Federación",
                   style="Success.TButton",
                   command=self._marcar_enviado).pack(side="left", padx=20)
        ttk.Button(btn_bar, text="📋 Ver pendientes Federación",
                   command=self._ver_pendientes).pack(side="left", padx=4)

        self._lbl_total = tk.Label(btn_bar, text="", font=FONTS["subtitle"],
                                    bg=COLORS["bg"], fg=COLORS["accent"])
        self._lbl_total.pack(side="right", padx=8)

        self._refresh_pacientes()

    # ── Datos ─────────────────────────────────────────────────────────────────

    def _refresh_pacientes(self):
        self._pacientes = models.get_pacientes()
        names = [f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})"
                 for p in self._pacientes]
        self._pac_combo["values"] = names

    def _on_patient_change(self, paciente_id=None, **kw):
        if paciente_id:
            for p in self._pacientes:
                if p["id"] == paciente_id:
                    self._pac_var.set(f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})")
                    self._pac_id = paciente_id
                    self._load()
                    break

    def _on_nueva_prestacion(self, fdi=None, superficie=None, **kw):
        """Llamado desde el odontograma para pre-llenar una nueva prestación."""
        self._new(fdi_preset=fdi, surf_preset=superficie)

    def _cargar_combo(self):
        val = self._pac_var.get()
        for p in self._pacientes:
            if val.startswith(f"{p['apellido']}, {p['nombre']}"):
                self._pac_id = p["id"]
                app_state.set_paciente(p["id"])
                self._load()
                return

    def _load(self):
        pac_id  = self._pac_id
        desde   = self._desde.get() or None
        hasta   = self._hasta.get() or None
        rows = models.get_prestaciones(paciente_id=pac_id, desde=desde, hasta=hasta)

        if pac_id:
            pac = models.get_paciente(pac_id)
            if pac:
                self._lbl_pac.configure(
                    text=f"Paciente: {pac['apellido']}, {pac['nombre']} — DNI: {pac.get('dni','')}"
                )

        self._tree.delete(*self._tree.get_children())
        total = 0.0
        for i, r in enumerate(rows):
            enviado = r.get("enviado_federacion", 0)
            if enviado:
                tag = "enviado"
            elif r.get("obra_social_id"):
                tag = "pendiente_fed"
            else:
                tag = "odd" if i % 2 else ""
            self._tree.insert("", "end", iid=str(r["id"]), tags=(tag,), values=(
                r["id"], r["fecha"],
                r.get("paciente_nombre",""), r.get("odontologo_nombre",""),
                r.get("nom_codigo",""), r.get("nom_descripcion",""),
                r.get("numero_fdi","") or "",
                r.get("superficies","") or "",
                f"${r.get('monto',0):,.0f}",
                r.get("obra_social_nombre","") or "Particular",
                "✅" if enviado else "⏳",
            ))
            total += float(r.get("monto", 0) or 0)
        self._lbl_total.configure(text=f"Total: ${total:,.0f}  ({len(rows)} prestaciones)")

    def _on_select(self, _):
        sel = self._tree.selection()
        self._selected_id = int(sel[0]) if sel else None

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _new(self, fdi_preset=None, surf_preset=None):
        dlg = PrestacionDialog(self, None,
                                pac_id=self._pac_id,
                                fdi_preset=fdi_preset,
                                surf_preset=surf_preset)
        self.wait_window(dlg)
        self._load()

    def _edit(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione una prestación.")
            return
        dlg = PrestacionDialog(self, self._selected_id)
        self.wait_window(dlg)
        self._load()

    def _delete(self):
        if not self._selected_id:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar esta prestación?"):
            models.delete_prestacion(self._selected_id)
            self._load()

    def _marcar_enviado(self):
        selected = [int(iid) for iid in self._tree.selection()]
        if not selected:
            messagebox.showinfo("Selección", "Seleccione una o más prestaciones con Ctrl+Click.")
            return
        if messagebox.askyesno("Confirmar",
                                f"¿Marcar {len(selected)} prestación(es) como enviada(s) a la Federación?"):
            models.marcar_enviado_federacion(selected)
            self._load()

    def _ver_pendientes(self):
        dlg = PendientesFederacionDialog(self)
        self.wait_window(dlg)

    def on_show(self):
        self._refresh_pacientes()
        pid = app_state.paciente_id
        if pid and pid != self._pac_id:
            self._pac_id = pid
            for p in self._pacientes:
                if p["id"] == pid:
                    self._pac_var.set(f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})")
                    break
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
# DIÁLOGO NUEVA / EDITAR PRESTACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class PrestacionDialog(tk.Toplevel):
    def __init__(self, parent, prestacion_id: Optional[int],
                 pac_id: Optional[int] = None,
                 fdi_preset: Optional[int] = None,
                 surf_preset: Optional[str] = None):
        super().__init__(parent)
        self._id         = prestacion_id
        self._pac_id_pre = pac_id
        self._fdi_preset = fdi_preset
        self._surf_preset= surf_preset
        self.title("Nueva Prestación" if not prestacion_id else "Editar Prestación")
        self.geometry("640x580")
        self.grab_set()
        self.configure(bg=COLORS["bg"])
        self._pacientes    = models.get_pacientes()
        self._odontologos  = models.get_odontologos()
        self._obras        = models.get_obras_sociales()
        self._nomenclador  = models.get_nomenclador()
        self._nom_categorias = ["(Todas)"] + models.get_categorias_nomenclador()
        self._data = {}
        if prestacion_id:
            rows = models.get_prestaciones()
            for r in rows:
                if r["id"] == prestacion_id:
                    self._data = r
                    break
        self._build()
        self._load()

    def _build(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=20, pady=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        # Paciente
        tk.Label(frame, text="Paciente *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self._pac_var = tk.StringVar()
        pac_names = [f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})"
                     for p in self._pacientes]
        ttk.Combobox(frame, textvariable=self._pac_var, values=pac_names,
                     width=36).grid(row=0, column=1, columnspan=3, sticky="ew", padx=6)

        # Odontólogo
        tk.Label(frame, text="Odontólogo *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self._od_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self._od_var,
                     values=[f"{o['apellido']}, {o['nombre']}" for o in self._odontologos],
                     width=36, state="readonly").grid(row=1, column=1, columnspan=3,
                                                       sticky="ew", padx=6)

        # Fecha — selector con calendario
        tk.Label(frame, text="Fecha *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self._fecha = DateEntry(frame)
        self._fecha.set(datetime.date.today().isoformat())
        self._fecha.grid(row=2, column=1, sticky="w", padx=6)

        # Categoría y prestación
        tk.Label(frame, text="Categoría", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self._cat_var = tk.StringVar()
        cat_cb = ttk.Combobox(frame, textvariable=self._cat_var,
                               values=self._nom_categorias, width=20, state="readonly")
        cat_cb.grid(row=3, column=1, sticky="w", padx=6)
        cat_cb.set("(Todas)")
        cat_cb.bind("<<ComboboxSelected>>", lambda _: self._filter_nomenclador())

        tk.Label(frame, text="Prestación *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=4, column=0, sticky="e", padx=6, pady=6)
        self._nom_var = tk.StringVar()
        self._nom_cb = ttk.Combobox(frame, textvariable=self._nom_var, width=46)
        self._nom_cb.grid(row=4, column=1, columnspan=3, sticky="ew", padx=6)
        self._nom_cb.bind("<<ComboboxSelected>>", lambda _: self._on_nom_select())
        self._filter_nomenclador()

        # Diente y superficies
        tk.Label(frame, text="N° Diente (FDI)", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=5, column=0, sticky="e", padx=6, pady=6)
        self._fdi_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._fdi_var, width=8
                  ).grid(row=5, column=1, sticky="w", padx=6)

        tk.Label(frame, text="Superficies", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=5, column=2, sticky="e", padx=6)
        self._surf_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._surf_var, width=12
                  ).grid(row=5, column=3, sticky="w", padx=6)
        tk.Label(frame, text="(ej: M,D,O)", font=FONTS["small"],
                 bg=COLORS["bg"], fg=COLORS["text_light"]).grid(row=6, column=3, sticky="w", padx=6)

        # Monto
        tk.Label(frame, text="Monto ($)", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=6, column=0, sticky="e", padx=6, pady=6)
        self._monto_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self._monto_var, width=12
                  ).grid(row=6, column=1, sticky="w", padx=6)

        # Obra social
        tk.Label(frame, text="Obra Social", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=7, column=0, sticky="e", padx=6, pady=6)
        self._os_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self._os_var,
                     values=["(Particular)"] + [o["nombre"] for o in self._obras],
                     width=24, state="readonly").grid(row=7, column=1, sticky="w", padx=6)
        self._os_var.set("(Particular)")

        tk.Label(frame, text="N° Afiliado", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=7, column=2, sticky="e", padx=6)
        self._afil_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._afil_var, width=16
                  ).grid(row=7, column=3, sticky="w", padx=6)

        # Enviado a Federación
        self._env_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Enviado a Federación Odontológica",
                         variable=self._env_var).grid(row=8, column=1, columnspan=2,
                                                       sticky="w", padx=6, pady=6)

        # Notas
        tk.Label(frame, text="Notas", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=9, column=0, sticky="ne", padx=6, pady=6)
        self._notas = tk.Text(frame, height=3, width=50, font=FONTS["body"], wrap="word")
        self._notas.grid(row=9, column=1, columnspan=3, sticky="ew", padx=6, pady=6)

        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=20, pady=8)
        ttk.Button(btn_bar, text="💾 Guardar", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _filter_nomenclador(self):
        cat = self._cat_var.get()
        if cat == "(Todas)":
            nom_list = self._nomenclador
        else:
            nom_list = [n for n in self._nomenclador if n.get("categoria") == cat]
        values = [f"{n['codigo']} — {n['descripcion']}" for n in nom_list]
        self._nom_cb["values"] = values
        self._nom_filtered = nom_list

    def _on_nom_select(self):
        val = self._nom_var.get()
        for n in getattr(self, "_nom_filtered", self._nomenclador):
            if val.startswith(n["codigo"]):
                self._monto_var.set(str(n.get("costo_base", 0)))
                break

    def _load(self):
        d = self._data
        # Presets from odontogram
        if self._fdi_preset:
            self._fdi_var.set(str(self._fdi_preset))
        if self._surf_preset:
            self._surf_var.set(self._surf_preset)
        if self._pac_id_pre:
            for p in self._pacientes:
                if p["id"] == self._pac_id_pre:
                    self._pac_var.set(f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})")
                    break
        if not d:
            return

        if d.get("paciente_id"):
            for p in self._pacientes:
                if p["id"] == d["paciente_id"]:
                    self._pac_var.set(f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})")
                    break
        if d.get("odontologo_id"):
            for o in self._odontologos:
                if o["id"] == d["odontologo_id"]:
                    self._od_var.set(f"{o['apellido']}, {o['nombre']}")
                    break
        self._fecha.set(d.get("fecha", datetime.date.today().isoformat()))
        if d.get("nomenclador_id"):
            for n in self._nomenclador:
                if n["id"] == d["nomenclador_id"]:
                    self._nom_var.set(f"{n['codigo']} — {n['descripcion']}")
                    break
        self._fdi_var.set(str(d.get("numero_fdi","") or ""))
        self._surf_var.set(d.get("superficies","") or "")
        self._monto_var.set(str(d.get("monto",0)))
        if d.get("obra_social_id"):
            for o in self._obras:
                if o["id"] == d["obra_social_id"]:
                    self._os_var.set(o["nombre"])
                    break
        self._afil_var.set(d.get("num_afiliado","") or "")
        self._env_var.set(bool(d.get("enviado_federacion",0)))
        if d.get("notas"):
            self._notas.insert("1.0", d["notas"])

    def _save(self):
        # Paciente
        pac_str = self._pac_var.get()
        pac_id = None
        for p in self._pacientes:
            if pac_str.startswith(f"{p['apellido']}, {p['nombre']}"):
                pac_id = p["id"]
                break
        # Odontólogo
        od_str = self._od_var.get()
        od_id = None
        for o in self._odontologos:
            if f"{o['apellido']}, {o['nombre']}" == od_str:
                od_id = o["id"]
                break
        # Nomenclador
        nom_val = self._nom_var.get()
        nom_id = None
        for n in self._nomenclador:
            if nom_val.startswith(n["codigo"]):
                nom_id = n["id"]
                break

        if not pac_id or not od_id or not nom_id:
            messagebox.showerror("Validación",
                                  "Paciente, Odontólogo y Prestación son obligatorios.")
            return

        os_name = self._os_var.get()
        os_id = None
        for o in self._obras:
            if o["nombre"] == os_name:
                os_id = o["id"]
                break

        fdi_str = self._fdi_var.get().strip()
        try:
            fdi = int(fdi_str) if fdi_str else None
        except ValueError:
            fdi = None
        try:
            monto = float(self._monto_var.get() or 0)
        except ValueError:
            monto = 0.0

        data = {
            "paciente_id":      pac_id,
            "odontologo_id":    od_id,
            "nomenclador_id":   nom_id,
            "fecha":            self._fecha.get(),
            "numero_fdi":       fdi,
            "superficies":      self._surf_var.get().strip() or None,
            "monto":            monto,
            "obra_social_id":   os_id,
            "num_afiliado":     self._afil_var.get().strip() or None,
            "enviado_federacion": 1 if self._env_var.get() else 0,
            "fecha_envio_fed":  None,
            "historial_id":     None,
            "notas":            self._notas.get("1.0","end-1c").strip() or None,
        }
        if self._id:
            data["id"] = self._id
        models.save_prestacion(data)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# DIÁLOGO PENDIENTES FEDERACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class PendientesFederacionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Prestaciones Pendientes de Envío a Federación")
        self.geometry("980x500")
        self.grab_set()
        self.configure(bg=COLORS["bg"])
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["warning"], pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📤  Prestaciones pendientes de envío a la Federación Odontológica de Córdoba",
                 font=FONTS["subtitle"], bg=COLORS["warning"], fg=COLORS["text"]).pack(padx=16, anchor="w")

        # Filtros de fecha
        ctrl = tk.Frame(self, bg=COLORS["bg"], pady=6, padx=12)
        ctrl.pack(fill="x")
        tk.Label(ctrl, text="Período:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left")
        self._desde_fed = DateEntry(ctrl)
        self._desde_fed.set(datetime.date.today().replace(day=1).isoformat())
        self._desde_fed.pack(side="left", padx=4)
        tk.Label(ctrl, text="→", bg=COLORS["bg"]).pack(side="left")
        self._hasta_fed = DateEntry(ctrl)
        self._hasta_fed.set(datetime.date.today().isoformat())
        self._hasta_fed.pack(side="left", padx=4)
        ttk.Button(ctrl, text="🔍 Filtrar", command=self._load).pack(side="left", padx=8)
        ttk.Button(ctrl, text="✅ Marcar seleccionados como enviados",
                   style="Success.TButton",
                   command=self._marcar).pack(side="right", padx=8)

        cols = ("ID", "Fecha", "Paciente", "N° Afiliado", "Obra Social",
                "Odontólogo", "Prestación", "Diente", "Monto")
        widths = (40, 95, 160, 100, 120, 150, 220, 60, 80)
        self._tree = ttk.Treeview(self, columns=cols, show="headings",
                                   selectmode="extended")
        for c, w in zip(cols, widths):
            self._tree.heading(c, text=c)
            self._tree.column(c, width=w)
        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_y.set)
        self._tree.tag_configure("odd", background=COLORS["row_odd"])
        scroll_y.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True, padx=12, pady=4)

        self._lbl_total = tk.Label(self, text="", font=FONTS["subtitle"],
                                    bg=COLORS["bg"], fg=COLORS["danger"])
        self._lbl_total.pack(pady=4)
        self._load()

    def _load(self):
        rows = models.get_prestaciones(
            desde=self._desde_fed.get() or None,
            hasta=self._hasta_fed.get() or None,
            pendiente_federacion=True,
        )
        # Filtrar solo los que tienen obra social
        rows = [r for r in rows if r.get("obra_social_id")]
        self._tree.delete(*self._tree.get_children())
        total = 0.0
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 else ""
            self._tree.insert("", "end", iid=str(r["id"]), tags=(tag,), values=(
                r["id"], r["fecha"],
                r.get("paciente_nombre",""),
                r.get("num_afiliado","") or "",
                r.get("obra_social_nombre",""),
                r.get("odontologo_nombre",""),
                r.get("nom_descripcion",""),
                r.get("numero_fdi","") or "",
                f"${r.get('monto',0):,.0f}",
            ))
            total += float(r.get("monto",0) or 0)
        self._lbl_total.configure(
            text=f"{len(rows)} prestación(es) pendientes — Total a cobrar: ${total:,.0f}"
        )

    def _marcar(self):
        selected = [int(iid) for iid in self._tree.selection()]
        if not selected:
            messagebox.showinfo("Selección",
                                "Seleccione prestaciones con Ctrl+Click o Shift+Click.")
            return
        if messagebox.askyesno("Confirmar",
                                f"¿Marcar {len(selected)} prestación(es) como enviadas?"):
            models.marcar_enviado_federacion(selected)
            self._load()
