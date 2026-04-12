"""
periodontograma_ui.py — Ficha periodontal con grilla de mediciones por diente.

Mediciones por diente: 6 sitios en 2 filas:
  Fila vestibular:  MB (mesio-bucal), B (bucal/vestibular), DB (disto-bucal)
  Fila lingual/palatino: ML, L, DL
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List
import datetime
import models
from ui.theme import COLORS, FONTS
from ui.app import app_state
from ui.widgets import DateEntry

# Dientes permanentes en orden de visualización
UPPER_TEETH = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
LOWER_TEETH = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]
SITES = ["MB", "B", "DB", "ML", "L", "DL"]
CELL_W = 30
CELL_H = 22


def color_for_depth(val: str) -> str:
    try:
        n = int(val)
        if n <= 3:  return COLORS["perio_ok"]
        if n <= 5:  return COLORS["perio_warn"]
        return COLORS["perio_alert"]
    except (ValueError, TypeError):
        return COLORS["white"]


class PeriodontogramaFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._pac_id: Optional[int] = None
        self._ficha_id: Optional[int] = None
        self._cells: Dict = {}       # {(row_key, fdi, site_idx): Entry}
        self._mediciones: Dict = {}  # {fdi: {prof_bolsa:..., margen_gingival:...}}
        self._build()
        app_state.register("patient_changed", lambda **kw: self._on_patient_change(**kw))

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔬  Ficha Periodontal",
                 font=FONTS["title"], bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")
        self._lbl_pac = tk.Label(hdr, text="Sin paciente seleccionado",
                                  font=FONTS["body"], bg=COLORS["header_bg"], fg="#BEE3F8")
        self._lbl_pac.pack(padx=20, anchor="w")

        # Controles superiores
        ctrl = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=8)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Paciente:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left")
        self._pac_var = tk.StringVar()
        self._pac_combo = ttk.Combobox(ctrl, textvariable=self._pac_var, width=34)
        self._pac_combo.pack(side="left", padx=6)
        ttk.Button(ctrl, text="Cargar", command=self._cargar_combo).pack(side="left")

        ttk.Button(ctrl, text="➕ Nueva Ficha", style="Accent.TButton",
                   command=self._nueva_ficha).pack(side="right", padx=4)
        ttk.Button(ctrl, text="💾 Guardar mediciones", style="Success.TButton",
                   command=self._guardar_mediciones).pack(side="right", padx=4)

        # Notebook: Fichas | Grilla
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=16, pady=8)

        self._tab_fichas = tk.Frame(self._nb, bg=COLORS["bg"])
        self._tab_grilla = tk.Frame(self._nb, bg=COLORS["bg"])
        self._nb.add(self._tab_fichas, text="  Historial de Fichas  ")
        self._nb.add(self._tab_grilla, text="  Grilla de Mediciones  ")

        self._build_tab_fichas()
        self._build_tab_grilla()
        self._refresh_pacientes()

    def _build_tab_fichas(self):
        f = self._tab_fichas
        cols = ("ID", "Fecha", "Odontólogo", "Estado Encías", "Índ. Placa", "Índ. Sangrado")
        self._fichas_tree = ttk.Treeview(f, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self._fichas_tree.heading(c, text=c)
        self._fichas_tree.column("ID", width=40)
        self._fichas_tree.column("Fecha", width=100)
        self._fichas_tree.column("Odontólogo", width=180)
        self._fichas_tree.column("Estado Encías", width=160)
        self._fichas_tree.column("Índ. Placa", width=90)
        self._fichas_tree.column("Índ. Sangrado", width=100)
        scroll = ttk.Scrollbar(f, orient="vertical", command=self._fichas_tree.yview)
        self._fichas_tree.configure(yscrollcommand=scroll.set)
        self._fichas_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self._fichas_tree.tag_configure("odd", background=COLORS["row_odd"])
        self._fichas_tree.bind("<<TreeviewSelect>>", self._on_ficha_select)

    def _build_tab_grilla(self):
        f = self._tab_grilla

        # Indicadores resumen
        sum_frame = tk.Frame(f, bg=COLORS["bg"], pady=4, padx=8)
        sum_frame.pack(fill="x")
        self._lbl_ficha_info = tk.Label(sum_frame, text="Sin ficha cargada",
                                         font=FONTS["body"], bg=COLORS["bg"])
        self._lbl_ficha_info.pack(side="left")

        # Canvas scrollable para la grilla
        canvas_container = tk.Frame(f, bg=COLORS["bg"])
        canvas_container.pack(fill="both", expand=True)

        self._grid_canvas = tk.Canvas(canvas_container, bg=COLORS["white"])
        hscroll = ttk.Scrollbar(canvas_container, orient="horizontal",
                                 command=self._grid_canvas.xview)
        vscroll = ttk.Scrollbar(canvas_container, orient="vertical",
                                 command=self._grid_canvas.yview)
        self._grid_canvas.configure(xscrollcommand=hscroll.set,
                                     yscrollcommand=vscroll.set)
        hscroll.pack(side="bottom", fill="x")
        vscroll.pack(side="right", fill="y")
        self._grid_canvas.pack(fill="both", expand=True)

        # Frame interno donde se colocan los Entry widgets
        self._grid_inner = tk.Frame(self._grid_canvas, bg=COLORS["white"])
        self._grid_canvas.create_window((0, 0), window=self._grid_inner, anchor="nw")
        self._grid_inner.bind("<Configure>",
                               lambda e: self._grid_canvas.configure(
                                   scrollregion=self._grid_canvas.bbox("all")))

        # Leyenda de colores
        leg = tk.Frame(f, bg=COLORS["bg"], pady=4, padx=8)
        leg.pack(fill="x")
        for text, color in [("≤3mm: sano", COLORS["perio_ok"]),
                             ("4-5mm: leve", COLORS["perio_warn"]),
                             ("≥6mm: grave", COLORS["perio_alert"])]:
            fr = tk.Frame(leg, bg=color, width=18, height=18, relief="solid", bd=1)
            fr.pack(side="left", padx=2)
            tk.Label(leg, text=text, font=FONTS["small"],
                     bg=COLORS["bg"]).pack(side="left", padx=(0, 10))

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
                    self._load_patient(paciente_id)
                    break

    def _cargar_combo(self):
        val = self._pac_var.get()
        for p in self._pacientes:
            if val.startswith(f"{p['apellido']}, {p['nombre']}"):
                app_state.set_paciente(p["id"])
                self._load_patient(p["id"])
                return

    def _load_patient(self, pac_id: int):
        self._pac_id = pac_id
        pac = models.get_paciente(pac_id)
        if pac:
            self._lbl_pac.configure(
                text=f"Paciente: {pac['apellido']}, {pac['nombre']} — DNI: {pac.get('dni','')}"
            )
        self._load_fichas()

    def _load_fichas(self):
        if not self._pac_id:
            return
        fichas = models.get_fichas_periodontales(self._pac_id)
        self._fichas_tree.delete(*self._fichas_tree.get_children())
        for i, f in enumerate(fichas):
            tag = "odd" if i % 2 else ""
            self._fichas_tree.insert("", "end", iid=str(f["id"]), tags=(tag,), values=(
                f["id"], f["fecha"], f.get("odontologo_nombre",""),
                f.get("estado_encias",""),
                f"{f.get('indice_placa',0):.1f}%" if f.get("indice_placa") is not None else "",
                f"{f.get('indice_sangrado',0):.1f}%" if f.get("indice_sangrado") is not None else "",
            ))

    def _on_ficha_select(self, _):
        sel = self._fichas_tree.selection()
        if sel:
            ficha_id = int(sel[0])
            self._ficha_id = ficha_id
            ficha = models.get_ficha_periodontal(ficha_id)
            if ficha:
                self._mediciones = ficha.get("mediciones", {})
                self._lbl_ficha_info.configure(
                    text=f"Ficha #{ficha_id} — {ficha['fecha']}  |  "
                         f"Estado encías: {ficha.get('estado_encias','')}  |  "
                         f"Índice placa: {ficha.get('indice_placa','')}"
                )
                self._render_grilla()
                self._nb.select(1)  # cambiar a pestaña grilla

    def _render_grilla(self):
        """Dibuja la grilla de mediciones en el canvas."""
        f = self._grid_inner
        for w in f.winfo_children():
            w.destroy()
        self._cells.clear()

        row_labels = [
            "Prof. bolsa\n(vestibular)",
            "Prof. bolsa\n(lingual)",
            "Margen gingival\n(vestibular)",
            "Margen gingival\n(lingual)",
            "Sangrado\n(vestib.)",
            "Sangrado\n(lingual)",
            "Placa\n(vestib.)",
            "Placa\n(lingual)",
        ]
        row_keys   = [
            ("prof_bolsa",      0, 1, 2),    # sitios MB,B,DB
            ("prof_bolsa",      3, 4, 5),    # sitios ML,L,DL
            ("margen_gingival", 0, 1, 2),
            ("margen_gingival", 3, 4, 5),
            ("sangrado",        0, 1, 2),
            ("sangrado",        3, 4, 5),
            ("placa",           0, 1, 2),
            ("placa",           3, 4, 5),
        ]

        # Encabezados dientes
        tk.Label(f, text="", bg=COLORS["white"], width=18
                 ).grid(row=0, column=0, sticky="w")
        all_teeth = UPPER_TEETH + LOWER_TEETH
        for col, fdi in enumerate(all_teeth):
            tk.Label(f, text=str(fdi), font=FONTS["small"], bg=COLORS["white"],
                     fg=COLORS["text"], width=4, anchor="center"
                     ).grid(row=0, column=col+1, padx=1)

        # Separador entre arcadas
        sep_col = len(UPPER_TEETH) + 1
        for row_i in range(len(row_labels) + 2):
            tk.Label(f, text="│", bg=COLORS["border"], width=1
                     ).grid(row=row_i, column=sep_col, sticky="ns")

        # Filas de medición
        for row_i, (rlabel, (field, s0, s1, s2)) in enumerate(zip(row_labels, row_keys)):
            tk.Label(f, text=rlabel, font=FONTS["small"], bg=COLORS["white"],
                     fg=COLORS["text"], anchor="e", justify="right", width=18
                     ).grid(row=row_i+1, column=0, sticky="e", padx=4, pady=1)

            is_depth = field == "prof_bolsa"
            for col, fdi in enumerate(all_teeth):
                med = self._mediciones.get(fdi, {})
                vals_str = med.get(field, "0,0,0,0,0,0")
                vals = vals_str.split(",")
                site_map = {0: s0, 1: s1, 2: s2}

                for site_rel, site_abs in site_map.items():
                    val = vals[site_abs] if site_abs < len(vals) else "0"
                    bg = color_for_depth(val) if is_depth else COLORS["white"]
                    var = tk.StringVar(value=val)
                    ent = tk.Entry(f, textvariable=var, width=2, font=FONTS["small"],
                                   bg=bg, relief="solid", bd=1, justify="center")
                    ent.grid(row=row_i+1, column=col+1, padx=0, pady=0, ipady=2)
                    if is_depth:
                        ent.bind("<FocusOut>", lambda e, v=var, en=ent: self._update_cell_color(v, en))
                        ent.bind("<Return>",   lambda e, v=var, en=ent: self._update_cell_color(v, en))
                    self._cells[(field, fdi, site_abs)] = (var, site_rel)

    def _update_cell_color(self, var: tk.StringVar, entry: tk.Entry):
        entry.configure(bg=color_for_depth(var.get()))

    def _guardar_mediciones(self):
        if not self._pac_id or not self._ficha_id:
            messagebox.showinfo("Info", "Seleccione una ficha primero.")
            return

        # Agrupar valores por diente y campo
        new_med: Dict[int, Dict[str, List[str]]] = {}
        for (field, fdi, site_abs), (var, _) in self._cells.items():
            if fdi not in new_med:
                new_med[fdi] = {
                    "prof_bolsa":      ["0","0","0","0","0","0"],
                    "margen_gingival": ["0","0","0","0","0","0"],
                    "sangrado":        ["0","0","0","0","0","0"],
                    "placa":           ["0","0","0","0","0","0"],
                }
            lst = new_med[fdi][field]
            lst[site_abs] = var.get().strip() or "0"

        ficha_data = {
            "id": self._ficha_id,
            "paciente_id": self._pac_id,
            "mediciones": {fdi: {k: ",".join(v) for k, v in fields.items()}
                           for fdi, fields in new_med.items()}
        }
        # Necesitamos también odontologo_id y fecha — los obtenemos de la ficha cargada
        ficha_actual = models.get_ficha_periodontal(self._ficha_id)
        if ficha_actual:
            ficha_data["odontologo_id"] = ficha_actual["odontologo_id"]
            ficha_data["fecha"] = ficha_actual["fecha"]
            ficha_data["estado_encias"] = ficha_actual.get("estado_encias","")
            ficha_data["indice_placa"]   = ficha_actual.get("indice_placa")
            ficha_data["indice_sangrado"]= ficha_actual.get("indice_sangrado")
            ficha_data["notas"]          = ficha_actual.get("notas","")

        models.save_ficha_periodontal(ficha_data)
        self._mediciones = {fdi: {k: ",".join(v) for k, v in fields.items()}
                            for fdi, fields in new_med.items()}
        messagebox.showinfo("Guardado", "Mediciones guardadas correctamente.")

    # ── Nueva ficha ───────────────────────────────────────────────────────────

    def _nueva_ficha(self):
        if not self._pac_id:
            messagebox.showinfo("Paciente", "Seleccione un paciente primero.")
            return
        dlg = NuevaFichaDialog(self, self._pac_id)
        self.wait_window(dlg)
        if dlg.ficha_id:
            self._ficha_id = dlg.ficha_id
            self._load_fichas()
            ficha = models.get_ficha_periodontal(dlg.ficha_id)
            if ficha:
                self._mediciones = ficha.get("mediciones", {})
                self._render_grilla()
                self._nb.select(1)

    def on_show(self):
        self._refresh_pacientes()
        pid = app_state.paciente_id
        if pid and pid != self._pac_id:
            self._load_patient(pid)


class NuevaFichaDialog(tk.Toplevel):
    def __init__(self, parent, pac_id: int):
        super().__init__(parent)
        self._pac_id = pac_id
        self.ficha_id: Optional[int] = None
        self.title("Nueva Ficha Periodontal")
        self.geometry("460x360")
        self.grab_set()
        self.configure(bg=COLORS["bg"])
        self._odontologos = models.get_odontologos()
        self._build()

    def _build(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=20, pady=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Odontólogo *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=0, column=0, sticky="e", padx=6, pady=8)
        self._od_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self._od_var,
                     values=[f"{o['apellido']}, {o['nombre']}" for o in self._odontologos],
                     width=28, state="readonly").grid(row=0, column=1, sticky="w", padx=6)

        tk.Label(frame, text="Fecha *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=1, column=0, sticky="e", padx=6, pady=8)
        self._fecha = DateEntry(frame)
        self._fecha.set(datetime.date.today().isoformat())
        self._fecha.grid(row=1, column=1, sticky="w", padx=6)

        tk.Label(frame, text="Estado de encías", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=2, column=0, sticky="e", padx=6, pady=8)
        self._encias_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=self._encias_var,
                     values=["Sano","Gingivitis leve","Gingivitis moderada",
                             "Gingivitis severa","Periodontitis leve",
                             "Periodontitis moderada","Periodontitis severa"],
                     width=28, state="readonly").grid(row=2, column=1, sticky="w", padx=6)

        tk.Label(frame, text="Índice de placa (%)", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=3, column=0, sticky="e", padx=6, pady=8)
        self._placa_var = tk.StringVar(value="0.0")
        ttk.Entry(frame, textvariable=self._placa_var, width=8
                  ).grid(row=3, column=1, sticky="w", padx=6)

        tk.Label(frame, text="Índice de sangrado (%)", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=4, column=0, sticky="e", padx=6, pady=8)
        self._sangrado_var = tk.StringVar(value="0.0")
        ttk.Entry(frame, textvariable=self._sangrado_var, width=8
                  ).grid(row=4, column=1, sticky="w", padx=6)

        tk.Label(frame, text="Notas", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=5, column=0, sticky="ne", padx=6, pady=8)
        self._notas = tk.Text(frame, height=3, width=30, font=FONTS["body"])
        self._notas.grid(row=5, column=1, sticky="ew", padx=6)

        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=20, pady=8)
        ttk.Button(btn_bar, text="✅ Crear Ficha", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _save(self):
        od_str = self._od_var.get()
        od_id = None
        for o in self._odontologos:
            if f"{o['apellido']}, {o['nombre']}" == od_str:
                od_id = o["id"]
                break
        if not od_id:
            messagebox.showerror("Validación", "Seleccione un odontólogo.")
            return
        try:
            placa   = float(self._placa_var.get() or 0)
            sangrado= float(self._sangrado_var.get() or 0)
        except ValueError:
            placa = sangrado = 0.0

        data = {
            "paciente_id":   self._pac_id,
            "odontologo_id": od_id,
            "fecha":         self._fecha.get(),
            "estado_encias": self._encias_var.get(),
            "indice_placa":  placa,
            "indice_sangrado": sangrado,
            "notas":         self._notas.get("1.0", "end-1c").strip(),
        }
        self.ficha_id = models.save_ficha_periodontal(data)
        self.destroy()
