"""
login_ui.py — Ventana de inicio de sesión.
Muestra un diálogo modal antes de abrir la aplicación principal.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import models
from ui.theme import COLORS, FONTS


class LoginWindow(tk.Tk):
    """Ventana raíz de login. Tras autenticación exitosa se destruye y
    la aplicación principal puede iniciarse con el usuario autenticado."""

    def __init__(self):
        super().__init__()
        self.title("Iniciar Sesión — Consultorio Passera")
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 420) // 2
        y = (self.winfo_screenheight() - 480) // 2
        self.geometry(f"420x480+{x}+{y}")

        self.current_user = None   # se asigna al autenticar
        self._build()

    # ── Construcción ─────────────────────────────────────────────────────────

    def _build(self):
        # Cabecera con color de marca
        hdr = tk.Frame(self, bg=COLORS["sidebar_bg"], height=120)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🦷", font=("Segoe UI", 36),
                 bg=COLORS["sidebar_bg"], fg=COLORS["white"]).pack(pady=(20, 0))
        tk.Label(hdr, text="Consultorio Passera",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["sidebar_bg"], fg=COLORS["white"]).pack()

        # Formulario
        body = tk.Frame(self, bg=COLORS["bg"], padx=40, pady=30)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Iniciar Sesión",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 20))

        # Usuario
        tk.Label(body, text="Usuario", font=FONTS["body"],
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        self._username_var = tk.StringVar()
        ttk.Entry(body, textvariable=self._username_var,
                  font=FONTS["body"], width=30).pack(fill="x", pady=(2, 12))

        # Contraseña
        tk.Label(body, text="Contraseña", font=FONTS["body"],
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        self._password_var = tk.StringVar()
        self._pwd_entry = ttk.Entry(body, textvariable=self._password_var,
                                    font=FONTS["body"], width=30, show="•")
        self._pwd_entry.pack(fill="x", pady=(2, 6))

        # Mostrar/ocultar contraseña
        self._show_pwd = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text="Mostrar contraseña",
                        variable=self._show_pwd,
                        command=self._toggle_pwd).pack(anchor="w", pady=(0, 20))

        # Botón ingresar
        ttk.Button(body, text="  Ingresar  ", style="Accent.TButton",
                   command=self._login).pack(fill="x", ipady=4)

        # Pie
        tk.Label(body, text="v1.0 — UNC 2024",
                 font=FONTS["small"], bg=COLORS["bg"],
                 fg=COLORS["text_light"]).pack(side="bottom")

        # Atajos de teclado
        self.bind("<Return>",   lambda _: self._login())
        self.bind("<Escape>",   lambda _: self.destroy())
        self._username_var.trace_add("write", lambda *_: None)

    # ── Acciones ─────────────────────────────────────────────────────────────

    def _toggle_pwd(self):
        self._pwd_entry.configure(show="" if self._show_pwd.get() else "•")

    def _login(self):
        username = self._username_var.get().strip()
        password = self._password_var.get()
        if not username or not password:
            messagebox.showwarning("Datos incompletos",
                                   "Ingrese usuario y contraseña.",
                                   parent=self)
            return
        user = models.authenticate_user(username, password)
        if user:
            self.current_user = user
            self.destroy()
        else:
            messagebox.showerror("Acceso denegado",
                                 "Usuario o contraseña incorrectos.\n"
                                 "Verifique sus datos e intente de nuevo.",
                                 parent=self)
            self._password_var.set("")
            self._pwd_entry.focus_set()
