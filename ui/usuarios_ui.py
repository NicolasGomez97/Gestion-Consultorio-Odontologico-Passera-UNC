"""
usuarios_ui.py — ABM (Alta / Baja / Modificación) de usuarios del sistema.
Solo accesible para usuarios con rol 'admin'.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import models
from ui.theme import COLORS, FONTS


class UsuariosFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._selected_id: Optional[int] = None
        self._build()

    def _build(self):
        # Encabezado
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="👤  Usuarios del Sistema",
                 font=FONTS["title"],
                 bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")
        tk.Label(hdr, text="Alta, baja y modificación de cuentas de acceso",
                 font=FONTS["body"],
                 bg=COLORS["header_bg"], fg="#BEE3F8").pack(padx=20, anchor="w")

        # Área de contenido (se rellena en on_show según rol)
        self._body = tk.Frame(self, bg=COLORS["bg"])
        self._body.pack(fill="both", expand=True)

    def _build_abm(self):
        """Construye el ABM completo (solo para admin)."""
        body = self._body
        padded = tk.Frame(body, bg=COLORS["bg"], padx=16, pady=12)
        padded.pack(fill="both", expand=True)

        btn_row = tk.Frame(padded, bg=COLORS["bg"])
        btn_row.pack(fill="x", pady=(0, 8))
        ttk.Button(btn_row, text="➕ Nuevo Usuario", style="Accent.TButton",
                   command=self._new).pack(side="left", padx=4)
        ttk.Button(btn_row, text="✏️ Editar",
                   command=self._edit).pack(side="left", padx=4)
        ttk.Button(btn_row, text="🗑️ Dar de baja", style="Danger.TButton",
                   command=self._delete).pack(side="left", padx=4)

        cols = ("ID", "Usuario", "Apellido", "Nombre", "Rol", "Estado", "Creado")
        widths = (40, 130, 140, 140, 90, 70, 140)
        self._tree = ttk.Treeview(padded, columns=cols, show="headings",
                                  selectmode="browse")
        for c, w in zip(cols, widths):
            self._tree.heading(c, text=c)
            self._tree.column(c, width=w)

        scroll_y = ttk.Scrollbar(padded, orient="vertical",
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll_y.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="left", fill="y")

        self._tree.tag_configure("odd", background=COLORS["row_odd"])
        self._tree.bind("<Double-1>", lambda _: self._edit())
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._load()

    def _build_sin_permiso(self):
        tk.Label(self._body,
                 text="⛔  Solo los administradores pueden gestionar usuarios.",
                 font=FONTS["subtitle"],
                 bg=COLORS["bg"], fg=COLORS["danger"]).pack(expand=True)

    # ── Carga y selección ────────────────────────────────────────────────────

    def _load(self):
        self._tree.delete(*self._tree.get_children())
        for i, u in enumerate(models.get_usuarios(solo_activos=False)):
            tag = "odd" if i % 2 else ""
            estado = "Activo" if u.get("activo", 1) else "Baja"
            self._tree.insert("", "end", iid=str(u["id"]), tags=(tag,), values=(
                u["id"], u["username"], u["apellido"], u["nombre"],
                u["rol"].capitalize(), estado,
                u.get("created_at", "")[:10],
            ))

    def _on_select(self, _):
        sel = self._tree.selection()
        self._selected_id = int(sel[0]) if sel else None

    # ── Acciones ─────────────────────────────────────────────────────────────

    def _new(self):
        dlg = UsuarioDialog(self, None)
        self.wait_window(dlg)
        self._load()

    def _edit(self):
        if not self._selected_id:
            messagebox.showinfo("Selección", "Seleccione un usuario.")
            return
        dlg = UsuarioDialog(self, self._selected_id)
        self.wait_window(dlg)
        self._load()

    def _delete(self):
        if not self._selected_id:
            return
        from ui.app import app_state
        if app_state.current_user and app_state.current_user["id"] == self._selected_id:
            messagebox.showwarning("Operación inválida",
                                   "No puede darse de baja a sí mismo.")
            return
        if messagebox.askyesno("Confirmar", "¿Dar de baja a este usuario?"):
            models.delete_usuario(self._selected_id)
            self._selected_id = None
            self._load()

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    def on_show(self):
        from ui.app import app_state
        # Limpiar body
        for w in self._body.winfo_children():
            w.destroy()
        user = app_state.current_user
        if user and user.get("rol") == "admin":
            self._build_abm()
        else:
            self._build_sin_permiso()


# ─────────────────────────────────────────────────────────────────────────────
# DIÁLOGO DE USUARIO
# ─────────────────────────────────────────────────────────────────────────────

class UsuarioDialog(tk.Toplevel):
    def __init__(self, parent, usuario_id: Optional[int]):
        super().__init__(parent)
        self._id = usuario_id
        es_nuevo = usuario_id is None
        self.title("Nuevo Usuario" if es_nuevo else "Editar Usuario")
        self.geometry("460x420")
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        # Centrar respecto al padre
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 460) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
        self.geometry(f"460x420+{px}+{py}")

        self._data = models.get_usuario(usuario_id) if usuario_id else {}
        self._vars: dict = {}
        self._build(es_nuevo)
        self._load()

    def _build(self, es_nuevo: bool):
        frame = tk.Frame(self, bg=COLORS["bg"], padx=24, pady=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Nombre *",   "nombre"),
            ("Apellido *", "apellido"),
            ("Usuario *",  "username"),
        ]
        for i, (label, key) in enumerate(fields):
            tk.Label(frame, text=label, font=FONTS["body"],
                     bg=COLORS["bg"]).grid(row=i, column=0, sticky="e",
                                           padx=8, pady=6)
            v = tk.StringVar()
            ttk.Entry(frame, textvariable=v, width=28).grid(
                row=i, column=1, sticky="ew", padx=8)
            self._vars[key] = v

        # Contraseña
        pwd_label = "Contraseña *" if es_nuevo else "Nueva contraseña"
        tk.Label(frame, text=pwd_label, font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self._pwd_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._pwd_var,
                  width=28, show="•").grid(row=3, column=1, sticky="ew", padx=8)
        if not es_nuevo:
            tk.Label(frame, text="(dejar vacío para no cambiar)",
                     font=FONTS["small"],
                     bg=COLORS["bg"], fg=COLORS["text_light"]).grid(
                row=4, column=1, sticky="w", padx=8)

        # Rol
        row_rol = 5 if not es_nuevo else 4
        tk.Label(frame, text="Rol *", font=FONTS["body"],
                 bg=COLORS["bg"]).grid(row=row_rol, column=0,
                                       sticky="e", padx=8, pady=6)
        self._rol_var = tk.StringVar(value="operador")
        ttk.Combobox(frame, textvariable=self._rol_var,
                     values=["admin", "operador"],
                     state="readonly", width=26).grid(
            row=row_rol, column=1, sticky="ew", padx=8)

        # Activo
        row_activo = row_rol + 1
        self._activo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Activo",
                        variable=self._activo_var).grid(
            row=row_activo, column=1, sticky="w", padx=8, pady=8)

        # Botones
        btn_bar = tk.Frame(self, bg=COLORS["bg"])
        btn_bar.pack(fill="x", padx=24, pady=10)
        ttk.Button(btn_bar, text="💾 Guardar", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=4)

    def _load(self):
        for k, v in self._vars.items():
            v.set(self._data.get(k, "") or "")
        self._rol_var.set(self._data.get("rol", "operador"))
        self._activo_var.set(bool(self._data.get("activo", 1)))

    def _save(self):
        data = {k: v.get().strip() for k, v in self._vars.items()}
        password = self._pwd_var.get()

        # Validaciones
        if not data.get("nombre") or not data.get("apellido") or not data.get("username"):
            messagebox.showerror("Validación",
                                 "Nombre, Apellido y Usuario son obligatorios.",
                                 parent=self)
            return
        if not self._id and not password:
            messagebox.showerror("Validación",
                                 "Debe ingresar una contraseña para el nuevo usuario.",
                                 parent=self)
            return

        data["rol"]    = self._rol_var.get()
        data["activo"] = 1 if self._activo_var.get() else 0
        if password:
            data["password"] = password
        if self._id:
            data["id"] = self._id

        try:
            models.save_usuario(data)
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Error al guardar",
                                 f"No se pudo guardar el usuario:\n{exc}",
                                 parent=self)
