"""
reportes_ui.py — Reportes clínicos y administrativos.
Consultorio Odontológico Passera
"""
from __future__ import annotations

import csv
import datetime
import os
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import List, Dict, Optional

import models
from ui.theme import COLORS, FONTS
from ui.widgets import DateEntry


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hoy() -> str:
    return datetime.date.today().isoformat()


def _primer_dia_mes() -> str:
    hoy = datetime.date.today()
    return hoy.replace(day=1).isoformat()


def _exportar_csv(columnas: List[str], filas: List[Dict], nombre_sugerido: str):
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        initialfile=nombre_sugerido,
        title="Exportar como CSV",
    )
    if not path:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filas)
    messagebox.showinfo("Exportar", f"Archivo guardado:\n{path}")


def _build_tree(parent: tk.Widget, columnas: List[str],
                widths: Optional[Dict[str, int]] = None) -> ttk.Treeview:
    frame = tk.Frame(parent, bg=COLORS["bg"])
    frame.pack(fill="both", expand=True)

    vsb = ttk.Scrollbar(frame, orient="vertical")
    hsb = ttk.Scrollbar(frame, orient="horizontal")
    tree = ttk.Treeview(
        frame, columns=columnas, show="headings",
        yscrollcommand=vsb.set, xscrollcommand=hsb.set,
    )
    vsb.configure(command=tree.yview)
    hsb.configure(command=tree.xview)

    vsb.pack(side="right",  fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    for col in columnas:
        w = (widths or {}).get(col, 130)
        tree.heading(col, text=col, anchor="w")
        tree.column(col, width=w, anchor="w", minwidth=50)

    tree.tag_configure("odd",  background=COLORS["row_odd"])
    tree.tag_configure("even", background=COLORS["row_even"])
    return tree


def _fill_tree(tree: ttk.Treeview, columnas: List[str], filas: List[Dict]):
    tree.delete(*tree.get_children())
    for i, row in enumerate(filas):
        tag = "odd" if i % 2 else "even"
        vals = [row.get(c, "") for c in columnas]
        tree.insert("", "end", values=vals, tags=(tag,))


def _fecha_entry(parent: tk.Widget, label: str, default: str) -> DateEntry:
    tk.Label(parent, text=label, bg=COLORS["bg"],
             font=FONTS["body"], fg=COLORS["text"]).pack(side="left", padx=(8, 2))
    entry = DateEntry(parent)
    entry.set(default)
    entry.pack(side="left", padx=(0, 8))
    return entry


# ─────────────────────────────────────────────────────────────────────────────
# Frame principal
# ─────────────────────────────────────────────────────────────────────────────

class ReportesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build()

    def _build(self):
        # Encabezado
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Reportes", font=FONTS["title"],
                 bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=24, anchor="w")
        tk.Label(hdr, text="Reportes clínicos y administrativos — exportables a CSV",
                 font=FONTS["body"], bg=COLORS["header_bg"], fg="#BEE3F8").pack(padx=24, anchor="w")

        # Notebook de pestañas
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=12)

        nb.add(ReporteTurnosTab(nb),             text="  📅  Turnos  ")
        nb.add(ReportePrestacionesTab(nb),       text="  💊  Prestaciones  ")
        nb.add(ReporteOdontologoTab(nb),         text="  👨‍⚕️  Por Odontólogo  ")
        nb.add(ReportePacientesOSTab(nb),        text="  👥  Pacientes / O.S.  ")
        nb.add(ReportePendientesFedTab(nb),      text="  📤  Pendientes Fed.  ")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — Reporte de Turnos
# ─────────────────────────────────────────────────────────────────────────────

