"""
historial_ui.py — Historial clínico electrónico por paciente.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import datetime
import models
from ui.theme import COLORS, FONTS
from ui.app import app_state
from ui.widgets import DateEntry


class HistorialFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._selected_historial_id: Optional[int] = None
        self._build()
        app_state.register("patient_changed", lambda **kw: self._on_patient_change(**kw))

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  Historial Clínico",
                 font=FONTS["title"], bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")
        self._lbl_paciente = tk.Label(hdr, text="Sin paciente seleccionado",
                                       font=FONTS["body"], bg=COLORS["header_bg"], fg="#BEE3F8")
        self._lbl_paciente.pack(padx=20, anchor="w")

        # Selector de paciente
        sel_row = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=8)
        sel_row.pack(fill="x")
        tk.Label(sel_row, text="Paciente:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left")
        self._pac_var = tk.StringVar()
        self._pac_combo = ttk.Combobox(sel_row, textvariable=self._pac_var, width=36)
        self._pac_combo.pack(side="left", padx=8)
        ttk.Button(sel_row, text="Cargar", command=self._cargar_por_combo).pack(side="left", padx=4)
        ttk.Button(sel_row, text="➕ Nueva Entrada", style="Accent.TButton",
                   command=self._new).pack(side="right", padx=8)

        # Paned: izquierda=lista, derecha=detalle
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=16, pady=8)

        # Lista de entradas
        left = tk.Frame(paned, bg=COLORS["bg"])
        paned.add(left, weight=1)

        cols = ("Fecha", "Odontólogo", "Diagnóstico")
        self._tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self._tree.heading(c, text=c)
        self._tree.column("Fecha", width=110)
        self._tree.column("Odontólogo", width=160)
        self._tree.column("Diagnóstico", width=220)
        scroll = ttk.Scrollbar(left, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.tag_configure("odd", background=COLORS["row_odd"])

        btn_left = tk.Frame(left, bg=COLORS["bg"])
        btn_left.pack(fill="x", pady=4)
        ttk.Button(btn_left, text="✏️ Editar",
                   command=self._edit).pack(side="left", padx=4)
        ttk.Button(btn_left, text="🗑️ Eliminar", style="Danger.TButton",
                   command=self._delete).pack(side="left", padx=4)

        # Panel de detalle
        right = tk.Frame(paned, bg=COLORS["bg"])
        paned.add(right, weight=2)

        tk.Label(right, text="Detalle de la entrada", font=FONTS["subtitle"],
                 bg=COLORS["bg"]).pack(anchor="w", pady=4)

        self._detail = tk.Frame(right, bg=COLORS["bg"])
        self._detail.pack(fill="both", expand=True)
        self._build_detail_empty()

        self._refresh_pacientes()

    def _build_detail_empty(self):
        for w in self._detail.winfo_children():
            w.destroy()
        tk.Label(self._detail, text="Seleccione una entrada para ver el detalle.",
                 font=FONTS["body"], bg=COLORS["bg"],
                 fg=COLORS["text_light"]).pack(pady=40)

    def _build_detail(self, entry: dict):
        for w in self._detail.winfo_children():
            w.destroy()
        f = self._detail
        f.columnconfigure(1, weight=1)

        def lbl(label, value, row):
            tk.Label(f, text=label, font=FONTS["subtitle"],
                     bg=COLORS["bg"], fg=COLORS["accent"]).grid(row=row, column=0, sticky="ne", padx=8, pady=4)
            t = tk.Text(f, height=3, font=FONTS["body"], wrap="word",
                        state="normal", bg=COLORS["white"])
            t.insert("1.0", str(value or ""))
            t.configure(state="disabled")
            t.grid(row=row, column=1, sticky="ew", padx=8, pady=4)

        tk.Label(f, text=f"📅 Fecha: {entry['fecha']}  |  👨‍⚕️ {entry.get('odontologo_nombre','')}",
                 font=FONTS["subtitle"], bg=COLORS["bg"]).grid(row=0, column=0, columnspan=2,
                                                                sticky="w", padx=8, pady=8)
        lbl("Diagnóstico:",      entry.get("diagnostico",""), 1)
        lbl("Tratamiento:",      entry.get("tratamiento",""), 2)
        lbl("Notas:",            entry.get("notas",""), 3)
        lbl("Informes externos:", entry.get("informes_ext",""), 4)

        rad = entry.get("radiografias", 0)
        tk.Label(f, text=f"📷 Radiografías adjuntas: {rad}",
                 font=FONTS["body"], bg=COLORS["bg"]).grid(row=5, column=0, columnspan=2,
                                                            sticky="w", padx=8, pady=4)

    def _refresh_pacientes(self):
        self._pacientes = models.get_pacientes()
        names = [f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})" for p in self._pacientes]
        self._pac_combo["values"] = names

    def _on_patient_change(self, paciente_id=None, **kw):
        if paciente_id:
            for p in self._pacientes:
                if p["id"] == paciente_id:
                    self._pac_var.set(f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})")
                    self._load(paciente_id)
                    break

    def _cargar_por_combo(self):
        val = self._pac_var.get()
        for p in self._pacientes:
            if val.startswith(f"{p['apellido']}, {p['nombre']}"):
                app_state.set_paciente(p["id"])
                self._load(p["id"])
                return

    def _load(self, paciente_id: int):
        pac = models.get_paciente(paciente_id)
        if pac:
            self._lbl_paciente.configure(
                text=f"Paciente: {pac['apellido']}, {pac['nombre']} — DNI: {pac.get('dni','')}"
            )
        self._entradas = models.get_historial(paciente_id)
        self._tree.delete(*self._tree.get_children())
        for i, e in enumerate(self._entradas):
            tag = "odd" if i % 2 else ""
            diag = (e.get("diagnostico") or "")[:50]
            self._tree.insert("", "end", iid=str(e["id"]), tags=(tag,), values=(
                e["fecha"], e.get("odontologo_nombre",""), diag,
            ))
        self._build_detail_empty()

    def _on_select(self, _):
        sel = self._tree.selection()
        if sel:
            self._selected_historial_id = int(sel[0])
            entry = models.get_historial_entry(self._selected_historial_id)
            if entry:
                od = models.get_odontologo(entry["odontologo_id"]) if entry.get("odontologo_id") else {}
                entry["odontologo_nombre"] = f"{od.get('apellido','')} {od.get('nombre','')}" if od else ""
                self._build_detail(entry)
        else:
            self._selected_historial_id = None

    def _new(self):
        pid = app_state.paciente_id
        if not pid:
            messagebox.showinfo("Paciente", "Seleccione un paciente primero.")
            return
        dlg = HistorialDialog(self, None, paciente_id=pid)
        self.wait_window(dlg)
        self._load(pid)

    def _edit(self):
        if not self._selected_historial_id:
            messagebox.showinfo("Selección", "Seleccione una entrada.")
            return
        pid = app_state.paciente_id
        dlg = HistorialDialog(self, self._selected_historial_id, paciente_id=pid)
        self.wait_window(dlg)
        if pid:
            self._load(pid)

    def _delete(self):
        if not self._selected_historial_id:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar esta entrada del historial?"):
            models.delete_historial(self._selected_historial_id)
            pid = app_state.paciente_id
            if pid:
                self._load(pid)
            self._build_detail_empty()

    def on_show(self):
        self._refresh_pacientes()
        pid = app_state.paciente_id
        if pid:
            self._load(pid)


class HistorialDialog(tk.Toplevel):
    def __init__(self, parent, historial_id: Optional[int], paciente_id: int):
        super().__init__(parent)
        self._id = historial_id
        self._pac_id = paciente_id
        self.title("Nueva Entrada Historial" if not historial_id else "Editar Entrada")
        self.geometry("640x560")
        self.grab_set()
        self.configure(bg=COLORS["bg"])
        self._data = models.get_historial_entry(historial_id) if historial_id else {}
        self._odontologos = models.get_odontologos()
        self._build()
        self._load()

    def _build(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=20, pady=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Odontólogo
        tk.Label(frame, text="Odontólogo *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self._od_var = tk.StringVar()
        od_names = [f"{o['apellido']}, {o['nombre']}" for o in self._odontologos]
        ttk.Combobox(frame, textvariable=self._od_var, values=od_names,
                     width=32, state="readonly").grid(row=0, column=1, sticky="w", padx=6)

        # Fecha — selector con calendario
        tk.Label(frame, text="Fecha *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self._fecha = DateEntry(frame)
        self._fecha.set(datetime.date.today().isoformat())
        self._fecha.grid(row=1, column=1, sticky="w", padx=6)

        # Radiografías
        tk.Label(frame, text="Radiografías (cantidad)", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self._rad_var = tk.StringVar(value="0")
        ttk.Spinbox(frame, textvariable=self._rad_var, from_=0, to=20,
                    width=6).grid(row=2, column=1, sticky="w", padx=6)

        def text_row(row, label, attr):
            tk.Label(frame, text=label, font=FONTS["body"],
                     bg=COLORS["bg"]).grid(row=row, column=0, sticky="ne", padx=6, pady=6)
            t = tk.Text(frame, height=4, width=55, font=FONTS["body"], wrap="word")
            t.grid(row=row, column=1, sticky="ew", padx=6, pady=6)
            setattr(self, f"_{attr}_text", t)

        text_row(3, "Diagnóstico *",    "diagnostico")
        text_row(4, "Tratamiento",      "tratamiento")
        text_row(5, "Notas",            "notas")
        text_row(6, "Informes externos","informes_ext")

        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=20, pady=8)
        ttk.Button(btn_bar, text="💾 Guardar", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _load(self):
        d = self._data
        if d.get("odontologo_id"):
            for o in self._odontologos:
                if o["id"] == d["odontologo_id"]:
                    self._od_var.set(f"{o['apellido']}, {o['nombre']}")
                    break
        if d.get("fecha"):
            self._fecha.set(d["fecha"])
        self._rad_var.set(str(d.get("radiografias", 0)))
        for attr in ("diagnostico", "tratamiento", "notas", "informes_ext"):
            t = getattr(self, f"_{attr}_text")
            t.insert("1.0", d.get(attr, "") or "")

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
        diag = self._diagnostico_text.get("1.0", "end-1c").strip()
        if not diag:
            messagebox.showerror("Validación", "El diagnóstico es obligatorio.")
            return
        data = {
            "paciente_id":   self._pac_id,
            "odontologo_id": od_id,
            "fecha":         self._fecha.get(),
            "diagnostico":   diag,
            "tratamiento":   self._tratamiento_text.get("1.0", "end-1c").strip(),
            "notas":         self._notas_text.get("1.0", "end-1c").strip(),
            "radiografias":  int(self._rad_var.get() or 0),
            "informes_ext":  self._informes_ext_text.get("1.0", "end-1c").strip(),
        }
        if self._id:
            data["id"] = self._id
        models.save_historial(data)
        self.destroy()
