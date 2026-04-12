"""
odontologos_ui.py — Gestión de odontólogos.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import models
from ui.theme import COLORS, FONTS


class OdontologosFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._selected_id: Optional[int] = None
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="👨‍⚕️  Odontólogos",
                 font=FONTS["title"], bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")

        body = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=12)
        body.pack(fill="both", expand=True)

        btn_row = tk.Frame(body, bg=COLORS["bg"])
        btn_row.pack(fill="x", pady=(0, 8))
        ttk.Button(btn_row, text="➕ Nuevo Odontólogo", style="Accent.TButton",
                   command=self._new).pack(side="left", padx=4)
        ttk.Button(btn_row, text="✏️ Editar", command=self._edit).pack(side="left", padx=4)
        ttk.Button(btn_row, text="🗑️ Dar de baja", style="Danger.TButton",
                   command=self._delete).pack(side="left", padx=4)

        cols = ("ID", "Apellido", "Nombre", "Especialidad", "Matrícula", "Círculo", "Teléfono", "Estado")
        widths = (40, 120, 120, 180, 100, 140, 110, 70)
        self._tree = ttk.Treeview(body, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, widths):
            self._tree.heading(c, text=c)
            self._tree.column(c, width=w)
        scroll_y = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_y.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="left", fill="y")
        self._tree.tag_configure("odd", background=COLORS["row_odd"])
        self._tree.bind("<Double-1>", lambda _: self._edit())
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._load()

    def _load(self):
        self._tree.delete(*self._tree.get_children())
        for i, o in enumerate(models.get_odontologos(solo_activos=False)):
            tag = "odd" if i % 2 else ""
            estado = "Activo" if o.get("activo", 1) else "Baja"
            self._tree.insert("", "end", iid=str(o["id"]), tags=(tag,), values=(
                o["id"], o["apellido"], o["nombre"],
                o.get("especialidad",""), o.get("matricula",""),
                o.get("circulo",""), o.get("telefono",""), estado,
            ))

    def _on_select(self, _):
        sel = self._tree.selection()
        self._selected_id = int(sel[0]) if sel else None

    def _new(self):
        dlg = OdontologoDialog(self, None)
        self.wait_window(dlg)
        self._load()

    def _edit(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un odontólogo.")
            return
        dlg = OdontologoDialog(self, self._selected_id)
        self.wait_window(dlg)
        self._load()

    def _delete(self):
        if not self._selected_id:
            return
        if messagebox.askyesno("Confirmar", "¿Dar de baja a este odontólogo?"):
            models.delete_odontologo(self._selected_id)
            self._load()

    def on_show(self):
        self._load()


class OdontologoDialog(tk.Toplevel):
    def __init__(self, parent, odontologo_id: Optional[int]):
        super().__init__(parent)
        self._id = odontologo_id
        self.title("Nuevo Odontólogo" if not odontologo_id else "Editar Odontólogo")
        self.geometry("480x400")
        self.grab_set()
        self.configure(bg=COLORS["bg"])
        self._data = models.get_odontologo(odontologo_id) if odontologo_id else {}
        self._vars = {}
        self._build()
        self._load()

    def _build(self):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=20, pady=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Nombre *",      "nombre"),
            ("Apellido *",    "apellido"),
            ("Especialidad",  "especialidad"),
            ("Matrícula *",   "matricula"),
            ("Círculo",       "circulo"),
            ("Teléfono",      "telefono"),
            ("Email",         "email"),
        ]
        for i, (label, key) in enumerate(fields):
            tk.Label(frame, text=label, font=FONTS["body"],
                     bg=COLORS["bg"]).grid(row=i, column=0, sticky="e", padx=6, pady=6)
            v = tk.StringVar()
            ttk.Entry(frame, textvariable=v, width=30).grid(row=i, column=1, sticky="ew", padx=6)
            self._vars[key] = v

        # Activo
        self._activo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Activo", variable=self._activo_var,
                        style="TCheckbutton").grid(row=len(fields), column=1, sticky="w", padx=6, pady=8)

        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=20, pady=8)
        ttk.Button(btn_bar, text="💾 Guardar", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar", command=self.destroy).pack(side="right", padx=4)

    def _load(self):
        for k, v in self._vars.items():
            v.set(self._data.get(k, "") or "")
        self._activo_var.set(bool(self._data.get("activo", 1)))

    def _save(self):
        data = {k: v.get().strip() for k, v in self._vars.items()}
        if not data.get("nombre") or not data.get("apellido") or not data.get("matricula"):
            messagebox.showerror("Validación", "Nombre, Apellido y Matrícula son obligatorios.")
            return
        data["activo"] = 1 if self._activo_var.get() else 0
        if self._id:
            data["id"] = self._id
        models.save_odontologo(data)
        self.destroy()