class ReporteTurnosTab(tk.Frame):
    COLS = ["Fecha", "Hora", "Duración (min)", "Paciente",
            "Odontólogo", "Motivo", "Estado", "Notas"]
    COL_KEYS = ["fecha", "hora", "duracion_min", "paciente",
                "odontologo", "motivo", "estado", "notas"]

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._data: List[Dict] = []
        self._build()

    def _build(self):
        # Filtros
        filtros = tk.Frame(self, bg=COLORS["bg"], pady=10)
        filtros.pack(fill="x", padx=12)

        self._desde = _fecha_entry(filtros, "Desde:", _primer_dia_mes())
        self._hasta = _fecha_entry(filtros, "Hasta:", _hoy())

        tk.Label(filtros, text="Odontólogo:", bg=COLORS["bg"],
                 font=FONTS["body"]).pack(side="left", padx=(8, 2))
        self._od_var = tk.StringVar(value="Todos")
        self._od_combo = ttk.Combobox(filtros, textvariable=self._od_var,
                                      state="readonly", width=22, font=FONTS["body"])
        self._od_combo.pack(side="left", padx=(0, 8))

        tk.Label(filtros, text="Estado:", bg=COLORS["bg"],
                 font=FONTS["body"]).pack(side="left", padx=(8, 2))
        self._est_var = tk.StringVar(value="Todos")
        estados = ["Todos", "Pendiente", "Confirmado", "Presente",
                   "Ausente", "Cancelado", "Reprogramado"]
        ttk.Combobox(filtros, textvariable=self._est_var, values=estados,
                     state="readonly", width=14, font=FONTS["body"]).pack(side="left", padx=(0, 12))

        tk.Button(filtros, text="Generar", bg=COLORS["accent"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._generar).pack(side="left", padx=4)
        tk.Button(filtros, text="Exportar CSV", bg=COLORS["success"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._exportar).pack(side="left", padx=4)

        # Totalizador
        self._lbl_total = tk.Label(self, text="", font=FONTS["subtitle"],
                                   bg=COLORS["bg"], fg=COLORS["text"])
        self._lbl_total.pack(anchor="w", padx=16, pady=(0, 4))

        widths = {"Fecha": 90, "Hora": 60, "Duración (min)": 100,
                  "Paciente": 180, "Odontólogo": 180, "Motivo": 200,
                  "Estado": 100, "Notas": 200}
        self._tree = _build_tree(self, self.COLS, widths)
        self._load_combos()

    def _load_combos(self):
        ods = [{"id": None, "label": "Todos"}] + [
            {"id": r["id"], "label": r["apellido"] + ", " + r["nombre"]}
            for r in models.get_odontologos()
        ]
        self._od_map = {r["label"]: r["id"] for r in ods}
        self._od_combo["values"] = list(self._od_map.keys())
        self._od_combo.set("Todos")

    def _generar(self):
        od_id = self._od_map.get(self._od_var.get())
        estado = None if self._est_var.get() == "Todos" else self._est_var.get()
        try:
            rows = models.reporte_turnos(
                self._desde.get(), self._hasta.get(), od_id, estado)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        # Normalizar claves para el tree
        self._data = [{col: r.get(key, "") for col, key in zip(self.COLS, self.COL_KEYS)}
                      for r in rows]
        _fill_tree(self._tree, self.COLS, self._data)
        self._lbl_total.configure(
            text=f"Total turnos: {len(rows)}"
            + (f"  |  Presentes: {sum(1 for r in rows if r['estado']=='Presente')}" if rows else ""))

    def _exportar(self):
        if not self._data:
            messagebox.showwarning("Sin datos", "Genere el reporte primero.")
            return
        _exportar_csv(self.COLS, self._data, f"turnos_{self._desde.get()}_{self._hasta.get()}.csv")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — Reporte de Prestaciones
# ─────────────────────────────────────────────────────────────────────────────

class ReportePrestacionesTab(tk.Frame):
    COLS = ["Fecha", "Paciente", "Odontólogo", "Código",
            "Prestación", "Categoría", "Diente", "Monto", "Obra Social", "Env. Fed."]
    COL_KEYS = ["fecha", "paciente", "odontologo", "cod_nomenclador",
                "prestacion", "categoria", "numero_fdi", "monto",
                "obra_social", "enviado_fed"]

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._data: List[Dict] = []
        self._build()

    def _build(self):
        filtros = tk.Frame(self, bg=COLORS["bg"], pady=10)
        filtros.pack(fill="x", padx=12)

        self._desde = _fecha_entry(filtros, "Desde:", _primer_dia_mes())
        self._hasta = _fecha_entry(filtros, "Hasta:", _hoy())

        tk.Label(filtros, text="Odontólogo:", bg=COLORS["bg"],
                 font=FONTS["body"]).pack(side="left", padx=(8, 2))
        self._od_var = tk.StringVar(value="Todos")
        self._od_combo = ttk.Combobox(filtros, textvariable=self._od_var,
                                      state="readonly", width=22, font=FONTS["body"])
        self._od_combo.pack(side="left", padx=(0, 8))

        tk.Label(filtros, text="Obra Social:", bg=COLORS["bg"],
                 font=FONTS["body"]).pack(side="left", padx=(8, 2))
        self._os_var = tk.StringVar(value="Todas")
        self._os_combo = ttk.Combobox(filtros, textvariable=self._os_var,
                                      state="readonly", width=16, font=FONTS["body"])
        self._os_combo.pack(side="left", padx=(0, 12))

        tk.Button(filtros, text="Generar", bg=COLORS["accent"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._generar).pack(side="left", padx=4)
        tk.Button(filtros, text="Exportar CSV", bg=COLORS["success"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._exportar).pack(side="left", padx=4)

        self._lbl_total = tk.Label(self, text="", font=FONTS["subtitle"],
                                   bg=COLORS["bg"], fg=COLORS["text"])
        self._lbl_total.pack(anchor="w", padx=16, pady=(0, 4))

        widths = {"Fecha": 90, "Paciente": 170, "Odontólogo": 170,
                  "Código": 70, "Prestación": 220, "Categoría": 120,
                  "Diente": 60, "Monto": 90, "Obra Social": 130, "Env. Fed.": 80}
        self._tree = _build_tree(self, self.COLS, widths)
        self._load_combos()

    def _load_combos(self):
        ods = [{"id": None, "label": "Todos"}] + [
            {"id": r["id"], "label": r["apellido"] + ", " + r["nombre"]}
            for r in models.get_odontologos()
        ]
        self._od_map = {r["label"]: r["id"] for r in ods}
        self._od_combo["values"] = list(self._od_map.keys())
        self._od_combo.set("Todos")

        oss = [{"id": None, "label": "Todas"}] + [
            {"id": r["id"], "label": r["nombre"]}
            for r in models.get_obras_sociales()
        ]
        self._os_map = {r["label"]: r["id"] for r in oss}
        self._os_combo["values"] = list(self._os_map.keys())
        self._os_combo.set("Todas")

    def _generar(self):
        od_id = self._od_map.get(self._od_var.get())
        os_id = self._os_map.get(self._os_var.get())
        try:
            rows = models.reporte_prestaciones(
                self._desde.get(), self._hasta.get(), od_id, os_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._data = [{col: r.get(key, "") for col, key in zip(self.COLS, self.COL_KEYS)}
                      for r in rows]
        _fill_tree(self._tree, self.COLS, self._data)
        total = sum(float(r.get("monto", 0) or 0) for r in rows)
        self._lbl_total.configure(
            text=f"Total prestaciones: {len(rows)}   |   Facturación total: ${total:,.2f}")

    def _exportar(self):
        if not self._data:
            messagebox.showwarning("Sin datos", "Genere el reporte primero.")
            return
        _exportar_csv(self.COLS, self._data,
                      f"prestaciones_{self._desde.get()}_{self._hasta.get()}.csv")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 — Reporte por Odontólogo
# ─────────────────────────────────────────────────────────────────────────────

class ReporteOdontologoTab(tk.Frame):
    COLS = ["Odontólogo", "Especialidad", "Prestaciones", "Pacientes Únicos", "Total Facturado"]
    COL_KEYS = ["odontologo", "especialidad", "cant_prestaciones",
                "cant_pacientes", "total_facturado"]

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._data: List[Dict] = []
        self._build()

    def _build(self):
        filtros = tk.Frame(self, bg=COLORS["bg"], pady=10)
        filtros.pack(fill="x", padx=12)

        self._desde = _fecha_entry(filtros, "Desde:", _primer_dia_mes())
        self._hasta = _fecha_entry(filtros, "Hasta:", _hoy())

        tk.Button(filtros, text="Generar", bg=COLORS["accent"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._generar).pack(side="left", padx=4)
        tk.Button(filtros, text="Exportar CSV", bg=COLORS["success"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._exportar).pack(side="left", padx=4)

        self._lbl_total = tk.Label(self, text="", font=FONTS["subtitle"],
                                   bg=COLORS["bg"], fg=COLORS["text"])
        self._lbl_total.pack(anchor="w", padx=16, pady=(0, 4))

        widths = {"Odontólogo": 200, "Especialidad": 200,
                  "Prestaciones": 120, "Pacientes Únicos": 130, "Total Facturado": 140}
        self._tree = _build_tree(self, self.COLS, widths)

    def _generar(self):
        try:
            rows = models.reporte_por_odontologo(self._desde.get(), self._hasta.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        # Formatear monto
        for r in rows:
            r["total_facturado"] = f"${float(r.get('total_facturado', 0)):,.2f}"
        self._data = [{col: r.get(key, "") for col, key in zip(self.COLS, self.COL_KEYS)}
                      for r in rows]
        _fill_tree(self._tree, self.COLS, self._data)
        self._lbl_total.configure(text=f"Odontólogos con actividad: {len(rows)}")

    def _exportar(self):
        if not self._data:
            messagebox.showwarning("Sin datos", "Genere el reporte primero.")
            return
        _exportar_csv(self.COLS, self._data,
                      f"por_odontologo_{self._desde.get()}_{self._hasta.get()}.csv")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 4 — Pacientes por Obra Social
# ─────────────────────────────────────────────────────────────────────────────

class ReportePacientesOSTab(tk.Frame):
    COLS = ["Obra Social", "Total Pacientes", "Masculino", "Femenino"]
    COL_KEYS = ["obra_social", "cant_pacientes", "masculino", "femenino"]

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._data: List[Dict] = []
        self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=COLORS["bg"], pady=10)
        toolbar.pack(fill="x", padx=12)

        tk.Label(toolbar, text="Distribución de pacientes activos por cobertura.",
                 bg=COLORS["bg"], font=FONTS["body"], fg=COLORS["text_light"]).pack(side="left", padx=8)
        tk.Button(toolbar, text="Actualizar", bg=COLORS["accent"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._generar).pack(side="left", padx=4)
        tk.Button(toolbar, text="Exportar CSV", bg=COLORS["success"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._exportar).pack(side="left", padx=4)

        self._lbl_total = tk.Label(self, text="", font=FONTS["subtitle"],
                                   bg=COLORS["bg"], fg=COLORS["text"])
        self._lbl_total.pack(anchor="w", padx=16, pady=(0, 4))

        widths = {"Obra Social": 220, "Total Pacientes": 130,
                  "Masculino": 110, "Femenino": 110}
        self._tree = _build_tree(self, self.COLS, widths)
        self._generar()

    def _generar(self):
        try:
            rows = models.reporte_pacientes_por_obra_social()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._data = [{col: r.get(key, "") for col, key in zip(self.COLS, self.COL_KEYS)}
                      for r in rows]
        _fill_tree(self._tree, self.COLS, self._data)
        total = sum(int(r.get("cant_pacientes", 0)) for r in rows)
        self._lbl_total.configure(text=f"Total pacientes activos: {total}")

    def _exportar(self):
        if not self._data:
            messagebox.showwarning("Sin datos", "No hay datos para exportar.")
            return
        _exportar_csv(self.COLS, self._data, "pacientes_por_obra_social.csv")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 5 — Pendientes Federación
# ─────────────────────────────────────────────────────────────────────────────

class ReportePendientesFedTab(tk.Frame):
    COLS = ["ID", "Fecha", "Paciente", "DNI", "N° Afiliado",
            "Obra Social", "Odontólogo", "Código", "Prestación", "Diente", "Monto"]
    COL_KEYS = ["id", "fecha", "paciente", "dni", "num_afiliado",
                "obra_social", "odontologo", "cod_nomenclador",
                "prestacion", "numero_fdi", "monto"]

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._data: List[Dict] = []
        self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=COLORS["bg"], pady=10)
        toolbar.pack(fill="x", padx=12)

        tk.Label(toolbar, text="Prestaciones pendientes de envío a la Federación.",
                 bg=COLORS["bg"], font=FONTS["body"], fg=COLORS["text_light"]).pack(side="left", padx=8)
        tk.Button(toolbar, text="Actualizar", bg=COLORS["accent"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._generar).pack(side="left", padx=4)
        tk.Button(toolbar, text="Exportar CSV", bg=COLORS["success"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._exportar).pack(side="left", padx=4)
        tk.Button(toolbar, text="Marcar seleccionadas como enviadas",
                  bg=COLORS["warning"], fg=COLORS["white"],
                  font=FONTS["body"], relief="flat", padx=10, cursor="hand2",
                  command=self._marcar_enviadas).pack(side="left", padx=4)

        self._lbl_total = tk.Label(self, text="", font=FONTS["subtitle"],
                                   bg=COLORS["bg"], fg=COLORS["danger"])
        self._lbl_total.pack(anchor="w", padx=16, pady=(0, 4))

        widths = {"ID": 45, "Fecha": 90, "Paciente": 160, "DNI": 90,
                  "N° Afiliado": 100, "Obra Social": 120, "Odontólogo": 160,
                  "Código": 65, "Prestación": 200, "Diente": 55, "Monto": 90}
        self._tree = _build_tree(self, self.COLS, widths)
        self._tree.configure(selectmode="extended")
        self._generar()

    def _generar(self):
        try:
            rows = models.reporte_pendientes_federacion()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._raw = rows
        self._data = [{col: r.get(key, "") for col, key in zip(self.COLS, self.COL_KEYS)}
                      for r in rows]
        _fill_tree(self._tree, self.COLS, self._data)
        total = sum(float(r.get("monto", 0) or 0) for r in rows)
        self._lbl_total.configure(
            text=f"Pendientes: {len(rows)}   |   Total: ${total:,.2f}")

    def _marcar_enviadas(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Sin selección",
                                   "Seleccione una o más filas para marcar como enviadas.")
            return
        ids = []
        for item in sel:
            idx = self._tree.index(item)
            if idx < len(self._raw):
                ids.append(self._raw[idx]["id"])
        if not ids:
            return
        if not messagebox.askyesno("Confirmar",
                                   f"¿Marcar {len(ids)} prestación(es) como enviadas a Federación?"):
            return
        models.marcar_enviado_federacion(ids)
        self._generar()

    def _exportar(self):
        if not self._data:
            messagebox.showwarning("Sin datos", "No hay datos para exportar.")
            return
        _exportar_csv(self.COLS, self._data, "pendientes_federacion.csv")
